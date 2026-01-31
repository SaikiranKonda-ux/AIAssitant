import os
import glob
from typing import List, Set
from ..models.schemas import FileInfo, FileStructure

EXCLUDED_DIRS = {
    '.venv', 'venv', 'env', '__pycache__', '.pytest_cache',
    '.git', '.github', 'node_modules', 'build', 'dist',
    '.tox', '.eggs', '*.egg-info', '.mypy_cache', '.ruff_cache'
}

SUPPORTED_EXTENSIONS = {'.py', '.ipynb', '.toml', '.yml', '.yaml', '.sql'}


def file_search(project_path: str) -> FileStructure:
    directories = []
    files = []

    for root, dirs, filenames in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith('.')]

        rel_root = os.path.relpath(root, project_path)
        if rel_root != '.':
            directories.append(rel_root)

        for filename in filenames:
            file_path = os.path.join(root, filename)
            ext = os.path.splitext(filename)[1]

            if ext not in SUPPORTED_EXTENSIONS:
                continue

            try:
                file_size = os.path.getsize(file_path)
                line_count = _count_lines(file_path)

                files.append(FileInfo(
                    path=file_path,
                    size=file_size,
                    extension=ext,
                    line_count=line_count
                ))
            except Exception:
                continue

    return FileStructure(
        root_path=project_path,
        directories=directories,
        files=files
    )


def _count_lines(file_path: str) -> int:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except Exception:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return sum(1 for _ in f)
        except Exception:
            return 0
