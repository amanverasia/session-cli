"""
Export tools for Session MCP Server.
"""

import tempfile
from pathlib import Path
from typing import Optional

from session_mcp.server import mcp
from session_controller import SessionDatabase, SessionConfig


def _get_config(profile: Optional[str] = None) -> SessionConfig:
    """Get SessionConfig with optional profile."""
    return SessionConfig(profile=profile) if profile else SessionConfig()


@mcp.tool()
def export_conversation(
    conversation_id: str,
    format: str = "json",
    profile: Optional[str] = None,
) -> dict:
    """Export a conversation to JSON, CSV, or HTML format.

    The exported content is returned directly (for JSON/CSV) or as a file path (for HTML with attachments).

    Args:
        conversation_id: The conversation ID to export
        format: Export format - "json", "csv", or "html" (default: "json")
        profile: Optional Session profile name

    Returns:
        Dict with export data or file path
    """
    config = _get_config(profile)

    if format not in ("json", "csv", "html"):
        return {"success": False, "error": f"Invalid format: {format}. Use json, csv, or html."}

    try:
        with SessionDatabase(config) as db:
            convo = db.get_conversation(conversation_id)
            if not convo:
                return {"success": False, "error": f"Conversation not found: {conversation_id}"}

            # Create temp file for export
            suffix = f".{format}"
            with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as f:
                output_path = f.name

            if format == "json":
                db.export_conversation_to_json(conversation_id, output_path)
                # Read back the JSON content
                with open(output_path, "r") as f:
                    import json
                    content = json.load(f)
                Path(output_path).unlink()  # Clean up temp file
                return {
                    "success": True,
                    "format": "json",
                    "conversation_id": conversation_id,
                    "conversation_name": convo.name,
                    "data": content,
                }

            elif format == "csv":
                db.export_conversation_to_csv(conversation_id, output_path)
                with open(output_path, "r") as f:
                    content = f.read()
                Path(output_path).unlink()
                return {
                    "success": True,
                    "format": "csv",
                    "conversation_id": conversation_id,
                    "conversation_name": convo.name,
                    "data": content,
                }

            else:  # html
                db.export_conversation_to_html(conversation_id, output_path, include_attachments=True)
                with open(output_path, "r") as f:
                    content = f.read()
                Path(output_path).unlink()
                return {
                    "success": True,
                    "format": "html",
                    "conversation_id": conversation_id,
                    "conversation_name": convo.name,
                    "data": content,
                }

    except Exception as e:
        return {"success": False, "error": str(e)}
