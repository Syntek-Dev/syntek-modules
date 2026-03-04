#!/usr/bin/env python3
"""
optimiser-tool.py

Analyses agent performance metrics and manages prompt optimisation proposals.
Prepares data for the optimiser agent and handles applying/rejecting improvements.
"""
import json
import sys
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


def get_metrics_dir() -> Path:
    """Get the docs/METRICS directory path."""
    cwd = Path(os.getcwd())
    return cwd / "docs" / "METRICS"


def get_plugin_dir() -> Path:
    """Get the plugin directory (where agents are stored)."""
    cwd = Path(os.getcwd())
    possible_paths = [
        Path(os.environ.get("CLAUDE_PLUGIN_DIR", "")),
        cwd,  # Current working directory (syntek-dev-suite)
        Path(__file__).parent.parent,  # Parent of plugins directory
    ]
    for path in possible_paths:
        if path.exists() and (path / "agents").exists():
            return path
    return cwd


def ensure_directories():
    """Ensure all required directories exist."""
    metrics_dir = get_metrics_dir()
    subdirs = [
        "optimisations/pending",
        "optimisations/applied",
        "optimisations/rejected",
        "templates",
    ]
    for subdir in subdirs:
        (metrics_dir / subdir).mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load the metrics configuration."""
    config_path = get_metrics_dir() / "config.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            return json.load(f)
    return {"auto_optimisation_enabled": True, "min_runs_for_analysis": 50}


def query_runs(agent: Optional[str] = None, days: int = 14) -> list:
    """Query run records for analysis."""
    runs_dir = get_metrics_dir() / "runs"
    if not runs_dir.exists():
        return []

    cutoff_date = datetime.now() - timedelta(days=days)
    runs = []

    for month_dir in sorted(runs_dir.iterdir(), reverse=True):
        if not month_dir.is_dir():
            continue
        for run_file in month_dir.glob("*.json"):
            with open(run_file, "r") as f:
                run_data = json.load(f)
            run_time = datetime.fromisoformat(run_data["timestamp"].replace("Z", "+00:00"))
            if run_time.replace(tzinfo=None) < cutoff_date:
                continue
            if agent and run_data.get("agent") != agent:
                continue
            runs.append(run_data)

    return runs


def query_feedback(agent: Optional[str] = None, days: int = 14) -> list:
    """Query feedback records for analysis."""
    feedback_dir = get_metrics_dir() / "feedback"
    if not feedback_dir.exists():
        return []

    cutoff_date = datetime.now() - timedelta(days=days)
    records = []

    for month_dir in sorted(feedback_dir.iterdir(), reverse=True):
        if not month_dir.is_dir():
            continue
        for fb_file in month_dir.glob("*.json"):
            with open(fb_file, "r") as f:
                fb_data = json.load(f)
            fb_time = datetime.fromisoformat(fb_data["timestamp"].replace("Z", "+00:00"))
            if fb_time.replace(tzinfo=None) < cutoff_date:
                continue
            if agent and fb_data.get("agent") != agent:
                continue
            records.append(fb_data)

    return records


def get_agent_prompt(agent: str) -> Optional[str]:
    """Get the current prompt for an agent."""
    plugin_dir = get_plugin_dir()
    agent_file = plugin_dir / "agents" / f"{agent}.md"
    if agent_file.exists():
        return agent_file.read_text()
    return None


def analyse_agent(agent: str, days: int = 14) -> dict:
    """
    Analyse an agent's performance to identify improvement opportunities.

    Args:
        agent: Agent name
        days: Number of days to analyse

    Returns:
        Analysis results
    """
    config = load_config()
    min_runs = config.get("min_runs_for_analysis", 50)

    runs = query_runs(agent=agent, days=days)
    feedback = query_feedback(agent=agent, days=days)

    if len(runs) < min_runs:
        return {
            "agent": agent,
            "ready_for_optimisation": False,
            "reason": f"Need at least {min_runs} runs (have {len(runs)})",
            "runs_count": len(runs),
            "feedback_count": len(feedback),
        }

    # Calculate metrics
    total_runs = len(runs)
    completed = sum(1 for r in runs if r.get("status") == "completed")
    failed = sum(1 for r in runs if r.get("status") == "failed")

    # Feedback analysis
    positive_fb = [f for f in feedback if f.get("satisfaction") == 1]
    negative_fb = [f for f in feedback if f.get("satisfaction") == -1]

    positive_comments = [f.get("comment") for f in positive_fb if f.get("comment")]
    negative_comments = [f.get("comment") for f in negative_fb if f.get("comment")]

    satisfaction_rate = len(positive_fb) / (len(positive_fb) + len(negative_fb)) if (positive_fb or negative_fb) else None

    # Duration analysis
    durations = [r.get("duration_seconds", 0) for r in runs if r.get("duration_seconds")]
    avg_duration = sum(durations) / len(durations) if durations else 0

    # Identify patterns
    patterns = {
        "success_factors": [],
        "failure_factors": [],
    }

    # Simple pattern detection from comments
    if positive_comments:
        patterns["success_factors"].append(f"{len(positive_comments)} positive comments received")
    if negative_comments:
        patterns["failure_factors"].append(f"{len(negative_comments)} negative comments received")

    if satisfaction_rate and satisfaction_rate < 0.7:
        patterns["failure_factors"].append(f"Satisfaction rate below 70% ({satisfaction_rate:.1%})")
    if failed > total_runs * 0.1:
        patterns["failure_factors"].append(f"Failure rate above 10% ({failed}/{total_runs})")

    return {
        "agent": agent,
        "period_days": days,
        "ready_for_optimisation": len(patterns["failure_factors"]) > 0 or len(negative_comments) >= 3,
        "metrics": {
            "total_runs": total_runs,
            "completed": completed,
            "failed": failed,
            "completion_rate": completed / total_runs if total_runs > 0 else 0,
            "feedback_count": len(feedback),
            "positive_feedback": len(positive_fb),
            "negative_feedback": len(negative_fb),
            "satisfaction_rate": satisfaction_rate,
            "avg_duration_seconds": round(avg_duration, 2),
        },
        "patterns": patterns,
        "positive_comments": positive_comments[:5],
        "negative_comments": negative_comments[:5],
    }


def prepare_analysis_context(agent: str, days: int = 14) -> dict:
    """
    Prepare full context for the optimiser agent.

    Args:
        agent: Agent name
        days: Number of days to analyse

    Returns:
        Complete context for LLM analysis
    """
    analysis = analyse_agent(agent, days)
    current_prompt = get_agent_prompt(agent)

    if not current_prompt:
        return {"error": f"Agent not found: {agent}"}

    return {
        "agent": agent,
        "analysis": analysis,
        "current_prompt": current_prompt,
        "current_prompt_length": len(current_prompt),
        "generated_at": datetime.now().isoformat(),
    }


def create_proposal(
    agent: str,
    changes: list,
    rationale: str,
    confidence: float = 0.7,
) -> dict:
    """
    Create an optimisation proposal.

    Args:
        agent: Agent name
        changes: List of proposed changes
        rationale: Overall rationale
        confidence: Confidence score (0-1)

    Returns:
        Created proposal
    """
    ensure_directories()
    metrics_dir = get_metrics_dir()

    proposal_id = f"opt-{datetime.now().strftime('%Y%m%d%H%M%S')}-{agent}"

    proposal = {
        "proposal_id": proposal_id,
        "agent": agent,
        "timestamp": datetime.now().isoformat(),
        "status": "pending",
        "changes": changes,
        "rationale": rationale,
        "confidence_score": confidence,
        "requires_approval": True,
    }

    # Save proposal
    proposal_file = metrics_dir / "optimisations" / "pending" / f"{proposal_id}.json"
    with open(proposal_file, "w") as f:
        json.dump(proposal, f, indent=2)

    return {"success": True, "proposal_id": proposal_id, "proposal": proposal}


def list_proposals(status: str = "pending") -> dict:
    """List optimisation proposals."""
    metrics_dir = get_metrics_dir()
    proposals_dir = metrics_dir / "optimisations" / status

    if not proposals_dir.exists():
        return {"proposals": [], "count": 0}

    proposals = []
    for prop_file in sorted(proposals_dir.glob("*.json"), reverse=True):
        with open(prop_file, "r") as f:
            proposal = json.load(f)
        proposals.append({
            "proposal_id": proposal.get("proposal_id"),
            "agent": proposal.get("agent"),
            "timestamp": proposal.get("timestamp"),
            "confidence_score": proposal.get("confidence_score"),
            "changes_count": len(proposal.get("changes", [])),
        })

    return {"proposals": proposals, "count": len(proposals), "status": status}


def get_proposal(proposal_id: str) -> Optional[dict]:
    """Get a specific proposal."""
    metrics_dir = get_metrics_dir()

    for status in ["pending", "applied", "rejected"]:
        prop_file = metrics_dir / "optimisations" / status / f"{proposal_id}.json"
        if prop_file.exists():
            with open(prop_file, "r") as f:
                return json.load(f)

    return None


def apply_proposal(proposal_id: str) -> dict:
    """
    Apply an optimisation proposal to an agent.

    Args:
        proposal_id: Proposal ID

    Returns:
        Result of applying
    """
    metrics_dir = get_metrics_dir()
    pending_file = metrics_dir / "optimisations" / "pending" / f"{proposal_id}.json"

    if not pending_file.exists():
        return {"error": f"Proposal not found: {proposal_id}"}

    with open(pending_file, "r") as f:
        proposal = json.load(f)

    agent = proposal.get("agent")
    plugin_dir = get_plugin_dir()
    agent_file = plugin_dir / "agents" / f"{agent}.md"

    if not agent_file.exists():
        return {"error": f"Agent not found: {agent}"}

    # Backup current agent
    backup_dir = metrics_dir / "optimisations" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_file = backup_dir / f"{agent}-{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
    shutil.copy(agent_file, backup_file)

    # Apply changes
    current_content = agent_file.read_text()
    new_content = current_content

    for change in proposal.get("changes", []):
        old_text = change.get("old_text", "")
        new_text = change.get("new_text", "")
        if old_text and old_text in new_content:
            new_content = new_content.replace(old_text, new_text, 1)

    agent_file.write_text(new_content)

    # Move proposal to applied
    proposal["status"] = "applied"
    proposal["applied_at"] = datetime.now().isoformat()
    proposal["backup_file"] = str(backup_file)

    applied_file = metrics_dir / "optimisations" / "applied" / f"{proposal_id}.json"
    with open(applied_file, "w") as f:
        json.dump(proposal, f, indent=2)

    pending_file.unlink()

    return {
        "success": True,
        "proposal_id": proposal_id,
        "agent": agent,
        "backup": str(backup_file),
        "changes_applied": len(proposal.get("changes", [])),
    }


def reject_proposal(proposal_id: str, reason: str = "") -> dict:
    """
    Reject an optimisation proposal.

    Args:
        proposal_id: Proposal ID
        reason: Reason for rejection

    Returns:
        Result
    """
    metrics_dir = get_metrics_dir()
    pending_file = metrics_dir / "optimisations" / "pending" / f"{proposal_id}.json"

    if not pending_file.exists():
        return {"error": f"Proposal not found: {proposal_id}"}

    with open(pending_file, "r") as f:
        proposal = json.load(f)

    proposal["status"] = "rejected"
    proposal["rejected_at"] = datetime.now().isoformat()
    proposal["rejection_reason"] = reason

    rejected_file = metrics_dir / "optimisations" / "rejected" / f"{proposal_id}.json"
    with open(rejected_file, "w") as f:
        json.dump(proposal, f, indent=2)

    pending_file.unlink()

    return {"success": True, "proposal_id": proposal_id, "reason": reason}


def rollback_agent(agent: str) -> dict:
    """
    Rollback an agent to its previous version.

    Args:
        agent: Agent name

    Returns:
        Rollback result
    """
    metrics_dir = get_metrics_dir()
    backup_dir = metrics_dir / "optimisations" / "backups"

    if not backup_dir.exists():
        return {"error": "No backups available"}

    # Find latest backup for this agent
    backups = sorted(backup_dir.glob(f"{agent}-*.md"), reverse=True)
    if not backups:
        return {"error": f"No backups found for agent: {agent}"}

    latest_backup = backups[0]
    plugin_dir = get_plugin_dir()
    agent_file = plugin_dir / "agents" / f"{agent}.md"

    if not agent_file.exists():
        return {"error": f"Agent not found: {agent}"}

    # Restore from backup
    shutil.copy(latest_backup, agent_file)

    return {
        "success": True,
        "agent": agent,
        "restored_from": str(latest_backup),
    }


def get_status() -> dict:
    """Get overall optimisation status."""
    metrics_dir = get_metrics_dir()
    config = load_config()

    pending = list_proposals("pending")
    applied = list_proposals("applied")

    return {
        "auto_optimisation_enabled": config.get("auto_optimisation_enabled", True),
        "min_runs_for_analysis": config.get("min_runs_for_analysis", 50),
        "pending_proposals": pending.get("count", 0),
        "applied_proposals": applied.get("count", 0),
    }


def main():
    """Main entry point for the optimiser tool."""
    if len(sys.argv) < 2:
        print(json.dumps(get_status(), indent=2))
        return

    command = sys.argv[1].lower()

    if command == "status":
        print(json.dumps(get_status(), indent=2))

    elif command == "analyse":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Agent name required"}))
            return
        agent = sys.argv[2]
        days = 14
        for i, arg in enumerate(sys.argv):
            if arg == "--days" and i + 1 < len(sys.argv):
                days = int(sys.argv[i + 1])
        print(json.dumps(analyse_agent(agent, days), indent=2))

    elif command == "context":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Agent name required"}))
            return
        agent = sys.argv[2]
        days = 14
        for i, arg in enumerate(sys.argv):
            if arg == "--days" and i + 1 < len(sys.argv):
                days = int(sys.argv[i + 1])
        print(json.dumps(prepare_analysis_context(agent, days), indent=2))

    elif command == "list":
        status = "pending"
        if len(sys.argv) > 2:
            status = sys.argv[2]
        print(json.dumps(list_proposals(status), indent=2))

    elif command == "get":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Proposal ID required"}))
            return
        proposal = get_proposal(sys.argv[2])
        print(json.dumps(proposal or {"error": "Proposal not found"}, indent=2))

    elif command == "apply":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Proposal ID required"}))
            return
        print(json.dumps(apply_proposal(sys.argv[2]), indent=2))

    elif command == "reject":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Proposal ID required"}))
            return
        reason = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        print(json.dumps(reject_proposal(sys.argv[2], reason), indent=2))

    elif command == "rollback":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Agent name required"}))
            return
        print(json.dumps(rollback_agent(sys.argv[2]), indent=2))

    else:
        print(json.dumps({
            "error": f"Unknown command: {command}",
            "available_commands": ["status", "analyse", "context", "list", "get", "apply", "reject", "rollback"]
        }, indent=2))


if __name__ == "__main__":
    main()
