import os
from pathlib import Path


class Config:
    """Base configuration.

    Notes:
    - Uses SQLite by default.
    - Uploads are stored under `static/uploads/`.
    """

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # Admin is determined dynamically:
    # a normal user becomes admin if their email equals ADMIN_EMAIL.
    ADMIN_EMAIL = (os.environ.get("ADMIN_EMAIL") or "admin@matrimony.local").strip().lower()

    BASE_DIR = Path(__file__).resolve().parent
    # IMPORTANT: The app uses the existing SQLite file at `database/matrimony.db`.
    # Match scores are computed dynamically and are not stored.
    DB_PATH = os.environ.get("DB_PATH", str(BASE_DIR / "database" / "matrimony.db"))

    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", str(BASE_DIR / "static" / "uploads"))
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB

    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png"}
