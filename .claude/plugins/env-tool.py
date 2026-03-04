#!/usr/bin/env python3
"""
env-tool.py

Provides environment file management utilities for Claude Code agents.
Returns structured JSON output for integration with setup, backend, and cicd agents.
Supports reading, comparing, and validating environment files across environments.
"""
import json
import sys
import os
import re
from pathlib import Path
from typing import Optional


def find_env_files(directory: Optional[str] = None) -> dict:
    """
    Find all environment files in the specified directory.

    Args:
        directory: Directory to search (uses current directory if None)

    Returns:
        Dictionary containing found environment files
    """
    search_dir = Path(directory) if directory else Path.cwd()

    if not search_dir.exists():
        return {"error": f"Directory not found: {search_dir}"}

    env_patterns = [
        ".env",
        ".env.*",
        "*.env",
    ]

    env_files = []
    for pattern in env_patterns:
        for file_path in search_dir.glob(pattern):
            if file_path.is_file():
                # Determine environment type
                name = file_path.name
                env_type = "unknown"

                if name == ".env":
                    env_type = "default"
                elif "example" in name.lower() or "sample" in name.lower():
                    env_type = "example"
                elif "dev" in name.lower() or "development" in name.lower():
                    env_type = "development"
                elif "staging" in name.lower() or "stage" in name.lower():
                    env_type = "staging"
                elif "prod" in name.lower() or "production" in name.lower():
                    env_type = "production"
                elif "test" in name.lower():
                    env_type = "test"
                elif "local" in name.lower():
                    env_type = "local"

                env_files.append({
                    "name": name,
                    "path": str(file_path),
                    "type": env_type,
                    "size": file_path.stat().st_size,
                    "is_example": "example" in name.lower() or "sample" in name.lower(),
                })

    # Sort by type priority
    type_order = ["default", "development", "staging", "production", "test", "local", "example", "unknown"]
    env_files.sort(key=lambda x: (type_order.index(x["type"]) if x["type"] in type_order else 99, x["name"]))

    return {
        "files": env_files,
        "count": len(env_files),
        "directory": str(search_dir)
    }


def parse_env_file(file_path: str) -> dict:
    """
    Parse an environment file and extract variables.

    Args:
        file_path: Path to the environment file

    Returns:
        Dictionary containing parsed variables (values masked for security)
    """
    path = Path(file_path)

    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    if not path.is_file():
        return {"error": f"Not a file: {file_path}"}

    variables = []
    comments = []
    line_count = 0
    empty_lines = 0

    # Patterns for sensitive keys
    sensitive_patterns = [
        r"password", r"secret", r"key", r"token", r"api_key", r"apikey",
        r"auth", r"credential", r"private", r"access", r"bearer"
    ]

    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line_count += 1
                stripped = line.strip()

                if not stripped:
                    empty_lines += 1
                    continue

                if stripped.startswith('#'):
                    comments.append({
                        "line": line_num,
                        "content": stripped[1:].strip()
                    })
                    continue

                # Parse variable assignment
                if '=' in stripped:
                    key, _, value = stripped.partition('=')
                    key = key.strip()
                    value = value.strip()

                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]

                    # Determine if sensitive
                    is_sensitive = any(
                        re.search(pattern, key, re.IGNORECASE)
                        for pattern in sensitive_patterns
                    )

                    # Mask sensitive values
                    if is_sensitive and value:
                        masked_value = value[:2] + "*" * (len(value) - 4) + value[-2:] if len(value) > 4 else "****"
                    else:
                        masked_value = value

                    variables.append({
                        "key": key,
                        "value": masked_value,
                        "line": line_num,
                        "is_sensitive": is_sensitive,
                        "is_empty": not value,
                        "has_placeholder": value.startswith("${") or value.startswith("$"),
                    })

        return {
            "file": str(path),
            "variables": variables,
            "variable_count": len(variables),
            "comment_count": len(comments),
            "line_count": line_count,
            "empty_lines": empty_lines,
            "sensitive_count": sum(1 for v in variables if v["is_sensitive"]),
            "empty_value_count": sum(1 for v in variables if v["is_empty"]),
        }

    except Exception as e:
        return {"error": f"Failed to parse file: {e}"}


def compare_env_files(file1: str, file2: str) -> dict:
    """
    Compare two environment files and find differences.

    Args:
        file1: Path to first environment file
        file2: Path to second environment file

    Returns:
        Dictionary containing comparison results
    """
    parsed1 = parse_env_file(file1)
    parsed2 = parse_env_file(file2)

    if "error" in parsed1:
        return parsed1
    if "error" in parsed2:
        return parsed2

    vars1 = {v["key"]: v for v in parsed1["variables"]}
    vars2 = {v["key"]: v for v in parsed2["variables"]}

    keys1 = set(vars1.keys())
    keys2 = set(vars2.keys())

    only_in_first = sorted(keys1 - keys2)
    only_in_second = sorted(keys2 - keys1)
    common = sorted(keys1 & keys2)

    # Find value differences in common keys
    different_values = []
    for key in common:
        # Compare actual empty status, not masked values
        if vars1[key]["is_empty"] != vars2[key]["is_empty"]:
            different_values.append({
                "key": key,
                "in_first": "empty" if vars1[key]["is_empty"] else "has value",
                "in_second": "empty" if vars2[key]["is_empty"] else "has value",
            })

    return {
        "file1": file1,
        "file2": file2,
        "only_in_first": only_in_first,
        "only_in_second": only_in_second,
        "common_count": len(common),
        "different_values": different_values,
        "missing_in_first": len(only_in_second),
        "missing_in_second": len(only_in_first),
        "is_synced": len(only_in_first) == 0 and len(only_in_second) == 0,
    }


def validate_env_file(file_path: str, example_file: Optional[str] = None) -> dict:
    """
    Validate an environment file against an example file or common requirements.

    Args:
        file_path: Path to the environment file to validate
        example_file: Optional path to example file to compare against

    Returns:
        Dictionary containing validation results
    """
    parsed = parse_env_file(file_path)

    if "error" in parsed:
        return parsed

    issues = []
    warnings = []

    # Check for empty sensitive values
    for var in parsed["variables"]:
        if var["is_sensitive"] and var["is_empty"]:
            issues.append({
                "type": "empty_sensitive",
                "key": var["key"],
                "line": var["line"],
                "message": f"Sensitive variable '{var['key']}' has no value"
            })

        if var["has_placeholder"]:
            warnings.append({
                "type": "placeholder",
                "key": var["key"],
                "line": var["line"],
                "message": f"Variable '{var['key']}' contains a placeholder reference"
            })

    # Compare against example file if provided
    missing_from_example = []
    extra_not_in_example = []

    if example_file:
        comparison = compare_env_files(example_file, file_path)
        if "error" not in comparison:
            missing_from_example = comparison["only_in_first"]
            extra_not_in_example = comparison["only_in_second"]

            for key in missing_from_example:
                issues.append({
                    "type": "missing",
                    "key": key,
                    "message": f"Variable '{key}' is in example but missing from env file"
                })

            for key in extra_not_in_example:
                warnings.append({
                    "type": "extra",
                    "key": key,
                    "message": f"Variable '{key}' is not in example file"
                })

    return {
        "file": file_path,
        "example_file": example_file,
        "is_valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "issue_count": len(issues),
        "warning_count": len(warnings),
        "variable_count": parsed["variable_count"],
    }


def get_required_vars(file_path: str) -> dict:
    """
    Extract list of required environment variables from a file.

    Args:
        file_path: Path to the environment file

    Returns:
        Dictionary containing required variables list
    """
    parsed = parse_env_file(file_path)

    if "error" in parsed:
        return parsed

    # Group variables by category based on common prefixes
    categories = {}
    for var in parsed["variables"]:
        key = var["key"]
        prefix = key.split("_")[0] if "_" in key else "GENERAL"

        if prefix not in categories:
            categories[prefix] = []

        categories[prefix].append({
            "key": key,
            "is_sensitive": var["is_sensitive"],
            "is_empty": var["is_empty"],
        })

    return {
        "file": file_path,
        "categories": categories,
        "total_variables": parsed["variable_count"],
        "sensitive_variables": parsed["sensitive_count"],
    }


def main():
    """Main entry point for the Environment tool."""
    if len(sys.argv) < 2:
        # Default: find env files in current directory
        print(json.dumps(find_env_files(), indent=2))
        return

    command = sys.argv[1].lower()

    if command == "find":
        directory = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(find_env_files(directory), indent=2))

    elif command == "parse":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "File path required"}, indent=2))
            return
        print(json.dumps(parse_env_file(sys.argv[2]), indent=2))

    elif command == "compare":
        if len(sys.argv) < 4:
            print(json.dumps({"error": "Two file paths required"}, indent=2))
            return
        print(json.dumps(compare_env_files(sys.argv[2], sys.argv[3]), indent=2))

    elif command == "validate":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "File path required"}, indent=2))
            return
        example = sys.argv[3] if len(sys.argv) > 3 else None
        print(json.dumps(validate_env_file(sys.argv[2], example), indent=2))

    elif command == "vars":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "File path required"}, indent=2))
            return
        print(json.dumps(get_required_vars(sys.argv[2]), indent=2))

    else:
        print(json.dumps({
            "error": f"Unknown command: {command}",
            "available_commands": ["find", "parse", "compare", "validate", "vars"]
        }, indent=2))


if __name__ == "__main__":
    main()
