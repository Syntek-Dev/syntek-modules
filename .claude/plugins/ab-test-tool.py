#!/usr/bin/env python3
"""
ab-test-tool.py

Manages A/B testing of agent prompt variants.
Creates tests, randomly selects variants, tracks results, and calculates statistical significance.
"""
import json
import sys
import os
import random
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional


def get_metrics_dir() -> Path:
    """Get the docs/METRICS directory path."""
    cwd = Path(os.getcwd())
    return cwd / "docs" / "METRICS"


def get_plugin_dir() -> Path:
    """Get the plugin directory (where agents are stored)."""
    # Try to find the plugin directory
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
        "variants",
        "ab-tests/active",
        "ab-tests/archive",
    ]
    for subdir in subdirs:
        (metrics_dir / subdir).mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load the metrics configuration."""
    config_path = get_metrics_dir() / "config.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            return json.load(f)
    return {"ab_testing_enabled": True}


def get_agent_prompt(agent: str) -> Optional[str]:
    """Get the current prompt for an agent."""
    plugin_dir = get_plugin_dir()
    agent_file = plugin_dir / "agents" / f"{agent}.md"
    if agent_file.exists():
        return agent_file.read_text()
    return None


def create_test(
    agent: str,
    variant_name: str,
    variant_content: str,
    description: str = "",
    weight: int = 50,
) -> dict:
    """
    Create a new A/B test for an agent.

    Args:
        agent: Agent name
        variant_name: Name for the variant (e.g., 'enhanced-security')
        variant_content: The modified prompt content
        description: Description of what this variant changes
        weight: Traffic weight (0-100)

    Returns:
        Test configuration
    """
    config = load_config()
    if not config.get("ab_testing_enabled", True):
        return {"error": "A/B testing is disabled"}

    ensure_directories()
    metrics_dir = get_metrics_dir()

    # Check if agent exists
    original_prompt = get_agent_prompt(agent)
    if not original_prompt:
        return {"error": f"Agent not found: {agent}"}

    # Create variant directory
    variant_dir = metrics_dir / "variants" / agent
    variant_dir.mkdir(parents=True, exist_ok=True)

    # Save baseline if not exists
    baseline_file = variant_dir / "baseline.md"
    if not baseline_file.exists():
        baseline_file.write_text(original_prompt)

    # Save variant
    variant_file = variant_dir / f"{variant_name}.md"
    variant_file.write_text(variant_content)

    # Check for existing test
    test_id = f"{agent}-test"
    test_file = metrics_dir / "ab-tests" / "active" / f"{test_id}.json"

    if test_file.exists():
        # Add variant to existing test
        with open(test_file, "r") as f:
            test_config = json.load(f)
        test_config["variants"].append({
            "id": variant_name,
            "file": f"variants/{agent}/{variant_name}.md",
            "weight": weight,
            "description": description,
        })
        # Rebalance weights
        total_variants = len(test_config["variants"])
        for v in test_config["variants"]:
            v["weight"] = 100 // total_variants
        test_config["updated"] = datetime.now().isoformat()
    else:
        # Create new test
        test_config = {
            "test_id": test_id,
            "agent": agent,
            "status": "active",
            "created": datetime.now().isoformat(),
            "variants": [
                {
                    "id": "baseline",
                    "file": f"variants/{agent}/baseline.md",
                    "weight": 100 - weight,
                    "description": "Original prompt",
                },
                {
                    "id": variant_name,
                    "file": f"variants/{agent}/{variant_name}.md",
                    "weight": weight,
                    "description": description,
                },
            ],
            "results": {
                "runs_per_variant": {},
                "satisfaction_per_variant": {},
            },
        }

    with open(test_file, "w") as f:
        json.dump(test_config, f, indent=2)

    return {
        "success": True,
        "test_id": test_id,
        "agent": agent,
        "variants": len(test_config["variants"]),
        "message": f"A/B test created for {agent} with variant '{variant_name}'",
    }


def select_variant(agent: str, session_id: Optional[str] = None) -> dict:
    """
    Select a variant for an agent run.

    Args:
        agent: Agent name
        session_id: Optional session ID for consistent assignment

    Returns:
        Selected variant information
    """
    config = load_config()
    if not config.get("ab_testing_enabled", True):
        return {"variant": None, "reason": "A/B testing disabled"}

    metrics_dir = get_metrics_dir()
    test_file = metrics_dir / "ab-tests" / "active" / f"{agent}-test.json"

    if not test_file.exists():
        return {"variant": None, "reason": "No active test for this agent"}

    with open(test_file, "r") as f:
        test_config = json.load(f)

    if test_config.get("status") != "active":
        return {"variant": None, "reason": "Test is not active"}

    variants = test_config.get("variants", [])
    if not variants:
        return {"variant": None, "reason": "No variants configured"}

    # Calculate cumulative weights
    total_weight = sum(v.get("weight", 0) for v in variants)
    if total_weight == 0:
        return {"variant": None, "reason": "All weights are zero"}

    # Use session hash for consistency or random for each run
    if session_id:
        seed = int(hashlib.md5(session_id.encode()).hexdigest()[:8], 16)
        random.seed(seed)

    roll = random.uniform(0, total_weight)
    cumulative = 0

    selected = variants[-1]  # Default to last
    for variant in variants:
        cumulative += variant.get("weight", 0)
        if roll <= cumulative:
            selected = variant
            break

    # Get the variant content
    variant_file = metrics_dir / selected["file"]
    variant_content = None
    if variant_file.exists():
        variant_content = variant_file.read_text()

    return {
        "variant": selected["id"],
        "test_id": test_config["test_id"],
        "file": selected["file"],
        "has_content": variant_content is not None,
    }


def update_results(agent: str, variant: str, satisfaction: Optional[int] = None) -> dict:
    """
    Update test results with a new run.

    Args:
        agent: Agent name
        variant: Variant that was used
        satisfaction: User satisfaction (-1, 0, 1)

    Returns:
        Updated results
    """
    metrics_dir = get_metrics_dir()
    test_file = metrics_dir / "ab-tests" / "active" / f"{agent}-test.json"

    if not test_file.exists():
        return {"error": "No active test for this agent"}

    with open(test_file, "r") as f:
        test_config = json.load(f)

    results = test_config.get("results", {})

    # Update run counts
    runs = results.get("runs_per_variant", {})
    runs[variant] = runs.get(variant, 0) + 1
    results["runs_per_variant"] = runs

    # Update satisfaction if provided
    if satisfaction is not None:
        sat = results.get("satisfaction_per_variant", {})
        if variant not in sat:
            sat[variant] = {"positive": 0, "negative": 0, "neutral": 0}
        if satisfaction > 0:
            sat[variant]["positive"] += 1
        elif satisfaction < 0:
            sat[variant]["negative"] += 1
        else:
            sat[variant]["neutral"] += 1
        results["satisfaction_per_variant"] = sat

    test_config["results"] = results
    test_config["updated"] = datetime.now().isoformat()

    with open(test_file, "w") as f:
        json.dump(test_config, f, indent=2)

    return {"success": True, "results": results}


def get_test_status(agent: str) -> dict:
    """
    Get the status of an A/B test.

    Args:
        agent: Agent name

    Returns:
        Test status and results
    """
    metrics_dir = get_metrics_dir()
    test_file = metrics_dir / "ab-tests" / "active" / f"{agent}-test.json"

    if not test_file.exists():
        return {"error": f"No active test for agent: {agent}"}

    with open(test_file, "r") as f:
        test_config = json.load(f)

    # Calculate satisfaction rates
    results = test_config.get("results", {})
    satisfaction = results.get("satisfaction_per_variant", {})
    runs = results.get("runs_per_variant", {})

    rates = {}
    for variant_id, sat_data in satisfaction.items():
        total = sat_data.get("positive", 0) + sat_data.get("negative", 0)
        if total > 0:
            rates[variant_id] = {
                "satisfaction_rate": round(sat_data.get("positive", 0) / total, 3),
                "total_rated": total,
                "total_runs": runs.get(variant_id, 0),
            }

    # Check for significance
    significance = calculate_significance(test_config)

    return {
        "test_id": test_config["test_id"],
        "agent": agent,
        "status": test_config.get("status"),
        "created": test_config.get("created"),
        "variants": [v["id"] for v in test_config.get("variants", [])],
        "runs_per_variant": runs,
        "satisfaction_rates": rates,
        "significance": significance,
    }


def calculate_significance(test_config: dict) -> dict:
    """
    Calculate statistical significance of A/B test results.
    Uses a simple chi-squared approximation.

    Args:
        test_config: Test configuration with results

    Returns:
        Significance analysis
    """
    results = test_config.get("results", {})
    satisfaction = results.get("satisfaction_per_variant", {})

    if len(satisfaction) < 2:
        return {"calculated": False, "reason": "Need at least 2 variants with feedback"}

    # Get the two main variants (baseline and first variant)
    variants = list(satisfaction.keys())[:2]

    data = []
    for v in variants:
        sat = satisfaction.get(v, {})
        positive = sat.get("positive", 0)
        negative = sat.get("negative", 0)
        total = positive + negative
        if total < 10:
            return {"calculated": False, "reason": f"Need at least 10 rated runs per variant (have {total} for {v})"}
        data.append({"variant": v, "positive": positive, "negative": negative, "total": total})

    # Calculate rates
    rate_a = data[0]["positive"] / data[0]["total"]
    rate_b = data[1]["positive"] / data[1]["total"]

    # Pooled rate
    pooled_positive = data[0]["positive"] + data[1]["positive"]
    pooled_total = data[0]["total"] + data[1]["total"]
    pooled_rate = pooled_positive / pooled_total

    # Standard error
    se = (pooled_rate * (1 - pooled_rate) * (1/data[0]["total"] + 1/data[1]["total"])) ** 0.5

    if se == 0:
        return {"calculated": False, "reason": "Cannot calculate - no variance"}

    # Z-score
    z_score = abs(rate_a - rate_b) / se

    # Approximate p-value (two-tailed)
    # Using rough approximation: p ≈ 2 * e^(-0.5 * z^2) for large z
    import math
    p_value = 2 * math.exp(-0.5 * z_score * z_score) if z_score < 4 else 0.0001

    significant = p_value < 0.05
    winner = None
    if significant:
        winner = data[0]["variant"] if rate_a > rate_b else data[1]["variant"]

    return {
        "calculated": True,
        "variants_compared": variants,
        "rates": {data[0]["variant"]: round(rate_a, 3), data[1]["variant"]: round(rate_b, 3)},
        "z_score": round(z_score, 3),
        "p_value": round(p_value, 4),
        "significant": significant,
        "winner": winner,
        "recommendation": f"Conclude test - {winner} is significantly better" if significant else "Continue collecting data",
    }


def conclude_test(agent: str, winner: Optional[str] = None) -> dict:
    """
    Conclude an A/B test and optionally apply the winner.

    Args:
        agent: Agent name
        winner: Winning variant to apply (or None to just archive)

    Returns:
        Conclusion result
    """
    metrics_dir = get_metrics_dir()
    test_file = metrics_dir / "ab-tests" / "active" / f"{agent}-test.json"

    if not test_file.exists():
        return {"error": f"No active test for agent: {agent}"}

    with open(test_file, "r") as f:
        test_config = json.load(f)

    # Update status
    test_config["status"] = "concluded"
    test_config["concluded"] = datetime.now().isoformat()
    test_config["winner"] = winner

    # Archive the test
    archive_dir = metrics_dir / "ab-tests" / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_file = archive_dir / f"{agent}-test-{datetime.now().strftime('%Y%m%d')}.json"

    with open(archive_file, "w") as f:
        json.dump(test_config, f, indent=2)

    # Remove active test
    test_file.unlink()

    result = {
        "success": True,
        "test_id": test_config["test_id"],
        "winner": winner,
        "archived_to": str(archive_file),
    }

    # Apply winner if specified and not baseline
    if winner and winner != "baseline":
        variant_file = metrics_dir / "variants" / agent / f"{winner}.md"
        if variant_file.exists():
            plugin_dir = get_plugin_dir()
            agent_file = plugin_dir / "agents" / f"{agent}.md"
            if agent_file.exists():
                # Backup current
                backup_file = plugin_dir / "agents" / f"{agent}.md.backup"
                shutil.copy(agent_file, backup_file)
                # Apply winner
                shutil.copy(variant_file, agent_file)
                result["applied"] = True
                result["backup"] = str(backup_file)

    return result


def list_tests() -> dict:
    """List all active A/B tests."""
    metrics_dir = get_metrics_dir()
    active_dir = metrics_dir / "ab-tests" / "active"

    if not active_dir.exists():
        return {"tests": [], "count": 0}

    tests = []
    for test_file in active_dir.glob("*.json"):
        with open(test_file, "r") as f:
            test_config = json.load(f)
        tests.append({
            "test_id": test_config.get("test_id"),
            "agent": test_config.get("agent"),
            "status": test_config.get("status"),
            "variants": len(test_config.get("variants", [])),
            "created": test_config.get("created"),
        })

    return {"tests": tests, "count": len(tests)}


def main():
    """Main entry point for the A/B test tool."""
    if len(sys.argv) < 2:
        print(json.dumps(list_tests(), indent=2))
        return

    command = sys.argv[1].lower()

    if command == "list":
        print(json.dumps(list_tests(), indent=2))

    elif command == "status":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Agent name required"}))
            return
        agent = sys.argv[2]
        print(json.dumps(get_test_status(agent), indent=2))

    elif command == "select":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Agent name required"}))
            return
        agent = sys.argv[2]
        session_id = sys.argv[3] if len(sys.argv) > 3 else None
        print(json.dumps(select_variant(agent, session_id), indent=2))

    elif command == "create":
        # Parse arguments
        agent = None
        variant_name = None
        description = ""

        i = 2
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg == "--agent" and i + 1 < len(sys.argv):
                agent = sys.argv[i + 1]
                i += 2
            elif arg == "--variant" and i + 1 < len(sys.argv):
                variant_name = sys.argv[i + 1]
                i += 2
            elif arg == "--description" and i + 1 < len(sys.argv):
                description = sys.argv[i + 1]
                i += 2
            else:
                i += 1

        if not agent or not variant_name:
            print(json.dumps({"error": "Required: --agent <name> --variant <name>"}))
            return

        # Read variant content from stdin
        print(json.dumps({"message": "Provide variant content via stdin or use the command to create manually"}))

    elif command == "conclude":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Agent name required"}))
            return
        agent = sys.argv[2]
        winner = sys.argv[3] if len(sys.argv) > 3 else None
        print(json.dumps(conclude_test(agent, winner), indent=2))

    elif command == "update":
        # Update results with a run
        agent = None
        variant = None
        satisfaction = None

        i = 2
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg == "--agent" and i + 1 < len(sys.argv):
                agent = sys.argv[i + 1]
                i += 2
            elif arg == "--variant" and i + 1 < len(sys.argv):
                variant = sys.argv[i + 1]
                i += 2
            elif arg == "--satisfaction" and i + 1 < len(sys.argv):
                satisfaction = int(sys.argv[i + 1])
                i += 2
            else:
                i += 1

        if not agent or not variant:
            print(json.dumps({"error": "Required: --agent <name> --variant <name>"}))
            return

        print(json.dumps(update_results(agent, variant, satisfaction), indent=2))

    else:
        print(json.dumps({
            "error": f"Unknown command: {command}",
            "available_commands": ["list", "status", "select", "create", "conclude", "update"]
        }, indent=2))


if __name__ == "__main__":
    main()
