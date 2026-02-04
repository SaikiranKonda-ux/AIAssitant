from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class AssessmentLevel(str, Enum):
    APPROVED = "APPROVED"
    NEEDS_REVISION = "NEEDS_REVISION"
    MAJOR_CONCERNS = "MAJOR_CONCERNS"


class SeverityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Concern(BaseModel):
    issue: str = Field(description="Description of the concern")
    severity: SeverityLevel = Field(description="Severity level")
    affected_area: str = Field(description="Which part is affected (file, component, etc.)")
    suggestion: str = Field(description="Suggested fix or improvement")
    rationale: str = Field(description="Why this is a concern")


class Alternative(BaseModel):
    approach: str = Field(description="Alternative approach description")
    pros: List[str] = Field(description="Advantages of this approach")
    cons: List[str] = Field(description="Disadvantages of this approach")
    complexity: str = Field(description="LOW, MEDIUM, or HIGH")


class CritiqueFeedback(BaseModel):
    overall_assessment: AssessmentLevel = Field(description="Overall quality assessment")
    confidence_score: float = Field(description="0.0-1.0 confidence in assessment", ge=0.0, le=1.0)

    strengths: List[str] = Field(description="Positive aspects of the plan")
    concerns: List[Concern] = Field(description="Issues identified")
    alternative_approaches: List[Alternative] = Field(default_factory=list, description="Alternative solutions")

    security_issues: List[str] = Field(default_factory=list, description="Security vulnerabilities")
    performance_concerns: List[str] = Field(default_factory=list, description="Performance issues")
    completeness_gaps: List[str] = Field(default_factory=list, description="Missing components")

    recommended_changes: List[str] = Field(description="Specific changes to make")

    iteration_number: int = Field(default=0, description="Which iteration of critique this is")
    reasoning: str = Field(description="Chain-of-thought reasoning for assessment")
    timestamp: str = Field(description="ISO timestamp of critique")
