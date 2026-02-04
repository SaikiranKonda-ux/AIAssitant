import os
import sys
from pathlib import Path
from typing import Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from agents.code_writing_agent.models.schemas import FileModification, ModificationType, ValidationStatus
from agents.code_writing_agent.tools.backup_manager import BackupManager
from agents.code_writing_agent.tools.syntax_validator import SyntaxValidator


class FileModifier:
    def __init__(self, backup_manager: Optional[BackupManager] = None):
        self.backup_manager = backup_manager or BackupManager()
        self.validator = SyntaxValidator()

    def prepare_modification(self, file_path: str, new_content: str, modification_type: ModificationType) -> FileModification:
        original_content = None
        backup_info = None

        if modification_type in [ModificationType.MODIFY, ModificationType.DELETE]:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()

                backup_info = self.backup_manager.create_backup(file_path)

        modification = FileModification(
            file_path=file_path,
            modification_type=modification_type,
            original_content=original_content,
            new_content=new_content,
            backup_info=backup_info
        )

        if modification_type != ModificationType.DELETE and new_content:
            is_valid, errors = self.validator.validate_content_before_write(file_path, new_content)
            modification.syntax_validation = ValidationStatus.PASSED if is_valid else ValidationStatus.FAILED
            modification.syntax_errors = errors

        return modification

    def apply_modification(self, modification: FileModification) -> Tuple[bool, Optional[str]]:
        if not modification.user_approved:
            return False, "Modification not approved by user"

        if modification.syntax_validation == ValidationStatus.FAILED:
            return False, f"Syntax validation failed: {'; '.join(modification.syntax_errors)}"

        try:
            if modification.modification_type == ModificationType.CREATE:
                os.makedirs(os.path.dirname(modification.file_path), exist_ok=True)
                with open(modification.file_path, 'w', encoding='utf-8') as f:
                    f.write(modification.new_content)

            elif modification.modification_type == ModificationType.MODIFY:
                with open(modification.file_path, 'w', encoding='utf-8') as f:
                    f.write(modification.new_content)

            elif modification.modification_type == ModificationType.DELETE:
                if os.path.exists(modification.file_path):
                    os.remove(modification.file_path)

            modification.applied = True
            return True, None

        except Exception as e:
            error_msg = f"Failed to apply modification: {str(e)}"

            if modification.backup_info:
                if self.backup_manager.restore_from_backup(modification.backup_info):
                    error_msg += " (backup restored)"

            return False, error_msg

    def rollback_modification(self, modification: FileModification) -> bool:
        if not modification.backup_info:
            return False

        return self.backup_manager.restore_from_backup(modification.backup_info)

    def show_diff(self, modification: FileModification) -> str:
        if not modification.original_content or not modification.new_content:
            return "No diff available"

        original_lines = modification.original_content.splitlines()
        new_lines = modification.new_content.splitlines()

        diff_lines = []
        diff_lines.append(f"--- {modification.file_path} (original)")
        diff_lines.append(f"+++ {modification.file_path} (new)")

        max_lines = max(len(original_lines), len(new_lines))

        for i in range(min(max_lines, 20)):
            if i < len(original_lines):
                orig_line = original_lines[i]
                if i >= len(new_lines) or orig_line != new_lines[i]:
                    diff_lines.append(f"- {orig_line}")

            if i < len(new_lines):
                new_line = new_lines[i]
                if i >= len(original_lines) or original_lines[i] != new_line:
                    diff_lines.append(f"+ {new_line}")

        if max_lines > 20:
            diff_lines.append(f"... ({max_lines - 20} more lines)")

        return "\n".join(diff_lines)
