import sys
import json
from pathlib import Path
from typing import List
from openai import AzureOpenAI

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.prompts import OrchestratorPrompts
from orchestrator.models.task_classification import TaskClassification, ComplexityLevel, TaskType


def plan_workflow_rule_based(task_classification: TaskClassification) -> List[str]:
    workflow = []

    if task_classification.requires_research:
        workflow.append("research")

    if task_classification.requires_code_understanding:
        workflow.append("code_understanding")

    if task_classification.requires_planning:
        workflow.append("planning")

    if task_classification.requires_critic:
        workflow.append("critic")

    if task_classification.requires_code_writing:
        workflow.append("code_writing")

    if not workflow:
        workflow = ["planning"]

    return workflow


def plan_workflow_llm_based(task_classification: TaskClassification, requirement_text: str, azure_client: AzureOpenAI, deployment_name: str) -> List[str]:
    system_prompt = OrchestratorPrompts.WORKFLOW_PLANNER_SYSTEM

    user_prompt = OrchestratorPrompts.WORKFLOW_PLANNER_USER.format(
        requirement_text=requirement_text,
        task_type=task_classification.task_type.value,
        complexity=task_classification.complexity.value,
        estimated_files=task_classification.estimated_files_affected,
        reasoning=task_classification.reasoning
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

    workflow = result.get("workflow", [])

    if not workflow:
        workflow = plan_workflow_rule_based(task_classification)

    return workflow


def plan_workflow_hybrid(task_classification: TaskClassification, requirement_text: str, azure_client: AzureOpenAI, deployment_name: str, use_llm_threshold: float = 0.6) -> List[str]:
    if task_classification.confidence >= 0.8 and task_classification.complexity == ComplexityLevel.LOW:
        return plan_workflow_rule_based(task_classification)

    if task_classification.confidence < use_llm_threshold or task_classification.complexity == ComplexityLevel.HIGH:
        return plan_workflow_llm_based(task_classification, requirement_text, azure_client, deployment_name)

    rule_based_workflow = plan_workflow_rule_based(task_classification)

    return rule_based_workflow
