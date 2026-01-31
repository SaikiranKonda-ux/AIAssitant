import json
from openai import AzureOpenAI
from ..models.schemas import ClassifiedRequest, RequestScope, ChangeType, ImportMap


def request_classifier(
    user_request: str,
    import_map: ImportMap,
    azure_client: AzureOpenAI,
    deployment_name: str
) -> ClassifiedRequest:
    system_prompt = """You are a code analysis request classifier. Analyze user requests and determine:

1. Scope: FULL_PROJECT, SPECIFIC_MODULES, CROSS_CUTTING, DEPENDENCY_TRACE
2. Change type: CODE_UPDATED, FILES_ADDED, NONE
3. Target files: Specific files to analyze (use import map to find dependencies)
4. Aspects: Key aspects to focus on (auth, database, API, etc.)

Use import map to intelligently identify all related files."""

    import_summary = {
        "total_files": len(import_map.file_imports),
        "entry_points": import_map.entry_points,
        "sample_imports": dict(list(import_map.file_imports.items())[:10])
    }

    user_prompt = f"""Classify this request:
"{user_request}"

Import map context:
{json.dumps(import_summary, indent=2)}

Return JSON with:
- scope: FULL_PROJECT | SPECIFIC_MODULES | CROSS_CUTTING | DEPENDENCY_TRACE
- change_type: CODE_UPDATED | FILES_ADDED | NONE
- target_files: Array of specific file paths (use import map to find dependencies)
- aspects: Array of specific aspects (e.g., ["authentication", "database"])
- requires_full_analysis: boolean"""

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

    return ClassifiedRequest(
        scope=RequestScope(result.get("scope", "FULL_PROJECT")),
        change_type=ChangeType(result.get("change_type", "NONE")),
        target_files=result.get("target_files", []),
        aspects=result.get("aspects", []),
        requires_full_analysis=result.get("requires_full_analysis", True)
    )
