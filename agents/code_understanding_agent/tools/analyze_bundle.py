import json
from openai import AzureOpenAI
from ..models.schemas import BundleContent, BundleAnalysis, ControlFlow, BusinessRule


def analyze_bundle(
    bundle_content: BundleContent,
    azure_client: AzureOpenAI,
    deployment_name: str
) -> BundleAnalysis:
    system_prompt = """You are a code analysis expert in the MAP PHASE of analysis.

Analyze code at FUNCTION-LEVEL granularity. Extract:

1. Control Flows: if/else, loops, switches, try/catch logic
2. Business Rules: validation, authorization, domain logic
3. Key Functions: most important functions and their purposes
4. Dependencies: external libraries used

Generate detailed markdown documentation."""

    files_preview = {}
    for file_path, content in bundle_content.file_contents.items():
        preview = content[:3000] if len(content) > 3000 else content
        files_preview[file_path] = preview

    user_prompt = f"""Analyze this code bundle: {bundle_content.bundle_id}

Files ({len(files_preview)}):
{json.dumps(files_preview, indent=2)}

Return JSON with:
- bundle_id: "{bundle_content.bundle_id}"
- summary: High-level summary (2-3 sentences)
- control_flows: Array of objects with:
  - function_name: name
  - file_path: path
  - conditions: array of condition descriptions
  - flow_description: explanation
- business_rules: Array of objects with:
  - rule_name: name
  - file_path: path
  - condition: rule condition
  - action: action taken
- key_functions: Array of function names
- dependencies: Array of external dependencies
- markdown_content: Full markdown documentation with:
  - File structure
  - Function signatures
  - Control flow diagrams (text)
  - Business rules
  - Usage examples"""

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

    control_flows = [
        ControlFlow(
            function_name=cf.get("function_name", ""),
            file_path=cf.get("file_path", ""),
            conditions=cf.get("conditions", []),
            flow_description=cf.get("flow_description", "")
        )
        for cf in result.get("control_flows", [])
    ]

    business_rules = [
        BusinessRule(
            rule_name=br.get("rule_name", ""),
            file_path=br.get("file_path", ""),
            condition=br.get("condition", ""),
            action=br.get("action", "")
        )
        for br in result.get("business_rules", [])
    ]

    return BundleAnalysis(
        bundle_id=bundle_content.bundle_id,
        summary=result.get("summary", ""),
        control_flows=control_flows,
        business_rules=business_rules,
        key_functions=result.get("key_functions", []),
        dependencies=result.get("dependencies", []),
        markdown_content=result.get("markdown_content", "")
    )
