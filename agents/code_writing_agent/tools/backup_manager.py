import os
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from agents.code_writing_agent.models.schemas import BackupInfo


class BackupManager:
    def __init__(self, backup_root: str = ".code_agent_backups"):
        self.backup_root = backup_root

    def create_backup(self, file_path: str) -> Optional[BackupInfo]:
        if not os.path.exists(file_path):
            return None

        os.makedirs(self.backup_root, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = os.path.basename(file_path)
        backup_name = f"{file_name}.{timestamp}.backup"
        backup_path = os.path.join(self.backup_root, backup_name)

        shutil.copy2(file_path, backup_path)

        with open(file_path, 'rb') as f:
            file_content = f.read()
            checksum = hashlib.md5(file_content).hexdigest()

        file_size = os.path.getsize(file_path)

        return BackupInfo(
            file_path=file_path,
            backup_path=backup_path,
            file_size=file_size,
            checksum=checksum
        )

    def restore_from_backup(self, backup_info: BackupInfo) -> bool:
        if not os.path.exists(backup_info.backup_path):
            return False

        try:
            shutil.copy2(backup_info.backup_path, backup_info.file_path)

            with open(backup_info.file_path, 'rb') as f:
                restored_content = f.read()
                restored_checksum = hashlib.md5(restored_content).hexdigest()

            return restored_checksum == backup_info.checksum

        except Exception:
            return False

    def cleanup_old_backups(self, keep_latest: int = 10):
        if not os.path.exists(self.backup_root):
            return

        backup_files = []
        for file in os.listdir(self.backup_root):
            if file.endswith('.backup'):
                full_path = os.path.join(self.backup_root, file)
                mtime = os.path.getmtime(full_path)
                backup_files.append((mtime, full_path))

        backup_files.sort(reverse=True)

        for _, backup_path in backup_files[keep_latest:]:
            try:
                os.remove(backup_path)
            except Exception:
                pass

    def list_backups(self, file_path: Optional[str] = None) -> list:
        if not os.path.exists(self.backup_root):
            return []

        backups = []
        file_name = os.path.basename(file_path) if file_path else None

        for backup_file in os.listdir(self.backup_root):
            if backup_file.endswith('.backup'):
                if file_name and not backup_file.startswith(file_name):
                    continue

                backup_path = os.path.join(self.backup_root, backup_file)
                mtime = os.path.getmtime(backup_path)
                backups.append({
                    "backup_file": backup_file,
                    "backup_path": backup_path,
                    "modified_time": datetime.fromtimestamp(mtime).isoformat()
                })

        backups.sort(key=lambda x: x["modified_time"], reverse=True)
        return backups
