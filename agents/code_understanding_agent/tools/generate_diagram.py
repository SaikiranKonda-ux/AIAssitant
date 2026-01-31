import json
from openai import AzureOpenAI
from ..models.schemas import ImportMap, ImportDiagram


def generate_diagram(
    import_map: ImportMap,
    azure_client: AzureOpenAI,
    deployment_name: str
) -> ImportDiagram:
    system_prompt = """You are a code dependency visualization expert. Generate Mermaid diagrams showing module dependencies.

Create clear, hierarchical diagrams that show:
- Entry points at the top
- Module import relationships
- Circular dependencies marked with warning

Use Mermaid graph TD (top-down) syntax."""

    import_data = {
        "file_imports": import_map.file_imports,
        "entry_points": import_map.entry_points,
        "circular_deps": import_map.circular_deps
    }

    user_prompt = f"""Generate import dependency diagram for this codebase:

{json.dumps(import_data, indent=2)}

Return JSON with:
- mermaid_diagram: Valid Mermaid syntax (graph TD)
- text_summary: Human-readable dependency summary (3-5 sentences)
- critical_paths: List of critical execution paths from entry points"""

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

    return ImportDiagram(
        mermaid_diagram=result.get("mermaid_diagram", ""),
        text_summary=result.get("text_summary", ""),
        critical_paths=result.get("critical_paths", [])
    )
