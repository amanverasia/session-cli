#!/usr/bin/env python3
"""
Export Session conversation example.

Run: python examples/export_conversation.py <conversation_id>
"""

import sys
import os
from pathlib import Path

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from session_controller import SessionDatabase, SessionConfig


def main():
    if len(sys.argv) < 2:
        print("Usage: python export_conversation.py <conversation_id>")
        print("\nTo find conversation IDs:")
        print("  python examples/export_conversation.py list")
        return 1

    conversation_id = sys.argv[1]

    if conversation_id == "list":
        print("Listing all conversations...")
        config = SessionConfig()
        with SessionDatabase(config) as db:
            convos = db.get_conversations()
            print("\nAvailable conversations:")
            for c in convos:
                print(f"  {c.name} ({c.id})")
        return 0

    config = SessionConfig()
    output_dir = Path("exports")
    output_dir.mkdir(exist_ok=True)

    print(f"Exporting conversation: {conversation_id}\n")

    with SessionDatabase(config) as db:
        convo = db.get_conversation(conversation_id)
        if not convo:
            print(f"Conversation not found: {conversation_id}")
            print("Use 'list' to see available conversations")
            return 1

        print(f"Name: {convo.name}")
        print(f"Type: {convo.type}")
        print()

        json_file = output_dir / f"{convo.name}.json"
        csv_file = output_dir / f"{convo.name}.csv"
        html_file = output_dir / f"{convo.name}.html"

        print("Exporting to JSON...")
        db.export_conversation_to_json(
            conversation_id, str(json_file), include_attachments=True
        )
        print(f"  ✓ {json_file}")

        print("\nExporting to CSV...")
        db.export_conversation_to_csv(conversation_id, str(csv_file))
        print(f"  ✓ {csv_file}")

        print("\nExporting to HTML (with embedded images)...")
        db.export_conversation_to_html(
            conversation_id, str(html_file), include_attachments=True
        )
        print(f"  ✓ {html_file}")

        print(f"\nAll exports saved to: {output_dir}")
        print("\nOpen HTML in browser:")
        print(f"  open {html_file.absolute()}")


if __name__ == "__main__":
    main()
