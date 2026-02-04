from __future__ import annotations

import secrets
from pathlib import Path
from typing import Iterable, Optional

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


def allowed_file(filename: str, allowed_exts: Iterable[str]) -> bool:
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in {e.lower() for e in allowed_exts}


def save_profile_image(
    file: Optional[FileStorage],
    upload_folder: str,
    allowed_exts: Iterable[str],
) -> Optional[str]:
    """Securely save a profile image and return stored filename.

    - Uses Werkzeug's `secure_filename`
    - Adds a random token to avoid collisions
    - Restricts extensions to JPEG/PNG

    Note: This demo does not do deep content inspection.
    For production, consider validating MIME type and decoding via Pillow.
    """
    if not file or not file.filename:
        return None

    original = secure_filename(file.filename)
    if not allowed_file(original, allowed_exts):
        raise ValueError("Invalid image type. Only JPG/JPEG/PNG allowed.")

    ext = original.rsplit(".", 1)[1].lower()
    token = secrets.token_hex(8)
    stored_name = f"profile_{token}.{ext}"

    folder = Path(upload_folder)
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / stored_name
    file.save(dest)

    return stored_name


def save_message_attachment(
    file: Optional[FileStorage],
    upload_folder: str,
    allowed_exts: Iterable[str],
) -> Optional[str]:
    """Securely save a message attachment and return stored filename.

    Images-first: caller should restrict `allowed_exts` to web-safe image types.
    This function is intentionally light (no heavy MIME sniffing) to keep
    dependencies minimal.
    """
    if not file or not file.filename:
        return None

    original = secure_filename(file.filename)
    if not allowed_file(original, allowed_exts):
        raise ValueError("Invalid attachment type.")

    ext = original.rsplit(".", 1)[1].lower()
    token = secrets.token_hex(8)
    stored_name = f"msg_{token}.{ext}"

    folder = Path(upload_folder)
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / stored_name
    file.save(dest)

    return stored_name
