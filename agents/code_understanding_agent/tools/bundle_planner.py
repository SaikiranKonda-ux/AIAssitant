import json
from typing import List
from openai import AzureOpenAI
from ..models.schemas import FileMetadata, Bundle, BundlePlan


def bundle_planner(
    metadata: List[FileMetadata],
    azure_client: AzureOpenAI,
    deployment_name: str,
    max_lines_per_bundle: int = 2000
) -> BundlePlan:
    system_prompt = f"""You are a code bundling strategist for the PLANNER MODULE.

CRITICAL CONSTRAINT: Each bundle MUST contain ≤{max_lines_per_bundle} lines total.

Rules:
1. Single file >{max_lines_per_bundle} lines → split into parts
   Example: user.py (3500 lines) → Bundle 1: lines 1-2000, Bundle 2: lines 2001-3500

2. Combine related files up to {max_lines_per_bundle} lines
   Example: auth/login.py (800) + auth/perms.py (700) + auth/utils.py (400) = 1900 ✓

3. Prioritize files with import relationships (files that import each other should be together)

4. Each bundle must have unique id, rationale, and exact line count

5. If splitting large file, set part_of_large_file and line_range fields"""

    metadata_json = []
    for m in metadata:
        metadata_json.append({
            "path": m.path,
            "lines": m.line_count,
            "imports": m.imports[:5],
            "imported_by": m.imported_by[:5],
            "file_type": m.file_type
        })

    user_prompt = f"""Create optimal bundles for {len(metadata)} files. Total lines: {sum(m.line_count for m in metadata)}

Metadata:
{json.dumps(metadata_json, indent=2)}

Return JSON with:
- bundles: Array of bundles, each with:
  - id: descriptive name (e.g., "auth_module" or "user_model_part1")
  - files: array of file metadata objects
  - total_lines: MUST be ≤{max_lines_per_bundle}
  - rationale: why these files grouped
  - part_of_large_file: file name if this is a split (or null)
  - line_range: "1-2000" if split (or null)
- planning_rationale: overall strategy explanation
- total_bundles: count
- estimated_time_seconds: 5 seconds per bundle"""

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

    bundles = []
    for bundle_data in result.get("bundles", []):
        bundle_files = []
        for file_data in bundle_data.get("files", []):
            matching_metadata = next((m for m in metadata if m.path == file_data.get("path")), None)
            if matching_metadata:
                bundle_files.append(matching_metadata)

        if bundle_files:
            bundles.append(Bundle(
                id=bundle_data.get("id", ""),
                files=bundle_files,
                total_lines=bundle_data.get("total_lines", 0),
                rationale=bundle_data.get("rationale", ""),
                part_of_large_file=bundle_data.get("part_of_large_file"),
                line_range=bundle_data.get("line_range")
            ))

    for bundle in bundles:
        if bundle.total_lines > max_lines_per_bundle:
            raise ValueError(f"Bundle {bundle.id} exceeds {max_lines_per_bundle} lines: {bundle.total_lines}")

    return BundlePlan(
        bundles=bundles,
        planning_rationale=result.get("planning_rationale", ""),
        total_bundles=len(bundles),
        estimated_time_seconds=result.get("estimated_time_seconds", len(bundles) * 5)
    )
