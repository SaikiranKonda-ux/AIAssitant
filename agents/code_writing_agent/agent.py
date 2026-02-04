import sys
import os
from pathlib import Path
from typing import Optional, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.azure_config import AzureOpenAIConfig
from config.azure_client import AzureClientManager
from agents.code_writing_agent.models.schemas import CodeChange, FileModification, ModificationType, ValidationStatus
from agents.code_writing_agent.tools import BackupManager, FileModifier, GitIntegration


class CodeWritingAgent:
    def __init__(self, azure_config: Optional[AzureOpenAIConfig] = None, code_directory: str = "."):
        self.config = azure_config or AzureOpenAIConfig()
        self.code_directory = code_directory

        config_dict = self.config.get_client_config()
        self.deployment_name = config_dict["deployment_name"]
        self.azure_client = AzureClientManager.get_client(self.config)

        self.backup_manager = BackupManager(os.path.join(code_directory, ".code_agent_backups"))
        self.file_modifier = FileModifier(self.backup_manager)
        self.git_integration = GitIntegration(code_directory)

    async def execute_plan(self, implementation_plan, interactive: bool = True, auto_commit: bool = False) -> CodeChange:
        print(f"\n{'='*60}")
        print(f"CODE WRITING AGENT: Executing Implementation Plan")
        print(f"{'='*60}")
        print(f"Plan: {implementation_plan.requirement_text}")
        print(f"Files to modify: {len(implementation_plan.affected_files)}")
        print(f"Interactive mode: {interactive}")
        print(f"Auto-commit: {auto_commit}\n")

        code_change = CodeChange(
            requirement_summary=implementation_plan.summary
        )

        modifications = []

        for file_action in implementation_plan.affected_files:
            file_path = os.path.join(self.code_directory, file_action.file_path)

            if file_action.action.value == "CREATE":
                modification_type = ModificationType.CREATE
                new_content = self._generate_file_content(file_action, implementation_plan)
            elif file_action.action.value == "MODIFY":
                modification_type = ModificationType.MODIFY
                new_content = self._generate_file_content(file_action, implementation_plan)
            elif file_action.action.value == "DELETE":
                modification_type = ModificationType.DELETE
                new_content = None
            else:
                continue

            modification = self.file_modifier.prepare_modification(
                file_path=file_path,
                new_content=new_content,
                modification_type=modification_type
            )

            if interactive:
                approved = self._request_user_approval(modification)
                modification.user_approved = approved
            else:
                modification.user_approved = True

            modifications.append(modification)

        code_change.modifications = modifications

        code_change.all_backups_created = all(
            m.backup_info is not None or m.modification_type == ModificationType.CREATE
            for m in modifications
        )

        code_change.all_syntax_valid = all(
            m.syntax_validation != ValidationStatus.FAILED
            for m in modifications
        )

        code_change.user_approved_all = all(m.user_approved for m in modifications)

        if code_change.user_approved_all:
            print("\nApplying modifications...")

            for modification in modifications:
                success, error = self.file_modifier.apply_modification(modification)

                if success:
                    if modification.modification_type == ModificationType.CREATE:
                        code_change.total_files_created += 1
                    elif modification.modification_type == ModificationType.MODIFY:
                        code_change.total_files_modified += 1
                    elif modification.modification_type == ModificationType.DELETE:
                        code_change.total_files_deleted += 1

                    print(f"  ✓ {modification.modification_type.value}: {modification.file_path}")
                else:
                    code_change.errors.append(error)
                    print(f"  ✗ {modification.modification_type.value}: {modification.file_path} - {error}")

            code_change.successfully_applied = len(code_change.errors) == 0

            if code_change.successfully_applied and self.git_integration.is_git_repo():
                if auto_commit or (interactive and self._request_git_commit()):
                    file_paths = [m.file_path for m in modifications if m.applied]
                    commit_message = f"AI: {implementation_plan.summary}\n\nImplementation plan executed by CodeWritingAgent"

                    success, commit_sha, error = self.git_integration.commit(commit_message, file_paths)

                    if success:
                        code_change.git_commit_sha = commit_sha
                        code_change.rollback_available = True
                        print(f"\n✓ Git commit: {commit_sha[:8]}")
                    else:
                        code_change.warnings.append(f"Git commit failed: {error}")
                        print(f"\n⚠ Git commit failed: {error}")

        else:
            print("\n✗ Not all modifications approved. Skipping execution.")

        print(f"\n{'='*60}")
        print(code_change.summarize())
        print(f"{'='*60}\n")

        return code_change

    def _generate_file_content(self, file_action, implementation_plan) -> str:
        return f"# AI-generated file for: {file_action.file_path}\n# TODO: Implement based on plan\n"

    def _request_user_approval(self, modification: FileModification) -> bool:
        print(f"\n--- {modification.modification_type.value}: {modification.file_path} ---")

        if modification.syntax_validation == ValidationStatus.FAILED:
            print(f"⚠ SYNTAX ERRORS:")
            for error in modification.syntax_errors:
                print(f"  - {error}")
            print("\nThis file has syntax errors. Approve anyway?")

        if modification.modification_type == ModificationType.DELETE:
            print("This file will be DELETED.")
        elif modification.new_content:
            print(f"\nPreview (first 500 chars):")
            print(modification.new_content[:500])
            if len(modification.new_content) > 500:
                print("...")

        choice = input(f"\nApprove this {modification.modification_type.value}? (yes/no): ")
        return choice.lower() in ["yes", "y"]

    def _request_git_commit(self) -> bool:
        choice = input("\nCommit changes to git? (yes/no): ")
        return choice.lower() in ["yes", "y"]

    def rollback(self, code_change: CodeChange) -> bool:
        if code_change.git_commit_sha and code_change.rollback_available:
            print(f"Rolling back to commit before {code_change.git_commit_sha[:8]}...")

            success, error = self.git_integration.rollback_to_commit(
                code_change.git_commit_sha + "~1",
                hard=True
            )

            if success:
                print("✓ Git rollback successful")
                return True
            else:
                print(f"✗ Git rollback failed: {error}")

        print("Attempting file-level rollback...")
        all_success = True

        for modification in code_change.modifications:
            if modification.applied and modification.backup_info:
                if self.file_modifier.rollback_modification(modification):
                    print(f"  ✓ Restored: {modification.file_path}")
                else:
                    print(f"  ✗ Failed to restore: {modification.file_path}")
                    all_success = False

        return all_success
