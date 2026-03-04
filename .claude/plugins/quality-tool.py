#!/usr/bin/env python3
"""
quality-tool.py

Measures code quality metrics by running linters and analysing code.
Supports PHP (phpstan/pint), Python (ruff/black), and JavaScript/TypeScript (eslint).
Used to track quality changes before and after agent modifications.
"""
import subprocess
import json
import sys
import os
from pathlib import Path
from typing import Optional


def detect_stack() -> dict:
    """Detect the project stack based on configuration files."""
    cwd = Path(os.getcwd())

    stack = {
        "language": None,
        "framework": None,
        "linter": None,
        "linter_command": None,
    }

    # Check for PHP/Laravel
    if (cwd / "composer.json").exists():
        stack["language"] = "php"
        if (cwd / "artisan").exists():
            stack["framework"] = "laravel"
        # Check for phpstan
        if (cwd / "phpstan.neon").exists() or (cwd / "phpstan.neon.dist").exists():
            stack["linter"] = "phpstan"
            stack["linter_command"] = ["vendor/bin/phpstan", "analyse", "--error-format=json", "--no-progress"]
        elif (cwd / "vendor/bin/pint").exists():
            stack["linter"] = "pint"
            stack["linter_command"] = ["vendor/bin/pint", "--test", "--format=json"]

    # Check for Python/Django
    elif (cwd / "requirements.txt").exists() or (cwd / "pyproject.toml").exists():
        stack["language"] = "python"
        if (cwd / "manage.py").exists():
            stack["framework"] = "django"
        # Check for ruff
        if (cwd / "ruff.toml").exists() or (cwd / "pyproject.toml").exists():
            stack["linter"] = "ruff"
            stack["linter_command"] = ["ruff", "check", "--output-format=json", "."]

    # Check for Node.js/React
    elif (cwd / "package.json").exists():
        stack["language"] = "javascript"
        pkg_json = cwd / "package.json"
        with open(pkg_json, "r") as f:
            pkg = json.load(f)
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

        if "next" in deps:
            stack["framework"] = "nextjs"
        elif "react" in deps:
            stack["framework"] = "react"

        if "typescript" in deps:
            stack["language"] = "typescript"

        # Check for eslint
        if (cwd / ".eslintrc.js").exists() or (cwd / ".eslintrc.json").exists() or (cwd / "eslint.config.js").exists():
            stack["linter"] = "eslint"
            stack["linter_command"] = ["npx", "eslint", "--format=json", "."]

    return stack


def run_linter(files: Optional[list] = None) -> dict:
    """
    Run the detected linter and return error counts.

    Args:
        files: Specific files to lint (default: entire project)

    Returns:
        Linting results with error counts
    """
    stack = detect_stack()

    if not stack["linter"]:
        return {
            "success": False,
            "error": "No linter detected",
            "stack": stack,
        }

    command = stack["linter_command"].copy()

    # Add specific files if provided
    if files and stack["linter"] != "pint":
        command.extend(files)

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=os.getcwd(),
        )

        # Parse output based on linter
        errors = 0
        warnings = 0
        details = []

        if stack["linter"] == "phpstan":
            try:
                data = json.loads(result.stdout)
                errors = data.get("totals", {}).get("errors", 0)
                warnings = data.get("totals", {}).get("warnings", 0)
                for file_path, file_errors in data.get("files", {}).items():
                    for msg in file_errors.get("messages", []):
                        details.append({
                            "file": file_path,
                            "line": msg.get("line"),
                            "message": msg.get("message"),
                            "type": "error" if msg.get("ignorable", True) else "warning",
                        })
            except json.JSONDecodeError:
                errors = result.returncode

        elif stack["linter"] == "ruff":
            try:
                data = json.loads(result.stdout) if result.stdout else []
                errors = len([d for d in data if d.get("type") == "error"])
                warnings = len([d for d in data if d.get("type") == "warning"])
                for item in data[:20]:  # Limit details
                    details.append({
                        "file": item.get("filename"),
                        "line": item.get("location", {}).get("row"),
                        "message": item.get("message"),
                        "code": item.get("code"),
                    })
            except json.JSONDecodeError:
                errors = result.returncode

        elif stack["linter"] == "eslint":
            try:
                data = json.loads(result.stdout) if result.stdout else []
                for file_result in data:
                    errors += file_result.get("errorCount", 0)
                    warnings += file_result.get("warningCount", 0)
                    for msg in file_result.get("messages", [])[:5]:
                        details.append({
                            "file": file_result.get("filePath"),
                            "line": msg.get("line"),
                            "message": msg.get("message"),
                            "rule": msg.get("ruleId"),
                        })
            except json.JSONDecodeError:
                errors = result.returncode

        elif stack["linter"] == "pint":
            # Pint returns exit code 1 if there are changes needed
            errors = result.returncode
            if result.stdout:
                details.append({"message": result.stdout[:500]})

        return {
            "success": True,
            "linter": stack["linter"],
            "errors": errors,
            "warnings": warnings,
            "exit_code": result.returncode,
            "details": details[:10],  # Limit to 10 details
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Linter timed out"}
    except FileNotFoundError:
        return {"success": False, "error": f"Linter not found: {stack['linter']}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def check_quality(files: Optional[list] = None) -> dict:
    """
    Run a comprehensive quality check.

    Args:
        files: Specific files to check

    Returns:
        Quality check results
    """
    stack = detect_stack()
    linter_result = run_linter(files)

    return {
        "stack": stack,
        "linting": linter_result,
        "summary": {
            "has_linter": stack["linter"] is not None,
            "total_errors": linter_result.get("errors", 0) if linter_result.get("success") else None,
            "total_warnings": linter_result.get("warnings", 0) if linter_result.get("success") else None,
        },
    }


def compare_quality(before: dict, after: dict) -> dict:
    """
    Compare quality metrics before and after changes.

    Args:
        before: Quality check before changes
        after: Quality check after changes

    Returns:
        Comparison results
    """
    before_errors = before.get("summary", {}).get("total_errors", 0) or 0
    after_errors = after.get("summary", {}).get("total_errors", 0) or 0

    before_warnings = before.get("summary", {}).get("total_warnings", 0) or 0
    after_warnings = after.get("summary", {}).get("total_warnings", 0) or 0

    error_delta = after_errors - before_errors
    warning_delta = after_warnings - before_warnings

    # Determine quality change
    if error_delta < 0:
        quality_change = "improved"
    elif error_delta > 0:
        quality_change = "degraded"
    else:
        quality_change = "unchanged"

    return {
        "before": {
            "errors": before_errors,
            "warnings": before_warnings,
        },
        "after": {
            "errors": after_errors,
            "warnings": after_warnings,
        },
        "delta": {
            "errors": error_delta,
            "warnings": warning_delta,
        },
        "quality_change": quality_change,
    }


def get_status() -> dict:
    """Get the current quality tool status."""
    stack = detect_stack()

    return {
        "stack": stack,
        "linter_available": stack["linter"] is not None,
        "linter": stack["linter"],
    }


def main():
    """Main entry point for the quality tool."""
    if len(sys.argv) < 2:
        print(json.dumps(get_status(), indent=2))
        return

    command = sys.argv[1].lower()

    if command == "status":
        print(json.dumps(get_status(), indent=2))

    elif command == "check":
        files = sys.argv[2:] if len(sys.argv) > 2 else None
        result = check_quality(files)
        print(json.dumps(result, indent=2))

    elif command == "lint":
        files = sys.argv[2:] if len(sys.argv) > 2 else None
        result = run_linter(files)
        print(json.dumps(result, indent=2))

    elif command == "stack":
        print(json.dumps(detect_stack(), indent=2))

    else:
        print(json.dumps({
            "error": f"Unknown command: {command}",
            "available_commands": ["status", "check", "lint", "stack"]
        }, indent=2))


if __name__ == "__main__":
    main()
