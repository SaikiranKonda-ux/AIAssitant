from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class ModificationType(str, Enum):
    CREATE = "CREATE"
    MODIFY = "MODIFY"
    DELETE = "DELETE"


class ValidationStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class BackupInfo(BaseModel):
    file_path: str = Field(description="Original file path")
    backup_path: str = Field(description="Backup file path")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    file_size: int = Field(description="File size in bytes")
    checksum: str = Field(description="MD5 checksum of original file")


class FileModification(BaseModel):
    file_path: str = Field(description="Path to file being modified")
    modification_type: ModificationType = Field(description="Type of modification")

    original_content: Optional[str] = Field(default=None, description="Content before modification")
    new_content: Optional[str] = Field(default=None, description="Content after modification")

    backup_info: Optional[BackupInfo] = Field(default=None, description="Backup information")

    syntax_validation: ValidationStatus = Field(default=ValidationStatus.SKIPPED)
    syntax_errors: List[str] = Field(default_factory=list)

    user_approved: bool = Field(default=False, description="User confirmed change")
    applied: bool = Field(default=False, description="Change has been applied")

    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CodeChange(BaseModel):
    requirement_summary: str = Field(description="What this change implements")

    modifications: List[FileModification] = Field(description="All file modifications")

    total_files_created: int = Field(default=0)
    total_files_modified: int = Field(default=0)
    total_files_deleted: int = Field(default=0)

    all_backups_created: bool = Field(default=False)
    all_syntax_valid: bool = Field(default=False)
    user_approved_all: bool = Field(default=False)
    successfully_applied: bool = Field(default=False)

    git_commit_sha: Optional[str] = Field(default=None, description="Git commit hash if committed")
    rollback_available: bool = Field(default=False)

    started_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = Field(default=None)

    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    def summarize(self) -> str:
        return f"""Code Change Summary:
- Files Created: {self.total_files_created}
- Files Modified: {self.total_files_modified}
- Files Deleted: {self.total_files_deleted}
- Backups: {'✓' if self.all_backups_created else '✗'}
- Syntax Valid: {'✓' if self.all_syntax_valid else '✗'}
- User Approved: {'✓' if self.user_approved_all else '✗'}
- Applied: {'✓' if self.successfully_applied else '✗'}
- Git Commit: {self.git_commit_sha or 'N/A'}
- Errors: {len(self.errors)}
- Warnings: {len(self.warnings)}"""
