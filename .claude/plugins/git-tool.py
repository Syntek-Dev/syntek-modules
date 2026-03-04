#!/usr/bin/env python3
"""
git-tool.py

Provides Git repository status and information utilities for Claude Code agents.
Returns structured JSON output for integration with cicd, setup, and code-reviewer agents.
Supports repository status, branch info, remote detection, and commit history.
"""
import subprocess
import json
import sys
import shutil
import os
from typing import Optional


def is_git_installed() -> bool:
    """Check if Git is installed and available in PATH."""
    return shutil.which("git") is not None


def is_git_repo(path: Optional[str] = None) -> bool:
    """
    Check if the current or specified directory is a Git repository.

    Args:
        path: Optional path to check (uses current directory if None)

    Returns:
        True if the path is inside a Git repository
    """
    try:
        cwd = path or os.getcwd()
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=10
        )
        return result.returncode == 0 and result.stdout.strip() == "true"
    except (subprocess.TimeoutExpired, Exception):
        return False


def run_git_command(args: list[str], cwd: Optional[str] = None, timeout: int = 30) -> tuple[bool, str, str]:
    """
    Execute a Git command and return the result.

    Args:
        args: List of command arguments to pass to git
        cwd: Working directory for the command
        timeout: Command timeout in seconds

    Returns:
        Tuple of (success, stdout, stderr)
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except FileNotFoundError:
        return False, "", "Git is not installed"
    except Exception as e:
        return False, "", str(e)


def get_git_status() -> dict:
    """
    Get comprehensive Git repository status.

    Returns:
        Dictionary containing repository status information
    """
    if not is_git_installed():
        return {"error": "Git is not installed", "installed": False}

    if not is_git_repo():
        return {"error": "Not a Git repository", "installed": True, "is_repo": False}

    result = {
        "installed": True,
        "is_repo": True,
    }

    # Get current branch
    success, stdout, _ = run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
    result["branch"] = stdout.strip() if success else None

    # Get remote URL
    success, stdout, _ = run_git_command(["remote", "get-url", "origin"])
    result["remote_url"] = stdout.strip() if success else None

    # Check for uncommitted changes
    success, stdout, _ = run_git_command(["status", "--porcelain"])
    if success:
        lines = [l for l in stdout.strip().split('\n') if l]
        result["has_changes"] = len(lines) > 0
        result["changes_count"] = len(lines)

        # Categorise changes
        staged = sum(1 for l in lines if l[0] != ' ' and l[0] != '?')
        unstaged = sum(1 for l in lines if l[1] != ' ' and l[0] != '?')
        untracked = sum(1 for l in lines if l.startswith('??'))

        result["staged"] = staged
        result["unstaged"] = unstaged
        result["untracked"] = untracked

    # Get ahead/behind status
    success, stdout, _ = run_git_command(["rev-list", "--left-right", "--count", "@{u}...HEAD"])
    if success:
        parts = stdout.strip().split()
        if len(parts) == 2:
            result["behind"] = int(parts[0])
            result["ahead"] = int(parts[1])

    # Get last commit info
    success, stdout, _ = run_git_command([
        "log", "-1", "--format=%H|%h|%s|%an|%ae|%ai"
    ])
    if success and stdout.strip():
        parts = stdout.strip().split("|")
        if len(parts) >= 6:
            result["last_commit"] = {
                "hash": parts[0],
                "short_hash": parts[1],
                "message": parts[2],
                "author": parts[3],
                "email": parts[4],
                "date": parts[5],
            }

    return result


def get_branches(include_remote: bool = False) -> dict:
    """
    List Git branches.

    Args:
        include_remote: Whether to include remote branches

    Returns:
        Dictionary containing branch information
    """
    if not is_git_installed():
        return {"error": "Git is not installed", "installed": False}

    if not is_git_repo():
        return {"error": "Not a Git repository", "is_repo": False}

    args = ["branch", "--format=%(refname:short)|%(objectname:short)|%(upstream:short)"]
    if include_remote:
        args.insert(1, "-a")

    success, stdout, stderr = run_git_command(args)

    if not success:
        return {"error": stderr or "Failed to list branches"}

    # Get current branch
    _, current_stdout, _ = run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
    current_branch = current_stdout.strip()

    branches = []
    for line in stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split("|")
        branch_name = parts[0]
        branches.append({
            "name": branch_name,
            "short_hash": parts[1] if len(parts) > 1 else None,
            "upstream": parts[2] if len(parts) > 2 and parts[2] else None,
            "is_current": branch_name == current_branch,
            "is_remote": branch_name.startswith("remotes/"),
        })

    local = [b for b in branches if not b["is_remote"]]
    remote = [b for b in branches if b["is_remote"]]

    return {
        "current": current_branch,
        "branches": branches,
        "local_count": len(local),
        "remote_count": len(remote),
    }


def get_remotes() -> dict:
    """
    List Git remotes and their URLs.

    Returns:
        Dictionary containing remote information
    """
    if not is_git_installed():
        return {"error": "Git is not installed", "installed": False}

    if not is_git_repo():
        return {"error": "Not a Git repository", "is_repo": False}

    success, stdout, stderr = run_git_command(["remote", "-v"])

    if not success:
        return {"error": stderr or "Failed to list remotes"}

    remotes = {}
    for line in stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            name = parts[0]
            url = parts[1]
            remote_type = parts[2].strip("()") if len(parts) > 2 else "fetch"

            if name not in remotes:
                remotes[name] = {"name": name}
            remotes[name][remote_type] = url

    return {
        "remotes": list(remotes.values()),
        "count": len(remotes)
    }


def get_recent_commits(count: int = 10) -> dict:
    """
    Get recent commit history.

    Args:
        count: Number of commits to retrieve

    Returns:
        Dictionary containing commit history
    """
    if not is_git_installed():
        return {"error": "Git is not installed", "installed": False}

    if not is_git_repo():
        return {"error": "Not a Git repository", "is_repo": False}

    success, stdout, stderr = run_git_command([
        "log", f"-{count}",
        "--format=%H|%h|%s|%an|%ae|%ai|%D"
    ])

    if not success:
        return {"error": stderr or "Failed to get commit history"}

    commits = []
    for line in stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split("|")
        if len(parts) >= 6:
            commits.append({
                "hash": parts[0],
                "short_hash": parts[1],
                "message": parts[2],
                "author": parts[3],
                "email": parts[4],
                "date": parts[5],
                "refs": parts[6] if len(parts) > 6 and parts[6] else None,
            })

    return {
        "commits": commits,
        "count": len(commits)
    }


def get_tags() -> dict:
    """
    List Git tags.

    Returns:
        Dictionary containing tag information
    """
    if not is_git_installed():
        return {"error": "Git is not installed", "installed": False}

    if not is_git_repo():
        return {"error": "Not a Git repository", "is_repo": False}

    success, stdout, stderr = run_git_command([
        "tag", "-l", "--format=%(refname:short)|%(objectname:short)|%(creatordate:iso)"
    ])

    if not success:
        return {"error": stderr or "Failed to list tags"}

    tags = []
    for line in stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split("|")
        tags.append({
            "name": parts[0],
            "short_hash": parts[1] if len(parts) > 1 else None,
            "date": parts[2] if len(parts) > 2 else None,
        })

    # Sort by date descending (newest first)
    tags.sort(key=lambda x: x.get("date", ""), reverse=True)

    return {
        "tags": tags,
        "count": len(tags),
        "latest": tags[0]["name"] if tags else None
    }


def get_stash_list() -> dict:
    """
    List Git stashes.

    Returns:
        Dictionary containing stash information
    """
    if not is_git_installed():
        return {"error": "Git is not installed", "installed": False}

    if not is_git_repo():
        return {"error": "Not a Git repository", "is_repo": False}

    success, stdout, stderr = run_git_command(["stash", "list"])

    if not success:
        return {"error": stderr or "Failed to list stashes"}

    stashes = []
    for line in stdout.strip().split('\n'):
        if not line:
            continue
        # Parse stash format: stash@{0}: WIP on branch: message
        if ": " in line:
            parts = line.split(": ", 2)
            stashes.append({
                "ref": parts[0],
                "branch_info": parts[1] if len(parts) > 1 else None,
                "message": parts[2] if len(parts) > 2 else None,
            })

    return {
        "stashes": stashes,
        "count": len(stashes)
    }


def detect_git_host() -> dict:
    """
    Detect the Git hosting provider from the remote URL.

    Returns:
        Dictionary containing host detection information
    """
    if not is_git_installed():
        return {"error": "Git is not installed", "installed": False}

    if not is_git_repo():
        return {"error": "Not a Git repository", "is_repo": False}

    success, stdout, _ = run_git_command(["remote", "get-url", "origin"])

    if not success or not stdout.strip():
        return {"host": None, "detected": False}

    url = stdout.strip().lower()

    hosts = {
        "github.com": "github",
        "gitlab.com": "gitlab",
        "bitbucket.org": "bitbucket",
        "dev.azure.com": "azure",
        "ssh.dev.azure.com": "azure",
        "codecommit": "aws-codecommit",
    }

    detected_host = None
    for pattern, host_name in hosts.items():
        if pattern in url:
            detected_host = host_name
            break

    return {
        "host": detected_host,
        "remote_url": stdout.strip(),
        "detected": detected_host is not None
    }


def main():
    """Main entry point for the Git tool."""
    if len(sys.argv) < 2:
        # Default: return repository status
        print(json.dumps(get_git_status(), indent=2))
        return

    command = sys.argv[1].lower()

    if command == "status":
        print(json.dumps(get_git_status(), indent=2))
    elif command == "branches":
        include_remote = "--all" in sys.argv or "-a" in sys.argv
        print(json.dumps(get_branches(include_remote), indent=2))
    elif command == "remotes":
        print(json.dumps(get_remotes(), indent=2))
    elif command == "commits":
        count = 10
        for arg in sys.argv[2:]:
            if arg.isdigit():
                count = int(arg)
                break
        print(json.dumps(get_recent_commits(count), indent=2))
    elif command == "tags":
        print(json.dumps(get_tags(), indent=2))
    elif command == "stash":
        print(json.dumps(get_stash_list(), indent=2))
    elif command == "host":
        print(json.dumps(detect_git_host(), indent=2))
    elif command == "installed":
        print(json.dumps({
            "installed": is_git_installed(),
            "is_repo": is_git_repo()
        }, indent=2))
    else:
        print(json.dumps({
            "error": f"Unknown command: {command}",
            "available_commands": ["status", "branches", "remotes", "commits", "tags", "stash", "host", "installed"]
        }, indent=2))


if __name__ == "__main__":
    main()
