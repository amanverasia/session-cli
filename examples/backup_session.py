#!/usr/bin/env python3
"""
Backup and restore Session data example.

Run: python examples/backup_session.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from session_controller import SessionDatabase, SessionConfig


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Session Backup Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # backup
    backup_parser = subparsers.add_parser("backup", help="Create backup")
    backup_parser.add_argument(
        "--include-attachments",
        "-a",
        action="store_true",
        help="Include attachments in backup",
    )
    backup_parser.add_argument(
        "--encrypt", "-e", action="store_true", help="Encrypt backup with password"
    )
    backup_parser.add_argument(
        "--output",
        "-o",
        default="./backups",
        help="Output directory (default: ./backups)",
    )
    backup_parser.set_defaults(func=cmd_backup)

    # incremental
    inc_parser = subparsers.add_parser("incremental", help="Create incremental backup")
    inc_parser.add_argument(
        "--since",
        "-s",
        required=True,
        help="Starting timestamp (milliseconds) or 'yesterday', 'week'",
    )
    inc_parser.add_argument(
        "--include-attachments",
        "-a",
        action="store_true",
        help="Include new attachments",
    )
    inc_parser.add_argument(
        "--output",
        "-o",
        default="./backups",
        help="Output directory (default: ./backups)",
    )
    inc_parser.set_defaults(func=cmd_incremental)

    # restore
    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("backup_path", help="Path to backup")
    restore_parser.add_argument(
        "--password", "-p", help="Backup password (if encrypted)"
    )
    restore_parser.set_defaults(func=cmd_restore)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args) or 0


def cmd_backup(args):
    """Create a full backup."""
    config = SessionConfig()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"session-backup-{timestamp}"
    backup_path = output_dir / backup_name

    print(f"Creating backup: {backup_name}\n")

    import getpass

    backup_password = None
    if args.encrypt:
        backup_password = getpass.getpass(
            "Backup password (leave empty for no encryption): "
        )
        if backup_password == "":
            backup_password = None

    with SessionDatabase(config) as db:
        result = db.create_backup(
            str(backup_path),
            include_attachments=args.include_attachments,
            backup_password=backup_password,
        )

    print(f"\n✓ Backup created successfully!")
    print(f"  Location: {result['backup_path']}")
    print(f"  Encrypted: {result.get('is_encrypted', False)}")
    print(f"  Conversations: {result.get('conversation_count', 0)}")
    print(f"  Includes attachments: {result['includes_attachments']}")
    print(f"  Session ID: {result.get('session_id', 'unknown')}")


def cmd_incremental(args):
    """Create incremental backup."""
    import time
    from datetime import timedelta

    config = SessionConfig()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    since_timestamp = args.since
    if since_timestamp == "yesterday":
        since_timestamp = int((datetime.now() - timedelta(days=1)).timestamp() * 1000)
    elif since_timestamp == "week":
        since_timestamp = int((datetime.now() - timedelta(weeks=1)).timestamp() * 1000)
    else:
        since_timestamp = int(since_timestamp)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"session-incremental-{timestamp}"
    backup_path = output_dir / backup_name

    print(f"Creating incremental backup: {backup_name}")
    print(
        f"Since: {since_timestamp} ({datetime.fromtimestamp(since_timestamp / 1000).isoformat()})\n"
    )

    with SessionDatabase(config) as db:
        result = db.create_incremental_backup(
            str(backup_path),
            since_timestamp=since_timestamp,
            include_attachments=args.include_attachments,
        )

    print(f"\n✓ Incremental backup created!")
    print(f"  Location: {result['backup_path']}")
    print(f"  New messages: {result.get('message_count', 0)}")
    print(f"  New attachments: {result.get('new_attachments', 0)}")
    print(f"  Backup type: {result.get('backup_type', 'incremental')}")


def cmd_restore(args):
    """Restore from backup."""
    config = SessionConfig()
    backup_path = Path(args.backup_path)

    print(f"Restoring from: {backup_path}")
    print(f"Target: {config.data_path}\n")

    with SessionDatabase(config) as db:
        db.restore_from_backup(str(backup_path), args.password)


if __name__ == "__main__":
    sys.exit(main())
