from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class RequirementType(str, Enum):
    NEW_FEATURE_FROM_SCRATCH = "NEW_FEATURE_FROM_SCRATCH"
    MODIFY_EXISTING_CODE = "MODIFY_EXISTING_CODE"
    NEW_FEATURE_WITH_INTEGRATION = "NEW_FEATURE_WITH_INTEGRATION"
    UNDERSTAND_SPECIFIC_FILES = "UNDERSTAND_SPECIFIC_FILES"


class ActionType(str, Enum):
    CREATE = "CREATE"
    MODIFY = "MODIFY"
    DELETE = "DELETE"
    READ = "READ"


class ComplexityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RequirementClassification(BaseModel):
    requirement_type: RequirementType
    confidence: float
    reasoning: str
    ambiguities: List[str]
    related_files: List[str]
    requires_codebase_analysis: bool


class FileAction(BaseModel):
    file_path: str
    action: ActionType
    rationale: str


class ImplementationStep(BaseModel):
    step_number: int
    description: str
    files_affected: List[str]
    estimated_time: str
    dependencies: List[str]


class ImplementationPlan(BaseModel):
    requirement_text: str
    requirement_type: RequirementType
    summary: str
    affected_files: List[FileAction]
    steps: List[ImplementationStep]
    dependencies: List[str]
    risks: List[str]
    estimated_complexity: ComplexityLevel
    markdown_content: str
    timestamp: str


class CodebaseContext(BaseModel):
    has_agent_knowledge: bool
    imports_understanding: Optional[str]
    central_understanding: Optional[str]
    project_summary: Optional[str]


class UserClarification(BaseModel):
    question: str
    answer: str
