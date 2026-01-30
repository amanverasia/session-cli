#!/usr/bin/env python3
"""
Basic usage examples for Session Controller.

Run from the session_controller directory:
    source .venv/bin/activate
    python examples/basic_usage.py
"""

import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from database import SessionDatabase
from config import SessionConfig


def main():
    # Initialize with production Session
    config = SessionConfig()
    print(f"Using Session data from: {config.data_path}")

    # Connect to database
    with SessionDatabase(config) as db:
        # Get our Session ID
        our_id = db.get_our_pubkey()
        print(f"\nOur Session ID: {our_id}")

        # List all conversations
        print("\n=== Conversations ===")
        conversations = db.get_conversations()
        for convo in conversations:
            print(f"  [{convo.type}] {convo.name}")
            print(f"       ID: {convo.id[:20]}...")
            print(f"       Last: {convo.last_message[:50] if convo.last_message else '(empty)'}...")
            print(f"       Unread: {convo.unread_count}")
            print()

        # Get messages from first conversation
        if conversations:
            convo = conversations[0]
            print(f"\n=== Messages from {convo.name} ===")
            messages = db.get_messages(convo.id, limit=5)
            for msg in reversed(messages):  # Show oldest first
                direction = "→" if msg.is_outgoing else "←"
                sender = "You" if msg.is_outgoing else msg.source[:8]
                body = msg.body[:60] if msg.body else "(no text)"
                print(f"  {direction} [{sender}] {body}")

        # Search messages
        print("\n=== Search Example ===")
        search_term = "hello"
        results = db.search_messages(search_term, limit=3)
        print(f"  Found {len(results)} messages containing '{search_term}'")
        for msg in results:
            print(f"    - {msg.body[:50] if msg.body else '(no text)'}...")


if __name__ == "__main__":
    main()
