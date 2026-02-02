"""
Session Controller - Python package for programmatic control of Session Desktop.

Session Controller provides two modes of operation:
1. Database mode (read-only): Direct access to Session's SQLCipher database
2. CDP mode (full control): Chrome DevTools Protocol when Session is running

Example:
    from session_controller import SessionDatabase, SessionCDP, SessionConfig

    # Read messages (Session doesn't need to be running)
    with SessionDatabase() as db:
        for convo in db.get_conversations():
            print(f"{convo.name}: {convo.last_message}")

    # Manage requests
    requests = db.get_pending_requests()
    for req in requests:
        print(f"{req.name}: {req.type}")

    # Send messages (Session must be running with --remote-debugging-port)
    with SessionCDP() as cdp:
        cdp.send_message("05abc...", "Hello!")

CLI Usage:
    session-cli --version               # Show version
    session-cli list                    # List conversations
    session-cli messages <id>           # Show messages
    session-cli send <id> <message>     # Send message
    session-cli watch                   # Watch for new messages
    session-cli search <query>          # Search messages
    session-cli requests                # List pending requests

For more information, see: https://github.com/amanverasia/session-cli
"""

__version__ = "1.7.0"
__author__ = "Session Controller Contributors"
__license__ = "MIT"

from .database import SessionDatabase, Message, Conversation, Request
from .cdp import SessionCDP
from .config import SessionConfig
from .user_config import UserConfig
from .repl import SessionREPL

__all__ = [
    "SessionDatabase",
    "SessionCDP",
    "SessionConfig",
    "UserConfig",
    "SessionREPL",
    "Message",
    "Conversation",
    "Request",
]
