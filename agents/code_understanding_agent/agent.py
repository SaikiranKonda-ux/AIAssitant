import asyncio
import sys
import os
from pathlib import Path
from typing import List, Optional
from openai import AzureOpenAI

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.azure_config import AzureOpenAIConfig
from agents.code_understanding_agent.models.schemas import (
    ImportMap,
    ImportDiagram,
    ClassifiedRequest,
    BundlePlan,
    BundleAnalysis,
    CentralUnderstanding
)
from agents.code_understanding_agent.tools import (
    extract_imports,
    generate_diagram,
    file_search,
    request_classifier,
    create_metadata,
    bundle_planner,
    read_bundle,
    analyze_bundle,
    synthesize,
    write_markdown,
    read_markdown
)


class CodeUnderstandingAgent:
    def __init__(
        self,
        azure_config: Optional[AzureOpenAIConfig] = None,
        max_concurrent_bundles: int = 5,
        max_lines_per_bundle: int = 2000
    ):
        self.config = azure_config or AzureOpenAIConfig()
        self.max_concurrent_bundles = max_concurrent_bundles
        self.max_lines_per_bundle = max_lines_per_bundle

        config_dict = self.config.get_client_config()
        self.deployment_name = config_dict["deployment_name"]
        self.azure_client = AzureOpenAI(
            api_key=config_dict["api_key"],
            api_version=config_dict["api_version"],
            azure_endpoint=config_dict["endpoint"]
        )

    async def analyze(
        self,
        project_path: str,
        user_request: str
    ) -> CentralUnderstanding:
        print(f"\n🔍 Starting code analysis for: {project_path}")
        print(f"📝 Request: {user_request}\n")

        agent_knowledge_path = os.path.join(project_path, "agent_knowledge")

        imports_md = await self._ensure_imports_understanding(project_path, agent_knowledge_path)
        print(f"✓ Imports understanding ready")

        file_structure = file_search(project_path)
        print(f"✓ Found {len(file_structure.files)} files")

        classification = request_classifier(
            user_request,
            imports_md,
            self.azure_client,
            self.deployment_name
        )
        print(f"✓ Classified request: {classification.scope.value}")

        relevant_files = self._filter_files(file_structure.files, classification)
        print(f"✓ Relevant files: {len(relevant_files)}")

        if not await self._user_permission_gate(relevant_files):
            raise Exception("Analysis cancelled by user")

        metadata = create_metadata(relevant_files, imports_md)
        print(f"✓ Created metadata for {len(metadata)} files")

        plan = bundle_planner(
            metadata,
            self.azure_client,
            self.deployment_name,
            self.max_lines_per_bundle
        )
        print(f"✓ Planned {plan.total_bundles} bundles")
        print(f"  Planning: {plan.planning_rationale[:100]}...")

        bundle_contents = await self._execute_map_phase_read(plan.bundles)
        print(f"✓ Read {len(bundle_contents)} bundles")

        bundle_analyses = await self._execute_map_phase_analyze(bundle_contents)
        print(f"✓ Analyzed {len(bundle_analyses)} bundles")

        for analysis in bundle_analyses:
            write_markdown(
                analysis.markdown_content,
                agent_knowledge_path,
                f"{analysis.bundle_id}.md"
            )
        print(f"✓ Wrote {len(bundle_analyses)} bundle .md files")

        central = synthesize(
            bundle_analyses,
            os.path.basename(project_path),
            self.azure_client,
            self.deployment_name
        )

        write_markdown(
            central.markdown_content,
            agent_knowledge_path,
            "central_understanding.md"
        )
        print(f"✓ Generated central_understanding.md")

        return central

    async def _ensure_imports_understanding(
        self,
        project_path: str,
        agent_knowledge_path: str
    ) -> ImportMap:
        imports_file = os.path.join(agent_knowledge_path, "imports_understanding.md")

        if os.path.exists(imports_file):
            print("  Using cached imports_understanding.md")
            import_map_text = read_markdown(imports_file)
            return self._parse_imports_from_md(import_map_text, project_path)

        print("  Generating imports_understanding.md...")
        file_structure = file_search(project_path)

        py_files = [f.path for f in file_structure.files if f.extension == '.py']
        ipynb_files = [f.path for f in file_structure.files if f.extension == '.ipynb']

        all_files = py_files + ipynb_files
        import_map = extract_imports(all_files)

        diagram = generate_diagram(
            import_map,
            self.azure_client,
            self.deployment_name
        )

        md_content = self._format_imports_md(diagram)
        write_markdown(md_content, agent_knowledge_path, "imports_understanding.md")

        return import_map

    def _format_imports_md(self, diagram: ImportDiagram) -> str:
        return f"""# Imports Understanding

## Summary
{diagram.text_summary}

## Dependency Diagram
```mermaid
{diagram.mermaid_diagram}
```

## Critical Paths
{chr(10).join(f"- {path}" for path in diagram.critical_paths)}
"""

    def _parse_imports_from_md(self, md_content: str, project_path: str) -> ImportMap:
        file_structure = file_search(project_path)
        py_files = [f.path for f in file_structure.files if f.extension == '.py']
        ipynb_files = [f.path for f in file_structure.files if f.extension == '.ipynb']
        return extract_imports(py_files + ipynb_files)

    def _filter_files(self, files: List, classification: ClassifiedRequest) -> List:
        if classification.scope.value == "FULL_PROJECT":
            return files

        if classification.target_files:
            return [f for f in files if f.path in classification.target_files]

        return files

    async def _user_permission_gate(self, files: List) -> bool:
        py_files = [f for f in files if f.path.endswith('.py')]

        if len(py_files) <= 20:
            return True

        total_lines = sum(f.line_count for f in files)
        estimated_bundles = (total_lines // 1800) + 1
        estimated_time = estimated_bundles * 5
        estimated_cost = estimated_bundles * 0.015

        print(f"\n{'='*60}")
        print(f"ANALYSIS SCOPE REVIEW")
        print(f"{'='*60}")
        print(f"📁 Python files: {len(py_files)}")
        print(f"📄 Total lines: {total_lines:,}")
        print(f"📦 Estimated bundles: {estimated_bundles}")
        print(f"⏱️  Estimated time: ~{estimated_time}s")
        print(f"💰 Estimated cost: ~${estimated_cost:.2f}")
        print(f"{'='*60}\n")

        user_input = input("Proceed? (yes/no): ")
        return user_input.lower() in ["yes", "y"]

    async def _execute_map_phase_read(self, bundles: List) -> List:
        tasks = [asyncio.to_thread(read_bundle, bundle) for bundle in bundles]
        return await asyncio.gather(*tasks)

    async def _execute_map_phase_analyze(self, bundle_contents: List) -> List[BundleAnalysis]:
        all_analyses = []

        for i in range(0, len(bundle_contents), self.max_concurrent_bundles):
            batch = bundle_contents[i:i + self.max_concurrent_bundles]

            tasks = [
                asyncio.to_thread(
                    analyze_bundle,
                    content,
                    self.azure_client,
                    self.deployment_name
                )
                for content in batch
            ]

            batch_analyses = await asyncio.gather(*tasks)
            all_analyses.extend(batch_analyses)

            print(f"  Analyzed batch {i//self.max_concurrent_bundles + 1}/{(len(bundle_contents)-1)//self.max_concurrent_bundles + 1}")

        return all_analyses


async def main():
    agent = CodeUnderstandingAgent(
        max_concurrent_bundles=5,
        max_lines_per_bundle=2000
    )

    result = await agent.analyze(
        project_path="/path/to/your/project",
        user_request="Understand the entire project structure"
    )

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print(f"\nProject: {result.project_name}")
    print(f"Summary: {result.summary}")
    print(f"\nBundles analyzed: {result.total_bundles_analyzed}")
    print(f"Control flows: {len(result.control_flows)}")
    print(f"Business rules: {len(result.business_rules)}")


if __name__ == "__main__":
    asyncio.run(main())
