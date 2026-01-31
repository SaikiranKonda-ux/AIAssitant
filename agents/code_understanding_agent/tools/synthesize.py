import json
from typing import List
from datetime import datetime
from openai import AzureOpenAI
from ..models.schemas import BundleAnalysis, CentralUnderstanding, ControlFlow, BusinessRule


def synthesize(
    bundle_analyses: List[BundleAnalysis],
    project_name: str,
    azure_client: AzureOpenAI,
    deployment_name: str
) -> CentralUnderstanding:
    system_prompt = """You are a code synthesis expert in the REDUCE PHASE of analysis.

Aggregate multiple bundle analyses into a unified understanding. Tasks:

1. Deduplicate overlapping information across bundles
2. Identify cross-module dependencies and patterns
3. Rank control flows and business rules by importance
4. Create a comprehensive project overview

Generate master markdown documentation."""

    bundles_summary = []
    for analysis in bundle_analyses:
        bundles_summary.append({
            "bundle_id": analysis.bundle_id,
            "summary": analysis.summary,
            "control_flows_count": len(analysis.control_flows),
            "business_rules_count": len(analysis.business_rules),
            "key_functions": analysis.key_functions[:5],
            "dependencies": analysis.dependencies[:5]
        })

    user_prompt = f"""Synthesize {len(bundle_analyses)} bundle analyses into central understanding.

Bundles:
{json.dumps(bundles_summary, indent=2)}

Return JSON with:
- project_name: "{project_name}"
- summary: Overall project summary (4-6 sentences)
- total_bundles_analyzed: {len(bundle_analyses)}
- control_flows: Consolidated array (top 10 most important)
- business_rules: Consolidated array (top 10 most important)
- cross_module_dependencies: Array of patterns that span multiple bundles
- markdown_content: Complete markdown with:
  - Project Overview
  - Architecture Summary
  - Module Index (link to bundle .md files)
  - Critical Control Flows
  - Business Rules
  - Cross-Module Dependencies
  - Dependency Graph
- timestamp: current ISO timestamp"""

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

    all_control_flows = []
    for analysis in bundle_analyses:
        all_control_flows.extend(analysis.control_flows)

    all_business_rules = []
    for analysis in bundle_analyses:
        all_business_rules.extend(analysis.business_rules)

    return CentralUnderstanding(
        project_name=project_name,
        summary=result.get("summary", ""),
        total_bundles_analyzed=len(bundle_analyses),
        control_flows=all_control_flows[:10],
        business_rules=all_business_rules[:10],
        cross_module_dependencies=result.get("cross_module_dependencies", []),
        markdown_content=result.get("markdown_content", ""),
        timestamp=datetime.now().isoformat()
    )
