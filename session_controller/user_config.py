"""
User configuration file support for Session CLI.

Loads defaults from ~/.config/session-cli/config.yaml (Linux)
or ~/Library/Application Support/session-cli/config.yaml (macOS).
"""

import platform
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


@dataclass
class CommandDefaults:
    """Per-command default settings."""

    messages_limit: int = 20
    search_limit: int = 20
    watch_interval: float = 1.0
    watch_media_dir: str = "./media"
    export_format: str = "json"


@dataclass
class UserConfig:
    """
    User configuration loaded from config file.

    Priority order (highest to lowest):
    1. CLI arguments
    2. Config file values
    3. Hardcoded defaults
    """

    profile: Optional[str] = None
    port: int = 9222
    json_output: bool = False
    commands: CommandDefaults = field(default_factory=CommandDefaults)

    @staticmethod
    def get_config_path() -> Path:
        """Get platform-specific config file path."""
        system = platform.system()
        if system == "Darwin":
            base = Path.home() / "Library" / "Application Support"
        elif system == "Linux":
            base = Path.home() / ".config"
        else:
            # Fallback for other platforms
            base = Path.home() / ".config"

        return base / "session-cli" / "config.yaml"

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "UserConfig":
        """
        Load configuration from YAML file.

        Args:
            config_path: Optional custom path to config file.
                        Uses default platform path if not specified.

        Returns:
            UserConfig instance with loaded values or defaults.
        """
        if config_path is None:
            config_path = cls.get_config_path()

        # Return defaults if file doesn't exist or YAML not available
        if not config_path.exists():
            return cls()

        if not YAML_AVAILABLE:
            return cls()

        try:
            with open(config_path) as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            # Return defaults on any parsing error
            return cls()

        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "UserConfig":
        """Create UserConfig from parsed YAML dict."""
        # Parse command defaults
        commands_data = data.get("commands", {})
        commands = CommandDefaults(
            messages_limit=commands_data.get("messages", {}).get("limit", 20),
            search_limit=commands_data.get("search", {}).get("limit", 20),
            watch_interval=commands_data.get("watch", {}).get("interval", 1.0),
            watch_media_dir=commands_data.get("watch", {}).get("media_dir", "./media"),
            export_format=commands_data.get("export", {}).get("format", "json"),
        )

        return cls(
            profile=data.get("profile"),
            port=data.get("port", 9222),
            json_output=data.get("json", False),
            commands=commands,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dict for serialization."""
        return {
            "profile": self.profile,
            "port": self.port,
            "json": self.json_output,
            "commands": {
                "messages": {"limit": self.commands.messages_limit},
                "search": {"limit": self.commands.search_limit},
                "watch": {
                    "interval": self.commands.watch_interval,
                    "media_dir": self.commands.watch_media_dir,
                },
                "export": {"format": self.commands.export_format},
            },
        }

    def save(self, config_path: Optional[Path] = None) -> None:
        """
        Save configuration to YAML file.

        Args:
            config_path: Optional custom path. Uses default if not specified.
        """
        if not YAML_AVAILABLE:
            raise RuntimeError("PyYAML is required to save config. Install with: pip install pyyaml")

        if config_path is None:
            config_path = self.get_config_path()

        # Create parent directory if needed
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            yaml.safe_dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)

    def __repr__(self) -> str:
        return (
            f"UserConfig(profile={self.profile!r}, port={self.port}, "
            f"json={self.json_output}, config_path={self.get_config_path()})"
        )
