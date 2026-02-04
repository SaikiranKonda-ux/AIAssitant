from typing import List, Tuple


AGENT_COSTS = {
    "research": {
        "time_minutes": 3,
        "cost_usd": 0.15,
        "tokens_estimate": 3000
    },
    "code_understanding": {
        "time_minutes": 5,
        "cost_usd": 0.25,
        "tokens_estimate": 5000
    },
    "planning": {
        "time_minutes": 2,
        "cost_usd": 0.10,
        "tokens_estimate": 2000
    },
    "critic": {
        "time_minutes": 2,
        "cost_usd": 0.12,
        "tokens_estimate": 2500
    },
    "code_writing": {
        "time_minutes": 3,
        "cost_usd": 0.08,
        "tokens_estimate": 1500
    }
}


def estimate_workflow_cost(workflow: List[str]) -> Tuple[int, float, int]:
    total_time = 0
    total_cost = 0.0
    total_tokens = 0

    for agent_name in workflow:
        if agent_name in AGENT_COSTS:
            total_time += AGENT_COSTS[agent_name]["time_minutes"]
            total_cost += AGENT_COSTS[agent_name]["cost_usd"]
            total_tokens += AGENT_COSTS[agent_name]["tokens_estimate"]

    overhead_time = 1
    overhead_cost = 0.02

    total_time += overhead_time
    total_cost += overhead_cost

    return total_time, total_cost, total_tokens


def estimate_task_cost(task_classification) -> Tuple[int, float]:
    workflow = task_classification.recommended_workflow

    total_time, total_cost, _ = estimate_workflow_cost(workflow)

    complexity_multiplier = {
        "LOW": 1.0,
        "MEDIUM": 1.5,
        "HIGH": 2.5
    }

    multiplier = complexity_multiplier.get(task_classification.complexity.value, 1.0)

    final_time = int(total_time * multiplier)
    final_cost = round(total_cost * multiplier, 2)

    return final_time, final_cost


def format_cost_estimate(workflow: List[str], total_time: int, total_cost: float) -> str:
    lines = []
    lines.append("Cost Estimate:")
    lines.append("=" * 40)

    for agent_name in workflow:
        if agent_name in AGENT_COSTS:
            agent_cost = AGENT_COSTS[agent_name]
            lines.append(f"  {agent_name.capitalize():<20} {agent_cost['time_minutes']:>2} min   ${agent_cost['cost_usd']:.2f}")

    lines.append("-" * 40)
    lines.append(f"  {'Total':<20} {total_time:>2} min   ${total_cost:.2f}")
    lines.append("=" * 40)

    return "\n".join(lines)
