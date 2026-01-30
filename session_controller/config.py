"""
Session configuration and path handling.
"""

import json
import os
import platform
from pathlib import Path
from typing import Optional


class SessionConfig:
    """Handles Session Desktop configuration and data paths."""

    def __init__(self, profile: Optional[str] = None):
        """
        Initialize Session config.

        Args:
            profile: Optional profile name (e.g., "development", "devprod1").
                     None for production Session.
        """
        self.profile = profile
        self._config_cache: Optional[dict] = None

    @property
    def base_path(self) -> Path:
        """Get the base Application Support / config path for the current platform."""
        system = platform.system()
        if system == "Darwin":
            return Path.home() / "Library" / "Application Support"
        elif system == "Linux":
            return Path.home() / ".config"
        else:
            raise NotImplementedError(f"Platform {system} not supported yet")

    @property
    def session_folder_name(self) -> str:
        """Get the Session folder name based on profile."""
        if self.profile:
            return f"Session-{self.profile}"
        return "Session"

    @property
    def data_path(self) -> Path:
        """Get the full path to Session data directory."""
        return self.base_path / self.session_folder_name

    @property
    def config_path(self) -> Path:
        """Get path to config.json."""
        return self.data_path / "config.json"

    @property
    def db_path(self) -> Path:
        """Get path to the SQLCipher database."""
        return self.data_path / "sql" / "db.sqlite"

    @property
    def attachments_path(self) -> Path:
        """Get path to attachments directory."""
        return self.data_path / "attachments.noindex"

    def exists(self) -> bool:
        """Check if Session data directory exists."""
        return self.data_path.exists()

    def load_config(self) -> dict:
        """Load and cache config.json."""
        if self._config_cache is None:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Config not found: {self.config_path}")
            with open(self.config_path) as f:
                self._config_cache = json.load(f)
        return self._config_cache

    @property
    def db_key(self) -> str:
        """
        Get the database encryption key.

        Returns:
            64-character hex string (the raw key) if no password set,
            or the user's password if dbHasPassword is true.
        """
        config = self.load_config()
        return config.get("key", "")

    @property
    def has_password(self) -> bool:
        """Check if user has set a database password."""
        config = self.load_config()
        return config.get("dbHasPassword", False)

    def get_attachment_path(self, filename: str) -> Path:
        """
        Get full path for an attachment file.

        The filename from the database already includes the subdirectory,
        e.g., "3b/3b8c131324c98..." -> attachments.noindex/3b/3b8c131324c98...
        """
        return self.attachments_path / filename

    @classmethod
    def find_profiles(cls) -> list[str]:
        """Find all Session profiles on this system."""
        profiles = []
        system = platform.system()

        if system == "Darwin":
            base = Path.home() / "Library" / "Application Support"
        elif system == "Linux":
            base = Path.home() / ".config"
        else:
            return profiles

        if not base.exists():
            return profiles

        for item in base.iterdir():
            if item.is_dir() and item.name.startswith("Session"):
                if item.name == "Session":
                    profiles.append("")  # Production
                elif item.name.startswith("Session-"):
                    profiles.append(item.name[8:])  # Remove "Session-" prefix

        return profiles

    def __repr__(self) -> str:
        return f"SessionConfig(profile={self.profile!r}, path={self.data_path})"
