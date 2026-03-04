#!/usr/bin/env python3
"""
pm-tool.py

Detects and analyses project management tool configurations for Claude Code agents.
Returns structured JSON output for integration with the PM setup agent.
Supports ClickUp, Linear, Jira, GitHub Projects, Monday.com, Asana, Trello,
Notion, Azure DevOps, Shortcut, and other PM tools.
"""
import json
import sys
import os
from pathlib import Path
from typing import Optional


# PM tool detection configurations
PM_TOOLS = {
    "clickup": {
        "name": "ClickUp",
        "config_files": [".clickup.json", "clickup.config.json", ".clickuprc"],
        "env_vars": ["CLICKUP_API_KEY", "CLICKUP_TOKEN", "CLICKUP_WORKSPACE_ID"],
        "api_type": "REST",
        "tier": 1,
        "docs_url": "https://clickup.com/api",
    },
    "linear": {
        "name": "Linear",
        "config_files": [".linear.json", "linear.config.json", ".linearrc"],
        "env_vars": ["LINEAR_API_KEY", "LINEAR_TOKEN", "LINEAR_TEAM_ID"],
        "api_type": "GraphQL",
        "tier": 1,
        "docs_url": "https://developers.linear.app/docs",
    },
    "jira": {
        "name": "Jira",
        "config_files": [".jira.json", "jira.config.json", ".jirarc", "atlassian.json"],
        "env_vars": ["JIRA_API_TOKEN", "JIRA_HOST", "JIRA_EMAIL", "JIRA_PROJECT_KEY", "ATLASSIAN_TOKEN"],
        "api_type": "REST",
        "tier": 1,
        "docs_url": "https://developer.atlassian.com/cloud/jira/platform/rest/v3/",
    },
    "github_projects": {
        "name": "GitHub Projects",
        "config_files": [".github/project.json", ".github/projects.yml", ".github-projects.json"],
        "env_vars": ["GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PROJECT_NUMBER"],
        "api_type": "GraphQL",
        "tier": 1,
        "docs_url": "https://docs.github.com/en/graphql",
    },
    "monday": {
        "name": "Monday.com",
        "config_files": [".monday.json", "monday.config.json", ".mondayrc"],
        "env_vars": ["MONDAY_API_KEY", "MONDAY_TOKEN", "MONDAY_BOARD_ID"],
        "api_type": "GraphQL",
        "tier": 2,
        "docs_url": "https://developer.monday.com/api-reference/",
    },
    "asana": {
        "name": "Asana",
        "config_files": [".asana.json", "asana.config.json", ".asanarc"],
        "env_vars": ["ASANA_ACCESS_TOKEN", "ASANA_TOKEN", "ASANA_WORKSPACE_ID", "ASANA_PROJECT_ID"],
        "api_type": "REST",
        "tier": 2,
        "docs_url": "https://developers.asana.com/docs",
    },
    "trello": {
        "name": "Trello",
        "config_files": [".trello.json", "trello.config.json", ".trellorc"],
        "env_vars": ["TRELLO_API_KEY", "TRELLO_TOKEN", "TRELLO_BOARD_ID"],
        "api_type": "REST",
        "tier": 2,
        "docs_url": "https://developer.atlassian.com/cloud/trello/rest/",
    },
    "notion": {
        "name": "Notion",
        "config_files": [".notion.json", "notion.config.json", ".notionrc"],
        "env_vars": ["NOTION_API_KEY", "NOTION_TOKEN", "NOTION_DATABASE_ID"],
        "api_type": "REST",
        "tier": 2,
        "docs_url": "https://developers.notion.com/",
    },
    "azure_devops": {
        "name": "Azure DevOps",
        "config_files": [".azure-devops.json", "azure-devops.config.json", ".azuredevopsrc"],
        "env_vars": ["AZURE_DEVOPS_PAT", "AZURE_DEVOPS_ORG", "AZURE_DEVOPS_PROJECT"],
        "api_type": "REST",
        "tier": 3,
        "docs_url": "https://docs.microsoft.com/en-us/rest/api/azure/devops/",
    },
    "shortcut": {
        "name": "Shortcut",
        "config_files": [".shortcut.json", "shortcut.config.json", ".shortcutrc", ".clubhouse.json"],
        "env_vars": ["SHORTCUT_API_TOKEN", "CLUBHOUSE_TOKEN", "SHORTCUT_WORKSPACE_ID"],
        "api_type": "REST",
        "tier": 3,
        "docs_url": "https://developer.shortcut.com/api/",
    },
    "basecamp": {
        "name": "Basecamp",
        "config_files": [".basecamp.json", "basecamp.config.json", ".basecamprc"],
        "env_vars": ["BASECAMP_ACCESS_TOKEN", "BASECAMP_ACCOUNT_ID"],
        "api_type": "REST",
        "tier": 3,
        "docs_url": "https://github.com/basecamp/bc3-api",
    },
    "wrike": {
        "name": "Wrike",
        "config_files": [".wrike.json", "wrike.config.json", ".wrikerc"],
        "env_vars": ["WRIKE_ACCESS_TOKEN", "WRIKE_TOKEN"],
        "api_type": "REST",
        "tier": 3,
        "docs_url": "https://developers.wrike.com/",
    },
    "height": {
        "name": "Height",
        "config_files": [".height.json", "height.config.json"],
        "env_vars": ["HEIGHT_API_KEY", "HEIGHT_TOKEN"],
        "api_type": "REST",
        "tier": 3,
        "docs_url": "https://height.notion.site/Height-API",
    },
    "plane": {
        "name": "Plane",
        "config_files": [".plane.json", "plane.config.json"],
        "env_vars": ["PLANE_API_KEY", "PLANE_TOKEN"],
        "api_type": "REST",
        "tier": 3,
        "docs_url": "https://docs.plane.so/api-reference/",
    },
}


def load_env_file(env_path: Path) -> dict:
    """
    Load environment variables from a .env file.

    Args:
        env_path: Path to the .env file

    Returns:
        Dictionary of environment variables
    """
    env_vars = {}
    if not env_path.exists():
        return env_vars

    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    env_vars[key] = value
    except Exception:
        pass

    return env_vars


def detect_pm_tool(directory: Optional[str] = None) -> dict:
    """
    Detect which PM tool is configured in the project.

    Args:
        directory: Directory to analyse (uses current directory if None)

    Returns:
        Dictionary containing detected PM tool information
    """
    search_dir = Path(directory) if directory else Path.cwd()

    if not search_dir.exists():
        return {"error": f"Directory not found: {search_dir}"}

    # Load environment variables from various .env files
    env_files = [
        ".env",
        ".env.local",
        ".env.dev",
        ".env.development",
        ".env.staging",
        ".env.production",
    ]

    all_env_vars = dict(os.environ)  # Start with system env vars
    for env_file in env_files:
        env_path = search_dir / env_file
        file_vars = load_env_file(env_path)
        all_env_vars.update(file_vars)

    detected_tools = []

    for tool_key, tool_config in PM_TOOLS.items():
        detection = {
            "key": tool_key,
            "name": tool_config["name"],
            "tier": tool_config["tier"],
            "api_type": tool_config["api_type"],
            "docs_url": tool_config["docs_url"],
            "config_found": False,
            "env_vars_found": [],
            "env_vars_missing": [],
            "config_file": None,
            "confidence": 0,
        }

        # Check for config files
        for config_file in tool_config["config_files"]:
            config_path = search_dir / config_file
            if config_path.exists():
                detection["config_found"] = True
                detection["config_file"] = config_file
                detection["confidence"] += 3
                break

        # Check for environment variables
        for env_var in tool_config["env_vars"]:
            if env_var in all_env_vars and all_env_vars[env_var]:
                detection["env_vars_found"].append(env_var)
                detection["confidence"] += 2
            else:
                detection["env_vars_missing"].append(env_var)

        # Only include if we found something
        if detection["confidence"] > 0:
            detected_tools.append(detection)

    # Sort by confidence
    detected_tools.sort(key=lambda x: x["confidence"], reverse=True)

    # Check for generic PM config file
    generic_config_path = search_dir / "config" / "pm-config.json"
    has_generic_config = generic_config_path.exists()

    generic_config = None
    if has_generic_config:
        try:
            with open(generic_config_path, 'r') as f:
                generic_config = json.load(f)
        except Exception:
            pass

    primary = detected_tools[0] if detected_tools else None

    return {
        "detected": detected_tools,
        "primary": primary["key"] if primary else None,
        "primary_name": primary["name"] if primary else None,
        "has_config": any(d["config_found"] for d in detected_tools),
        "has_env_vars": any(len(d["env_vars_found"]) > 0 for d in detected_tools),
        "generic_config": has_generic_config,
        "generic_config_data": generic_config,
        "directory": str(search_dir),
    }


def get_tool_info(tool_key: str) -> dict:
    """
    Get detailed information about a specific PM tool.

    Args:
        tool_key: The tool key (e.g., 'clickup', 'linear')

    Returns:
        Dictionary containing tool information
    """
    tool_key = tool_key.lower().replace("-", "_").replace(" ", "_")

    if tool_key not in PM_TOOLS:
        # Try to find a matching tool
        for key, config in PM_TOOLS.items():
            if config["name"].lower().replace(" ", "_") == tool_key:
                tool_key = key
                break

    if tool_key not in PM_TOOLS:
        return {
            "error": f"Unknown PM tool: {tool_key}",
            "available_tools": list(PM_TOOLS.keys()),
        }

    tool = PM_TOOLS[tool_key]

    return {
        "key": tool_key,
        "name": tool["name"],
        "tier": tool["tier"],
        "tier_description": {
            1: "Full Integration Support",
            2: "Standard Integration Support",
            3: "Basic Integration Support",
        }.get(tool["tier"], "Unknown"),
        "api_type": tool["api_type"],
        "config_files": tool["config_files"],
        "env_vars": tool["env_vars"],
        "docs_url": tool["docs_url"],
    }


def list_tools(tier: Optional[int] = None) -> dict:
    """
    List all supported PM tools.

    Args:
        tier: Optional tier filter (1, 2, or 3)

    Returns:
        Dictionary containing list of tools
    """
    tools = []

    for key, config in PM_TOOLS.items():
        if tier is None or config["tier"] == tier:
            tools.append({
                "key": key,
                "name": config["name"],
                "tier": config["tier"],
                "api_type": config["api_type"],
            })

    # Sort by tier, then by name
    tools.sort(key=lambda x: (x["tier"], x["name"]))

    return {
        "tools": tools,
        "total": len(tools),
        "filter_tier": tier,
    }


def check_github_integration(directory: Optional[str] = None) -> dict:
    """
    Check for PM-related GitHub Actions workflows.

    Args:
        directory: Directory to analyse (uses current directory if None)

    Returns:
        Dictionary containing GitHub integration information
    """
    search_dir = Path(directory) if directory else Path.cwd()
    workflows_dir = search_dir / ".github" / "workflows"

    if not workflows_dir.exists():
        return {
            "has_workflows_dir": False,
            "pm_workflows": [],
            "has_pm_integration": False,
            "directory": str(search_dir),
        }

    pm_keywords = [
        "pm-sync", "project-sync", "issue-sync",
        "clickup", "linear", "jira", "monday", "asana", "trello", "notion",
        "ticket", "story", "sprint",
    ]

    pm_workflows = []

    for workflow_file in workflows_dir.glob("*.yml"):
        try:
            content = workflow_file.read_text().lower()
            matched_keywords = [kw for kw in pm_keywords if kw in content]
            if matched_keywords:
                pm_workflows.append({
                    "file": workflow_file.name,
                    "keywords": matched_keywords,
                })
        except Exception:
            pass

    for workflow_file in workflows_dir.glob("*.yaml"):
        try:
            content = workflow_file.read_text().lower()
            matched_keywords = [kw for kw in pm_keywords if kw in content]
            if matched_keywords:
                pm_workflows.append({
                    "file": workflow_file.name,
                    "keywords": matched_keywords,
                })
        except Exception:
            pass

    return {
        "has_workflows_dir": True,
        "pm_workflows": pm_workflows,
        "has_pm_integration": len(pm_workflows) > 0,
        "directory": str(search_dir),
    }


def get_status() -> dict:
    """
    Get comprehensive PM tool status for the current project.

    Returns:
        Dictionary containing complete PM tool analysis
    """
    detection = detect_pm_tool()
    github_integration = check_github_integration()

    return {
        "pm_tool_detected": detection["primary"] is not None,
        "primary_tool": detection["primary_name"],
        "all_detected": [d["name"] for d in detection["detected"]],
        "has_config": detection["has_config"],
        "has_env_vars": detection["has_env_vars"],
        "has_generic_config": detection["generic_config"],
        "has_github_integration": github_integration["has_pm_integration"],
        "github_workflows": [w["file"] for w in github_integration["pm_workflows"]],
        "setup_complete": (
            detection["primary"] is not None and
            detection["has_config"] and
            detection["has_env_vars"]
        ),
        "recommendations": _get_recommendations(detection, github_integration),
    }


def _get_recommendations(detection: dict, github_integration: dict) -> list:
    """Generate setup recommendations based on current state."""
    recommendations = []

    if not detection["detected"]:
        recommendations.append({
            "priority": "high",
            "message": "No PM tool detected. Run /agent:pm-setup to configure a PM tool.",
        })
        return recommendations

    primary = detection["detected"][0] if detection["detected"] else None

    if primary and not primary["config_found"]:
        recommendations.append({
            "priority": "medium",
            "message": f"Create a config file for {primary['name']}: {primary['key']}.config.json",
        })

    if primary and primary["env_vars_missing"]:
        missing = ", ".join(primary["env_vars_missing"][:3])
        recommendations.append({
            "priority": "high",
            "message": f"Set missing environment variables: {missing}",
        })

    if not detection["generic_config"]:
        recommendations.append({
            "priority": "low",
            "message": "Create config/pm-config.json for status mapping and sync settings.",
        })

    if not github_integration["has_pm_integration"]:
        recommendations.append({
            "priority": "medium",
            "message": "Add GitHub Actions workflow for PM sync: .github/workflows/pm-sync.yml",
        })

    return recommendations


def main():
    """Main entry point for the PM tool."""
    if len(sys.argv) < 2:
        # Default: show status
        print(json.dumps(get_status(), indent=2))
        return

    command = sys.argv[1].lower()

    if command == "detect":
        directory = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(detect_pm_tool(directory), indent=2))

    elif command == "status":
        print(json.dumps(get_status(), indent=2))

    elif command == "list":
        tier = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else None
        print(json.dumps(list_tools(tier), indent=2))

    elif command == "info":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Tool name required. Usage: pm-tool.py info <tool_name>"}, indent=2))
            return
        tool_key = sys.argv[2]
        print(json.dumps(get_tool_info(tool_key), indent=2))

    elif command == "github":
        directory = sys.argv[2] if len(sys.argv) > 2 else None
        print(json.dumps(check_github_integration(directory), indent=2))

    else:
        print(json.dumps({
            "error": f"Unknown command: {command}",
            "available_commands": ["detect", "status", "list", "info", "github"],
            "examples": [
                "pm-tool.py detect",
                "pm-tool.py status",
                "pm-tool.py list",
                "pm-tool.py list 1",
                "pm-tool.py info clickup",
                "pm-tool.py github",
            ]
        }, indent=2))


if __name__ == "__main__":
    main()
