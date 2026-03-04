#!/usr/bin/env python3
"""
ddev-tool.py

Provides DDEV project status and management utilities for Claude Code agents.
Returns structured JSON output for integration with setup, cicd, and backend agents.
Supports project listing, service status, and configuration detection.
"""
import subprocess
import json
import sys
import shutil
from typing import Optional


def is_ddev_installed() -> bool:
    """Check if DDEV is installed and available in PATH."""
    return shutil.which("ddev") is not None


def run_ddev_command(args: list[str], timeout: int = 30) -> tuple[bool, str, str]:
    """
    Execute a DDEV command and return the result.

    Args:
        args: List of command arguments to pass to ddev
        timeout: Command timeout in seconds

    Returns:
        Tuple of (success, stdout, stderr)
    """
    try:
        result = subprocess.run(
            ["ddev"] + args,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except FileNotFoundError:
        return False, "", "DDEV is not installed"
    except Exception as e:
        return False, "", str(e)


def get_ddev_status() -> dict:
    """
    Return running DDEV projects in JSON format.

    Returns:
        Dictionary containing projects list or error information
    """
    if not is_ddev_installed():
        return {"error": "DDEV is not installed", "installed": False}

    success, stdout, stderr = run_ddev_command(["list", "-j"])

    if not success:
        return {"error": stderr or "Failed to get DDEV status", "installed": True}

    try:
        data = json.loads(stdout)
        projects = []

        for proj in data.get("raw", []):
            projects.append({
                "name": proj.get("name"),
                "status": proj.get("status"),
                "url": proj.get("httpurl"),
                "https_url": proj.get("httpsurl"),
                "type": proj.get("type"),
                "php_version": proj.get("php_version"),
                "webserver": proj.get("webserver_type"),
                "database": proj.get("dbinfo", {}).get("type") if isinstance(proj.get("dbinfo"), dict) else None,
                "nodejs_version": proj.get("nodejs_version"),
                "mutagen_enabled": proj.get("mutagen_enabled", False),
            })

        return {
            "installed": True,
            "projects": projects,
            "count": len(projects),
            "running": sum(1 for p in projects if p.get("status") == "running")
        }
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse DDEV output: {e}", "installed": True}


def get_project_config(project_name: Optional[str] = None) -> dict:
    """
    Get detailed configuration for a specific DDEV project.

    Args:
        project_name: Name of the project (uses current directory if None)

    Returns:
        Dictionary containing project configuration or error
    """
    if not is_ddev_installed():
        return {"error": "DDEV is not installed", "installed": False}

    args = ["describe", "-j"]
    if project_name:
        args.extend(["-p", project_name])

    success, stdout, stderr = run_ddev_command(args)

    if not success:
        return {"error": stderr or "Project not found or not configured"}

    try:
        data = json.loads(stdout)
        raw = data.get("raw", {})

        return {
            "name": raw.get("name"),
            "type": raw.get("type"),
            "docroot": raw.get("docroot"),
            "php_version": raw.get("php_version"),
            "webserver": raw.get("webserver_type"),
            "database": raw.get("database", {}).get("type"),
            "database_version": raw.get("database", {}).get("version"),
            "nodejs_version": raw.get("nodejs_version"),
            "composer_version": raw.get("composer_version"),
            "router_http_port": raw.get("router_http_port"),
            "router_https_port": raw.get("router_https_port"),
            "mailpit_http_port": raw.get("mailpit_http_port"),
            "xdebug_enabled": raw.get("xdebug_enabled", False),
            "mutagen_enabled": raw.get("mutagen_enabled", False),
            "primary_url": raw.get("primary_url"),
            "approot": raw.get("approot"),
        }
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse project config: {e}"}


def get_ddev_services() -> dict:
    """
    Get status of DDEV services including custom services.

    Returns:
        Dictionary containing services information
    """
    if not is_ddev_installed():
        return {"error": "DDEV is not installed", "installed": False}

    success, stdout, stderr = run_ddev_command(["describe", "-j"])

    if not success:
        return {"error": stderr or "No active DDEV project in current directory"}

    try:
        data = json.loads(stdout)
        raw = data.get("raw", {})
        services = []

        # Core services
        if raw.get("status") == "running":
            services.append({
                "name": "web",
                "type": "webserver",
                "status": "running",
                "ports": f"{raw.get('router_http_port', 80)}, {raw.get('router_https_port', 443)}"
            })
            services.append({
                "name": "db",
                "type": "database",
                "status": "running",
                "engine": raw.get("database", {}).get("type")
            })

        # Additional services from docker-compose files
        extra_services = raw.get("extra_services", [])
        for svc in extra_services:
            services.append({
                "name": svc.get("name"),
                "type": "custom",
                "status": svc.get("status", "unknown"),
                "image": svc.get("image")
            })

        return {
            "project": raw.get("name"),
            "services": services,
            "count": len(services)
        }
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse services: {e}"}


def main():
    """Main entry point for the DDEV tool."""
    if len(sys.argv) < 2:
        # Default: return project status
        print(json.dumps(get_ddev_status(), indent=2))
        return

    command = sys.argv[1].lower()

    if command == "status":
        print(json.dumps(get_ddev_status(), indent=2))
    elif command == "config":
        project_name = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(get_project_config(project_name), indent=2))
    elif command == "services":
        print(json.dumps(get_ddev_services(), indent=2))
    elif command == "installed":
        print(json.dumps({"installed": is_ddev_installed()}, indent=2))
    else:
        print(json.dumps({
            "error": f"Unknown command: {command}",
            "available_commands": ["status", "config", "services", "installed"]
        }, indent=2))


if __name__ == "__main__":
    main()
