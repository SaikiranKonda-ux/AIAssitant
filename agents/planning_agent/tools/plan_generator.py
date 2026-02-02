import json
from datetime import datetime
from openai import AzureOpenAI
from ..models.schemas import (
    RequirementClassification,
    ImplementationPlan,
    FileAction,
    ImplementationStep,
    ActionType,
    ComplexityLevel
)


def plan_generator(requirement_text, classification, codebase_context, clarifications, azure_client, deployment_name):
    system_prompt = """Generate detailed implementation plans for software requirements.

Include:
- Summary of changes
- Files to create/modify/delete with rationale
- Step-by-step implementation ordered by dependencies
- External dependencies needed
- Potential risks
- Complexity estimate (LOW/MEDIUM/HIGH)
- Complete markdown documentation"""

    codebase_info = "No existing codebase context"
    if codebase_context.has_agent_knowledge:
        codebase_info = f"Existing codebase summary:\n{codebase_context.project_summary}"

    clarification_text = ""
    if clarifications:
        clarification_text = "\n\nUser Clarifications:\n"
        for c in clarifications:
            clarification_text += f"Q: {c.question}\nA: {c.answer}\n"

    user_prompt = f"""Requirement: "{requirement_text}"

Type: {classification.requirement_type.value}
Reasoning: {classification.reasoning}

{codebase_info}
{clarification_text}

Generate implementation plan. Return JSON with:
- summary: brief overview (2-3 sentences)
- affected_files: array of objects with file_path, action (CREATE/MODIFY/DELETE/READ), rationale
- steps: array of objects with step_number, description, files_affected, estimated_time, dependencies
- dependencies: array of external dependencies (libraries, tools)
- risks: array of potential risks or considerations
- estimated_complexity: LOW | MEDIUM | HIGH
- markdown_content: complete markdown plan with:
  ## Summary
  ## Requirement
  ## Affected Files
  ## Implementation Steps
  ## Dependencies
  ## Risks and Considerations
  ## Estimated Complexity"""

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

    affected_files = []
    for file_data in result.get("affected_files", []):
        affected_files.append(FileAction(
            file_path=file_data.get("file_path", ""),
            action=ActionType(file_data.get("action", "CREATE")),
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
        requirement_text=requirement_text,
        requirement_type=classification.requirement_type,
        summary=result.get("summary", ""),
        affected_files=affected_files,
        steps=steps,
        dependencies=result.get("dependencies", []),
        risks=result.get("risks", []),
        estimated_complexity=ComplexityLevel(result.get("estimated_complexity", "MEDIUM")),
        markdown_content=result.get("markdown_content", ""),
        timestamp=datetime.now().isoformat()
    )
