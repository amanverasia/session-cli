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

    # Send messages (Session must be running with --remote-debugging-port)
    with SessionCDP() as cdp:
        cdp.send_message("05abc...", "Hello!")

CLI Usage:
    session-ctl list                    # List conversations
    session-ctl messages <id>           # Show messages
    session-ctl send <id> <message>     # Send message
    session-ctl watch                   # Watch for new messages
    session-ctl search <query>          # Search messages

For more information, see: https://github.com/amanverasia/session-ctl
"""

__version__ = "1.0.0"
__author__ = "Session Controller Contributors"
__license__ = "MIT"

from .database import SessionDatabase, Message, Conversation
from .cdp import SessionCDP
from .config import SessionConfig

__all__ = [
    "SessionDatabase",
    "SessionCDP",
    "SessionConfig",
    "Message",
    "Conversation",
]
