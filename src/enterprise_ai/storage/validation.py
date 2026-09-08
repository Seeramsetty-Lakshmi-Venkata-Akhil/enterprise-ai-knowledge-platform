from fastapi import UploadFile

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "text/plain",
}


def validate_upload_file(upload: UploadFile) -> None:
    if not upload.filename:
        raise ValueError("Uploaded file must have a filename")

    if upload.content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError("Unsupported file type")
