import ast
import json
import os
from typing import List, Dict, Set, Tuple
from ..models.schemas import ImportMap

FILE_TYPE_RULES = {
    ".py": {"extract_imports": True, "patterns": ["from", "import"]},
    ".ipynb": {"extract_imports": True, "parse_mode": "code_cells"},
    ".toml": {"extract_imports": False, "read_mode": "all_lines"},
    ".yml": {"extract_imports": False, "read_mode": "all_lines"},
    ".yaml": {"extract_imports": False, "read_mode": "all_lines"},
    ".sql": {"extract_imports": False, "read_mode": "all_lines"}
}


def extract_imports(file_paths: List[str]) -> ImportMap:
    file_imports = {}
    dependency_graph = {}

    for file_path in file_paths:
        ext = os.path.splitext(file_path)[1]

        if ext not in FILE_TYPE_RULES:
            continue

        if ext == ".py":
            imports = _extract_python_imports(file_path)
            file_imports[file_path] = imports
        elif ext == ".ipynb":
            imports = _extract_notebook_imports(file_path)
            file_imports[file_path] = imports
        else:
            file_imports[file_path] = []

    for file_path, imports in file_imports.items():
        for imp in imports:
            if imp not in dependency_graph:
                dependency_graph[imp] = []
            dependency_graph[imp].append(file_path)

    entry_points = _identify_entry_points(file_paths, file_imports)
    circular_deps = _detect_circular_dependencies(file_imports)

    return ImportMap(
        file_imports=file_imports,
        dependency_graph=dependency_graph,
        entry_points=entry_points,
        circular_deps=circular_deps
    )


def _extract_python_imports(file_path: str) -> List[str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        return list(set(imports))
    except Exception:
        return []


def _extract_notebook_imports(file_path: str) -> List[str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)

        imports = []
        for cell in notebook.get('cells', []):
            if cell.get('cell_type') == 'code':
                source = ''.join(cell.get('source', []))
                try:
                    tree = ast.parse(source)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imports.append(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                imports.append(node.module)
                except Exception:
                    continue

        return list(set(imports))
    except Exception:
        return []


def _identify_entry_points(file_paths: List[str], file_imports: Dict[str, List[str]]) -> List[str]:
    entry_points = []

    for file_path in file_paths:
        if not file_path.endswith('.py'):
            continue

        filename = os.path.basename(file_path)
        if filename in ['main.py', 'app.py', '__main__.py', 'run.py', 'start.py']:
            entry_points.append(file_path)
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if 'if __name__ == "__main__"' in content or "if __name__ == '__main__'" in content:
                entry_points.append(file_path)
        except Exception:
            continue

    return entry_points


def _detect_circular_dependencies(file_imports: Dict[str, List[str]]) -> List[Tuple[str, str]]:
    circular = []

    module_to_files = {}
    for file_path, imports in file_imports.items():
        module_name = _file_to_module(file_path)
        module_to_files[module_name] = file_path

    for file_path, imports in file_imports.items():
        current_module = _file_to_module(file_path)

        for imp in imports:
            if imp in module_to_files:
                imported_file = module_to_files[imp]
                imported_module_imports = file_imports.get(imported_file, [])

                if current_module in imported_module_imports:
                    pair = tuple(sorted([file_path, imported_file]))
                    if pair not in circular:
                        circular.append(pair)

    return circular


def _file_to_module(file_path: str) -> str:
    return os.path.splitext(os.path.basename(file_path))[0]
