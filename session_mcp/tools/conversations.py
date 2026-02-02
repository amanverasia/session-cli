"""
Conversation tools for Session MCP Server.
"""

from datetime import datetime
from typing import Optional

from session_mcp.server import mcp
from session_controller import SessionDatabase, SessionConfig


def _format_conversation(convo) -> dict:
    """Format a Conversation object for MCP response."""
    return {
        "id": convo.id,
        "name": convo.name,
        "type": convo.type,
        "display_name": convo.display_name,
        "nickname": convo.nickname,
        "last_message": convo.last_message,
        "active_at": convo.active_at,
        "active_at_iso": (
            datetime.fromtimestamp(convo.active_at / 1000).isoformat()
            if convo.active_at
            else None
        ),
        "unread_count": convo.unread_count,
        "is_group": convo.is_group,
        "is_private": convo.is_private,
    }


def _get_config(profile: Optional[str] = None) -> SessionConfig:
    """Get SessionConfig with optional profile."""
    return SessionConfig(profile=profile) if profile else SessionConfig()


@mcp.tool()
def list_conversations(
    limit: int = 50,
    profile: Optional[str] = None,
) -> list[dict]:
    """List all Session conversations with metadata.

    Args:
        limit: Maximum number of conversations to return (default: 50)
        profile: Optional Session profile name (e.g., "development")

    Returns:
        List of conversation objects with id, name, type, last_message, etc.
    """
    config = _get_config(profile)
    with SessionDatabase(config) as db:
        convos = db.get_conversations()[:limit]
        return [_format_conversation(c) for c in convos]


@mcp.tool()
def get_conversation(
    conversation_id: str,
    profile: Optional[str] = None,
) -> Optional[dict]:
    """Get details of a specific conversation by ID.

    Args:
        conversation_id: The conversation ID (Session ID or group ID)
        profile: Optional Session profile name

    Returns:
        Conversation object if found, None otherwise
    """
    config = _get_config(profile)
    with SessionDatabase(config) as db:
        convo = db.get_conversation(conversation_id)
        if convo:
            return _format_conversation(convo)
        return None


@mcp.tool()
def find_conversation(
    search: str,
    profile: Optional[str] = None,
) -> Optional[dict]:
    """Find a conversation by name or partial ID.

    Searches by exact ID first, then by display name or nickname (case-insensitive).

    Args:
        search: Conversation ID, display name, or nickname to search for
        profile: Optional Session profile name

    Returns:
        Conversation object if found, None otherwise
    """
    config = _get_config(profile)
    with SessionDatabase(config) as db:
        convo = db.find_conversation(search)
        if convo:
            return _format_conversation(convo)
        return None
