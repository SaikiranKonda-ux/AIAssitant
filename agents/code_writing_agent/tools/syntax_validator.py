import ast
import json
import tempfile
import os
from pathlib import Path
from typing import Tuple, List


class SyntaxValidator:
    @staticmethod
    def validate_python(content: str) -> Tuple[bool, List[str]]:
        errors = []
        try:
            ast.parse(content)
            return True, []
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
            return False, errors
        except Exception as e:
            errors.append(f"Parse error: {str(e)}")
            return False, errors

    @staticmethod
    def validate_json(content: str) -> Tuple[bool, List[str]]:
        errors = []
        try:
            json.loads(content)
            return True, []
        except json.JSONDecodeError as e:
            errors.append(f"JSON error at line {e.lineno}, col {e.colno}: {e.msg}")
            return False, errors
        except Exception as e:
            errors.append(f"JSON parse error: {str(e)}")
            return False, errors

    @staticmethod
    def validate_by_extension(file_path: str, content: str) -> Tuple[bool, List[str]]:
        ext = Path(file_path).suffix.lower()

        if ext == '.py':
            return SyntaxValidator.validate_python(content)
        elif ext == '.json':
            return SyntaxValidator.validate_json(content)
        elif ext in ['.txt', '.md', '.yml', '.yaml', '.toml', '.ini', '.cfg']:
            return True, []
        else:
            return True, [f"No validator for extension {ext}, skipping"]

    @staticmethod
    def validate_file(file_path: str) -> Tuple[bool, List[str]]:
        if not os.path.exists(file_path):
            return False, [f"File not found: {file_path}"]

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return SyntaxValidator.validate_by_extension(file_path, content)

        except Exception as e:
            return False, [f"Error reading file: {str(e)}"]

    @staticmethod
    def validate_content_before_write(file_path: str, content: str) -> Tuple[bool, List[str]]:
        is_valid, errors = SyntaxValidator.validate_by_extension(file_path, content)

        if not is_valid:
            return False, errors

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix=Path(file_path).suffix, delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            _, validation_errors = SyntaxValidator.validate_file(tmp_path)

            os.unlink(tmp_path)

            if validation_errors:
                return False, validation_errors

            return True, []

        except Exception as e:
            return False, [f"Validation error: {str(e)}"]
