#!/usr/bin/env python3
"""
Session Controller CLI

Usage:
    session-cli list                     # List conversations
    session-cli messages <id> [--limit N]  # Show messages from conversation
    session-cli send <id> <message>      # Send a message (requires CDP)
    session-cli watch [--convo <id>]     # Watch for new messages
    session-cli info                     # Show Session info
    session-cli search <query>           # Search messages
"""

import argparse
import sys
import os
import time
from datetime import datetime
from pathlib import Path

# Add parent to path if running directly
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database import SessionDatabase
    from config import SessionConfig
    from cdp import SessionCDP
except ImportError:
    from .database import SessionDatabase
    from .config import SessionConfig
    from .cdp import SessionCDP


def cmd_list(args):
    """List all conversations."""
    config = SessionConfig(profile=args.profile)
    with SessionDatabase(config) as db:
        convos = db.get_conversations()

        if args.json:
            import json

            print(json.dumps([c.raw for c in convos], indent=2))
            return

        print(f"Found {len(convos)} conversations:\n")
        for c in convos:
            unread = f" ({c.unread_count} unread)" if c.unread_count else ""
            last = (
                c.last_message[:40] + "..."
                if c.last_message and len(c.last_message) > 40
                else (c.last_message or "(empty)")
            )
            print(f"  [{c.type:8}] {c.name}")
            print(f"            ID: {c.id}")
            print(f"            Last: {last}{unread}")
            print()


def cmd_messages(args):
    """Show messages from a conversation."""
    config = SessionConfig(profile=args.profile)
    with SessionDatabase(config) as db:
        # Find conversation
        convo = db.get_conversation(args.id)
        if not convo:
            # Try partial match
            convos = db.get_conversations()
            matches = [
                c
                for c in convos
                if args.id.lower() in c.id.lower() or args.id.lower() in c.name.lower()
            ]
            if len(matches) == 1:
                convo = matches[0]
            elif len(matches) > 1:
                print(f"Multiple matches for '{args.id}':")
                for c in matches:
                    print(f"  - {c.name} ({c.id[:20]}...)")
                return 1
            else:
                print(f"Conversation not found: {args.id}")
                return 1

        messages = db.get_messages(convo.id, limit=args.limit)

        if args.json:
            import json

            print(json.dumps([m.raw for m in messages], indent=2))
            return

        print(f"Messages from {convo.name} ({len(messages)} shown):\n")
        for msg in reversed(messages):
            time_str = msg.sent_at.strftime("%Y-%m-%d %H:%M")
            direction = "→" if msg.is_outgoing else "←"
            sender = "You" if msg.is_outgoing else msg.source[:8]
            body = msg.body or "(no text)"

            print(f"[{time_str}] {direction} {sender}")
            print(f"  {body}")
            if msg.attachments:
                print(f"  📎 {len(msg.attachments)} attachment(s)")
            print()


def cmd_send(args):
    """Send a message via CDP."""
    try:
        cdp = SessionCDP(port=args.port)
        cdp.connect()
    except Exception as e:
        print(f"Error: Cannot connect to Session CDP at port {args.port}")
        print(
            f"Make sure Session is running with: {SessionCDP.get_launch_command(args.port)}"
        )
        print(f"\nDetails: {e}")
        return 1

    try:
        # Check if conversation exists
        convo = cdp.get_conversation(args.id)
        if not convo:
            print(f"Conversation not found: {args.id}")
            print("The conversation must already exist in Session.")
            return 1

        result = cdp.send_message(args.id, args.message)
        if result:
            print(f"✓ Message sent to {convo['name']}")
        else:
            print("✗ Failed to send message")
            return 1
    finally:
        cdp.close()


def cmd_watch(args):
    """Watch for new messages."""
    config = SessionConfig(profile=args.profile)

    # Create output directory for media if saving
    if args.save_media:
        media_dir = Path(args.media_dir).expanduser()
        media_dir.mkdir(parents=True, exist_ok=True)
        print(f"Saving media to: {media_dir}")

    print("Watching for new messages... (Ctrl+C to stop)\n")

    with SessionDatabase(config) as db:
        # Get conversation names
        convos = {c.id: c.name for c in db.get_conversations()}

        try:
            for msg in db.watch_messages(
                poll_interval=args.interval, conversation_id=args.convo
            ):
                time_str = msg.sent_at.strftime("%H:%M:%S")
                convo_name = convos.get(msg.conversation_id, msg.conversation_id[:12])
                direction = "→" if msg.is_outgoing else "←"
                sender = "You" if msg.is_outgoing else msg.source[:8]
                body = msg.body[:60] if msg.body else "(no text)"

                print(f"[{time_str}] {convo_name}")
                print(f"  {direction} {sender}: {body}")

                # Handle attachments
                if msg.attachments:
                    print(f"  📎 {len(msg.attachments)} attachment(s):")
                    for att in msg.attachments:
                        att_type = att.get("contentType", "unknown")
                        att_name = att.get("fileName", "unnamed")
                        att_size = att.get("size", 0)
                        att_path = att.get("path")

                        print(f"     - {att_name} ({att_type}, {att_size} bytes)")

                        # Save media if enabled
                        if args.save_media and att_path:
                            try:
                                decrypted = db.decrypt_attachment(att_path)

                                # Create filename: timestamp_sender_filename.ext
                                safe_name = att_name.replace("/", "_").replace(
                                    "\\", "_"
                                )
                                ext = Path(att_name).suffix or _guess_extension(
                                    att_type
                                )
                                # Remove extension from safe_name to avoid duplicates
                                base_name = Path(safe_name).stem
                                out_name = f"{msg.timestamp}_{sender}_{base_name}{ext}"
                                out_path = media_dir / out_name

                                with open(out_path, "wb") as f:
                                    f.write(decrypted)
                                print(f"       ✓ Saved to {out_path}")
                            except Exception as e:
                                print(f"       ✗ Failed to save: {e}")

                print()

        except KeyboardInterrupt:
            print("\nStopped watching.")


def cmd_search(args):
    """Search messages."""
    config = SessionConfig(profile=args.profile)
    with SessionDatabase(config) as db:
        results = db.search_messages(args.query, limit=args.limit)

        if args.json:
            import json

            print(json.dumps([m.raw for m in results], indent=2))
            return

        print(f"Found {len(results)} messages matching '{args.query}':\n")

        convos = {c.id: c.name for c in db.get_conversations()}

        for msg in results:
            time_str = msg.sent_at.strftime("%Y-%m-%d %H:%M")
            convo_name = convos.get(msg.conversation_id, msg.conversation_id[:12])
            body = msg.body[:60] if msg.body else "(no text)"

            print(f"[{time_str}] {convo_name}")
            print(f"  {body}...")
            print()


def cmd_media(args):
    """Download media from a conversation."""
    config = SessionConfig(profile=args.profile)

    # Create output directory
    media_dir = Path(args.output).expanduser()
    media_dir.mkdir(parents=True, exist_ok=True)

    with SessionDatabase(config) as db:
        # Get messages with attachments
        conn = db.connection
        cursor = conn.execute(
            """
            SELECT json FROM messages
            WHERE conversationId = ? AND hasAttachments = 1
            ORDER BY sent_at DESC
            LIMIT ?
        """,
            (args.id, args.limit),
        )

        import json as json_module

        messages = [db._parse_message(json_module.loads(row[0])) for row in cursor]

        if not messages:
            print(
                f"No messages with attachments found in conversation {args.id[:16]}..."
            )
            return

        print(f"Found {len(messages)} messages with attachments")
        print(f"Saving to: {media_dir}\n")

        total_saved = 0
        for msg in messages:
            time_str = msg.sent_at.strftime("%Y%m%d_%H%M%S")
            sender = "You" if msg.is_outgoing else msg.source[:8]

            for att in msg.attachments:
                att_name = att.get("fileName", "unnamed")
                att_path = att.get("path")
                att_type = att.get("contentType", "unknown")
                att_size = att.get("size", 0)

                if not att_path:
                    print(f"  ✗ {att_name} - no path (not downloaded yet?)")
                    continue

                # Check if file exists
                full_path = config.get_attachment_path(att_path)
                if not full_path.exists():
                    print(f"  ✗ {att_name} - file not found")
                    continue

                try:
                    decrypted = db.decrypt_attachment(att_path)

                    # Create output filename
                    ext = Path(att_name).suffix or _guess_extension(att_type)
                    safe_name = att_name.replace("/", "_").replace("\\", "_")
                    # Remove extension from safe_name to avoid duplicates
                    base_name = Path(safe_name).stem
                    out_name = f"{time_str}_{sender}_{base_name}{ext}"
                    out_path = media_dir / out_name

                    with open(out_path, "wb") as f:
                        f.write(decrypted)

                    print(f"  ✓ {out_name} ({len(decrypted)} bytes)")
                    total_saved += 1

                except Exception as e:
                    print(f"  ✗ {att_name} - {e}")

        print(f"\nSaved {total_saved} files to {media_dir}")


def _guess_extension(content_type: str) -> str:
    """Guess file extension from content type."""
    mapping = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "video/mp4": ".mp4",
        "video/webm": ".webm",
        "audio/mpeg": ".mp3",
        "audio/ogg": ".ogg",
        "audio/aac": ".aac",
        "application/pdf": ".pdf",
    }
    return mapping.get(content_type, "")


def cmd_info(args):
    """Show Session info."""
    config = SessionConfig(profile=args.profile)

    print("Session Info:")
    print(f"  Data path: {config.data_path}")
    print(f"  Exists: {config.exists()}")

    if not config.exists():
        print("\n  Session data not found. Run Session at least once.")
        return 1

    print(f"  Has password: {config.has_password}")

    with SessionDatabase(config) as db:
        our_id = db.get_our_pubkey()
        print(f"  Session ID: {our_id}")

        convos = db.get_conversations()
        print(f"  Conversations: {len(convos)}")

    # Check CDP
    print("\n  CDP Status:")
    try:
        import urllib.request

        with urllib.request.urlopen(f"http://localhost:{args.port}/json", timeout=1):
            print(f"    ✓ Available on port {args.port}")
    except:
        print(f"    ✗ Not available (port {args.port})")
        print(f"    Start with: {SessionCDP.get_launch_command(args.port)}")


def main():
    parser = argparse.ArgumentParser(
        description="Session Desktop Controller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  session-cli list                          # List conversations
  session-cli messages 05abc123...          # Show messages
  session-cli send 05abc123... "Hello!"     # Send message
  session-cli watch                         # Watch for new messages
  session-cli search "keyword"              # Search messages
        """,
    )
    parser.add_argument(
        "--profile", "-p", help="Session profile name (default: production)"
    )
    parser.add_argument(
        "--port", type=int, default=9222, help="CDP port (default: 9222)"
    )
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")

    subparsers = parser.add_subparsers(dest="command", help="Command")

    # list
    list_parser = subparsers.add_parser("list", help="List conversations")
    list_parser.set_defaults(func=cmd_list)

    # messages
    msg_parser = subparsers.add_parser(
        "messages", help="Show messages from conversation"
    )
    msg_parser.add_argument("id", help="Conversation ID or name")
    msg_parser.add_argument(
        "--limit", "-n", type=int, default=20, help="Number of messages"
    )
    msg_parser.set_defaults(func=cmd_messages)

    # send
    send_parser = subparsers.add_parser("send", help="Send a message")
    send_parser.add_argument("id", help="Conversation ID")
    send_parser.add_argument("message", help="Message text")
    send_parser.set_defaults(func=cmd_send)

    # watch
    watch_parser = subparsers.add_parser("watch", help="Watch for new messages")
    watch_parser.add_argument("--convo", "-c", help="Only watch this conversation")
    watch_parser.add_argument(
        "--interval", "-i", type=float, default=1.0, help="Poll interval in seconds"
    )
    watch_parser.add_argument(
        "--save-media", "-m", action="store_true", help="Save media attachments"
    )
    watch_parser.add_argument(
        "--media-dir",
        "-d",
        default="./media",
        help="Directory to save media (default: ./media)",
    )
    watch_parser.set_defaults(func=cmd_watch)

    # search
    search_parser = subparsers.add_parser("search", help="Search messages")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "--limit", "-n", type=int, default=20, help="Number of results"
    )
    search_parser.set_defaults(func=cmd_search)

    # media
    media_parser = subparsers.add_parser(
        "media", help="Download media from a conversation"
    )
    media_parser.add_argument("id", help="Conversation ID")
    media_parser.add_argument(
        "--output", "-o", default="./media", help="Output directory (default: ./media)"
    )
    media_parser.add_argument(
        "--limit", "-n", type=int, default=100, help="Max messages to scan"
    )
    media_parser.set_defaults(func=cmd_media)

    # info
    info_parser = subparsers.add_parser("info", help="Show Session info")
    info_parser.set_defaults(func=cmd_info)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
