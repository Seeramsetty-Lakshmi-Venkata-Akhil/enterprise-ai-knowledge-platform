from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import UploadFile

CHUNK_SIZE = 1024 * 1024
MAX_UPLOAD_SIZE = 10 * 1024 * 1024


class UploadTooLargeError(ValueError):
    pass


async def save_upload_to_temp_file(upload: UploadFile) -> Path:
    temp_path: Path | None = None
    total_size = 0

    try:
        with NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)

            while chunk := await upload.read(CHUNK_SIZE):
                total_size += len(chunk)

                if total_size > MAX_UPLOAD_SIZE:
                    raise UploadTooLargeError("Uploaded file exceeds 10 MB limit")

                temp_file.write(chunk)

        return temp_path

    except Exception:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

        raise
