import sys
from pathlib import Path
from typing import Optional, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from models.shared_context import SharedContext


class HITLGates:
    @staticmethod
    def request_workflow_approval(workflow: list, estimated_time: int, estimated_cost: float) -> bool:
        print(f"\n{'='*60}")
        print("WORKFLOW APPROVAL REQUIRED")
        print(f"{'='*60}")
        print(f"Planned Workflow: {' → '.join(workflow)}")
        print(f"Estimated Time: {estimated_time} minutes")
        print(f"Estimated Cost: ${estimated_cost:.2f}")
        print(f"{'='*60}")

        response = input("\nProceed with this workflow? (yes/no): ")
        approved = response.lower() in ["yes", "y"]

        if approved:
            print("✓ Workflow approved\n")
        else:
            print("✗ Workflow rejected by user\n")

        return approved

    @staticmethod
    def request_stall_intervention(shared_context: SharedContext, stall_reason: str) -> str:
        print(f"\n{'='*60}")
        print("WORKFLOW STALL DETECTED")
        print(f"{'='*60}")
        print(f"Reason: {stall_reason}")
        print(f"Current State: {shared_context.workflow_state.value}")
        print(f"Rounds Completed: {shared_context.round_count}")
        print(f"Stall Count: {shared_context.stall_count}")
        print(f"{'='*60}")
        print("\nOptions:")
        print("  1. Continue - Attempt to continue workflow")
        print("  2. Retry - Retry last agent")
        print("  3. Skip - Skip current step and continue")
        print("  4. Abort - Terminate workflow")
        print(f"{'='*60}")

        response = input("\nYour choice (1-4): ").strip()

        if response == "1":
            print("✓ Continuing workflow\n")
            return "continue"
        elif response == "2":
            print("✓ Retrying last agent\n")
            return "retry"
        elif response == "3":
            print("✓ Skipping current step\n")
            return "skip"
        else:
            print("✓ Aborting workflow\n")
            return "abort"

    @staticmethod
    def request_plan_review(implementation_plan) -> bool:
        print(f"\n{'='*60}")
        print("IMPLEMENTATION PLAN REVIEW")
        print(f"{'='*60}")
        print(f"Requirement: {implementation_plan.requirement_text}")
        print(f"Complexity: {implementation_plan.estimated_complexity.value}")
        print(f"Affected Files: {len(implementation_plan.affected_files)}")
        print(f"Steps: {len(implementation_plan.steps)}")

        if implementation_plan.risks:
            print(f"\nRisks:")
            for risk in implementation_plan.risks[:3]:
                print(f"  - {risk}")

        print(f"{'='*60}")

        response = input("\nApprove this plan? (yes/no): ")
        approved = response.lower() in ["yes", "y"]

        if approved:
            print("✓ Plan approved\n")
        else:
            print("✗ Plan rejected by user\n")

        return approved

    @staticmethod
    def request_code_changes_approval(code_change) -> bool:
        print(f"\n{'='*60}")
        print("CODE CHANGES APPROVAL")
        print(f"{'='*60}")
        print(code_change.summarize())
        print(f"{'='*60}")

        response = input("\nApprove these code changes? (yes/no): ")
        approved = response.lower() in ["yes", "y"]

        if approved:
            print("✓ Code changes approved\n")
        else:
            print("✗ Code changes rejected by user\n")

        return approved

    @staticmethod
    def gather_user_feedback(prompt: str) -> str:
        print(f"\n{'='*60}")
        print("USER INPUT REQUIRED")
        print(f"{'='*60}")
        print(prompt)
        print(f"{'='*60}")

        response = input("\nYour response: ")
        return response.strip()

    @staticmethod
    def confirm_action(action_description: str) -> bool:
        print(f"\n{action_description}")
        response = input("Confirm? (yes/no): ")
        return response.lower() in ["yes", "y"]

    @staticmethod
    def display_progress(shared_context: SharedContext):
        print(f"\n{'─'*60}")
        print(f"Progress Update:")
        print(f"  State: {shared_context.workflow_state.value}")
        print(f"  Round: {shared_context.round_count}")
        print(f"  Agents Invoked: {len(shared_context.agent_invocations)}")

        if shared_context.agent_invocations:
            last_agent = shared_context.agent_invocations[-1]
            status = "✓" if last_agent.success else "✗"
            print(f"  Last Agent: {status} {last_agent.agent_name}")

        print(f"{'─'*60}\n")
