import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "Job Tracker API")
DATABASE_URL = os.getenv("DATABASE_URL")
def _read_secret(name: str) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    secret_file = os.getenv(f"{name}_FILE")
    if secret_file:
        return Path(secret_file).read_text(encoding="utf-8").strip()
    return None


SECRET_KEY = _read_secret("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)
CORS_ORIGINS = tuple(
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
)
LOGIN_RATE_LIMIT = int(os.getenv("LOGIN_RATE_LIMIT", "5"))
LOGIN_RATE_WINDOW_SECONDS = int(
    os.getenv("LOGIN_RATE_WINDOW_SECONDS", "60")
)
DEADLINE_REMINDER_DAYS = int(os.getenv("DEADLINE_REMINDER_DAYS", "3"))
DEADLINE_REMINDER_INTERVAL_SECONDS = int(
    os.getenv("DEADLINE_REMINDER_INTERVAL_SECONDS", "3600")
)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER or "")
DOCUMENT_STORAGE_PATH = Path(
    os.getenv("DOCUMENT_STORAGE_PATH", "/app/storage")
).expanduser()
if not DOCUMENT_STORAGE_PATH.is_absolute():
    DOCUMENT_STORAGE_PATH = (Path.cwd() / DOCUMENT_STORAGE_PATH).resolve()
MAX_DOCUMENT_SIZE_BYTES = int(os.getenv("MAX_DOCUMENT_SIZE_BYTES", "10485760"))
ALLOWED_DOCUMENT_EXTENSIONS = tuple(
    ext.strip().lower()
    for ext in os.getenv("ALLOWED_DOCUMENT_EXTENSIONS", ".pdf,.doc,.docx,.txt").split(",")
    if ext.strip()
)

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not configured")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY or SECRET_KEY_FILE is not configured")

if len(SECRET_KEY) < 32:
    raise ValueError("SECRET_KEY must be at least 32 characters")
if LOGIN_RATE_LIMIT < 1:
    raise ValueError("LOGIN_RATE_LIMIT must be positive")
if LOGIN_RATE_WINDOW_SECONDS < 1:
    raise ValueError("LOGIN_RATE_WINDOW_SECONDS must be positive")
if DEADLINE_REMINDER_DAYS < 0:
    raise ValueError("DEADLINE_REMINDER_DAYS must not be negative")
if DEADLINE_REMINDER_INTERVAL_SECONDS < 60:
    raise ValueError("DEADLINE_REMINDER_INTERVAL_SECONDS must be at least 60")
if SMTP_PORT < 1 or SMTP_PORT > 65535:
    raise ValueError("SMTP_PORT must be between 1 and 65535")
if MAX_DOCUMENT_SIZE_BYTES < 1:
    raise ValueError("MAX_DOCUMENT_SIZE_BYTES must be positive")