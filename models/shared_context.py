from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class WorkflowState(str, Enum):
    INITIALIZING = "INITIALIZING"
    CLASSIFYING = "CLASSIFYING"
    RESEARCHING = "RESEARCHING"
    CODE_UNDERSTANDING = "CODE_UNDERSTANDING"
    PLANNING = "PLANNING"
    CRITIQUING = "CRITIQUING"
    REFINING = "REFINING"
    CODING = "CODING"
    COMPLETED = "COMPLETED"
    STALLED = "STALLED"
    FAILED = "FAILED"


class MessageRole(str, Enum):
    USER = "USER"
    ORCHESTRATOR = "ORCHESTRATOR"
    AGENT = "AGENT"
    SYSTEM = "SYSTEM"


class Message(BaseModel):
    role: MessageRole = Field(description="Who sent the message")
    agent_name: Optional[str] = Field(default=None, description="Name of agent if role is AGENT")
    content: str = Field(description="Message content")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="ISO timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AgentInvocation(BaseModel):
    agent_name: str = Field(description="Name of agent invoked")
    started_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = Field(default=None)
    success: bool = Field(default=True)
    error_message: Optional[str] = Field(default=None)
    output_summary: Optional[str] = Field(default=None)


class SharedContext(BaseModel):
    requirement_text: str = Field(description="Original user requirement")
    code_directory: str = Field(description="Path to code directory")

    workflow_state: WorkflowState = Field(default=WorkflowState.INITIALIZING, description="Current workflow state")
    current_step: str = Field(default="initialization", description="Current step description")
    iteration_count: int = Field(default=0, description="Number of iterations in current workflow")

    task_classification: Optional[Any] = Field(default=None, description="TaskClassification from orchestrator")
    research_findings: Optional[Any] = Field(default=None, description="FinalReport from ResearchAgent")
    codebase_context: Optional[Any] = Field(default=None, description="CodebaseContext from CodeUnderstandingAgent")
    requirement_classification: Optional[Any] = Field(default=None, description="RequirementClassification from PlanningAgent")
    implementation_plan: Optional[Any] = Field(default=None, description="ImplementationPlan from PlanningAgent")
    critique_feedback: List[Any] = Field(default_factory=list, description="CritiqueFeedback from CriticAgent")
    code_changes: List[Any] = Field(default_factory=list, description="CodeChange from CodeWritingAgent")

    conversation_history: List[Message] = Field(default_factory=list, description="Full conversation log")
    agent_invocations: List[AgentInvocation] = Field(default_factory=list, description="Agent execution history")

    stall_count: int = Field(default=0, description="Number of times workflow stalled")
    round_count: int = Field(default=0, description="Total orchestration rounds")

    user_approvals: List[str] = Field(default_factory=list, description="User approval decisions")
    user_clarifications: List[Dict[str, str]] = Field(default_factory=list, description="User clarification Q&A")

    estimated_cost: float = Field(default=0.0, description="Estimated cost in USD")
    estimated_time: int = Field(default=0, description="Estimated time in seconds")

    final_output: Optional[str] = Field(default=None, description="Final workflow result")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def add_message(self, role: MessageRole, content: str, agent_name: Optional[str] = None, **kwargs):
        message = Message(role=role, content=content, agent_name=agent_name, metadata=kwargs)
        self.conversation_history.append(message)

    def start_agent_invocation(self, agent_name: str) -> AgentInvocation:
        invocation = AgentInvocation(agent_name=agent_name)
        self.agent_invocations.append(invocation)
        return invocation

    def complete_agent_invocation(self, agent_name: str, success: bool = True, error_message: Optional[str] = None, output_summary: Optional[str] = None):
        for invocation in reversed(self.agent_invocations):
            if invocation.agent_name == agent_name and invocation.completed_at is None:
                invocation.completed_at = datetime.now().isoformat()
                invocation.success = success
                invocation.error_message = error_message
                invocation.output_summary = output_summary
                break

    def increment_round(self):
        self.round_count += 1

    def increment_stall(self):
        self.stall_count += 1

    def update_state(self, new_state: WorkflowState, step_description: str):
        self.workflow_state = new_state
        self.current_step = step_description
        self.add_message(
            role=MessageRole.SYSTEM,
            content=f"Workflow state changed to {new_state.value}: {step_description}"
        )
