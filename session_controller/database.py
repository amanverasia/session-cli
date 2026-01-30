"""
Direct database access for Session Desktop.

Requires: sqlcipher3 or pysqlcipher3
Install: pip install sqlcipher3
"""

import json
from pathlib import Path
from typing import Optional, Iterator, Any
from dataclasses import dataclass
from datetime import datetime

try:
    from .config import SessionConfig
except ImportError:
    from config import SessionConfig

# Try different sqlcipher packages
try:
    from sqlcipher3 import dbapi2 as sqlite
except ImportError:
    try:
        from pysqlcipher3 import dbapi2 as sqlite
    except ImportError:
        sqlite = None


@dataclass
class Message:
    """Represents a Session message."""

    id: str
    conversation_id: str
    source: str  # Sender's Session ID
    body: Optional[str]
    timestamp: int  # sent_at in ms
    received_at: Optional[int]
    type: str  # 'incoming' or 'outgoing'
    attachments: list
    quote: Optional[dict]
    raw: dict  # Full JSON data

    @property
    def sent_at(self) -> datetime:
        """Get sent timestamp as datetime."""
        return datetime.fromtimestamp(self.timestamp / 1000)

    @property
    def is_incoming(self) -> bool:
        return self.type == "incoming"

    @property
    def is_outgoing(self) -> bool:
        return self.type == "outgoing"


@dataclass
class Conversation:
    """Represents a Session conversation."""

    id: str  # Session ID or group ID
    type: str  # 'private', 'group', 'groupv2'
    display_name: Optional[str]
    nickname: Optional[str]
    last_message: Optional[str]
    active_at: int
    unread_count: int
    raw: dict  # Full JSON data

    @property
    def name(self) -> str:
        """Get display name, preferring nickname."""
        return self.nickname or self.display_name or self.id[:8]

    @property
    def is_private(self) -> bool:
        return self.type == "private"

    @property
    def is_group(self) -> bool:
        return self.type in ("group", "groupv2")


class SessionDatabase:
    """
    Direct read-only access to Session's SQLCipher database.

    Example:
        db = SessionDatabase()
        for msg in db.get_messages("05abc123..."):
            print(f"{msg.source}: {msg.body}")
    """

    def __init__(
        self, config: Optional[SessionConfig] = None, password: Optional[str] = None
    ):
        """
        Initialize database connection.

        Args:
            config: SessionConfig instance. If None, uses production Session.
            password: Database password if user has set one. If None, uses key from config.
        """
        if sqlite is None:
            raise ImportError(
                "sqlcipher3 not installed. Install with: pip install sqlcipher3"
            )

        self.config = config or SessionConfig()
        self._password = password
        self._conn = None
        self._attachment_key: Optional[str] = None

    def _get_connection(self):
        """Get or create database connection."""
        if self._conn is not None:
            return self._conn

        if not self.config.db_path.exists():
            raise FileNotFoundError(
                f"Database not found: {self.config.db_path}\n"
                "Make sure Session has been run at least once."
            )

        self._conn = sqlite.connect(str(self.config.db_path))

        # Apply encryption key
        if self._password:
            # User-provided password
            self._conn.execute(f"PRAGMA key = '{self._password}'")
        elif self.config.has_password:
            raise ValueError(
                "Database has a password set. Provide it via the 'password' argument."
            )
        else:
            # Use hex key from config
            key = self.config.db_key
            self._conn.execute(f"PRAGMA key = \"x'{key}'\"")

        # Verify we can read the database
        try:
            self._conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
        except Exception as e:
            self._conn.close()
            self._conn = None
            raise ValueError(f"Failed to decrypt database: {e}")

        return self._conn

    @property
    def connection(self):
        """Get the raw database connection for custom queries."""
        return self._get_connection()

    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # === Conversations ===

    def get_conversations(self) -> list[Conversation]:
        """Get all conversations."""
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT id, type, active_at, displayNameInProfile, nickname,
                   lastMessage, unreadCount, members, groupAdmins,
                   isApproved, didApproveMe, avatarInProfile
            FROM conversations
            WHERE active_at > 0
            ORDER BY active_at DESC
        """)

        conversations = []
        for row in cursor:
            conversations.append(
                Conversation(
                    id=row[0],
                    type=row[1] or "private",
                    display_name=row[3],
                    nickname=row[4],
                    last_message=row[5],
                    active_at=row[2] or 0,
                    unread_count=row[6] or 0,
                    raw={
                        "id": row[0],
                        "type": row[1],
                        "active_at": row[2],
                        "displayNameInProfile": row[3],
                        "nickname": row[4],
                        "lastMessage": row[5],
                        "unreadCount": row[6],
                        "members": row[7],
                        "groupAdmins": row[8],
                        "isApproved": row[9],
                        "didApproveMe": row[10],
                        "avatarInProfile": row[11],
                    },
                )
            )

        return conversations

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a specific conversation by ID."""
        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT id, type, active_at, displayNameInProfile, nickname,
                   lastMessage, unreadCount
            FROM conversations WHERE id = ?
        """,
            (conversation_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        return Conversation(
            id=row[0],
            type=row[1] or "private",
            display_name=row[3],
            nickname=row[4],
            last_message=row[5],
            active_at=row[2] or 0,
            unread_count=row[6] or 0,
            raw={
                "id": row[0],
                "type": row[1],
                "active_at": row[2],
                "displayNameInProfile": row[3],
                "nickname": row[4],
                "lastMessage": row[5],
                "unreadCount": row[6],
            },
        )

    # === Messages ===

    def get_messages(
        self,
        conversation_id: str,
        limit: int = 100,
        before_timestamp: Optional[int] = None,
    ) -> list[Message]:
        """
        Get messages from a conversation.

        Args:
            conversation_id: The conversation ID (Session ID or group ID)
            limit: Maximum number of messages to return
            before_timestamp: Only get messages before this timestamp (ms)
        """
        conn = self._get_connection()

        if before_timestamp:
            cursor = conn.execute(
                """
                SELECT json FROM messages
                WHERE conversationId = ? AND sent_at < ?
                ORDER BY sent_at DESC
                LIMIT ?
            """,
                (conversation_id, before_timestamp, limit),
            )
        else:
            cursor = conn.execute(
                """
                SELECT json FROM messages
                WHERE conversationId = ?
                ORDER BY sent_at DESC
                LIMIT ?
            """,
                (conversation_id, limit),
            )

        messages = []
        for row in cursor:
            data = json.loads(row[0])
            messages.append(self._parse_message(data))

        return messages

    def get_new_messages(self, since_timestamp: int) -> list[Message]:
        """
        Get all new messages since a timestamp.

        Args:
            since_timestamp: Timestamp in milliseconds
        """
        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT json FROM messages
            WHERE received_at > ?
            ORDER BY received_at ASC
        """,
            (since_timestamp,),
        )

        return [self._parse_message(json.loads(row[0])) for row in cursor]

    def get_message_by_id(self, message_id: str) -> Optional[Message]:
        """Get a specific message by ID."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT json FROM messages WHERE id = ?", (message_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return self._parse_message(json.loads(row[0]))

    def search_messages(self, query: str, limit: int = 50) -> list[Message]:
        """
        Search messages by text content.

        Uses FTS5 full-text search on message body.
        """
        conn = self._get_connection()
        # FTS5 search using rowid to join back to messages
        cursor = conn.execute(
            """
            SELECT m.json FROM messages m
            WHERE m.rowid IN (
                SELECT rowid FROM messages_fts WHERE messages_fts MATCH ?
            )
            ORDER BY m.sent_at DESC
            LIMIT ?
        """,
            (query, limit),
        )

        return [self._parse_message(json.loads(row[0])) for row in cursor]

    def _parse_message(self, data: dict) -> Message:
        """Parse message JSON into Message object."""
        return Message(
            id=data.get("id", ""),
            conversation_id=data.get("conversationId", ""),
            source=data.get("source", ""),
            body=data.get("body"),
            timestamp=data.get("sent_at") or data.get("timestamp") or 0,
            received_at=data.get("received_at"),
            type=data.get("type", "incoming"),
            attachments=data.get("attachments", []),
            quote=data.get("quote"),
            raw=data,
        )

    # === Attachments ===

    def get_attachment_key(self) -> str:
        """Get the local attachment encryption key."""
        if self._attachment_key is None:
            # Try both possible key names
            key = self.get_setting("local_attachment_encrypted_key")
            if not key:
                key = self.get_setting("localAttachmentEncryptionKey")
            if not key:
                raise ValueError("Attachment encryption key not found in database")
            self._attachment_key = key
        return self._attachment_key

    def decrypt_attachment(self, filename: str) -> bytes:
        """
        Decrypt an attachment file.

        Args:
            filename: The attachment filename (from message.attachments[].path)

        Returns:
            Decrypted file contents as bytes
        """
        try:
            import nacl.bindings
        except ImportError:
            raise ImportError("PyNaCl not installed. Install with: pip install pynacl")

        key_hex = self.get_attachment_key()
        key = bytes.fromhex(key_hex)

        file_path = self.config.get_attachment_path(filename)
        if not file_path.exists():
            raise FileNotFoundError(f"Attachment not found: {file_path}")

        with open(file_path, "rb") as f:
            encrypted_data = f.read()

        # Header is first 24 bytes (crypto_secretstream_xchacha20poly1305_HEADERBYTES)
        header = encrypted_data[:24]
        ciphertext = encrypted_data[24:]

        # Create state and initialize for pulling (decryption)
        state = nacl.bindings.crypto_secretstream_xchacha20poly1305_state()
        nacl.bindings.crypto_secretstream_xchacha20poly1305_init_pull(
            state, header, key
        )

        # Decrypt
        plaintext, tag = nacl.bindings.crypto_secretstream_xchacha20poly1305_pull(
            state, ciphertext
        )

        return bytes(plaintext)

    # === Settings ===

    def get_setting(self, key: str) -> Any:
        """Get a setting value from the items table."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT json FROM items WHERE id = ?", (key,))
        row = cursor.fetchone()
        if not row:
            return None
        data = json.loads(row[0])
        return data.get("value")

    def get_our_pubkey(self) -> Optional[str]:
        """Get our own Session ID (public key)."""
        # Try different possible keys
        for key in ["primaryDevicePubKey", "number_id"]:
            val = self.get_setting(key)
            if val and isinstance(val, str) and len(val) == 66 and val.startswith("05"):
                return val

        return None

    # === Watching ===

    def watch_messages(
        self, poll_interval: float = 1.0, conversation_id: Optional[str] = None
    ) -> Iterator[Message]:
        """
        Generator that yields new messages as they arrive.

        Args:
            poll_interval: Seconds between database polls
            conversation_id: Only watch this conversation (None for all)

        Yields:
            New Message objects as they arrive
        """
        import time

        last_check = int(time.time() * 1000)

        while True:
            messages = self.get_new_messages(last_check)

            for msg in messages:
                if conversation_id is None or msg.conversation_id == conversation_id:
                    yield msg

            if messages:
                last_check = max(m.received_at or m.timestamp for m in messages)

            time.sleep(poll_interval)

    # === Export ===

    def export_conversation_to_json(
        self,
        conversation_id: str,
        output_path: str,
        include_attachments: bool = False,
        attachment_output_dir: Optional[str] = None,
    ) -> None:
        """
        Export a conversation to JSON format.

        Args:
            conversation_id: The conversation ID
            output_path: Path to output JSON file
            include_attachments: Download and include attachment files
            attachment_output_dir: Directory for attachments (default: same as output file)
        """
        from datetime import datetime
        import json as json_module

        convo = self.get_conversation(conversation_id)
        if not convo:
            raise ValueError(f"Conversation not found: {conversation_id}")

        messages = self.get_messages(conversation_id, limit=10000)

        export_data = {
            "conversation": {
                "id": convo.id,
                "name": convo.name,
                "type": convo.type,
                "exported_at": datetime.now().isoformat(),
            },
            "messages": [],
        }

        for msg in messages:
            msg_data = {
                "id": msg.id,
                "timestamp": msg.timestamp,
                "sent_at": msg.sent_at.isoformat(),
                "sender": msg.source,
                "direction": "outgoing" if msg.is_outgoing else "incoming",
                "body": msg.body,
                "has_attachments": len(msg.attachments) > 0,
                "attachments": [],
            }

            if include_attachments and msg.attachments:
                for att in msg.attachments:
                    att_path = att.get("path")
                    att_data = {
                        "filename": att.get("fileName"),
                        "size": att.get("size"),
                        "content_type": att.get("contentType"),
                    }

                    if att_path and attachment_output_dir:
                        try:
                            decrypted = self.decrypt_attachment(att_path)
                            base64_data = decrypted.hex()

                            att_data["data"] = base64_data

                            if attachment_output_dir:
                                att_dir = Path(attachment_output_dir)
                                att_dir.mkdir(parents=True, exist_ok=True)
                                safe_name = att.get("fileName") or "unnamed".replace(
                                    "/", "_"
                                )
                                out_path = att_dir / safe_name
                                with open(out_path, "wb") as f:
                                    f.write(decrypted)
                                att_data["saved_to"] = str(out_path)
                        except Exception as e:
                            att_data["error"] = str(e)

                    msg_data["attachments"].append(att_data)

            if msg.quote:
                msg_data["quote"] = msg.quote

            export_data["messages"].append(msg_data)

        with open(output_path, "w", encoding="utf-8") as f:
            json_module.dump(export_data, f, indent=2, ensure_ascii=False)

    def export_conversation_to_csv(
        self, conversation_id: str, output_path: str
    ) -> None:
        """
        Export a conversation to CSV format.

        Args:
            conversation_id: The conversation ID
            output_path: Path to output CSV file
        """
        import csv

        convo = self.get_conversation(conversation_id)
        if not convo:
            raise ValueError(f"Conversation not found: {conversation_id}")

        messages = self.get_messages(conversation_id, limit=10000)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Timestamp",
                    "Sender",
                    "Direction",
                    "Body",
                    "Has Attachments",
                    "Attachment Count",
                ]
            )

            for msg in reversed(messages):
                writer.writerow(
                    [
                        msg.sent_at.strftime("%Y-%m-%d %H:%M:%S"),
                        msg.source,
                        "outgoing" if msg.is_outgoing else "incoming",
                        msg.body or "",
                        "yes" if msg.attachments else "no",
                        len(msg.attachments),
                    ]
                )

    def export_conversation_to_html(
        self, conversation_id: str, output_path: str, include_attachments: bool = True
    ) -> None:
        """
        Export a conversation to HTML format with embedded images.

        Args:
            conversation_id: The conversation ID
            output_path: Path to output HTML file
            include_attachments: Embed images as base64
        """
        from datetime import datetime

        convo = self.get_conversation(conversation_id)
        if not convo:
            raise ValueError(f"Conversation not found: {conversation_id}")

        messages = self.get_messages(conversation_id, limit=10000)

        html_content = []
        html_content.append(
            """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>"""
            + f"{convo.name} - Session Export"
            + """</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f0f0f0;
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .message {
            display: flex;
            flex-direction: column;
            margin-bottom: 15px;
        }
        .message.outgoing {
            align-items: flex-end;
        }
        .message.incoming {
            align-items: flex-start;
        }
        .bubble {
            max-width: 70%;
            padding: 10px 15px;
            border-radius: 18px;
            position: relative;
        }
        .outgoing .bubble {
            background-color: #007aff;
            color: white;
            border-bottom-right-radius: 4px;
        }
        .incoming .bubble {
            background-color: white;
            color: #000;
            border-bottom-left-radius: 4px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        .sender {
            font-size: 12px;
            margin-bottom: 5px;
            opacity: 0.7;
        }
        .timestamp {
            font-size: 10px;
            opacity: 0.5;
            margin-top: 5px;
        }
        .attachment {
            margin-top: 10px;
        }
        .attachment img {
            max-width: 100%;
            border-radius: 8px;
            display: block;
        }
        .attachment-link {
            color: inherit;
            text-decoration: none;
            display: inline-block;
            background: rgba(0,0,0,0.1);
            padding: 8px 12px;
            border-radius: 8px;
            margin-top: 5px;
        }
        .quote {
            border-left: 3px solid rgba(0,0,0,0.2);
            padding: 8px 12px;
            margin-bottom: 10px;
            background: rgba(0,0,0,0.05);
            border-radius: 8px;
            font-size: 14px;
        }
        .quote-sender {
            font-size: 11px;
            color: rgba(0,0,0,0.5);
            margin-bottom: 4px;
            font-weight: 500;
        }
        .quote-text {
            color: rgba(0,0,0,0.7);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>"""
            + f"{convo.name}"
            + """</h1>
        <p>Conversation ID: """
            + f"{convo.id}"
            + """</p>
        <p>Exported on: """
            + f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            + """</p>
    </div>
    <div class="messages">
"""
        )

        for msg in reversed(messages):
            direction_class = "outgoing" if msg.is_outgoing else "incoming"
            sender = "You" if msg.is_outgoing else msg.source[:8]

            html_content.append(f"""
        <div class="message {direction_class}">
            <div class="sender">{sender}</div>
            <div class="bubble">""")

            if msg.quote:
                quote_sender = (
                    msg.quote.get("author") or msg.quote.get("sender") or "Unknown"
                )
                quote_text = self._escape_html(msg.quote.get("text", ""))
                html_content.append(f"""
                <div class="quote">
                    <div class="quote-sender">{quote_sender}</div>
                    <div class="quote-text">{quote_text}</div>
                </div>""")

            if msg.body:
                html_content.append(f"""
                <div>{self._escape_html(msg.body)}</div>""")

            if msg.attachments and include_attachments:
                for att in msg.attachments:
                    att_path = att.get("path")
                    att_name = att.get("fileName") or "attachment"
                    att_type = att.get("contentType") or ""

                    html_content.append(f"""
                <div class="attachment">""")

                    if att_type.startswith("image/") and att_path:
                        try:
                            decrypted = self.decrypt_attachment(att_path)
                            import base64 as base64_module

                            ext = att_type.split("/")[-1]
                            data_uri = f"data:{att_type};base64,{base64_module.b64encode(decrypted).decode()}"
                            html_content.append(f"""
                    <img src="{data_uri}" alt="{att_name}">""")
                        except Exception as e:
                            html_content.append(f"""
                    <span class="attachment-link">📎 {att_name} (failed to embed: {str(e)})</span>""")
                    else:
                        html_content.append(f"""
                    <span class="attachment-link">📎 {att_name}</span>""")

                    html_content.append("""
                </div>""")

            html_content.append(f"""
                <div class="timestamp">{msg.sent_at.strftime("%Y-%m-%d %H:%M:%S")}</div>
            </div>
        </div>""")

        html_content.append("""
    </div>
</body>
</html>
""")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("".join(html_content))

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        import html as html_module

        return html_module.escape(text)

    def export_all_conversations(
        self,
        output_dir: str,
        format: str = "json",
        include_attachments: bool = False,
        attachment_output_dir: Optional[str] = None,
    ) -> None:
        """
        Export all conversations to a directory.

        Args:
            output_dir: Directory to save exports
            format: Export format (json, csv, html)
            include_attachments: Download and include attachments
            attachment_output_dir: Directory for attachments (default: subdirectory)
        """
        from pathlib import Path

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if not attachment_output_dir:
            attachment_output_dir = str(output_path / "attachments")

        convos = self.get_conversations()

        for convo in convos:
            safe_name = self._sanitize_filename(convo.name)
            out_file = output_path / f"{safe_name}.{format}"

            try:
                if format == "json":
                    self.export_conversation_to_json(
                        convo.id,
                        str(out_file),
                        include_attachments=include_attachments,
                        attachment_output_dir=attachment_output_dir,
                    )
                elif format == "csv":
                    self.export_conversation_to_csv(convo.id, str(out_file))
                elif format == "html":
                    self.export_conversation_to_html(
                        convo.id, str(out_file), include_attachments=include_attachments
                    )
            except Exception as e:
                print(f"Failed to export {convo.name}: {e}")

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem."""
        import re

        sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)
        return sanitized[:200]  # Limit length

    # === Backup ===

    def create_backup(
        self,
        output_path: str,
        include_attachments: bool = True,
        backup_password: Optional[str] = None,
    ) -> dict:
        """
        Create a full backup of Session data.

        Args:
            output_path: Directory to create backup in
            include_attachments: Include encrypted attachments
            backup_password: Optional password to encrypt backup (None = no encryption)

        Returns:
            Dictionary with backup metadata
        """
        from pathlib import Path
        from datetime import datetime
        import shutil
        import hashlib
        import json as json_module

        backup_dir = Path(output_path)
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"session-backup-{timestamp}"
        backup_path = backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)

        try:
            db_path = backup_path / "db.sqlite"
            shutil.copy2(self.config.db_path, db_path)

            attachments_dir = backup_path / "attachments"
            if include_attachments and self.config.attachments_path.exists():
                shutil.copytree(
                    self.config.attachments_path, attachments_dir, dirs_exist_ok=True
                )

            our_id = self.get_our_pubkey()
            convos = self.get_conversations()

            metadata = {
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "session_id": our_id,
                "profile": self.config.profile or "production",
                "includes_attachments": include_attachments,
                "conversation_count": len(convos),
                "encrypted": backup_password is not None,
            }

            metadata_path = backup_path / "metadata.json"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json_module.dump(metadata, f, indent=2)

            checksum_path = backup_path / "checksum.txt"
            with open(checksum_path, "w", encoding="utf-8") as f:
                f.write(f"# Checksums created by session-cli\n")
                f.write(f"# Created: {metadata['created_at']}\n\n")

                if db_path.exists():
                    sha256 = self._hash_file(db_path)
                    f.write(f"{sha256}  db.sqlite\n")

                if include_attachments and attachments_dir.exists():
                    for att_file in attachments_dir.rglob("*"):
                        if att_file.is_file():
                            sha256 = self._hash_file(att_file)
                            rel_path = att_file.relative_to(backup_path)
                            f.write(f"{sha256}  {rel_path}\n")

                meta_sha256 = self._hash_file(metadata_path)
                f.write(f"{meta_sha256}  metadata.json\n")

            if backup_password:
                import zipfile
                import pyaes

                import tempfile
                import os

                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_path = Path(temp_dir) / f"{backup_name}.zip"

                    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                        for item in backup_path.rglob("*"):
                            if item.is_file():
                                zf.write(item, item.relative_to(backup_path))

                    with open(zip_path, "rb") as f:
                        data = f.read()

                    key = hashlib.sha256(backup_password.encode()).digest()
                    cipher = pyaes.AESModeOfOperationECB(key)

                    block_size = 16
                    padded_data = data + bytes(
                        block_size - (len(data) % block_size)
                        if len(data) % block_size != 0
                        else 0
                    )

                    encrypted = bytearray()
                    for i in range(0, len(padded_data), block_size):
                        block = padded_data[i : i + block_size]
                        encrypted_block = cipher.encrypt(block)
                        encrypted.extend(encrypted_block)

                    encrypted_path = backup_dir / f"{backup_name}.enc"
                    with open(encrypted_path, "wb") as f:
                        f.write(b"ENCRYPTED:\n")
                        f.write(encrypted)

                    shutil.rmtree(backup_path)

                    return {
                        **metadata,
                        "backup_path": str(encrypted_path),
                        "is_encrypted": True,
                    }

            return {**metadata, "backup_path": str(backup_path), "is_encrypted": False}

        except Exception as e:
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise RuntimeError(f"Backup failed: {e}") from e

    def create_incremental_backup(
        self, output_path: str, since_timestamp: int, include_attachments: bool = True
    ) -> dict:
        """
        Create an incremental backup with changes since timestamp.

        Args:
            output_path: Directory to create backup in
            since_timestamp: Unix timestamp in milliseconds
            include_attachments: Include new attachments

        Returns:
            Dictionary with backup metadata
        """
        from pathlib import Path
        from datetime import datetime
        import json as json_module

        backup_dir = Path(output_path)
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"session-incremental-{timestamp}"
        backup_path = backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)

        try:
            messages = self.get_new_messages(since_timestamp)

            new_attachment_paths = set()
            for msg in messages:
                for att in msg.attachments:
                    att_path = att.get("path")
                    if att_path:
                        new_attachment_paths.add(att_path)

            messages_path = backup_path / "messages.json"
            with open(messages_path, "w", encoding="utf-8") as f:
                json_module.dump([msg.raw for msg in messages], f, indent=2)

            attachments_dir = backup_path / "attachments"
            if include_attachments and new_attachment_paths:
                attachments_dir.mkdir(exist_ok=True)

                for att_path in new_attachment_paths:
                    src_path = self.config.get_attachment_path(att_path)
                    if src_path.exists():
                        rel_dir = str(attachments_dir / att_path[:2])
                        Path(rel_dir).mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_path, Path(rel_dir) / Path(att_path).name)

            metadata = {
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "since_timestamp": since_timestamp,
                "since_date": datetime.fromtimestamp(
                    since_timestamp / 1000
                ).isoformat(),
                "message_count": len(messages),
                "new_attachments": len(new_attachment_paths),
                "includes_attachments": include_attachments,
                "backup_type": "incremental",
            }

            metadata_path = backup_path / "metadata.json"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json_module.dump(metadata, f, indent=2)

            return {**metadata, "backup_path": str(backup_path)}

        except Exception as e:
            if backup_path.exists():
                import shutil

                shutil.rmtree(backup_path)
            raise RuntimeError(f"Incremental backup failed: {e}") from e

    def restore_from_backup(
        self, backup_path: str, backup_password: Optional[str] = None
    ) -> None:
        """
        Restore Session data from a backup.

        Args:
            backup_path: Path to backup directory or encrypted backup file
            backup_password: Password if backup is encrypted

        Warning: This will overwrite existing Session data. Make a backup first!
        """
        import shutil
        import zipfile
        import json as json_module
        from pathlib import Path

        backup = Path(backup_path)

        if not backup.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")

        print("WARNING: This will overwrite your existing Session data!")
        print(f"Target: {self.config.data_path}")
        response = input("Type 'yes' to continue: ")

        if response.lower() != "yes":
            print("Restore cancelled.")
            return

        temp_backup = None
        if self.config.data_path.exists():
            temp_backup = (
                self.config.data_path.parent
                / f"Session.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            shutil.move(str(self.config.data_path), str(temp_backup))
            print(f"Created safety backup: {temp_backup}")

        try:
            if backup.is_file() and backup.suffix == ".enc":
                import pyaes
                import hashlib

                print("Decrypting backup...")

                with open(backup, "rb") as f:
                    data = f.read()
                    if not data.startswith(b"ENCRYPTED:\n"):
                        raise ValueError("Invalid encrypted backup format")

                    encrypted = data[11:]

                    if not backup_password:
                        raise ValueError("Password required for encrypted backup")

                    key = hashlib.sha256(backup_password.encode()).digest()
                    cipher = pyaes.AESModeOfOperationECB(key)

                    decrypted = bytearray()
                    block_size = 16
                    for i in range(0, len(encrypted), block_size):
                        block = encrypted[i : i + block_size]
                        decrypted_block = cipher.decrypt(block)
                        decrypted.extend(decrypted_block)

                    decrypted = bytes(decrypted).rstrip(b"\x00")

                import tempfile

                with tempfile.NamedTemporaryFile(
                    suffix=".zip", delete=False
                ) as temp_zip:
                    temp_zip.write(decrypted)
                    temp_zip_path = Path(temp_zip.name)

                temp_extract = Path(tempfile.mkdtemp())
                with zipfile.ZipFile(temp_zip_path, "r") as zf:
                    zf.extractall(temp_extract)

                backup_path = temp_extract

            metadata_path = Path(backup_path) / "metadata.json"
            if not metadata_path.exists():
                raise FileNotFoundError("Invalid backup: metadata.json not found")

            with open(metadata_path) as f:
                metadata = json_module.load(f)

            print(f"Restoring backup from: {metadata['created_at']}")
            print(f"Session ID: {metadata.get('session_id', 'unknown')}")

            shutil.copy2(str(Path(backup_path) / "db.sqlite"), str(self.config.db_path))

            attachments_backup = Path(backup_path) / "attachments"
            if attachments_backup.exists():
                shutil.copytree(
                    attachments_backup,
                    str(self.config.attachments_path),
                    dirs_exist_ok=True,
                )

            print("Restore completed successfully!")
            if temp_backup:
                print(f"Safety backup saved to: {temp_backup}")

            print("\nPlease restart Session to load the restored data.")

        except Exception as e:
            print(f"Restore failed: {e}")
            if temp_backup and self.config.data_path.exists():
                shutil.rmtree(str(self.config.data_path))
                shutil.move(str(temp_backup), str(self.config.data_path))
                print("Rolled back to previous state.")
            raise

    def _hash_file(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        import hashlib

        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
