from typing import Dict
from ..models.schemas import Bundle, BundleContent


def read_bundle(bundle: Bundle) -> BundleContent:
    file_contents = {}
    total_lines_read = 0

    for file_metadata in bundle.files:
        file_path = file_metadata.path

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    lines = f.readlines()
            except Exception:
                file_contents[file_path] = f"Error: Could not read file {file_path}"
                continue
        except Exception:
            file_contents[file_path] = f"Error: Could not read file {file_path}"
            continue

        if bundle.line_range and bundle.part_of_large_file:
            start_line, end_line = _parse_line_range(bundle.line_range)
            selected_lines = lines[start_line-1:end_line]
            content = ''.join(selected_lines)
            total_lines_read += len(selected_lines)
        else:
            content = ''.join(lines)
            total_lines_read += len(lines)

        file_contents[file_path] = content

    return BundleContent(
        bundle_id=bundle.id,
        file_contents=file_contents,
        total_lines_read=total_lines_read
    )


def _parse_line_range(line_range: str) -> tuple:
    parts = line_range.split('-')
    start = int(parts[0])
    end = int(parts[1]) if len(parts) > 1 else start
    return start, end
