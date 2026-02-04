from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class ComplexityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TaskType(str, Enum):
    CODE_MODIFICATION = "CODE_MODIFICATION"
    NEW_FEATURE = "NEW_FEATURE"
    BUG_FIX = "BUG_FIX"
    REFACTORING = "REFACTORING"
    ANALYSIS_ONLY = "ANALYSIS_ONLY"
    RESEARCH_REQUIRED = "RESEARCH_REQUIRED"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskAssessment(BaseModel):
    risk_level: RiskLevel = Field(description="Overall risk level")
    risk_factors: List[str] = Field(description="Identified risk factors")
    mitigation_strategies: List[str] = Field(description="How to mitigate risks")


class TaskClassification(BaseModel):
    task_type: TaskType = Field(description="Type of task")
    complexity: ComplexityLevel = Field(description="Task complexity")
    confidence: float = Field(description="Classification confidence 0.0-1.0", ge=0.0, le=1.0)

    requires_research: bool = Field(default=False, description="Need ResearchAgent")
    requires_code_understanding: bool = Field(default=False, description="Need CodeUnderstandingAgent")
    requires_planning: bool = Field(default=True, description="Need PlanningAgent")
    requires_critic: bool = Field(default=False, description="Need CriticAgent")
    requires_code_writing: bool = Field(default=False, description="Need CodeWritingAgent")

    estimated_files_affected: int = Field(default=0, description="Number of files to modify")
    estimated_complexity_points: int = Field(default=1, description="Story points equivalent")

    risk_assessment: RiskAssessment = Field(description="Risk analysis")

    reasoning: str = Field(description="Why this classification")
    key_considerations: List[str] = Field(default_factory=list, description="Important points to consider")

    recommended_workflow: List[str] = Field(description="Ordered list of agents to use")
    estimated_time_minutes: int = Field(default=5, description="Estimated completion time")
    estimated_cost_usd: float = Field(default=0.1, description="Estimated API cost")
