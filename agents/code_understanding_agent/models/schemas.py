from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Tuple
from enum import Enum


class RequestScope(str, Enum):
    FULL_PROJECT = "FULL_PROJECT"
    SPECIFIC_MODULES = "SPECIFIC_MODULES"
    CROSS_CUTTING = "CROSS_CUTTING"
    DEPENDENCY_TRACE = "DEPENDENCY_TRACE"


class ChangeType(str, Enum):
    CODE_UPDATED = "CODE_UPDATED"
    FILES_ADDED = "FILES_ADDED"
    NONE = "NONE"


class FileInfo(BaseModel):
    path: str = Field(description="Absolute file path")
    size: int = Field(description="File size in bytes")
    extension: str = Field(description="File extension")
    line_count: int = Field(description="Number of lines in file")


class FileStructure(BaseModel):
    root_path: str = Field(description="Project root directory")
    directories: List[str] = Field(description="All directories found")
    files: List[FileInfo] = Field(description="All files with metadata")


class ImportInfo(BaseModel):
    module: str = Field(description="Imported module name")
    items: List[str] = Field(description="Specific items imported")
    is_relative: bool = Field(description="Whether import is relative")


class FileImports(BaseModel):
    file_path: str = Field(description="File containing imports")
    imports: List[ImportInfo] = Field(description="All imports in file")
    imported_by: List[str] = Field(description="Files that import this file")


class ImportMap(BaseModel):
    file_imports: Dict[str, List[str]] = Field(description="File to list of imported modules")
    dependency_graph: Dict[str, List[str]] = Field(description="Module to dependent modules")
    entry_points: List[str] = Field(description="Main entry point files")
    circular_deps: List[Tuple[str, str]] = Field(description="Circular dependency pairs")


class ImportDiagram(BaseModel):
    mermaid_diagram: str = Field(description="Mermaid syntax dependency diagram")
    text_summary: str = Field(description="Human-readable summary of dependencies")
    critical_paths: List[str] = Field(description="Critical execution paths identified")


class ClassifiedRequest(BaseModel):
    scope: RequestScope = Field(description="Scope of analysis requested")
    change_type: ChangeType = Field(description="Type of code change if rebasing")
    target_files: List[str] = Field(description="Specific files to analyze")
    aspects: List[str] = Field(description="Specific aspects to focus on")
    requires_full_analysis: bool = Field(description="Whether full project analysis needed")


class FileMetadata(BaseModel):
    path: str = Field(description="File path")
    line_count: int = Field(description="Total lines in file")
    imports: List[str] = Field(description="Modules this file imports")
    imported_by: List[str] = Field(description="Files that import this file")
    file_type: str = Field(description="File extension")


class Bundle(BaseModel):
    id: str = Field(description="Unique bundle identifier")
    files: List[FileMetadata] = Field(description="Files in this bundle")
    total_lines: int = Field(description="Total lines across all files")
    rationale: str = Field(description="Why these files are grouped")
    part_of_large_file: Optional[str] = Field(default=None, description="If split from large file")
    line_range: Optional[str] = Field(default=None, description="Line range if file split")


class BundlePlan(BaseModel):
    bundles: List[Bundle] = Field(description="All bundles created")
    planning_rationale: str = Field(description="Overall planning strategy explanation")
    total_bundles: int = Field(description="Total number of bundles")
    estimated_time_seconds: int = Field(description="Estimated processing time")


class BundleContent(BaseModel):
    bundle_id: str = Field(description="Bundle identifier")
    file_contents: Dict[str, str] = Field(description="File path to content mapping")
    total_lines_read: int = Field(description="Total lines read")


class ControlFlow(BaseModel):
    function_name: str = Field(description="Function containing control flow")
    file_path: str = Field(description="File containing function")
    conditions: List[str] = Field(description="Conditional logic descriptions")
    flow_description: str = Field(description="Overall flow explanation")


class BusinessRule(BaseModel):
    rule_name: str = Field(description="Name of business rule")
    file_path: str = Field(description="File containing rule")
    condition: str = Field(description="Rule condition")
    action: str = Field(description="Action taken when condition met")


class BundleAnalysis(BaseModel):
    bundle_id: str = Field(description="Bundle identifier")
    summary: str = Field(description="High-level summary of bundle")
    control_flows: List[ControlFlow] = Field(description="Control flows identified")
    business_rules: List[BusinessRule] = Field(description="Business rules found")
    key_functions: List[str] = Field(description="Important functions")
    dependencies: List[str] = Field(description="External dependencies")
    markdown_content: str = Field(description="Full markdown analysis")


class CentralUnderstanding(BaseModel):
    project_name: str = Field(description="Project name")
    summary: str = Field(description="Overall project summary")
    total_bundles_analyzed: int = Field(description="Number of bundles")
    control_flows: List[ControlFlow] = Field(description="All control flows")
    business_rules: List[BusinessRule] = Field(description="All business rules")
    cross_module_dependencies: List[str] = Field(description="Cross-module patterns")
    markdown_content: str = Field(description="Complete markdown content")
    timestamp: str = Field(description="When analysis completed")


class CacheStatus(BaseModel):
    imports_understanding_exists: bool = Field(description="Whether imports file exists")
    imports_understanding_valid: bool = Field(description="Whether imports file is current")
    cache_path: str = Field(description="Path to cache directory")
    full_logical_map_exists: bool = Field(description="Whether full map exists")
