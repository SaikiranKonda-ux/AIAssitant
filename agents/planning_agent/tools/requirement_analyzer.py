import json
from openai import AzureOpenAI
from ..models.schemas import RequirementClassification, RequirementType


def requirement_analyzer(requirement_text, codebase_context, azure_client, deployment_name):
    system_prompt = """Analyze requirements and classify them into:
- NEW_FEATURE_FROM_SCRATCH: No existing code for this feature
- MODIFY_EXISTING_CODE: Changes to existing functionality
- NEW_FEATURE_WITH_INTEGRATION: New feature that connects with existing code
- UNDERSTAND_SPECIFIC_FILES: Request to analyze specific files

Provide confidence score 0.0-1.0, reasoning, ambiguities, and related files."""

    context_summary = "No codebase context available"
    if codebase_context.has_agent_knowledge:
        context_summary = f"Project summary: {codebase_context.project_summary[:500] if codebase_context.project_summary else 'Available'}"

    user_prompt = f"""Requirement: "{requirement_text}"

Codebase Context:
{context_summary}

Return JSON with:
- requirement_type: one of NEW_FEATURE_FROM_SCRATCH, MODIFY_EXISTING_CODE, NEW_FEATURE_WITH_INTEGRATION, UNDERSTAND_SPECIFIC_FILES
- confidence: 0.0-1.0 (above 0.8 is HIGH, 0.5-0.8 is MEDIUM, below 0.5 is LOW)
- reasoning: chain-of-thought explanation
- ambiguities: list of unclear points or questions
- related_files: list of file paths from codebase (if any)
- requires_codebase_analysis: boolean (true if need full codebase analysis)"""

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

    return RequirementClassification(
        requirement_type=RequirementType(result.get("requirement_type")),
        confidence=result.get("confidence", 0.0),
        reasoning=result.get("reasoning", ""),
        ambiguities=result.get("ambiguities", []),
        related_files=result.get("related_files", []),
        requires_codebase_analysis=result.get("requires_codebase_analysis", False)
    )
