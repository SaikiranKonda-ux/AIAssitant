import os
from typing import List
from ..models.schemas import FileInfo, FileMetadata, ImportMap


def create_metadata(
    files: List[FileInfo],
    import_map: ImportMap
) -> List[FileMetadata]:
    metadata_list = []

    for file_info in files:
        file_path = file_info.path
        imports = import_map.file_imports.get(file_path, [])

        imported_by = []
        for other_file, other_imports in import_map.file_imports.items():
            file_module = _file_to_module(file_path)
            if file_module in other_imports and other_file != file_path:
                imported_by.append(other_file)

        metadata_list.append(FileMetadata(
            path=file_path,
            line_count=file_info.line_count,
            imports=imports,
            imported_by=imported_by,
            file_type=file_info.extension
        ))

    return metadata_list


def _file_to_module(file_path: str) -> str:
    return os.path.splitext(os.path.basename(file_path))[0]
