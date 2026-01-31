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
    session-cli requests                 # List pending requests
    session-cli accept-request <id>      # Accept a request
    session-cli decline-request <id>     # Decline a request
    session-cli block-request <id>       # Block a request
"""

import argparse
import json
import logging
import sys
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from .config import SessionConfig
    from .cdp import SessionCDP
    from .database import SessionDatabase
    from .exceptions import CDPError, SessionError
    from .user_config import UserConfig
    from .repl import SessionREPL
except ImportError:
    from config import SessionConfig
    from cdp import SessionCDP
    from database import SessionDatabase
    from exceptions import CDPError, SessionError
    from user_config import UserConfig
    from repl import SessionREPL

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

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


def get_version() -> str:
    """Get version from package or file."""
    try:
        from session_controller import __version__

        return __version__
    except ImportError:
        version_file = Path(__file__).parent / "__init__.py"
        if version_file.exists():
            for line in version_file.read_text().split("\n"):
                if "__version__" in line:
                    return line.split("=")[1].strip().strip('"')
    return "1.3.0"


__version__ = get_version()


def _connect_cdp(port: int) -> SessionCDP:
    """
    Connect to Session CDP with error handling.

    Args:
        port: CDP port number

    Returns:
        Connected SessionCDP instance

    Raises:
        SystemExit: If connection fails
    """
    try:
        cdp = SessionCDP(port=port)
        cdp.connect()
        return cdp
    except CDPError as e:
        logger.error(f"CDP connection failed: {e}")
        logger.error(
            f"Make sure Session is running with: {SessionCDP.get_launch_command(port)}"
        )
        sys.exit(1)
    except SessionError as e:
        logger.error(f"Session error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error connecting to Session CDP: {e}")
        sys.exit(1)


def cmd_list(args) -> Optional[int]:
    """List all conversations."""
    config = SessionConfig(profile=args.profile)
    with SessionDatabase(config) as db:
        convos = db.get_conversations()

        if args.json:
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
    cdp = _connect_cdp(args.port)

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
    """Search messages with enhanced filtering."""
    config = SessionConfig(profile=args.profile)
    with SessionDatabase(config) as db:
        # Parse date filters
        after_timestamp = None
        before_timestamp = None
        if args.after:
            try:
                after_timestamp = db.parse_date_filter(args.after)
            except ValueError as e:
                print(f"Invalid --after date: {e}")
                return 1

        if args.before:
            try:
                before_timestamp = db.parse_date_filter(args.before)
            except ValueError as e:
                print(f"Invalid --before date: {e}")
                return 1

        # Resolve conversation name to ID if needed
        conversation_id = None
        if args.conversation:
            convo = db.find_conversation(args.conversation)
            if convo:
                conversation_id = convo.id
            else:
                conversation_id = args.conversation

        # Resolve sender name to Session ID if needed
        sender = None
        if args.sender:
            sender = db.resolve_contact(args.sender)

        # Build search params
        search_params = {
            "query": args.query,
            "conversation_id": conversation_id,
            "after_timestamp": after_timestamp,
            "before_timestamp": before_timestamp,
            "message_type": args.type,
            "sender": sender,
            "unread_only": args.unread_only,
            "limit": args.limit,
        }

        results = db.search_messages_enhanced(**search_params)

        if args.json:
            print(json.dumps([m.raw for m in results], indent=2))
            return

        # Build filter description
        filter_desc = []
        if args.query:
            filter_desc.append(f"'{args.query}'")
        if args.conversation:
            filter_desc.append(f"conversation: {args.conversation}")
        if args.after:
            filter_desc.append(f"after: {args.after}")
        if args.before:
            filter_desc.append(f"before: {args.before}")
        if args.type != "all":
            filter_desc.append(f"type: {args.type}")
        if args.sender:
            filter_desc.append(f"sender: {args.sender}")
        if args.unread_only:
            filter_desc.append("unread only")

        filter_str = " AND ".join(filter_desc) if filter_desc else "all messages"
        print(f"Found {len(results)} messages matching {filter_str}:\n")

        if not results:
            return

        convos = {c.id: c.name for c in db.get_conversations()}

        for msg in results:
            time_str = msg.sent_at.strftime("%Y-%m-%d %H:%M")
            convo_name = convos.get(msg.conversation_id, msg.conversation_id[:12])
            body = msg.body[:60] if msg.body else "(no text)"

            msg_type = ""
            if msg.attachments:
                msg_type = " [📎 attachment]"
            if msg.quote:
                msg_type = " [↩ quote]"

            print(f"[{time_str}] {convo_name}{msg_type}")
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

        messages = [db._parse_message(json.loads(row[0])) for row in cursor]

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


def cmd_export(args):
    """Export a conversation to file."""
    config = SessionConfig(profile=args.profile)
    with SessionDatabase(config) as db:
        try:
            if args.format == "json":
                db.export_conversation_to_json(
                    args.id,
                    args.output,
                    include_attachments=args.include_attachments,
                    attachment_output_dir=args.attachments_dir,
                )
            elif args.format == "csv":
                db.export_conversation_to_csv(args.id, args.output)
            elif args.format == "html":
                db.export_conversation_to_html(
                    args.id, args.output, include_attachments=args.include_attachments
                )

            print(f"✓ Exported to {args.output}")
        except Exception as e:
            print(f"✗ Export failed: {e}")
            return 1


def cmd_export_all(args):
    """Export all conversations."""
    config = SessionConfig(profile=args.profile)
    with SessionDatabase(config) as db:
        try:
            db.export_all_conversations(
                args.output,
                format=args.format,
                include_attachments=args.include_attachments,
                attachment_output_dir=args.attachments_dir,
            )
            print(f"✓ Exported all conversations to {args.output}")
        except Exception as e:
            print(f"✗ Export failed: {e}")
            return 1


def cmd_backup(args):
    """Create a backup."""
    config = SessionConfig(profile=args.profile)
    with SessionDatabase(config) as db:
        try:
            import getpass

            backup_password = None
            if args.encrypt:
                backup_password = getpass.getpass(
                    "Backup password (leave empty for no encryption): "
                )
                if backup_password == "":
                    backup_password = None

            result = db.create_backup(
                args.output,
                include_attachments=args.include_attachments,
                backup_password=backup_password,
            )

            print(f"✓ Backup created successfully!")
            print(f"  Location: {result['backup_path']}")
            print(f"  Encrypted: {result.get('is_encrypted', False)}")
            print(f"  Conversations: {result.get('conversation_count', 0)}")
            print(f"  Includes attachments: {result['includes_attachments']}")
        except Exception as e:
            print(f"✗ Backup failed: {e}")
            return 1


def cmd_restore(args):
    """Restore from backup."""
    config = SessionConfig(profile=args.profile)
    with SessionDatabase(config) as db:
        try:
            import getpass

            backup_password = None
            if args.password:
                backup_password = args.password
            elif args.encrypt:
                backup_password = getpass.getpass("Backup password: ")

            db.restore_from_backup(args.backup_path, backup_password)
        except Exception as e:
            print(f"✗ Restore failed: {e}")
            return 1


def cmd_requests(args):
    """List pending requests."""
    config = SessionConfig(profile=args.profile)
    with SessionDatabase(config) as db:
        requests = db.get_pending_requests()

        # Apply filters
        if args.type:
            if args.type == "message":
                requests = [r for r in requests if r.is_message_request]
            elif args.type == "contact":
                requests = [
                    r
                    for r in requests
                    if r.is_contact_request and not r.is_message_request
                ]

        if args.conversation_type:
            if args.conversation_type == "private":
                requests = [r for r in requests if r.is_private]
            elif args.conversation_type == "group":
                requests = [r for r in requests if r.is_group]

        if args.unread:
            requests = [r for r in requests if r.unread_count > 0]

        if args.json:
            print(json.dumps([r.raw for r in requests], indent=2))
            return

        if not requests:
            print("No pending requests.")
            return

        print(f"Found {len(requests)} pending request(s):\n")

        if args.group:
            # Group by request type
            message_requests = [r for r in requests if r.is_message_request]
            contact_requests = [
                r for r in requests if r.is_contact_request and not r.is_message_request
            ]

            if message_requests:
                print("=== Message Requests ===")
                for i, r in enumerate(message_requests, 1):
                    _print_request(i, r)
                print()

            if contact_requests:
                print("=== Contact Requests ===")
                for i, r in enumerate(contact_requests, 1):
                    _print_request(i, r)
        else:
            # No grouping, just list all
            for i, r in enumerate(requests, 1):
                _print_request(i, r)


def _print_request(index: int, request):
    """Helper function to print a single request."""
    req_type = ""
    if request.is_message_request:
        req_type = " [Message Request]"
    elif request.is_contact_request:
        req_type = " [Contact Request]"

    unread = f" ({request.unread_count} unread)" if request.unread_count else ""
    last = (
        request.last_message[:40] + "..."
        if request.last_message and len(request.last_message) > 40
        else (request.last_message or "(no messages)")
    )
    time_str = (
        request.created_at_datetime.strftime("%Y-%m-%d %H:%M")
        if request.created_at
        else "Unknown"
    )

    print(f"{index}. {request.name}{req_type}")
    print(f"   ID: {request.id}")
    print(f"   Type: {request.type}")
    print(f"   Created: {time_str}")
    print(f"   Last message: {last}{unread}")
    print()


def cmd_accept_request(args):
    """Accept a pending request."""
    cdp = _connect_cdp(args.port)

    try:
        config = SessionConfig(profile=args.profile)
        with SessionDatabase(config) as db:
            request = db.get_request(args.id)
            if not request:
                print(f"Pending request not found: {args.id}")
                return 1

            print(f"Accepting request from {request.name}...")
            result = cdp.accept_request(args.id)
            if result:
                print(f"✓ Request accepted from {request.name}")
            else:
                print("✗ Failed to accept request")
                return 1
    finally:
        cdp.close()


def cmd_decline_request(args):
    """Decline a pending request."""
    cdp = _connect_cdp(args.port)

    try:
        config = SessionConfig(profile=args.profile)
        with SessionDatabase(config) as db:
            request = db.get_request(args.id)
            if not request:
                print(f"Pending request not found: {args.id}")
                return 1

            print(f"Declining request from {request.name}...")
            result = cdp.decline_request(args.id)
            if result:
                print(f"✓ Request declined from {request.name}")
            else:
                print("✗ Failed to decline request")
                return 1
    finally:
        cdp.close()


def cmd_block_request(args):
    """Block a request sender."""
    cdp = _connect_cdp(args.port)

    try:
        config = SessionConfig(profile=args.profile)
        with SessionDatabase(config) as db:
            request = db.get_request(args.id)
            if not request:
                print(f"Pending request not found: {args.id}")
                return 1

            print(f"Blocking {request.name}...")
            result = cdp.block_request(args.id)
            if result:
                print(f"✓ Blocked {request.name}")
            else:
                print("✗ Failed to block request")
                return 1
    finally:
        cdp.close()


def cmd_repl(args, user_config: UserConfig):
    """Start interactive REPL mode."""
    repl = SessionREPL(
        profile=args.profile,
        port=args.port,
        json_output=args.json,
        user_config=user_config,
    )
    repl.run()


# === Group Management Commands ===


def cmd_group_members(args):
    """List group members and admins."""
    cdp = _connect_cdp(args.port)

    try:
        result = cdp.get_group_members(args.id)
        if not result:
            print(f"Group not found or not a group: {args.id}")
            return 1

        if args.json:
            print(json.dumps(result, indent=2))
            return

        print(f"Group: {result['name']}")
        print(f"ID: {result['id']}")
        print(f"Type: {result['type']}")
        print(f"You are admin: {'Yes' if result['weAreAdmin'] else 'No'}")
        print()

        print(f"Admins ({len(result['admins'])}):")
        for admin in result['admins']:
            print(f"  * {admin}")

        print(f"\nMembers ({len(result['members'])}):")
        for member in result['members']:
            is_admin = " (admin)" if member in result['admins'] else ""
            print(f"  - {member}{is_admin}")

    finally:
        cdp.close()


def cmd_group_add(args):
    """Add a member to a group."""
    cdp = _connect_cdp(args.port)

    try:
        print(f"Adding {args.session_id} to group...")
        result = cdp.add_group_member(args.id, args.session_id)
        if result:
            print(f"✓ Added {args.session_id} to group")
        else:
            print("✗ Failed to add member")
            return 1
    except RuntimeError as e:
        print(f"✗ Error: {e}")
        return 1
    finally:
        cdp.close()


def cmd_group_remove(args):
    """Remove a member from a group."""
    cdp = _connect_cdp(args.port)

    try:
        print(f"Removing {args.session_id} from group...")
        result = cdp.remove_group_member(args.id, args.session_id)
        if result:
            print(f"✓ Removed {args.session_id} from group")
        else:
            print("✗ Failed to remove member")
            return 1
    except RuntimeError as e:
        print(f"✗ Error: {e}")
        return 1
    finally:
        cdp.close()


def cmd_group_promote(args):
    """Promote a member to admin."""
    cdp = _connect_cdp(args.port)

    try:
        print(f"Promoting {args.session_id} to admin...")
        result = cdp.promote_to_admin(args.id, args.session_id)
        if result:
            print(f"✓ Promoted {args.session_id} to admin")
        else:
            print("✗ Failed to promote member")
            return 1
    except RuntimeError as e:
        print(f"✗ Error: {e}")
        return 1
    finally:
        cdp.close()


def cmd_group_demote(args):
    """Demote an admin to regular member."""
    cdp = _connect_cdp(args.port)

    try:
        print(f"Demoting {args.session_id} from admin...")
        result = cdp.demote_admin(args.id, args.session_id)
        if result:
            print(f"✓ Demoted {args.session_id} from admin")
        else:
            print("✗ Failed to demote admin")
            return 1
    except RuntimeError as e:
        print(f"✗ Error: {e}")
        return 1
    finally:
        cdp.close()


def cmd_group_leave(args):
    """Leave a group."""
    cdp = _connect_cdp(args.port)

    try:
        # Get group info first
        info = cdp.get_group_members(args.id)
        if not info:
            print(f"Group not found: {args.id}")
            return 1

        group_name = info['name']

        if not args.yes:
            confirm = input(f"Leave group '{group_name}'? [y/N] ")
            if confirm.lower() != 'y':
                print("Cancelled.")
                return 0

        print(f"Leaving group '{group_name}'...")
        result = cdp.leave_group(args.id)
        if result:
            print(f"✓ Left group '{group_name}'")
        else:
            print("✗ Failed to leave group")
            return 1
    except RuntimeError as e:
        print(f"✗ Error: {e}")
        return 1
    finally:
        cdp.close()


def cmd_group_create(args):
    """Create a new group."""
    print("✗ Group creation is not supported via CLI.")
    print("  Session Desktop does not expose this API.")
    print("  Please use the Session GUI to create groups.")
    return 1


def cmd_group_rename(args):
    """Rename a group."""
    cdp = _connect_cdp(args.port)

    try:
        # Get current group info
        info = cdp.get_group_members(args.id)
        if not info:
            print(f"Group not found: {args.id}")
            return 1

        old_name = info['name']
        print(f"Renaming group '{old_name}' to '{args.name}'...")

        result = cdp.rename_group(args.id, args.name)
        if result:
            print(f"✓ Renamed group to '{args.name}'")
        else:
            print("✗ Failed to rename group")
            return 1
    except RuntimeError as e:
        print(f"✗ Error: {e}")
        return 1
    finally:
        cdp.close()


def main():
    # Load user configuration
    user_config = UserConfig.load()

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
  session-cli export 05abc... -o convo.json  # Export conversation
  session-cli backup -o ./backups           # Create backup
  session-cli requests                      # List pending requests
  session-cli accept-request 05abc...       # Accept a request
  session-cli repl                          # Interactive REPL mode

 Group Management:
  session-cli group members <id>            # List group members
  session-cli group add <id> <session_id>   # Add member to group
  session-cli group remove <id> <session_id>  # Remove member
  session-cli group promote <id> <session_id> # Promote to admin
  session-cli group demote <id> <session_id>  # Demote admin
  session-cli group leave <id>              # Leave a group
  session-cli group create "Name" <ids...>  # Create new group
  session-cli group rename <id> "New Name"  # Rename group
        """,
    )
    parser.add_argument(
        "--version", "-v", action="store_true", help="Show version and exit"
    )
    parser.add_argument(
        "--profile", "-p", help="Session profile name (default: production)"
    )
    parser.add_argument(
        "--port", type=int, default=9222, help="CDP port (default: 9222)"
    )
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")

    # Apply user config defaults (CLI args will override these)
    parser.set_defaults(
        profile=user_config.profile,
        port=user_config.port,
        json=user_config.json_output,
    )

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
    search_parser.add_argument(
        "query", nargs="?", help="Search query (leave empty to apply filters only)"
    )
    search_parser.add_argument(
        "--limit", "-n", type=int, default=20, help="Number of results"
    )
    search_parser.add_argument(
        "--conversation", "-c", help="Filter by conversation ID or name"
    )
    search_parser.add_argument(
        "--after",
        "-a",
        help="Filter messages after this date (e.g., 'today', 'yesterday', '7d', '2025-01-31')",
    )
    search_parser.add_argument(
        "--before", "-b", help="Filter messages before this date"
    )
    search_parser.add_argument(
        "--type",
        "-t",
        choices=["text", "attachment", "quote", "all"],
        default="all",
        help="Filter by message type",
    )
    search_parser.add_argument(
        "--sender", "-s", help="Filter by sender (Session ID or name)"
    )
    search_parser.add_argument(
        "--unread-only", "-u", action="store_true", help="Only show unread messages"
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

    # export
    export_parser = subparsers.add_parser("export", help="Export a conversation")
    export_parser.add_argument("id", help="Conversation ID or name")
    export_parser.add_argument(
        "--format",
        "-f",
        default="json",
        choices=["json", "csv", "html"],
        help="Export format",
    )
    export_parser.add_argument("--output", "-o", required=True, help="Output file")
    export_parser.add_argument(
        "--include-attachments",
        "-a",
        action="store_true",
        help="Include/download attachments",
    )
    export_parser.add_argument("--attachments-dir", help="Directory for attachments")
    export_parser.set_defaults(func=cmd_export)

    # export-all
    export_all_parser = subparsers.add_parser(
        "export-all", help="Export all conversations"
    )
    export_all_parser.add_argument(
        "--format",
        "-f",
        default="json",
        choices=["json", "csv", "html"],
        help="Export format",
    )
    export_all_parser.add_argument(
        "--output", "-o", required=True, help="Output directory"
    )
    export_all_parser.add_argument(
        "--include-attachments",
        "-a",
        action="store_true",
        help="Include/download attachments",
    )
    export_all_parser.add_argument(
        "--attachments-dir", help="Directory for attachments"
    )
    export_all_parser.set_defaults(func=cmd_export_all)

    # backup
    backup_parser = subparsers.add_parser("backup", help="Create a backup")
    backup_parser.add_argument("--output", "-o", required=True, help="Backup directory")
    backup_parser.add_argument(
        "--include-attachments",
        "-a",
        action="store_true",
        help="Include attachments in backup",
    )
    backup_parser.add_argument(
        "--encrypt", "-e", action="store_true", help="Encrypt backup with password"
    )
    backup_parser.set_defaults(func=cmd_backup)

    # restore
    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument(
        "backup_path", help="Path to backup directory or .enc file"
    )
    restore_parser.add_argument(
        "--password", "-p", help="Backup password (if encrypted)"
    )
    restore_parser.set_defaults(func=cmd_restore)

    # info
    info_parser = subparsers.add_parser("info", help="Show Session info")
    info_parser.set_defaults(func=cmd_info)

    # requests
    requests_parser = subparsers.add_parser("requests", help="List pending requests")
    requests_parser.add_argument(
        "--type",
        "-t",
        choices=["message", "contact", "all"],
        default="all",
        help="Filter by request type",
    )
    requests_parser.add_argument(
        "--conversation-type",
        "-c",
        choices=["private", "group", "all"],
        default="all",
        help="Filter by conversation type",
    )
    requests_parser.add_argument(
        "--unread",
        "-u",
        action="store_true",
        help="Only show requests with unread messages",
    )
    requests_parser.add_argument(
        "--group",
        "-g",
        action="store_true",
        help="Group requests by type",
    )
    requests_parser.set_defaults(func=cmd_requests)

    # accept-request
    accept_parser = subparsers.add_parser(
        "accept-request", help="Accept a pending request"
    )
    accept_parser.add_argument("id", help="Request ID (Session ID or conversation ID)")
    accept_parser.set_defaults(func=cmd_accept_request)

    # decline-request
    decline_parser = subparsers.add_parser(
        "decline-request", help="Decline a pending request"
    )
    decline_parser.add_argument("id", help="Request ID (Session ID or conversation ID)")
    decline_parser.set_defaults(func=cmd_decline_request)

    # block-request
    block_parser = subparsers.add_parser(
        "block-request", help="Block and decline a request"
    )
    block_parser.add_argument("id", help="Request ID (Session ID or conversation ID)")
    block_parser.set_defaults(func=cmd_block_request)

    # group - with nested subcommands
    group_parser = subparsers.add_parser(
        "group", help="Group management commands"
    )
    group_subparsers = group_parser.add_subparsers(dest="group_command", help="Group command")

    # group members
    group_members_parser = group_subparsers.add_parser(
        "members", help="List group members and admins"
    )
    group_members_parser.add_argument("id", help="Group ID")
    group_members_parser.set_defaults(func=cmd_group_members)

    # group add
    group_add_parser = group_subparsers.add_parser(
        "add", help="Add a member to a group"
    )
    group_add_parser.add_argument("id", help="Group ID")
    group_add_parser.add_argument("session_id", help="Session ID of user to add")
    group_add_parser.set_defaults(func=cmd_group_add)

    # group remove
    group_remove_parser = group_subparsers.add_parser(
        "remove", help="Remove a member from a group"
    )
    group_remove_parser.add_argument("id", help="Group ID")
    group_remove_parser.add_argument("session_id", help="Session ID of user to remove")
    group_remove_parser.set_defaults(func=cmd_group_remove)

    # group promote
    group_promote_parser = group_subparsers.add_parser(
        "promote", help="Promote a member to admin"
    )
    group_promote_parser.add_argument("id", help="Group ID")
    group_promote_parser.add_argument("session_id", help="Session ID of user to promote")
    group_promote_parser.set_defaults(func=cmd_group_promote)

    # group demote
    group_demote_parser = group_subparsers.add_parser(
        "demote", help="Demote an admin to regular member"
    )
    group_demote_parser.add_argument("id", help="Group ID")
    group_demote_parser.add_argument("session_id", help="Session ID of admin to demote")
    group_demote_parser.set_defaults(func=cmd_group_demote)

    # group leave
    group_leave_parser = group_subparsers.add_parser(
        "leave", help="Leave a group"
    )
    group_leave_parser.add_argument("id", help="Group ID")
    group_leave_parser.add_argument(
        "--yes", "-y", action="store_true", help="Skip confirmation"
    )
    group_leave_parser.set_defaults(func=cmd_group_leave)

    # group create
    group_create_parser = group_subparsers.add_parser(
        "create", help="Create a new group"
    )
    group_create_parser.add_argument("name", help="Name for the new group")
    group_create_parser.add_argument(
        "members", nargs="+", help="Session IDs of members to add"
    )
    group_create_parser.set_defaults(func=cmd_group_create)

    # group rename
    group_rename_parser = group_subparsers.add_parser(
        "rename", help="Rename a group"
    )
    group_rename_parser.add_argument("id", help="Group ID")
    group_rename_parser.add_argument("name", help="New name for the group")
    group_rename_parser.set_defaults(func=cmd_group_rename)

    # repl / interactive
    repl_parser = subparsers.add_parser(
        "repl", aliases=["interactive"], help="Start interactive REPL mode"
    )
    repl_parser.set_defaults(func=lambda args: cmd_repl(args, user_config))

    args = parser.parse_args()

    if args.version:
        print(f"session-cli {__version__}")
        return 0

    if not args.command:
        parser.print_help()
        return 1

    # Handle group command without subcommand
    if args.command == "group" and not getattr(args, "group_command", None):
        group_parser.print_help()
        return 1

    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
