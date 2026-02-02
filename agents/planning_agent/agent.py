import asyncio
import sys
import os
import hashlib
from pathlib import Path
from typing import Optional
from openai import AzureOpenAI

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.azure_config import AzureOpenAIConfig
from agents.code_understanding_agent import CodeUnderstandingAgent
from agents.planning_agent.models.schemas import (
    RequirementType,
    ImplementationPlan
)
from agents.planning_agent.tools import (
    requirement_analyzer,
    ambiguity_resolver,
    load_codebase_context,
    plan_generator,
    discussion_facilitator
)


class PlanningAgent:
    def __init__(self, azure_config=None):
        self.config = azure_config or AzureOpenAIConfig()

        config_dict = self.config.get_client_config()
        self.deployment_name = config_dict["deployment_name"]
        self.azure_client = AzureOpenAI(
            api_key=config_dict["api_key"],
            api_version=config_dict["api_version"],
            azure_endpoint=config_dict["endpoint"]
        )

    async def analyze_requirement(self, requirement_text, code_directory):
        print(f"\nAnalyzing requirement: {requirement_text}")
        print(f"Code directory: {code_directory}\n")

        codebase_context = load_codebase_context(code_directory)

        if not codebase_context.has_agent_knowledge:
            print("No existing codebase analysis found")
            should_analyze = input("Run CodeUnderstandingAgent? (yes/no): ")

            if should_analyze.lower() in ["yes", "y"]:
                codebase_context = await self._trigger_code_understanding(code_directory)
            else:
                print("Proceeding without codebase context")
        else:
            print("Found existing codebase analysis")

        classification = requirement_analyzer(
            requirement_text,
            codebase_context,
            self.azure_client,
            self.deployment_name
        )

        confirmed_classification, clarifications = ambiguity_resolver(classification)

        if confirmed_classification is None:
            additional_context = " ".join([c.answer for c in clarifications])
            new_requirement = f"{requirement_text}. Additional context: {additional_context}"

            classification = requirement_analyzer(
                new_requirement,
                codebase_context,
                self.azure_client,
                self.deployment_name
            )

            confirmed_classification, _ = ambiguity_resolver(classification)

            if confirmed_classification is None:
                print("\nUnable to classify requirement after clarification")
                return None

        discussion_clarifications = discussion_facilitator(
            requirement_text,
            confirmed_classification.requirement_type
        )

        all_clarifications = clarifications + discussion_clarifications

        print("\nGenerating implementation plan...")
        plan = plan_generator(
            requirement_text,
            confirmed_classification,
            codebase_context,
            all_clarifications,
            self.azure_client,
            self.deployment_name
        )

        self._save_plan(plan, code_directory)

        return plan

    async def _trigger_code_understanding(self, code_directory):
        print("\nTriggering CodeUnderstandingAgent...")
        print("=" * 60)

        code_agent = CodeUnderstandingAgent()
        await code_agent.analyze(
            project_path=code_directory,
            user_request="Full project analysis"
        )

        print("=" * 60)
        print("Codebase analysis complete\n")

        return load_codebase_context(code_directory)

    def _save_plan(self, plan, code_directory):
        planning_dir = os.path.join(code_directory, "agent_planning")
        requirements_dir = os.path.join(planning_dir, "requirements")
        classifications_dir = os.path.join(planning_dir, "classifications")
        plans_dir = os.path.join(planning_dir, "plans")

        os.makedirs(requirements_dir, exist_ok=True)
        os.makedirs(classifications_dir, exist_ok=True)
        os.makedirs(plans_dir, exist_ok=True)

        req_hash = hashlib.md5(plan.requirement_text.encode()).hexdigest()[:8]
        timestamp = plan.timestamp.replace(':', '').replace('-', '').split('.')[0]

        req_file = os.path.join(requirements_dir, f"{req_hash}_requirement.txt")
        with open(req_file, 'w', encoding='utf-8') as f:
            f.write(plan.requirement_text)

        classification_file = os.path.join(
            classifications_dir,
            f"{req_hash}_classification.md"
        )
        with open(classification_file, 'w', encoding='utf-8') as f:
            f.write(f"# Requirement Classification\n\n")
            f.write(f"Type: {plan.requirement_type.value}\n")
            f.write(f"Complexity: {plan.estimated_complexity.value}\n")
            f.write(f"Timestamp: {plan.timestamp}\n")

        plan_file = os.path.join(plans_dir, f"{plan.requirement_type.value.lower()}_{timestamp}.md")
        with open(plan_file, 'w', encoding='utf-8') as f:
            f.write(plan.markdown_content)

        print(f"\nPlan saved to: {plan_file}")
        print(f"Classification saved to: {classification_file}")
        print(f"Requirement saved to: {req_file}")


async def main():
    agent = PlanningAgent()

    plan = await agent.analyze_requirement(
        requirement_text="Add user authentication with JWT tokens",
        code_directory="/path/to/your/project"
    )

    if plan:
        print("\n" + "=" * 60)
        print("IMPLEMENTATION PLAN SUMMARY")
        print("=" * 60)
        print(f"\nRequirement: {plan.requirement_text}")
        print(f"Type: {plan.requirement_type.value}")
        print(f"Complexity: {plan.estimated_complexity.value}")
        print(f"\nSummary:")
        print(plan.summary)
        print(f"\nAffected Files: {len(plan.affected_files)}")
        for file_action in plan.affected_files:
            print(f"  - {file_action.action.value}: {file_action.file_path}")
        print(f"\nSteps: {len(plan.steps)}")
        print(f"\nDependencies: {', '.join(plan.dependencies)}")


if __name__ == "__main__":
    asyncio.run(main())
