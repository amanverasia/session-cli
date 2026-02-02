"""
Session MCP Server - Model Context Protocol server for Session Desktop.

Exposes Session CLI's read-only functionality to AI agents via MCP.

Example usage with Claude Desktop:
    Configure in ~/Library/Application Support/Claude/claude_desktop_config.json:
    {
        "mcpServers": {
            "session": {
                "command": "python",
                "args": ["-m", "session_mcp"]
            }
        }
    }

Example usage with Claude Code:
    Configure in .claude/settings.json:
    {
        "mcpServers": {
            "session": {
                "command": "python",
                "args": ["-m", "session_mcp"]
            }
        }
    }
"""

__version__ = "1.7.0"
__author__ = "Session Controller Contributors"

from .server import mcp, main

__all__ = ["mcp", "main", "__version__"]
