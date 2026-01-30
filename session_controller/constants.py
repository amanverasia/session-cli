"""
Constants for Session Controller.

This module contains magic numbers, default values, and configuration
constants used throughout the project.
"""

from typing import Final


# === Version Info ===
PACKAGE_NAME: Final = "session-controller"
VERSION: Final = "1.3.1"


# === CDP Configuration ===
DEFAULT_CDP_PORT: Final = 9222
CDP_HOST: Final = "localhost"
DEFAULT_ALLOW_ORIGINS: Final = "*"


# === Database Configuration ===
DEFAULT_MESSAGE_LIMIT: Final = 100
DEFAULT_SEARCH_LIMIT: Final = 50
DEFAULT_EXPORT_LIMIT: Final = 10000
DEFAULT_WATCH_INTERVAL: Final = 1.0


# === File Paths ===
ATTACHMENTS_DIR: Final = "attachments.noindex"
SQL_DIR: Final = "sql"
DB_FILENAME: Final = "db.sqlite"
CONFIG_FILENAME: Final = "config.json"


# === Encryption ===
AES_BLOCK_SIZE: Final = 16
CRYPTO_HEADER_BYTES: Final = 24


# === Platform Paths ===
PLATFORM_PATHS = {
    "Darwin": {
        "base": "Library/Application Support",
        "session_folder": "Session",
    },
    "Linux": {
        "base": ".config",
        "session_folder": "Session",
    },
}


# === Message Types ===
MSG_TYPE_TEXT: Final = "text"
MSG_TYPE_ATTACHMENT: Final = "attachment"
MSG_TYPE_QUOTE: Final = "quote"
MSG_TYPE_ALL: Final = "all"


# === Conversation Types ===
CONVO_TYPE_PRIVATE: Final = "private"
CONVO_TYPE_GROUP: Final = "group"
CONVO_TYPE_GROUPV2: Final = "groupv2"


# === Request Types ===
REQUEST_TYPE_MESSAGE: Final = "message"
REQUEST_TYPE_CONTACT: Final = "contact"
REQUEST_TYPE_ALL: Final = "all"


# === Export Formats ===
EXPORT_FORMAT_JSON: Final = "json"
EXPORT_FORMAT_CSV: Final = "csv"
EXPORT_FORMAT_HTML: Final = "html"


# === Attachment Content Type Mapping ===
CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "audio/mpeg": ".mp3",
    "audio/ogg": ".ogg",
    "audio/aac": ".aac",
    "application/pdf": ".pdf",
}


# === Date Filter Mappings ===
DATE_FILTERS = {
    "today": 0,
    "yesterday": 1,
    "1d": 1,
    "2d": 2,
    "3d": 3,
    "7d": 7,
    "14d": 14,
    "30d": 30,
    "1w": 7,
    "2w": 14,
    "1m": 30,
}


# === Date Format Patterns ===
DATE_FORMAT_PATTERNS = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d",
    "%Y-%m-%d %H:%M:%S",
]


# === Session ID Validation ===
SESSION_ID_LENGTH: Final = 66
SESSION_ID_PREFIX: Final = "05"


# === Filename Sanitization ===
FILENAME_MAX_LENGTH: Final = 200
FILENAME_INVALID_CHARS: Final = r'[<>:"/\\|?*]'


# === Backup ===
BACKUP_VERSION: Final = "1.0.0"
BACKUP_ENCRYPTED_HEADER: Final = b"ENCRYPTED:\n"
