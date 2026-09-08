from pathlib import PurePath, PureWindowsPath
from uuid import UUID


def get_safe_filename(filename: str) -> str:
    posix_name = PurePath(filename).name
    return PureWindowsPath(posix_name).name


def build_document_storage_path(
    *,
    organization_id: UUID,
    knowledge_base_id: UUID,
    document_id: UUID,
    filename: str,
) -> str:
    safe_filename = get_safe_filename(filename)

    return (
        f"organizations/{organization_id}/"
        f"knowledge-bases/{knowledge_base_id}/"
        f"documents/{document_id}/"
        f"{safe_filename}"
    )
