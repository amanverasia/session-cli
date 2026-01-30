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

    def __init__(self, config: Optional[SessionConfig] = None, password: Optional[str] = None):
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
            conversations.append(Conversation(
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
                }
            ))

        return conversations

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a specific conversation by ID."""
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT id, type, active_at, displayNameInProfile, nickname,
                   lastMessage, unreadCount
            FROM conversations WHERE id = ?
        """, (conversation_id,))
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
            }
        )

    # === Messages ===

    def get_messages(
        self,
        conversation_id: str,
        limit: int = 100,
        before_timestamp: Optional[int] = None
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
            cursor = conn.execute("""
                SELECT json FROM messages
                WHERE conversationId = ? AND sent_at < ?
                ORDER BY sent_at DESC
                LIMIT ?
            """, (conversation_id, before_timestamp, limit))
        else:
            cursor = conn.execute("""
                SELECT json FROM messages
                WHERE conversationId = ?
                ORDER BY sent_at DESC
                LIMIT ?
            """, (conversation_id, limit))

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
        cursor = conn.execute("""
            SELECT json FROM messages
            WHERE received_at > ?
            ORDER BY received_at ASC
        """, (since_timestamp,))

        return [self._parse_message(json.loads(row[0])) for row in cursor]

    def get_message_by_id(self, message_id: str) -> Optional[Message]:
        """Get a specific message by ID."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT json FROM messages WHERE id = ?",
            (message_id,)
        )
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
        cursor = conn.execute("""
            SELECT m.json FROM messages m
            WHERE m.rowid IN (
                SELECT rowid FROM messages_fts WHERE messages_fts MATCH ?
            )
            ORDER BY m.sent_at DESC
            LIMIT ?
        """, (query, limit))

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
            raw=data
        )

    # === Attachments ===

    def get_attachment_key(self) -> str:
        """Get the local attachment encryption key."""
        if self._attachment_key is None:
            # Try both possible key names
            key = self.get_setting('local_attachment_encrypted_key')
            if not key:
                key = self.get_setting('localAttachmentEncryptionKey')
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
            raise ImportError(
                "PyNaCl not installed. Install with: pip install pynacl"
            )

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
        nacl.bindings.crypto_secretstream_xchacha20poly1305_init_pull(state, header, key)

        # Decrypt
        plaintext, tag = nacl.bindings.crypto_secretstream_xchacha20poly1305_pull(state, ciphertext)

        return bytes(plaintext)

    # === Settings ===

    def get_setting(self, key: str) -> Any:
        """Get a setting value from the items table."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT json FROM items WHERE id = ?",
            (key,)
        )
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
        self,
        poll_interval: float = 1.0,
        conversation_id: Optional[str] = None
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
