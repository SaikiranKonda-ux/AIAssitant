import sys
import json
from pathlib import Path
from datetime import datetime
from openai import AzureOpenAI

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from config.prompts import CriticAgentPrompts


def refine_plan(original_plan, critique_feedback, azure_client: AzureOpenAI, deployment_name: str):
    concerns_text = "\n".join([
        f"- [{c.severity.value}] {c.issue} (in {c.affected_area})\n  Suggestion: {c.suggestion}"
        for c in critique_feedback.concerns
    ])

    recommendations_text = "\n".join([f"- {rec}" for rec in critique_feedback.recommended_changes])

    system_prompt = CriticAgentPrompts.REFINE_PLAN_SYSTEM

    user_prompt = CriticAgentPrompts.REFINE_PLAN_USER.format(
        original_plan=original_plan.markdown_content,
        concerns=concerns_text,
        recommendations=recommendations_text,
        reasoning=critique_feedback.reasoning
    )

    response = azure_client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.3
    )

    result = json.loads(response.choices[0].message.content)

    from agents.planning_agent.models.schemas import (
        ImplementationPlan,
        FileAction,
        ActionType,
        ImplementationStep,
        ComplexityLevel
    )

    affected_files = []
    for file_data in result.get("affected_files", []):
        affected_files.append(FileAction(
            file_path=file_data.get("file_path", ""),
            action=ActionType(file_data.get("action", "MODIFY")),
            rationale=file_data.get("rationale", "")
        ))

    steps = []
    for step_data in result.get("steps", []):
        steps.append(ImplementationStep(
            step_number=step_data.get("step_number", 0),
            description=step_data.get("description", ""),
            files_affected=step_data.get("files_affected", []),
            estimated_time=step_data.get("estimated_time", ""),
            dependencies=step_data.get("dependencies", [])
        ))

    return ImplementationPlan(
        requirement_text=original_plan.requirement_text,
        requirement_type=original_plan.requirement_type,
        summary=result.get("summary", original_plan.summary),
        affected_files=affected_files,
        steps=steps,
        dependencies=result.get("dependencies", original_plan.dependencies),
        risks=result.get("risks", original_plan.risks),
        estimated_complexity=ComplexityLevel(result.get("estimated_complexity", original_plan.estimated_complexity.value)),
        markdown_content=result.get("markdown_content", ""),
        timestamp=datetime.now().isoformat()
    )
