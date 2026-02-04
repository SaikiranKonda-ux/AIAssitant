import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.azure_config import AzureOpenAIConfig
from config.azure_client import AzureClientManager
from models.shared_context import SharedContext, WorkflowState, MessageRole
from orchestrator.models.task_classification import TaskClassification
from orchestrator.tools import classify_task, plan_workflow_hybrid, estimate_task_cost, format_cost_estimate, StallDetector, HITLGates

from agents.research_agent import ResearchAgent
from agents.code_understanding_agent import CodeUnderstandingAgent
from agents.planning_agent import PlanningAgent
from agents.critic_agent import CriticAgent
from agents.code_writing_agent import CodeWritingAgent


class OrchestratorManager:
    def __init__(
        self,
        azure_config: Optional[AzureOpenAIConfig] = None,
        max_rounds: int = 10,
        max_stalls: int = 3
    ):
        self.config = azure_config or AzureOpenAIConfig()
        self.max_rounds = max_rounds
        self.max_stalls = max_stalls

        config_dict = self.config.get_client_config()
        self.deployment_name = config_dict["deployment_name"]
        self.azure_client = AzureClientManager.get_client(self.config)

        self.stall_detector = StallDetector(max_stalls=max_stalls)
        self.hitl_gates = HITLGates()
        self.agents = {}

    def _initialize_agents(self, code_directory: str):
        if not self.agents:
            self.agents = {
                "research": ResearchAgent(self.config),
                "code_understanding": CodeUnderstandingAgent(self.config),
                "planning": PlanningAgent(self.config),
                "critic": CriticAgent(self.config, max_iterations=2),
                "code_writing": CodeWritingAgent(self.config, code_directory=code_directory)
            }

    async def execute(self, user_requirement: str, code_directory: str, interactive: bool = True) -> SharedContext:
        print(f"\n{'='*80}")
        print(f"ORCHESTRATOR MANAGER: Magentic Pattern Orchestration")
        print(f"{'='*80}")
        print(f"Requirement: {user_requirement}")
        print(f"Code Directory: {code_directory}")
        print(f"Interactive Mode: {interactive}")
        print(f"Max Rounds: {self.max_rounds}, Max Stalls: {self.max_stalls}")
        print(f"{'='*80}\n")

        self._initialize_agents(code_directory)

        shared_context = SharedContext(
            requirement_text=user_requirement,
            code_directory=code_directory
        )

        shared_context.add_message(
            role=MessageRole.USER,
            content=user_requirement
        )

        shared_context.update_state(
            WorkflowState.CLASSIFYING,
            "Classifying task and planning workflow"
        )

        task_classification = classify_task(
            requirement_text=user_requirement,
            code_directory=code_directory,
            azure_client=self.azure_client,
            deployment_name=self.deployment_name
        )

        shared_context.task_classification = task_classification

        print(f"Task Classification:")
        print(f"  Type: {task_classification.task_type.value}")
        print(f"  Complexity: {task_classification.complexity.value}")
        print(f"  Confidence: {task_classification.confidence:.2f}")
        print(f"  Risk Level: {task_classification.risk_assessment.risk_level.value}\n")

        workflow = plan_workflow_hybrid(
            task_classification=task_classification,
            requirement_text=user_requirement,
            azure_client=self.azure_client,
            deployment_name=self.deployment_name
        )

        estimated_time, estimated_cost = estimate_task_cost(task_classification)
        shared_context.estimated_time = estimated_time
        shared_context.estimated_cost = estimated_cost

        print(f"Planned Workflow: {' → '.join(workflow)}")
        print(f"\n{format_cost_estimate(workflow, estimated_time, estimated_cost)}\n")

        if interactive:
            approval = input("Proceed with this workflow? (yes/no): ")
            if approval.lower() not in ["yes", "y"]:
                shared_context.update_state(
                    WorkflowState.FAILED,
                    "User declined workflow execution"
                )
                return shared_context

        for step_name in workflow:
            shared_context.increment_round()

            if shared_context.round_count > self.max_rounds:
                shared_context.update_state(
                    WorkflowState.FAILED,
                    f"Max rounds ({self.max_rounds}) exceeded"
                )
                break

            print(f"\n{'─'*80}")
            print(f"Round {shared_context.round_count}/{self.max_rounds}: Executing {step_name.upper()}")
            print(f"{'─'*80}")

            shared_context.start_agent_invocation(step_name)

            try:
                result = await self._execute_agent(step_name, shared_context)

                shared_context.complete_agent_invocation(
                    agent_name=step_name,
                    success=True,
                    output_summary=self._summarize_result(step_name, result)
                )

                self._update_context_with_result(shared_context, step_name, result)

            except Exception as e:
                error_msg = f"Agent {step_name} failed: {str(e)}"
                print(f"\n✗ Error: {error_msg}")

                shared_context.complete_agent_invocation(
                    agent_name=step_name,
                    success=False,
                    error_message=error_msg
                )

                shared_context.update_state(
                    WorkflowState.FAILED,
                    error_msg
                )
                break

            is_stalled, stall_reason = self.stall_detector.check_for_stall(shared_context)

            if is_stalled:
                print(f"\n⚠ Stall detected: {stall_reason}")
                shared_context.increment_stall()
                shared_context.update_state(WorkflowState.STALLED, stall_reason)

                if interactive:
                    action = self.hitl_gates.request_stall_intervention(shared_context, stall_reason)

                    if action == "abort":
                        shared_context.update_state(WorkflowState.FAILED, "User aborted after stall")
                        break
                    elif action == "skip":
                        print(f"Skipping {step_name}")
                        continue
                    elif action == "continue":
                        print(f"Continuing despite stall")
                        shared_context.update_state(WorkflowState.CLASSIFYING, "Resuming after stall")
                else:
                    print("Non-interactive mode: Aborting on stall")
                    shared_context.update_state(WorkflowState.FAILED, f"Stalled: {stall_reason}")
                    break

        if shared_context.workflow_state != WorkflowState.FAILED:
            shared_context.update_state(
                WorkflowState.COMPLETED,
                "Workflow completed successfully"
            )

            if shared_context.code_changes:
                shared_context.final_output = shared_context.code_changes[-1].summarize()
            elif shared_context.implementation_plan:
                shared_context.final_output = shared_context.implementation_plan.summary
            else:
                shared_context.final_output = "Workflow completed"

        print(f"\n{'='*80}")
        print(f"ORCHESTRATION COMPLETE")
        print(f"{'='*80}")
        print(f"Final State: {shared_context.workflow_state.value}")
        print(f"Total Rounds: {shared_context.round_count}")
        print(f"Agents Invoked: {len(shared_context.agent_invocations)}")
        print(f"{'='*80}\n")

        return shared_context

    async def _execute_agent(self, agent_name: str, shared_context: SharedContext):
        if agent_name == "research":
            shared_context.update_state(WorkflowState.RESEARCHING, "Researching best practices")
            agent = self.agents["research"]
            result = await agent.research(shared_context.requirement_text)
            return result

        elif agent_name == "code_understanding":
            shared_context.update_state(WorkflowState.CODE_UNDERSTANDING, "Analyzing codebase")
            agent = self.agents["code_understanding"]
            result = await agent.analyze(
                project_path=shared_context.code_directory,
                user_request="Full project analysis"
            )
            return result

        elif agent_name == "planning":
            shared_context.update_state(WorkflowState.PLANNING, "Creating implementation plan")
            agent = self.agents["planning"]
            result = await agent.analyze_requirement(
                requirement_text=shared_context.requirement_text,
                code_directory=shared_context.code_directory
            )
            return result

        elif agent_name == "critic":
            shared_context.update_state(WorkflowState.CRITIQUING, "Reviewing implementation plan")
            agent = self.agents["critic"]
            refined_plan, critiques = await agent.review(
                implementation_plan=shared_context.implementation_plan,
                codebase_context=shared_context.codebase_context,
                auto_refine=False
            )
            return (refined_plan, critiques)

        elif agent_name == "code_writing":
            shared_context.update_state(WorkflowState.CODING, "Writing code changes")
            agent = self.agents["code_writing"]
            result = await agent.execute_plan(
                implementation_plan=shared_context.implementation_plan,
                interactive=True,
                auto_commit=False
            )
            return result

        else:
            raise ValueError(f"Unknown agent: {agent_name}")

    def _update_context_with_result(self, shared_context: SharedContext, agent_name: str, result):
        if agent_name == "research":
            shared_context.research_findings = result
        elif agent_name == "code_understanding":
            shared_context.codebase_context = result
        elif agent_name == "planning":
            shared_context.implementation_plan = result
        elif agent_name == "critic":
            refined_plan, critiques = result
            shared_context.implementation_plan = refined_plan
            shared_context.critique_feedback.extend(critiques)
        elif agent_name == "code_writing":
            shared_context.code_changes.append(result)

    def _summarize_result(self, agent_name: str, result) -> str:
        if agent_name == "research":
            return f"Research complete: {result.total_sources} sources"
        elif agent_name == "code_understanding":
            return f"Analysis complete: {result.total_bundles_analyzed} bundles"
        elif agent_name == "planning":
            return f"Plan created: {len(result.affected_files)} files, {len(result.steps)} steps"
        elif agent_name == "critic":
            refined_plan, critiques = result
            return f"Critique complete: {len(critiques)} iterations, {critiques[-1].overall_assessment.value}"
        elif agent_name == "code_writing":
            return f"Code changes: {result.total_files_created} created, {result.total_files_modified} modified"
        else:
            return "Complete"
