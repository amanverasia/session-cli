"""
FastMCP server for Session Desktop.

This module sets up the MCP server and registers all tools.
"""

from fastmcp import FastMCP

# Create the MCP server instance
mcp = FastMCP(
    "session",
    instructions="Session Desktop MCP Server - Read-only access to Session messenger data",
)

# Import tools to register them with the server
from .tools import conversations, messages, requests, stats, utility


def main():
    """Run the MCP server with stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
