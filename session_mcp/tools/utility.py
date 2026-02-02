"""
Utility tools for Session MCP Server.
"""

from typing import Optional

from session_mcp.server import mcp
from session_controller import SessionDatabase, SessionConfig


@mcp.tool()
def get_session_info(
    profile: Optional[str] = None,
) -> dict:
    """Get Session installation information.

    Returns information about the Session installation including:
    - Your Session ID (public key)
    - Data path location
    - Available profiles

    Args:
        profile: Optional Session profile name

    Returns:
        Dictionary with Session info:
        - session_id: Your Session ID (66-character public key starting with "05")
        - data_path: Path to Session data directory
        - db_path: Path to SQLCipher database
        - profile: Current profile name (empty string for production)
        - available_profiles: List of all Session profiles on this system
    """
    config = SessionConfig(profile=profile) if profile else SessionConfig()

    result = {
        "data_path": str(config.data_path),
        "db_path": str(config.db_path),
        "profile": config.profile or "",
        "available_profiles": SessionConfig.find_profiles(),
        "exists": config.exists(),
    }

    # Get Session ID if database is accessible
    if config.exists():
        try:
            with SessionDatabase(config) as db:
                session_id = db.get_our_pubkey()
                result["session_id"] = session_id
        except Exception as e:
            result["session_id"] = None
            result["error"] = str(e)
    else:
        result["session_id"] = None
        result["error"] = "Session data directory not found"

    return result


@mcp.tool()
def list_profiles() -> list[str]:
    """List all available Session profiles on this system.

    Session supports multiple profiles (e.g., "development", "devprod1").
    Each profile has its own database and attachments.

    Returns:
        List of profile names. Empty string represents the production profile.
    """
    return SessionConfig.find_profiles()
