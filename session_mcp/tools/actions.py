"""
Action tools for Session MCP Server (CDP-based write operations).

These tools require Session Desktop to be running with CDP enabled:
    session-desktop --remote-debugging-port=9222 --remote-allow-origins="*"
"""

from typing import Optional

from session_mcp.server import mcp
from session_controller import SessionCDP


def _get_cdp(port: int = 9222) -> SessionCDP:
    """Create and connect a CDP client."""
    cdp = SessionCDP(port=port)
    cdp.connect()
    return cdp


@mcp.tool()
def send_message(
    conversation_id: str,
    message: str,
    port: int = 9222,
) -> dict:
    """Send a text message to a conversation.

    Requires Session Desktop running with --remote-debugging-port=9222

    Args:
        conversation_id: The Session ID or group ID to send to
        message: The message text to send
        port: CDP port (default: 9222)

    Returns:
        Dict with success status and details
    """
    try:
        with SessionCDP(port=port) as cdp:
            result = cdp.send_message(conversation_id, message)
            return {
                "success": result,
                "conversation_id": conversation_id,
                "message_length": len(message),
            }
    except ConnectionError as e:
        return {
            "success": False,
            "error": str(e),
            "hint": "Make sure Session is running with --remote-debugging-port=9222 --remote-allow-origins=\"*\"",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def accept_request(
    request_id: str,
    port: int = 9222,
) -> dict:
    """Accept a pending contact or message request.

    Requires Session Desktop running with --remote-debugging-port=9222

    Args:
        request_id: The Session ID of the request to accept
        port: CDP port (default: 9222)

    Returns:
        Dict with success status
    """
    try:
        with SessionCDP(port=port) as cdp:
            result = cdp.accept_request(request_id)
            return {"success": result, "request_id": request_id, "action": "accepted"}
    except ConnectionError as e:
        return {
            "success": False,
            "error": str(e),
            "hint": "Make sure Session is running with --remote-debugging-port=9222 --remote-allow-origins=\"*\"",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def decline_request(
    request_id: str,
    port: int = 9222,
) -> dict:
    """Decline a pending request without blocking the sender.

    Requires Session Desktop running with --remote-debugging-port=9222

    Args:
        request_id: The Session ID of the request to decline
        port: CDP port (default: 9222)

    Returns:
        Dict with success status
    """
    try:
        with SessionCDP(port=port) as cdp:
            result = cdp.decline_request(request_id)
            return {"success": result, "request_id": request_id, "action": "declined"}
    except ConnectionError as e:
        return {
            "success": False,
            "error": str(e),
            "hint": "Make sure Session is running with --remote-debugging-port=9222 --remote-allow-origins=\"*\"",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def block_request(
    request_id: str,
    port: int = 9222,
) -> dict:
    """Decline a pending request and block the sender.

    Requires Session Desktop running with --remote-debugging-port=9222

    Args:
        request_id: The Session ID to block
        port: CDP port (default: 9222)

    Returns:
        Dict with success status
    """
    try:
        with SessionCDP(port=port) as cdp:
            result = cdp.block_request(request_id)
            return {"success": result, "request_id": request_id, "action": "blocked"}
    except ConnectionError as e:
        return {
            "success": False,
            "error": str(e),
            "hint": "Make sure Session is running with --remote-debugging-port=9222 --remote-allow-origins=\"*\"",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def add_group_member(
    group_id: str,
    session_id: str,
    port: int = 9222,
) -> dict:
    """Add a member to a group (requires admin privileges).

    Requires Session Desktop running with --remote-debugging-port=9222

    Args:
        group_id: The group conversation ID
        session_id: The Session ID of the user to add
        port: CDP port (default: 9222)

    Returns:
        Dict with success status
    """
    try:
        with SessionCDP(port=port) as cdp:
            result = cdp.add_group_member(group_id, session_id)
            return {
                "success": result,
                "group_id": group_id,
                "added_member": session_id,
            }
    except ConnectionError as e:
        return {
            "success": False,
            "error": str(e),
            "hint": "Make sure Session is running with --remote-debugging-port=9222 --remote-allow-origins=\"*\"",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def remove_group_member(
    group_id: str,
    session_id: str,
    port: int = 9222,
) -> dict:
    """Remove a member from a group (requires admin privileges).

    Requires Session Desktop running with --remote-debugging-port=9222

    Args:
        group_id: The group conversation ID
        session_id: The Session ID of the user to remove
        port: CDP port (default: 9222)

    Returns:
        Dict with success status
    """
    try:
        with SessionCDP(port=port) as cdp:
            result = cdp.remove_group_member(group_id, session_id)
            return {
                "success": result,
                "group_id": group_id,
                "removed_member": session_id,
            }
    except ConnectionError as e:
        return {
            "success": False,
            "error": str(e),
            "hint": "Make sure Session is running with --remote-debugging-port=9222 --remote-allow-origins=\"*\"",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def promote_to_admin(
    group_id: str,
    session_id: str,
    port: int = 9222,
) -> dict:
    """Promote a group member to admin (requires admin privileges).

    Requires Session Desktop running with --remote-debugging-port=9222

    Args:
        group_id: The group conversation ID
        session_id: The Session ID of the member to promote
        port: CDP port (default: 9222)

    Returns:
        Dict with success status
    """
    try:
        with SessionCDP(port=port) as cdp:
            result = cdp.promote_to_admin(group_id, session_id)
            return {
                "success": result,
                "group_id": group_id,
                "promoted_member": session_id,
            }
    except ConnectionError as e:
        return {
            "success": False,
            "error": str(e),
            "hint": "Make sure Session is running with --remote-debugging-port=9222 --remote-allow-origins=\"*\"",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def demote_admin(
    group_id: str,
    session_id: str,
    port: int = 9222,
) -> dict:
    """Demote a group admin to regular member (requires admin privileges).

    Requires Session Desktop running with --remote-debugging-port=9222

    Args:
        group_id: The group conversation ID
        session_id: The Session ID of the admin to demote
        port: CDP port (default: 9222)

    Returns:
        Dict with success status
    """
    try:
        with SessionCDP(port=port) as cdp:
            result = cdp.demote_admin(group_id, session_id)
            return {
                "success": result,
                "group_id": group_id,
                "demoted_admin": session_id,
            }
    except ConnectionError as e:
        return {
            "success": False,
            "error": str(e),
            "hint": "Make sure Session is running with --remote-debugging-port=9222 --remote-allow-origins=\"*\"",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def leave_group(
    group_id: str,
    port: int = 9222,
) -> dict:
    """Leave a group conversation.

    Requires Session Desktop running with --remote-debugging-port=9222

    Args:
        group_id: The group conversation ID to leave
        port: CDP port (default: 9222)

    Returns:
        Dict with success status
    """
    try:
        with SessionCDP(port=port) as cdp:
            result = cdp.leave_group(group_id)
            return {"success": result, "group_id": group_id, "action": "left"}
    except ConnectionError as e:
        return {
            "success": False,
            "error": str(e),
            "hint": "Make sure Session is running with --remote-debugging-port=9222 --remote-allow-origins=\"*\"",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def mark_as_read(
    conversation_id: str,
    port: int = 9222,
) -> dict:
    """Mark all messages in a conversation as read.

    Requires Session Desktop running with --remote-debugging-port=9222

    Args:
        conversation_id: The conversation ID to mark as read
        port: CDP port (default: 9222)

    Returns:
        Dict with success status
    """
    try:
        with SessionCDP(port=port) as cdp:
            result = cdp.mark_conversation_read(conversation_id)
            return {
                "success": result,
                "conversation_id": conversation_id,
                "action": "marked_read",
            }
    except ConnectionError as e:
        return {
            "success": False,
            "error": str(e),
            "hint": "Make sure Session is running with --remote-debugging-port=9222 --remote-allow-origins=\"*\"",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
