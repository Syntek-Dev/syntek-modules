#!/usr/bin/env python3
"""
log-tool.py

Provides logging configuration detection and log file analysis utilities for Claude Code agents.
Returns structured JSON output for integration with logging, backend, and debugging agents.
Supports log file discovery, configuration detection, and recent log entry extraction.
"""
import json
import sys
import os
import re
from pathlib import Path
from typing import Optional
from datetime import datetime


def find_log_files(directory: Optional[str] = None) -> dict:
    """
    Find log files in common locations.

    Args:
        directory: Directory to search (uses current directory if None)

    Returns:
        Dictionary containing found log files
    """
    search_dir = Path(directory) if directory else Path.cwd()

    if not search_dir.exists():
        return {"error": f"Directory not found: {search_dir}"}

    # Common log directories
    log_dirs = [
        "logs",
        "log",
        "storage/logs",  # Laravel
        "var/log",       # Symfony
        "runtime/logs",  # Yii
        "tmp/logs",
    ]

    found_files = []

    # Search log directories
    for log_dir in log_dirs:
        dir_path = search_dir / log_dir
        if dir_path.exists() and dir_path.is_dir():
            for log_file in dir_path.glob("*.log"):
                if log_file.is_file():
                    try:
                        stat = log_file.stat()
                        found_files.append({
                            "name": log_file.name,
                            "path": str(log_file),
                            "directory": log_dir,
                            "size": stat.st_size,
                            "size_human": _format_size(stat.st_size),
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        })
                    except PermissionError:
                        found_files.append({
                            "name": log_file.name,
                            "path": str(log_file),
                            "directory": log_dir,
                            "error": "Permission denied",
                        })

    # Also check for log files in root
    for log_file in search_dir.glob("*.log"):
        if log_file.is_file():
            try:
                stat = log_file.stat()
                found_files.append({
                    "name": log_file.name,
                    "path": str(log_file),
                    "directory": ".",
                    "size": stat.st_size,
                    "size_human": _format_size(stat.st_size),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
            except PermissionError:
                pass

    # Sort by modification time (newest first)
    found_files.sort(key=lambda x: x.get("modified", ""), reverse=True)

    return {
        "files": found_files,
        "count": len(found_files),
        "directory": str(search_dir),
    }


def _format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def detect_logging_config(directory: Optional[str] = None) -> dict:
    """
    Detect logging configuration in the project.

    Args:
        directory: Directory to search (uses current directory if None)

    Returns:
        Dictionary containing logging configuration information
    """
    search_dir = Path(directory) if directory else Path.cwd()

    if not search_dir.exists():
        return {"error": f"Directory not found: {search_dir}"}

    detected = {
        "framework": None,
        "config_file": None,
        "has_sentry": False,
        "log_channels": [],
        "log_level": None,
    }

    # Laravel logging config
    laravel_config = search_dir / "config" / "logging.php"
    if laravel_config.exists():
        detected["framework"] = "laravel"
        detected["config_file"] = str(laravel_config)
        try:
            content = laravel_config.read_text()
            # Extract channels
            channels = re.findall(r"'(\w+)'\s*=>\s*\[", content)
            detected["log_channels"] = [c for c in channels if c not in ['driver', 'level', 'path']]
        except Exception:
            pass

    # Check for Sentry in various config files
    sentry_indicators = [
        ".env",
        "config/sentry.php",
        "config/services.php",
        "package.json",
        "requirements.txt",
        "composer.json",
    ]

    for indicator in sentry_indicators:
        path = search_dir / indicator
        if path.exists():
            try:
                content = path.read_text().lower()
                if "sentry" in content:
                    detected["has_sentry"] = True
                    break
            except Exception:
                pass

    # Django logging
    django_settings = list(search_dir.glob("**/settings.py"))
    if django_settings:
        detected["framework"] = detected["framework"] or "django"
        for settings_file in django_settings:
            try:
                content = settings_file.read_text()
                if "LOGGING" in content:
                    detected["config_file"] = str(settings_file)
                    break
            except Exception:
                pass

    # Node.js logging (winston, pino, etc.)
    package_json = search_dir / "package.json"
    if package_json.exists():
        try:
            content = package_json.read_text().lower()
            if "winston" in content:
                detected["framework"] = detected["framework"] or "winston"
            elif "pino" in content:
                detected["framework"] = detected["framework"] or "pino"
            elif "bunyan" in content:
                detected["framework"] = detected["framework"] or "bunyan"
        except Exception:
            pass

    # Check .env for log level
    env_file = search_dir / ".env"
    if env_file.exists():
        try:
            content = env_file.read_text()
            level_match = re.search(r'LOG_LEVEL\s*=\s*(\w+)', content, re.IGNORECASE)
            if level_match:
                detected["log_level"] = level_match.group(1)
        except Exception:
            pass

    detected["detected"] = detected["framework"] is not None or detected["has_sentry"]

    return detected


def read_recent_logs(file_path: str, lines: int = 50, level_filter: Optional[str] = None) -> dict:
    """
    Read recent entries from a log file.

    Args:
        file_path: Path to the log file
        lines: Number of lines to read from the end
        level_filter: Optional filter for log level (ERROR, WARNING, etc.)

    Returns:
        Dictionary containing log entries
    """
    path = Path(file_path)

    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    if not path.is_file():
        return {"error": f"Not a file: {file_path}"}

    try:
        # Read last N lines efficiently
        with open(path, 'rb') as f:
            # Seek to end and work backwards
            f.seek(0, 2)
            file_size = f.tell()

            if file_size == 0:
                return {"file": file_path, "entries": [], "count": 0, "empty": True}

            # Read chunks from end to find enough lines
            chunk_size = 8192
            found_lines = []
            position = file_size

            while len(found_lines) <= lines and position > 0:
                read_size = min(chunk_size, position)
                position -= read_size
                f.seek(position)
                chunk = f.read(read_size).decode('utf-8', errors='replace')
                found_lines = chunk.split('\n') + found_lines[1:]

            log_lines = found_lines[-lines:] if len(found_lines) > lines else found_lines

        # Parse log entries
        entries = []
        log_patterns = [
            # Laravel/Monolog format
            r'\[(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[^\]]*)\]\s*(\w+)\.(\w+):\s*(.*)',
            # Standard format
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(\w+)\s+(.+)',
            # Simple timestamp
            r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]\s+\[(\w+)\]\s+(.*)',
        ]

        for line in log_lines:
            if not line.strip():
                continue

            parsed = False
            for pattern in log_patterns:
                match = re.match(pattern, line)
                if match:
                    groups = match.groups()
                    entry = {
                        "timestamp": groups[0],
                        "level": groups[1].upper() if len(groups) > 1 else "INFO",
                        "message": groups[-1][:500],  # Truncate long messages
                    }

                    # Apply level filter if specified
                    if level_filter:
                        if entry["level"] != level_filter.upper():
                            continue

                    entries.append(entry)
                    parsed = True
                    break

            # If no pattern matched, include as raw line
            if not parsed and line.strip():
                entries.append({
                    "raw": line[:500],
                    "level": "UNKNOWN",
                })

        # Categorise by level
        level_counts = {}
        for entry in entries:
            level = entry.get("level", "UNKNOWN")
            level_counts[level] = level_counts.get(level, 0) + 1

        return {
            "file": file_path,
            "entries": entries,
            "count": len(entries),
            "level_counts": level_counts,
            "filter_applied": level_filter,
        }

    except Exception as e:
        return {"error": f"Failed to read log file: {e}"}


def analyse_errors(file_path: str, max_entries: int = 100) -> dict:
    """
    Analyse error patterns in a log file.

    Args:
        file_path: Path to the log file
        max_entries: Maximum number of entries to analyse

    Returns:
        Dictionary containing error analysis
    """
    # Read recent logs with error filter
    logs = read_recent_logs(file_path, lines=max_entries * 5)

    if "error" in logs:
        return logs

    error_levels = ["ERROR", "CRITICAL", "FATAL", "EMERGENCY"]
    errors = [e for e in logs.get("entries", []) if e.get("level") in error_levels]

    # Group similar errors
    error_groups = {}
    for error in errors:
        message = error.get("message", error.get("raw", ""))
        # Simplify message for grouping (remove variable parts)
        simplified = re.sub(r'\d+', 'N', message)
        simplified = re.sub(r'"[^"]*"', '"..."', simplified)
        simplified = simplified[:100]

        if simplified not in error_groups:
            error_groups[simplified] = {
                "pattern": simplified,
                "count": 0,
                "first_occurrence": error.get("timestamp"),
                "last_occurrence": error.get("timestamp"),
                "sample": message[:200],
            }

        error_groups[simplified]["count"] += 1
        error_groups[simplified]["last_occurrence"] = error.get("timestamp")

    # Sort by count
    sorted_groups = sorted(error_groups.values(), key=lambda x: x["count"], reverse=True)

    return {
        "file": file_path,
        "total_errors": len(errors),
        "unique_patterns": len(error_groups),
        "error_groups": sorted_groups[:20],  # Top 20 error patterns
    }


def check_log_health(directory: Optional[str] = None) -> dict:
    """
    Check the health of logging in the project.

    Args:
        directory: Directory to check (uses current directory if None)

    Returns:
        Dictionary containing health check results
    """
    search_dir = Path(directory) if directory else Path.cwd()

    if not search_dir.exists():
        return {"error": f"Directory not found: {search_dir}"}

    issues = []
    warnings = []
    suggestions = []

    # Check for logging configuration
    config = detect_logging_config(str(search_dir))

    if not config.get("detected"):
        issues.append("No logging configuration detected")
        suggestions.append("Configure a logging framework (Laravel logging, Winston, Pino, etc.)")

    if not config.get("has_sentry"):
        suggestions.append("Consider adding Sentry for production error tracking")

    # Check for log files
    logs = find_log_files(str(search_dir))

    if logs.get("count", 0) == 0:
        warnings.append("No log files found - logs may not be persisted")

    # Check log file sizes
    large_logs = []
    for log_file in logs.get("files", []):
        size = log_file.get("size", 0)
        if size > 100 * 1024 * 1024:  # > 100MB
            large_logs.append({
                "name": log_file["name"],
                "size": log_file["size_human"],
            })

    if large_logs:
        warnings.append(f"Large log files detected: {len(large_logs)} files over 100MB")
        suggestions.append("Implement log rotation to manage log file sizes")

    # Check .gitignore for logs
    gitignore = search_dir / ".gitignore"
    if gitignore.exists():
        try:
            content = gitignore.read_text()
            if "*.log" not in content and "logs/" not in content:
                warnings.append("Log files may not be gitignored")
                suggestions.append("Add '*.log' and 'logs/' to .gitignore")
        except Exception:
            pass

    return {
        "healthy": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "suggestions": suggestions,
        "log_file_count": logs.get("count", 0),
        "logging_framework": config.get("framework"),
        "has_sentry": config.get("has_sentry", False),
    }


def main():
    """Main entry point for the Log tool."""
    if len(sys.argv) < 2:
        # Default: find log files
        print(json.dumps(find_log_files(), indent=2))
        return

    command = sys.argv[1].lower()

    if command == "find":
        directory = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(find_log_files(directory), indent=2))

    elif command == "config":
        directory = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(detect_logging_config(directory), indent=2))

    elif command == "read":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "File path required"}, indent=2))
            return
        file_path = sys.argv[2]
        lines = 50
        level_filter = None

        for arg in sys.argv[3:]:
            if arg.isdigit():
                lines = int(arg)
            elif arg.upper() in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                level_filter = arg

        print(json.dumps(read_recent_logs(file_path, lines, level_filter), indent=2))

    elif command == "errors":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "File path required"}, indent=2))
            return
        print(json.dumps(analyse_errors(sys.argv[2]), indent=2))

    elif command == "health":
        directory = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(check_log_health(directory), indent=2))

    else:
        print(json.dumps({
            "error": f"Unknown command: {command}",
            "available_commands": ["find", "config", "read", "errors", "health"]
        }, indent=2))


if __name__ == "__main__":
    main()
