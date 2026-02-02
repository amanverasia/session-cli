"""
Request tools for Session MCP Server.
"""

from datetime import datetime
from typing import Optional

from session_mcp.server import mcp
from session_controller import SessionDatabase, SessionConfig


def _format_request(req) -> dict:
    """Format a Request object for MCP response."""
    return {
        "id": req.id,
        "name": req.name,
        "type": req.type,
        "display_name": req.display_name,
        "nickname": req.nickname,
        "last_message": req.last_message,
        "created_at": req.created_at,
        "created_at_iso": (
            datetime.fromtimestamp(req.created_at / 1000).isoformat()
            if req.created_at
            else None
        ),
        "is_approved": req.is_approved,
        "did_approve_me": req.did_approve_me,
        "unread_count": req.unread_count,
        "is_contact_request": req.is_contact_request,
        "is_message_request": req.is_message_request,
        "is_group": req.is_group,
        "is_private": req.is_private,
    }


def _get_config(profile: Optional[str] = None) -> SessionConfig:
    """Get SessionConfig with optional profile."""
    return SessionConfig(profile=profile) if profile else SessionConfig()


@mcp.tool()
def list_pending_requests(
    profile: Optional[str] = None,
) -> list[dict]:
    """List all pending contact and message requests.

    Returns requests where:
    - Contact requests: Someone sent us a request (didApproveMe = 1) but we haven't approved
    - Message requests: Unapproved contacts who have sent messages

    Args:
        profile: Optional Session profile name

    Returns:
        List of pending request objects
    """
    config = _get_config(profile)
    with SessionDatabase(config) as db:
        requests = db.get_pending_requests()
        return [_format_request(r) for r in requests]


@mcp.tool()
def get_request(
    request_id: str,
    profile: Optional[str] = None,
) -> Optional[dict]:
    """Get details of a specific pending request.

    Args:
        request_id: The request ID (Session ID or group ID)
        profile: Optional Session profile name

    Returns:
        Request object if found and pending, None otherwise
    """
    config = _get_config(profile)
    with SessionDatabase(config) as db:
        req = db.get_request(request_id)
        if req:
            return _format_request(req)
        return None
