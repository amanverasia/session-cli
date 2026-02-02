"""
Statistics tools for Session MCP Server.
"""

from typing import Optional

from session_mcp.server import mcp
from session_controller import SessionDatabase, SessionConfig


def _get_config(profile: Optional[str] = None) -> SessionConfig:
    """Get SessionConfig with optional profile."""
    return SessionConfig(profile=profile) if profile else SessionConfig()


@mcp.tool()
def get_stats(
    conversation_id: Optional[str] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    profile: Optional[str] = None,
) -> dict:
    """Get messaging statistics.

    Returns comprehensive stats including message counts, conversation counts,
    activity by hour and day of week.

    Args:
        conversation_id: Optional conversation ID to get stats for specific conversation
        after: Only count messages after this date (supports: "today", "7d", "30d", "2025-01-31", etc.)
        before: Only count messages before this date
        profile: Optional Session profile name

    Returns:
        Dictionary with statistics including:
        - total_messages, sent, received, with_attachments
        - conversations count (private and group)
        - first_message, last_message dates
        - avg_per_day
        - by_hour: messages by hour of day
        - by_day: messages by day of week
    """
    config = _get_config(profile)
    with SessionDatabase(config) as db:
        # Parse date filters
        after_ts = db.parse_date_filter(after) if after else None
        before_ts = db.parse_date_filter(before) if before else None

        return db.get_stats(
            conversation_id=conversation_id,
            after_timestamp=after_ts,
            before_timestamp=before_ts,
        )


@mcp.tool()
def get_top_conversations(
    limit: int = 10,
    after: Optional[str] = None,
    profile: Optional[str] = None,
) -> list[dict]:
    """Get most active conversations by message count.

    Args:
        limit: Number of conversations to return (default: 10)
        after: Only count messages after this date (supports: "today", "7d", "30d", "2025-01-31", etc.)
        profile: Optional Session profile name

    Returns:
        List of conversations with message counts, ordered by activity (most active first):
        - id, name, type
        - message_count, sent, received
        - last_message_at
    """
    config = _get_config(profile)
    with SessionDatabase(config) as db:
        # Parse date filter
        after_ts = db.parse_date_filter(after) if after else None

        return db.get_top_conversations(
            limit=limit,
            after_timestamp=after_ts,
        )


@mcp.tool()
def get_activity(
    conversation_id: Optional[str] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    group_by: str = "day",
    profile: Optional[str] = None,
) -> list[dict]:
    """Get message activity breakdown by date.

    Args:
        conversation_id: Optional conversation ID to filter to
        after: Only count messages after this date
        before: Only count messages before this date
        group_by: Grouping period - "day", "week", or "month" (default: "day")
        profile: Optional Session profile name

    Returns:
        List of activity records with:
        - period: date string (format depends on group_by)
        - total: total message count
        - sent: outgoing message count
        - received: incoming message count
    """
    config = _get_config(profile)
    with SessionDatabase(config) as db:
        # Parse date filters
        after_ts = db.parse_date_filter(after) if after else None
        before_ts = db.parse_date_filter(before) if before else None

        return db.get_activity_by_date(
            conversation_id=conversation_id,
            after_timestamp=after_ts,
            before_timestamp=before_ts,
            group_by=group_by,
        )
