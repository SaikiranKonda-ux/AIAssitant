import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.azure_config import AzureOpenAIConfig
from config.azure_client import AzureClientManager
from agents.critic_agent.models.schemas import CritiqueFeedback, AssessmentLevel
from agents.critic_agent.tools import evaluate_plan, refine_plan


class CriticAgent:
    def __init__(self, azure_config: Optional[AzureOpenAIConfig] = None, max_iterations: int = 2):
        self.config = azure_config or AzureOpenAIConfig()
        self.max_iterations = max_iterations

        config_dict = self.config.get_client_config()
        self.deployment_name = config_dict["deployment_name"]
        self.azure_client = AzureClientManager.get_client(self.config)

    async def review(self, implementation_plan, codebase_context=None, auto_refine: bool = False) -> tuple:
        print(f"\n{'='*60}")
        print(f"CRITIC AGENT: Reviewing Implementation Plan")
        print(f"{'='*60}")
        print(f"Plan Type: {implementation_plan.requirement_type.value}")
        print(f"Complexity: {implementation_plan.estimated_complexity.value}")
        print(f"Max Iterations: {self.max_iterations}")
        print(f"Auto-Refine: {auto_refine}\n")

        current_plan = implementation_plan
        all_critiques = []

        for iteration in range(self.max_iterations):
            print(f"\n--- Iteration {iteration + 1}/{self.max_iterations} ---")

            critique = evaluate_plan(
                implementation_plan=current_plan,
                codebase_context=codebase_context,
                azure_client=self.azure_client,
                deployment_name=self.deployment_name,
                iteration_number=iteration
            )

            all_critiques.append(critique)

            print(f"\nAssessment: {critique.overall_assessment.value}")
            print(f"Confidence: {critique.confidence_score:.2f}")
            print(f"Strengths: {len(critique.strengths)}")
            print(f"Concerns: {len(critique.concerns)}")

            if critique.concerns:
                print("\nConcerns identified:")
                for concern in critique.concerns[:3]:
                    print(f"  [{concern.severity.value}] {concern.issue}")

            if critique.overall_assessment == AssessmentLevel.APPROVED:
                print("\n✓ Plan APPROVED")
                return current_plan, all_critiques

            if iteration < self.max_iterations - 1:
                if auto_refine:
                    print("\nAuto-refining plan based on critique...")
                    current_plan = refine_plan(
                        original_plan=current_plan,
                        critique_feedback=critique,
                        azure_client=self.azure_client,
                        deployment_name=self.deployment_name
                    )
                    print("✓ Plan refined")
                else:
                    print("\nCritique complete. Manual review required.")
                    user_choice = input("\nRefine plan automatically? (yes/no): ")

                    if user_choice.lower() in ["yes", "y"]:
                        print("\nRefining plan based on critique...")
                        current_plan = refine_plan(
                            original_plan=current_plan,
                            critique_feedback=critique,
                            azure_client=self.azure_client,
                            deployment_name=self.deployment_name
                        )
                        print("✓ Plan refined")
                    else:
                        print("\nStopping refinement. Returning current state.")
                        return current_plan, all_critiques
            else:
                print(f"\nMax iterations ({self.max_iterations}) reached")

        print(f"\n{'='*60}")
        print(f"Critique complete: {len(all_critiques)} iteration(s)")
        print(f"Final assessment: {all_critiques[-1].overall_assessment.value}")
        print(f"{'='*60}\n")

        return current_plan, all_critiques

    def should_trigger_critique(self, plan) -> bool:
        if plan.estimated_complexity.value in ["MEDIUM", "HIGH"]:
            return True

        if len(plan.affected_files) > 5:
            return True

        if len(plan.risks) > 3:
            return True

        return False
