#!/usr/bin/env python3
"""
docker-tool.py

Provides Docker container and compose status utilities for Claude Code agents.
Returns structured JSON output for integration with setup, cicd, and backend agents.
Supports container listing, compose project status, and image information.
"""
import subprocess
import json
import sys
import shutil
from typing import Optional


def is_docker_installed() -> bool:
    """Check if Docker is installed and available in PATH."""
    return shutil.which("docker") is not None


def is_docker_running() -> bool:
    """Check if Docker daemon is running and accessible."""
    if not is_docker_installed():
        return False
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, Exception):
        return False


def run_docker_command(args: list[str], timeout: int = 30) -> tuple[bool, str, str]:
    """
    Execute a Docker command and return the result.

    Args:
        args: List of command arguments to pass to docker
        timeout: Command timeout in seconds

    Returns:
        Tuple of (success, stdout, stderr)
    """
    try:
        result = subprocess.run(
            ["docker"] + args,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except FileNotFoundError:
        return False, "", "Docker is not installed"
    except Exception as e:
        return False, "", str(e)


def get_docker_status() -> dict:
    """
    Return running Docker containers in simplified JSON format.

    Returns:
        Dictionary containing containers list or error information
    """
    if not is_docker_installed():
        return {"error": "Docker is not installed", "installed": False, "running": False}

    if not is_docker_running():
        return {"error": "Docker daemon is not running", "installed": True, "running": False}

    success, stdout, stderr = run_docker_command([
        "ps", "--format", "{{json .}}"
    ])

    if not success:
        return {"error": stderr or "Failed to get Docker status", "installed": True, "running": True}

    containers = []
    for line in stdout.strip().split('\n'):
        if not line:
            continue
        try:
            c = json.loads(line)
            containers.append({
                "id": c.get("ID"),
                "name": c.get("Names"),
                "image": c.get("Image"),
                "status": c.get("Status"),
                "state": c.get("State"),
                "ports": c.get("Ports"),
                "created": c.get("CreatedAt"),
                "networks": c.get("Networks"),
            })
        except json.JSONDecodeError:
            continue

    return {
        "installed": True,
        "running": True,
        "containers": containers,
        "count": len(containers)
    }


def get_all_containers(include_stopped: bool = True) -> dict:
    """
    Return all Docker containers including stopped ones.

    Args:
        include_stopped: Whether to include stopped containers

    Returns:
        Dictionary containing all containers
    """
    if not is_docker_installed():
        return {"error": "Docker is not installed", "installed": False}

    if not is_docker_running():
        return {"error": "Docker daemon is not running", "installed": True, "running": False}

    args = ["ps", "--format", "{{json .}}"]
    if include_stopped:
        args.insert(1, "-a")

    success, stdout, stderr = run_docker_command(args)

    if not success:
        return {"error": stderr or "Failed to list containers"}

    containers = []
    for line in stdout.strip().split('\n'):
        if not line:
            continue
        try:
            c = json.loads(line)
            containers.append({
                "id": c.get("ID"),
                "name": c.get("Names"),
                "image": c.get("Image"),
                "status": c.get("Status"),
                "state": c.get("State"),
                "ports": c.get("Ports"),
            })
        except json.JSONDecodeError:
            continue

    running = sum(1 for c in containers if c.get("state") == "running")
    stopped = len(containers) - running

    return {
        "containers": containers,
        "total": len(containers),
        "running": running,
        "stopped": stopped
    }


def get_compose_status(project_name: Optional[str] = None) -> dict:
    """
    Get Docker Compose project status.

    Args:
        project_name: Optional project name to filter by

    Returns:
        Dictionary containing compose project information
    """
    if not is_docker_installed():
        return {"error": "Docker is not installed", "installed": False}

    if not is_docker_running():
        return {"error": "Docker daemon is not running", "installed": True, "running": False}

    # Check if docker compose is available
    success, _, _ = run_docker_command(["compose", "version"])
    if not success:
        return {"error": "Docker Compose is not available"}

    args = ["compose", "ls", "--format", "json"]
    success, stdout, stderr = run_docker_command(args)

    if not success:
        return {"error": stderr or "Failed to list compose projects"}

    try:
        projects = json.loads(stdout) if stdout.strip() else []

        if project_name:
            projects = [p for p in projects if p.get("Name") == project_name]

        result = []
        for proj in projects:
            result.append({
                "name": proj.get("Name"),
                "status": proj.get("Status"),
                "config_files": proj.get("ConfigFiles"),
            })

        return {
            "projects": result,
            "count": len(result)
        }
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse compose output: {e}"}


def get_docker_images(filter_dangling: bool = False) -> dict:
    """
    List Docker images.

    Args:
        filter_dangling: If True, only show dangling (unused) images

    Returns:
        Dictionary containing images list
    """
    if not is_docker_installed():
        return {"error": "Docker is not installed", "installed": False}

    if not is_docker_running():
        return {"error": "Docker daemon is not running", "installed": True, "running": False}

    args = ["images", "--format", "{{json .}}"]
    if filter_dangling:
        args.extend(["--filter", "dangling=true"])

    success, stdout, stderr = run_docker_command(args)

    if not success:
        return {"error": stderr or "Failed to list images"}

    images = []
    total_size = 0
    for line in stdout.strip().split('\n'):
        if not line:
            continue
        try:
            img = json.loads(line)
            images.append({
                "id": img.get("ID"),
                "repository": img.get("Repository"),
                "tag": img.get("Tag"),
                "size": img.get("Size"),
                "created": img.get("CreatedAt"),
            })
        except json.JSONDecodeError:
            continue

    return {
        "images": images,
        "count": len(images)
    }


def get_docker_networks() -> dict:
    """
    List Docker networks.

    Returns:
        Dictionary containing networks list
    """
    if not is_docker_installed():
        return {"error": "Docker is not installed", "installed": False}

    if not is_docker_running():
        return {"error": "Docker daemon is not running", "installed": True, "running": False}

    success, stdout, stderr = run_docker_command([
        "network", "ls", "--format", "{{json .}}"
    ])

    if not success:
        return {"error": stderr or "Failed to list networks"}

    networks = []
    for line in stdout.strip().split('\n'):
        if not line:
            continue
        try:
            net = json.loads(line)
            networks.append({
                "id": net.get("ID"),
                "name": net.get("Name"),
                "driver": net.get("Driver"),
                "scope": net.get("Scope"),
            })
        except json.JSONDecodeError:
            continue

    return {
        "networks": networks,
        "count": len(networks)
    }


def get_docker_volumes() -> dict:
    """
    List Docker volumes.

    Returns:
        Dictionary containing volumes list
    """
    if not is_docker_installed():
        return {"error": "Docker is not installed", "installed": False}

    if not is_docker_running():
        return {"error": "Docker daemon is not running", "installed": True, "running": False}

    success, stdout, stderr = run_docker_command([
        "volume", "ls", "--format", "{{json .}}"
    ])

    if not success:
        return {"error": stderr or "Failed to list volumes"}

    volumes = []
    for line in stdout.strip().split('\n'):
        if not line:
            continue
        try:
            vol = json.loads(line)
            volumes.append({
                "name": vol.get("Name"),
                "driver": vol.get("Driver"),
                "mountpoint": vol.get("Mountpoint"),
            })
        except json.JSONDecodeError:
            continue

    return {
        "volumes": volumes,
        "count": len(volumes)
    }


def main():
    """Main entry point for the Docker tool."""
    if len(sys.argv) < 2:
        # Default: return container status
        print(json.dumps(get_docker_status(), indent=2))
        return

    command = sys.argv[1].lower()

    if command == "status":
        print(json.dumps(get_docker_status(), indent=2))
    elif command == "containers":
        include_stopped = "--all" in sys.argv or "-a" in sys.argv
        print(json.dumps(get_all_containers(include_stopped), indent=2))
    elif command == "compose":
        project_name = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else None
        print(json.dumps(get_compose_status(project_name), indent=2))
    elif command == "images":
        dangling = "--dangling" in sys.argv
        print(json.dumps(get_docker_images(dangling), indent=2))
    elif command == "networks":
        print(json.dumps(get_docker_networks(), indent=2))
    elif command == "volumes":
        print(json.dumps(get_docker_volumes(), indent=2))
    elif command == "installed":
        print(json.dumps({
            "installed": is_docker_installed(),
            "running": is_docker_running()
        }, indent=2))
    else:
        print(json.dumps({
            "error": f"Unknown command: {command}",
            "available_commands": ["status", "containers", "compose", "images", "networks", "volumes", "installed"]
        }, indent=2))


if __name__ == "__main__":
    main()
