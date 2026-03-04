#!/usr/bin/env python3
"""
metrics-tool.py

Records and queries agent performance metrics for the self-learning system.
Stores run data in docs/METRICS/runs/ as JSON files organised by month.
Supports recording runs, querying history, and generating aggregates.
"""
import subprocess
import json
import sys
import os
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


def get_metrics_dir() -> Path:
    """Get the docs/METRICS directory path."""
    cwd = Path(os.getcwd())
    metrics_dir = cwd / "docs" / "METRICS"
    return metrics_dir


def ensure_directories():
    """Ensure all required directories exist."""
    metrics_dir = get_metrics_dir()
    subdirs = [
        "runs",
        "feedback",
        "aggregates/daily",
        "aggregates/weekly",
        "variants",
        "optimisations/pending",
        "optimisations/applied",
        "optimisations/rejected",
        "templates",
    ]
    for subdir in subdirs:
        (metrics_dir / subdir).mkdir(parents=True, exist_ok=True)


def generate_run_id() -> str:
    """Generate a unique run ID."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    random_suffix = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
    return f"run-{timestamp}-{random_suffix}"


def get_month_dir(base_dir: Path) -> Path:
    """Get the current month's subdirectory."""
    month = datetime.now().strftime("%Y-%m")
    month_dir = base_dir / month
    month_dir.mkdir(parents=True, exist_ok=True)
    return month_dir


def load_config() -> dict:
    """Load the metrics configuration."""
    config_path = get_metrics_dir() / "config.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            return json.load(f)
    return {"enabled": True}


def record_run(
    agent: str,
    command: str = "",
    variant: Optional[str] = None,
    status: str = "completed",
    duration: float = 0,
    error: Optional[str] = None,
    files_modified: int = 0,
    files_read: int = 0,
) -> dict:
    """
    Record a new agent run.

    Args:
        agent: Name of the agent that ran
        command: The command/arguments used
        variant: A/B test variant if applicable
        status: Run status (completed, failed, cancelled)
        duration: Duration in seconds
        error: Error message if failed
        files_modified: Number of files modified
        files_read: Number of files read

    Returns:
        The recorded run data
    """
    config = load_config()
    if not config.get("enabled", True):
        return {"error": "Metrics system is disabled"}

    ensure_directories()

    run_id = generate_run_id()
    timestamp = datetime.now().isoformat()

    run_data = {
        "run_id": run_id,
        "timestamp": timestamp,
        "agent": agent,
        "command": command,
        "variant": variant,
        "status": status,
        "duration_seconds": duration,
        "error": error,
        "outcome": {
            "files_modified": files_modified,
            "files_read": files_read,
        },
        "quality_metrics": {
            "linting_errors_before": None,
            "linting_errors_after": None,
            "test_pass_rate": None,
        },
        "feedback": None,
    }

    # Save to file
    runs_dir = get_metrics_dir() / "runs"
    month_dir = get_month_dir(runs_dir)
    run_file = month_dir / f"{run_id}.json"

    with open(run_file, "w") as f:
        json.dump(run_data, f, indent=2)

    # Store run_id for feedback linking
    last_run_file = get_metrics_dir() / ".last_run"
    with open(last_run_file, "w") as f:
        f.write(run_id)

    return run_data


def get_last_run_id() -> Optional[str]:
    """Get the ID of the last recorded run."""
    last_run_file = get_metrics_dir() / ".last_run"
    if last_run_file.exists():
        return last_run_file.read_text().strip()
    return None


def get_run(run_id: str) -> Optional[dict]:
    """Get a specific run by ID."""
    runs_dir = get_metrics_dir() / "runs"
    # Search in all month directories
    for month_dir in runs_dir.iterdir():
        if month_dir.is_dir():
            run_file = month_dir / f"{run_id}.json"
            if run_file.exists():
                with open(run_file, "r") as f:
                    return json.load(f)
    return None


def update_run(run_id: str, updates: dict) -> Optional[dict]:
    """Update an existing run record."""
    runs_dir = get_metrics_dir() / "runs"
    for month_dir in runs_dir.iterdir():
        if month_dir.is_dir():
            run_file = month_dir / f"{run_id}.json"
            if run_file.exists():
                with open(run_file, "r") as f:
                    run_data = json.load(f)
                run_data.update(updates)
                with open(run_file, "w") as f:
                    json.dump(run_data, f, indent=2)
                return run_data
    return None


def query_runs(
    agent: Optional[str] = None,
    days: int = 7,
    status: Optional[str] = None,
    variant: Optional[str] = None,
    limit: int = 100,
) -> list:
    """
    Query run records with optional filters.

    Args:
        agent: Filter by agent name
        days: Number of days to look back
        status: Filter by status
        variant: Filter by A/B variant
        limit: Maximum number of results

    Returns:
        List of matching run records
    """
    runs_dir = get_metrics_dir() / "runs"
    if not runs_dir.exists():
        return []

    cutoff_date = datetime.now() - timedelta(days=days)
    runs = []

    for month_dir in sorted(runs_dir.iterdir(), reverse=True):
        if not month_dir.is_dir():
            continue

        for run_file in sorted(month_dir.glob("*.json"), reverse=True):
            if len(runs) >= limit:
                break

            with open(run_file, "r") as f:
                run_data = json.load(f)

            # Parse timestamp
            run_time = datetime.fromisoformat(run_data["timestamp"].replace("Z", "+00:00"))
            if run_time.replace(tzinfo=None) < cutoff_date:
                continue

            # Apply filters
            if agent and run_data.get("agent") != agent:
                continue
            if status and run_data.get("status") != status:
                continue
            if variant and run_data.get("variant") != variant:
                continue

            runs.append(run_data)

    return runs[:limit]


def get_agent_summary(agent: Optional[str] = None, days: int = 30) -> dict:
    """
    Get summary statistics for an agent or all agents.

    Args:
        agent: Agent name (or None for all)
        days: Number of days to analyse

    Returns:
        Summary statistics
    """
    runs = query_runs(agent=agent, days=days, limit=1000)

    if not runs:
        return {"error": "No runs found", "agent": agent, "days": days}

    # Calculate statistics
    total_runs = len(runs)
    completed = sum(1 for r in runs if r.get("status") == "completed")
    failed = sum(1 for r in runs if r.get("status") == "failed")

    # Feedback statistics
    with_feedback = [r for r in runs if r.get("feedback") is not None]
    positive = sum(1 for r in with_feedback if r.get("feedback", {}).get("satisfaction") == 1)
    negative = sum(1 for r in with_feedback if r.get("feedback", {}).get("satisfaction") == -1)

    # Duration statistics
    durations = [r.get("duration_seconds", 0) for r in runs if r.get("duration_seconds")]
    avg_duration = sum(durations) / len(durations) if durations else 0

    # Group by agent if not filtered
    by_agent = {}
    for run in runs:
        agent_name = run.get("agent", "unknown")
        if agent_name not in by_agent:
            by_agent[agent_name] = {"runs": 0, "completed": 0, "positive_feedback": 0}
        by_agent[agent_name]["runs"] += 1
        if run.get("status") == "completed":
            by_agent[agent_name]["completed"] += 1
        if run.get("feedback", {}).get("satisfaction") == 1:
            by_agent[agent_name]["positive_feedback"] += 1

    return {
        "agent": agent or "all",
        "period_days": days,
        "total_runs": total_runs,
        "completed": completed,
        "failed": failed,
        "completion_rate": completed / total_runs if total_runs > 0 else 0,
        "feedback_count": len(with_feedback),
        "positive_feedback": positive,
        "negative_feedback": negative,
        "satisfaction_rate": positive / len(with_feedback) if with_feedback else None,
        "avg_duration_seconds": round(avg_duration, 2),
        "by_agent": by_agent if not agent else None,
    }


def aggregate_daily(date: Optional[str] = None) -> dict:
    """
    Generate daily aggregate for a specific date.

    Args:
        date: Date in YYYY-MM-DD format (default: today)

    Returns:
        Daily aggregate data
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    # Query runs for that day
    target_date = datetime.strptime(date, "%Y-%m-%d")
    next_date = target_date + timedelta(days=1)

    runs_dir = get_metrics_dir() / "runs"
    runs = []

    month = target_date.strftime("%Y-%m")
    month_dir = runs_dir / month

    if month_dir.exists():
        for run_file in month_dir.glob("*.json"):
            with open(run_file, "r") as f:
                run_data = json.load(f)
            run_time = datetime.fromisoformat(run_data["timestamp"].replace("Z", "+00:00"))
            run_time = run_time.replace(tzinfo=None)
            if target_date <= run_time < next_date:
                runs.append(run_data)

    # Calculate aggregates
    aggregate = {
        "date": date,
        "generated_at": datetime.now().isoformat(),
        "total_runs": len(runs),
        "by_agent": {},
        "by_status": {"completed": 0, "failed": 0, "cancelled": 0},
        "feedback": {"positive": 0, "negative": 0, "neutral": 0},
    }

    for run in runs:
        agent = run.get("agent", "unknown")
        status = run.get("status", "unknown")

        if agent not in aggregate["by_agent"]:
            aggregate["by_agent"][agent] = 0
        aggregate["by_agent"][agent] += 1

        if status in aggregate["by_status"]:
            aggregate["by_status"][status] += 1

        feedback = run.get("feedback", {})
        if feedback:
            satisfaction = feedback.get("satisfaction", 0)
            if satisfaction > 0:
                aggregate["feedback"]["positive"] += 1
            elif satisfaction < 0:
                aggregate["feedback"]["negative"] += 1
            else:
                aggregate["feedback"]["neutral"] += 1

    # Save aggregate
    ensure_directories()
    aggregate_file = get_metrics_dir() / "aggregates" / "daily" / f"{date}.json"
    with open(aggregate_file, "w") as f:
        json.dump(aggregate, f, indent=2)

    return aggregate


def get_status() -> dict:
    """Get the current status of the metrics system."""
    config = load_config()
    metrics_dir = get_metrics_dir()

    # Count runs
    runs_dir = metrics_dir / "runs"
    total_runs = 0
    if runs_dir.exists():
        for month_dir in runs_dir.iterdir():
            if month_dir.is_dir():
                total_runs += len(list(month_dir.glob("*.json")))

    # Get last run
    last_run_id = get_last_run_id()
    last_run = get_run(last_run_id) if last_run_id else None

    return {
        "enabled": config.get("enabled", True),
        "metrics_dir": str(metrics_dir),
        "total_runs": total_runs,
        "last_run_id": last_run_id,
        "last_run_agent": last_run.get("agent") if last_run else None,
        "last_run_time": last_run.get("timestamp") if last_run else None,
        "config": config,
    }


def main():
    """Main entry point for the metrics tool."""
    if len(sys.argv) < 2:
        print(json.dumps(get_status(), indent=2))
        return

    command = sys.argv[1].lower()

    if command == "status":
        print(json.dumps(get_status(), indent=2))

    elif command == "record":
        # Parse arguments
        agent = None
        cmd = ""
        variant = None
        status = "completed"
        duration = 0

        i = 2
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg == "--agent" and i + 1 < len(sys.argv):
                agent = sys.argv[i + 1]
                i += 2
            elif arg == "--command" and i + 1 < len(sys.argv):
                cmd = sys.argv[i + 1]
                i += 2
            elif arg == "--variant" and i + 1 < len(sys.argv):
                variant = sys.argv[i + 1]
                i += 2
            elif arg == "--status" and i + 1 < len(sys.argv):
                status = sys.argv[i + 1]
                i += 2
            elif arg == "--duration" and i + 1 < len(sys.argv):
                duration = float(sys.argv[i + 1])
                i += 2
            else:
                i += 1

        if not agent:
            print(json.dumps({"error": "Agent name required (--agent)"}))
            return

        result = record_run(agent=agent, command=cmd, variant=variant, status=status, duration=duration)
        print(json.dumps(result, indent=2))

    elif command == "query":
        agent = None
        days = 7
        limit = 100

        i = 2
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg == "--agent" and i + 1 < len(sys.argv):
                agent = sys.argv[i + 1]
                i += 2
            elif arg == "--days" and i + 1 < len(sys.argv):
                days = int(sys.argv[i + 1])
                i += 2
            elif arg == "--limit" and i + 1 < len(sys.argv):
                limit = int(sys.argv[i + 1])
                i += 2
            else:
                i += 1

        runs = query_runs(agent=agent, days=days, limit=limit)
        print(json.dumps({"runs": runs, "count": len(runs)}, indent=2))

    elif command == "summary":
        agent = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else None
        days = 30

        for i, arg in enumerate(sys.argv):
            if arg == "--days" and i + 1 < len(sys.argv):
                days = int(sys.argv[i + 1])

        print(json.dumps(get_agent_summary(agent=agent, days=days), indent=2))

    elif command == "aggregate":
        date = None
        for i, arg in enumerate(sys.argv):
            if arg == "--date" and i + 1 < len(sys.argv):
                date = sys.argv[i + 1]
        print(json.dumps(aggregate_daily(date=date), indent=2))

    elif command == "last":
        run_id = get_last_run_id()
        if run_id:
            run = get_run(run_id)
            print(json.dumps(run or {"error": "Run not found"}, indent=2))
        else:
            print(json.dumps({"error": "No runs recorded yet"}))

    else:
        print(json.dumps({
            "error": f"Unknown command: {command}",
            "available_commands": ["status", "record", "query", "summary", "aggregate", "last"]
        }, indent=2))


if __name__ == "__main__":
    main()
