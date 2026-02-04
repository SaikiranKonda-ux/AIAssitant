import sys
import json
from pathlib import Path
from datetime import datetime
from openai import AzureOpenAI

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from config.prompts import CriticAgentPrompts
from agents.critic_agent.models.schemas import CritiqueFeedback, Concern, Alternative, AssessmentLevel, SeverityLevel


def evaluate_plan(implementation_plan, codebase_context, azure_client: AzureOpenAI, deployment_name: str, iteration_number: int = 0) -> CritiqueFeedback:
    plan_summary = f"""
Requirement: {implementation_plan.requirement_text}
Type: {implementation_plan.requirement_type.value}
Complexity: {implementation_plan.estimated_complexity.value}
Affected Files: {len(implementation_plan.affected_files)}
Steps: {len(implementation_plan.steps)}
Dependencies: {', '.join(implementation_plan.dependencies) if implementation_plan.dependencies else 'None'}
Risks: {len(implementation_plan.risks)}
"""

    codebase_summary = "No codebase context available"
    if codebase_context and codebase_context.has_agent_knowledge:
        codebase_summary = f"Project analyzed: {codebase_context.project_summary[:200] if codebase_context.project_summary else 'Available'}"

    system_prompt = CriticAgentPrompts.EVALUATE_PLAN_SYSTEM

    user_prompt = CriticAgentPrompts.EVALUATE_PLAN_USER.format(
        plan_summary=plan_summary,
        plan_details=implementation_plan.markdown_content[:2000],
        codebase_summary=codebase_summary,
        iteration_number=iteration_number
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

    concerns = []
    for concern_data in result.get("concerns", []):
        concerns.append(Concern(
            issue=concern_data.get("issue", ""),
            severity=SeverityLevel(concern_data.get("severity", "MEDIUM")),
            affected_area=concern_data.get("affected_area", ""),
            suggestion=concern_data.get("suggestion", ""),
            rationale=concern_data.get("rationale", "")
        ))

    alternatives = []
    for alt_data in result.get("alternative_approaches", []):
        alternatives.append(Alternative(
            approach=alt_data.get("approach", ""),
            pros=alt_data.get("pros", []),
            cons=alt_data.get("cons", []),
            complexity=alt_data.get("complexity", "MEDIUM")
        ))

    return CritiqueFeedback(
        overall_assessment=AssessmentLevel(result.get("overall_assessment", "NEEDS_REVISION")),
        confidence_score=result.get("confidence_score", 0.7),
        strengths=result.get("strengths", []),
        concerns=concerns,
        alternative_approaches=alternatives,
        security_issues=result.get("security_issues", []),
        performance_concerns=result.get("performance_concerns", []),
        completeness_gaps=result.get("completeness_gaps", []),
        recommended_changes=result.get("recommended_changes", []),
        iteration_number=iteration_number,
        reasoning=result.get("reasoning", ""),
        timestamp=datetime.now().isoformat()
    )
