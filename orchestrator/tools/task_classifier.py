import sys
import json
from pathlib import Path
from openai import AzureOpenAI

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.prompts import OrchestratorPrompts
from orchestrator.models.task_classification import TaskClassification, ComplexityLevel, TaskType, RiskLevel, RiskAssessment


def classify_task(requirement_text: str, code_directory: str, azure_client: AzureOpenAI, deployment_name: str) -> TaskClassification:
    system_prompt = OrchestratorPrompts.TASK_CLASSIFIER_SYSTEM

    user_prompt = OrchestratorPrompts.TASK_CLASSIFIER_USER.format(
        requirement_text=requirement_text,
        code_directory=code_directory
    )

    response = azure_client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.2
    )

    result = json.loads(response.choices[0].message.content)

    risk_assessment = RiskAssessment(
        risk_level=RiskLevel(result.get("risk_assessment", {}).get("risk_level", "MEDIUM")),
        risk_factors=result.get("risk_assessment", {}).get("risk_factors", []),
        mitigation_strategies=result.get("risk_assessment", {}).get("mitigation_strategies", [])
    )

    return TaskClassification(
        task_type=TaskType(result.get("task_type", "CODE_MODIFICATION")),
        complexity=ComplexityLevel(result.get("complexity", "MEDIUM")),
        confidence=result.get("confidence", 0.7),
        requires_research=result.get("requires_research", False),
        requires_code_understanding=result.get("requires_code_understanding", False),
        requires_planning=result.get("requires_planning", True),
        requires_critic=result.get("requires_critic", False),
        requires_code_writing=result.get("requires_code_writing", False),
        estimated_files_affected=result.get("estimated_files_affected", 0),
        estimated_complexity_points=result.get("estimated_complexity_points", 1),
        risk_assessment=risk_assessment,
        reasoning=result.get("reasoning", ""),
        key_considerations=result.get("key_considerations", []),
        recommended_workflow=result.get("recommended_workflow", []),
        estimated_time_minutes=result.get("estimated_time_minutes", 5),
        estimated_cost_usd=result.get("estimated_cost_usd", 0.1)
    )
