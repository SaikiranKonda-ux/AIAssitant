import subprocess
import os
from typing import Optional, Tuple, List


class GitIntegration:
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def is_git_repo(self) -> bool:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_current_branch(self) -> Optional[str]:
        if not self.is_git_repo():
            return None

        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        return None

    def stage_files(self, file_paths: List[str]) -> Tuple[bool, Optional[str]]:
        if not self.is_git_repo():
            return False, "Not a git repository"

        try:
            for file_path in file_paths:
                result = subprocess.run(
                    ["git", "add", file_path],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    return False, f"Failed to stage {file_path}: {result.stderr}"

            return True, None

        except Exception as e:
            return False, str(e)

    def commit(self, message: str, file_paths: Optional[List[str]] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        if not self.is_git_repo():
            return False, None, "Not a git repository"

        try:
            if file_paths:
                success, error = self.stage_files(file_paths)
                if not success:
                    return False, None, error

            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return False, None, f"Commit failed: {result.stderr}"

            commit_sha = self.get_last_commit_sha()
            return True, commit_sha, None

        except Exception as e:
            return False, None, str(e)

    def get_last_commit_sha(self) -> Optional[str]:
        if not self.is_git_repo():
            return None

        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        return None

    def rollback_to_commit(self, commit_sha: str, hard: bool = False) -> Tuple[bool, Optional[str]]:
        if not self.is_git_repo():
            return False, "Not a git repository"

        try:
            reset_type = "--hard" if hard else "--soft"
            result = subprocess.run(
                ["git", "reset", reset_type, commit_sha],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return False, f"Rollback failed: {result.stderr}"

            return True, None

        except Exception as e:
            return False, str(e)

    def get_status(self) -> Optional[str]:
        if not self.is_git_repo():
            return None

        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        return None

    def create_branch(self, branch_name: str) -> Tuple[bool, Optional[str]]:
        if not self.is_git_repo():
            return False, "Not a git repository"

        try:
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return False, f"Failed to create branch: {result.stderr}"

            return True, None

        except Exception as e:
            return False, str(e)
