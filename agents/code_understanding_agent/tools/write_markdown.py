import os


def write_markdown(
    content: str,
    output_path: str,
    filename: str
) -> str:
    os.makedirs(output_path, exist_ok=True)

    full_path = os.path.join(output_path, filename)

    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return full_path


def read_markdown(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return ""
