#!/usr/bin/env python3
"""
feedback-tool.py

Collects and stores user feedback for agent runs.
Links feedback to specific runs and supports querying feedback patterns.
"""
import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


def get_metrics_dir() -> Path:
    """Get the docs/METRICS directory path."""
    cwd = Path(os.getcwd())
    return cwd / "docs" / "METRICS"


def get_month_dir(base_dir: Path) -> Path:
    """Get the current month's subdirectory."""
    month = datetime.now().strftime("%Y-%m")
    month_dir = base_dir / month
    month_dir.mkdir(parents=True, exist_ok=True)
    return month_dir


def get_last_run_id() -> Optional[str]:
    """Get the ID of the last recorded run."""
    last_run_file = get_metrics_dir() / ".last_run"
    if last_run_file.exists():
        return last_run_file.read_text().strip()
    return None


def get_run(run_id: str) -> Optional[dict]:
    """Get a specific run by ID."""
    runs_dir = get_metrics_dir() / "runs"
    if not runs_dir.exists():
        return None
    for month_dir in runs_dir.iterdir():
        if month_dir.is_dir():
            run_file = month_dir / f"{run_id}.json"
            if run_file.exists():
                with open(run_file, "r") as f:
                    return json.load(f)
    return None


def update_run(run_id: str, updates: dict) -> bool:
    """Update an existing run record."""
    runs_dir = get_metrics_dir() / "runs"
    if not runs_dir.exists():
        return False
    for month_dir in runs_dir.iterdir():
        if month_dir.is_dir():
            run_file = month_dir / f"{run_id}.json"
            if run_file.exists():
                with open(run_file, "r") as f:
                    run_data = json.load(f)
                run_data.update(updates)
                with open(run_file, "w") as f:
                    json.dump(run_data, f, indent=2)
                return True
    return False


def record_feedback(
    rating: str,
    comment: Optional[str] = None,
    run_id: Optional[str] = None,
) -> dict:
    """
    Record user feedback for an agent run.

    Args:
        rating: 'good', 'bad', or 'skip'
        comment: Optional comment
        run_id: Specific run ID (default: last run)

    Returns:
        Feedback record
    """
    # Determine run ID
    if not run_id:
        run_id = get_last_run_id()

    if not run_id:
        return {"error": "No run ID found. Record a run first."}

    # Get the run to validate it exists
    run = get_run(run_id)
    if not run:
        return {"error": f"Run not found: {run_id}"}

    # Map rating to satisfaction score
    satisfaction_map = {
        "good": 1,
        "bad": -1,
        "skip": 0,
        "neutral": 0,
    }
    satisfaction = satisfaction_map.get(rating.lower(), 0)

    # Create feedback record
    feedback_id = f"fb-{run_id.replace('run-', '')}"
    timestamp = datetime.now().isoformat()

    feedback_data = {
        "feedback_id": feedback_id,
        "run_id": run_id,
        "timestamp": timestamp,
        "rating": rating.lower(),
        "satisfaction": satisfaction,
        "comment": comment,
        "agent": run.get("agent"),
        "variant": run.get("variant"),
    }

    # Save feedback to separate file
    feedback_dir = get_metrics_dir() / "feedback"
    month_dir = get_month_dir(feedback_dir)
    feedback_file = month_dir / f"{feedback_id}.json"

    with open(feedback_file, "w") as f:
        json.dump(feedback_data, f, indent=2)

    # Also update the run record with feedback
    update_run(run_id, {"feedback": feedback_data})

    return {
        "success": True,
        "feedback_id": feedback_id,
        "run_id": run_id,
        "rating": rating,
        "agent": run.get("agent"),
        "message": f"Feedback recorded for {run.get('agent')} agent",
    }


def query_feedback(
    agent: Optional[str] = None,
    rating: Optional[str] = None,
    days: int = 30,
    limit: int = 100,
) -> list:
    """
    Query feedback records with optional filters.

    Args:
        agent: Filter by agent name
        rating: Filter by rating (good/bad/skip)
        days: Number of days to look back
        limit: Maximum results

    Returns:
        List of feedback records
    """
    feedback_dir = get_metrics_dir() / "feedback"
    if not feedback_dir.exists():
        return []

    cutoff_date = datetime.now() - timedelta(days=days)
    records = []

    for month_dir in sorted(feedback_dir.iterdir(), reverse=True):
        if not month_dir.is_dir():
            continue

        for fb_file in sorted(month_dir.glob("*.json"), reverse=True):
            if len(records) >= limit:
                break

            with open(fb_file, "r") as f:
                fb_data = json.load(f)

            # Parse timestamp
            fb_time = datetime.fromisoformat(fb_data["timestamp"].replace("Z", "+00:00"))
            if fb_time.replace(tzinfo=None) < cutoff_date:
                continue

            # Apply filters
            if agent and fb_data.get("agent") != agent:
                continue
            if rating and fb_data.get("rating") != rating.lower():
                continue

            records.append(fb_data)

    return records[:limit]


def analyse_feedback(agent: Optional[str] = None, days: int = 30) -> dict:
    """
    Analyse feedback patterns for an agent.

    Args:
        agent: Agent name (or None for all)
        days: Number of days to analyse

    Returns:
        Analysis results
    """
    feedback = query_feedback(agent=agent, days=days, limit=1000)

    if not feedback:
        return {"error": "No feedback found", "agent": agent, "days": days}

    # Count by rating
    by_rating = {"good": 0, "bad": 0, "skip": 0}
    for fb in feedback:
        rating = fb.get("rating", "skip")
        if rating in by_rating:
            by_rating[rating] += 1

    # Calculate satisfaction rate
    total_rated = by_rating["good"] + by_rating["bad"]
    satisfaction_rate = by_rating["good"] / total_rated if total_rated > 0 else None

    # Group by agent
    by_agent = {}
    for fb in feedback:
        agent_name = fb.get("agent", "unknown")
        if agent_name not in by_agent:
            by_agent[agent_name] = {"good": 0, "bad": 0, "skip": 0}
        rating = fb.get("rating", "skip")
        if rating in by_agent[agent_name]:
            by_agent[agent_name][rating] += 1

    # Extract comments
    positive_comments = [fb.get("comment") for fb in feedback if fb.get("rating") == "good" and fb.get("comment")]
    negative_comments = [fb.get("comment") for fb in feedback if fb.get("rating") == "bad" and fb.get("comment")]

    return {
        "agent": agent or "all",
        "period_days": days,
        "total_feedback": len(feedback),
        "by_rating": by_rating,
        "satisfaction_rate": round(satisfaction_rate, 3) if satisfaction_rate else None,
        "by_agent": by_agent if not agent else None,
        "positive_comments": positive_comments[:10],
        "negative_comments": negative_comments[:10],
    }


def generate_prompt() -> dict:
    """Generate a feedback prompt message for the user."""
    run_id = get_last_run_id()
    run = get_run(run_id) if run_id else None

    if not run:
        return {"prompt": None, "message": "No recent run to provide feedback for"}

    agent = run.get("agent", "agent")

    prompt_text = f"""
---
How was this {agent} response?
  /learning:feedback good     - Worked well
  /learning:feedback bad      - Needs improvement
  /learning:feedback skip     - Skip this time
---
"""

    return {
        "prompt": prompt_text.strip(),
        "run_id": run_id,
        "agent": agent,
    }


def get_status() -> dict:
    """Get the current status of feedback collection."""
    feedback_dir = get_metrics_dir() / "feedback"

    total_feedback = 0
    if feedback_dir.exists():
        for month_dir in feedback_dir.iterdir():
            if month_dir.is_dir():
                total_feedback += len(list(month_dir.glob("*.json")))

    # Get recent feedback stats
    recent = analyse_feedback(days=7)

    return {
        "total_feedback": total_feedback,
        "last_7_days": {
            "count": recent.get("total_feedback", 0),
            "satisfaction_rate": recent.get("satisfaction_rate"),
        },
        "last_run_id": get_last_run_id(),
    }


def main():
    """Main entry point for the feedback tool."""
    if len(sys.argv) < 2:
        print(json.dumps(get_status(), indent=2))
        return

    command = sys.argv[1].lower()

    if command == "status":
        print(json.dumps(get_status(), indent=2))

    elif command == "record":
        # Parse arguments
        rating = "skip"
        comment = None
        run_id = None

        # First positional arg after 'record' is the rating
        if len(sys.argv) > 2 and not sys.argv[2].startswith("--"):
            rating = sys.argv[2]

        # Parse optional arguments
        i = 3
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg == "--comment" and i + 1 < len(sys.argv):
                comment = sys.argv[i + 1]
                i += 2
            elif arg == "--run-id" and i + 1 < len(sys.argv):
                run_id = sys.argv[i + 1]
                i += 2
            elif not arg.startswith("--") and comment is None:
                # Treat remaining args as comment
                comment = " ".join(sys.argv[i:])
                break
            else:
                i += 1

        result = record_feedback(rating=rating, comment=comment, run_id=run_id)
        print(json.dumps(result, indent=2))

    elif command == "query":
        agent = None
        rating = None
        days = 30
        limit = 100

        i = 2
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg == "--agent" and i + 1 < len(sys.argv):
                agent = sys.argv[i + 1]
                i += 2
            elif arg == "--rating" and i + 1 < len(sys.argv):
                rating = sys.argv[i + 1]
                i += 2
            elif arg == "--days" and i + 1 < len(sys.argv):
                days = int(sys.argv[i + 1])
                i += 2
            elif arg == "--limit" and i + 1 < len(sys.argv):
                limit = int(sys.argv[i + 1])
                i += 2
            else:
                i += 1

        feedback = query_feedback(agent=agent, rating=rating, days=days, limit=limit)
        print(json.dumps({"feedback": feedback, "count": len(feedback)}, indent=2))

    elif command == "analyse":
        agent = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else None
        days = 30

        for i, arg in enumerate(sys.argv):
            if arg == "--days" and i + 1 < len(sys.argv):
                days = int(sys.argv[i + 1])

        print(json.dumps(analyse_feedback(agent=agent, days=days), indent=2))

    elif command == "prompt":
        result = generate_prompt()
        # Print just the prompt text for display
        if result.get("prompt"):
            print(result["prompt"])
        else:
            print(json.dumps(result, indent=2))

    else:
        print(json.dumps({
            "error": f"Unknown command: {command}",
            "available_commands": ["status", "record", "query", "analyse", "prompt"]
        }, indent=2))


if __name__ == "__main__":
    main()
