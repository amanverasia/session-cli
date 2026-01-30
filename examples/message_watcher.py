#!/usr/bin/env python3
"""
Watch for new messages in real-time.

This polls the database for new messages. Session must be running
to receive messages (this just reads from the local DB).

Run:
    source .venv/bin/activate
    python examples/message_watcher.py
"""

import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from database import SessionDatabase
from config import SessionConfig
from datetime import datetime


def main():
    config = SessionConfig()
    print(f"Watching for new messages...")
    print(f"Session data: {config.data_path}")
    print("Press Ctrl+C to stop\n")

    with SessionDatabase(config) as db:
        # Get conversation names for display
        convos = {c.id: c.name for c in db.get_conversations()}

        for msg in db.watch_messages(poll_interval=1.0):
            time_str = msg.sent_at.strftime("%H:%M:%S")
            convo_name = convos.get(msg.conversation_id, msg.conversation_id[:12])
            direction = "→" if msg.is_outgoing else "←"
            sender = "You" if msg.is_outgoing else msg.source[:8]
            body = msg.body[:60] if msg.body else "(attachment/media)"

            print(f"[{time_str}] {convo_name}")
            print(f"  {direction} {sender}: {body}")

            if msg.attachments:
                print(f"  📎 {len(msg.attachments)} attachment(s)")

            print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped watching.")
