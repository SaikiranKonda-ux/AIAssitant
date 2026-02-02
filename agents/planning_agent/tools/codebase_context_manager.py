import os
from ..models.schemas import CodebaseContext


def load_codebase_context(code_directory):
    agent_knowledge_path = os.path.join(code_directory, "agent_knowledge")

    if not os.path.exists(agent_knowledge_path):
        return CodebaseContext(
            has_agent_knowledge=False,
            imports_understanding=None,
            central_understanding=None,
            project_summary=None
        )

    imports_file = os.path.join(agent_knowledge_path, "imports_understanding.md")
    central_file = os.path.join(agent_knowledge_path, "central_understanding.md")

    imports_content = None
    if os.path.exists(imports_file):
        with open(imports_file, 'r', encoding='utf-8') as f:
            imports_content = f.read()

    central_content = None
    project_summary = None
    if os.path.exists(central_file):
        with open(central_file, 'r', encoding='utf-8') as f:
            central_content = f.read()
            project_summary = _extract_summary(central_content)

    return CodebaseContext(
        has_agent_knowledge=True,
        imports_understanding=imports_content,
        central_understanding=central_content,
        project_summary=project_summary
    )


def _extract_summary(markdown_content):
    lines = markdown_content.split('\n')
    summary_lines = []
    in_summary = False

    for line in lines:
        if '## Summary' in line or '# Summary' in line:
            in_summary = True
            continue
        if in_summary:
            if line.startswith('#'):
                break
            if line.strip():
                summary_lines.append(line)

    return '\n'.join(summary_lines[:10]) if summary_lines else markdown_content[:500]
