"""
Message tools for Session MCP Server.
"""

from datetime import datetime
from typing import Optional

from session_mcp.server import mcp
from session_controller import SessionDatabase, SessionConfig


def _format_message(msg) -> dict:
    """Format a Message object for MCP response."""
    return {
        "id": msg.id,
        "conversation_id": msg.conversation_id,
        "source": msg.source,
        "body": msg.body,
        "timestamp": msg.timestamp,
        "sent_at_iso": msg.sent_at.isoformat() if msg.timestamp else None,
        "received_at": msg.received_at,
        "type": msg.type,
        "is_incoming": msg.is_incoming,
        "is_outgoing": msg.is_outgoing,
        "has_attachments": len(msg.attachments) > 0,
        "attachment_count": len(msg.attachments),
        "has_quote": msg.quote is not None,
    }


def _get_config(profile: Optional[str] = None) -> SessionConfig:
    """Get SessionConfig with optional profile."""
    return SessionConfig(profile=profile) if profile else SessionConfig()


@mcp.tool()
def get_messages(
    conversation_id: str,
    limit: int = 50,
    before_timestamp: Optional[int] = None,
    profile: Optional[str] = None,
) -> list[dict]:
    """Get messages from a specific conversation.

    Args:
        conversation_id: The conversation ID (Session ID or group ID)
        limit: Maximum number of messages to return (default: 50)
        before_timestamp: Only get messages before this timestamp in milliseconds (for pagination)
        profile: Optional Session profile name

    Returns:
        List of message objects ordered by timestamp (newest first)
    """
    config = _get_config(profile)
    with SessionDatabase(config) as db:
        messages = db.get_messages(
            conversation_id,
            limit=limit,
            before_timestamp=before_timestamp,
        )
        return [_format_message(m) for m in messages]


@mcp.tool()
def search_messages(
    query: str,
    conversation_id: Optional[str] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    sender: Optional[str] = None,
    limit: int = 50,
    profile: Optional[str] = None,
) -> list[dict]:
    """Search messages across all conversations with filters.

    Uses full-text search (FTS5) on message body.

    Args:
        query: Search query string (supports FTS5 syntax)
        conversation_id: Optional conversation ID to limit search to
        after: Only messages after this date (supports: "today", "7d", "30d", "2025-01-31", etc.)
        before: Only messages before this date
        sender: Filter by sender Session ID
        limit: Maximum number of results (default: 50)
        profile: Optional Session profile name

    Returns:
        List of matching message objects
    """
    config = _get_config(profile)
    with SessionDatabase(config) as db:
        # Parse date filters
        after_ts = db.parse_date_filter(after) if after else None
        before_ts = db.parse_date_filter(before) if before else None

        messages = db.search_messages_enhanced(
            query=query,
            conversation_id=conversation_id,
            after_timestamp=after_ts,
            before_timestamp=before_ts,
            sender=sender,
            limit=limit,
        )
        return [_format_message(m) for m in messages]


@mcp.tool()
def get_message(
    message_id: str,
    profile: Optional[str] = None,
) -> Optional[dict]:
    """Get a specific message by its ID.

    Args:
        message_id: The message ID
        profile: Optional Session profile name

    Returns:
        Message object if found, None otherwise
    """
    config = _get_config(profile)
    with SessionDatabase(config) as db:
        msg = db.get_message_by_id(message_id)
        if msg:
            return _format_message(msg)
        return None
