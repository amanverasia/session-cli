"""Tests for export and backup functionality."""

import pytest
import json
import csv
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO


class TestExport:
    """Test export methods."""

    @pytest.fixture
    def mock_db(self):
        with patch("session_controller.database.sqlite") as mock_sqlite:
            mock_conn = MagicMock()
            mock_sqlite.connect.return_value = mock_conn
            mock_conn.execute.return_value.fetchall.return_value = []

            from session_controller.database import SessionDatabase
            from session_controller.config import SessionConfig

            config = SessionConfig()
            db = SessionDatabase(config)
            db._conn = mock_conn

            yield db

    @patch("session_controller.database.SessionDatabase.get_conversation")
    @patch("session_controller.database.SessionDatabase.get_messages")
    @patch("builtins.open")
    def test_export_conversation_to_json(
        self, mock_open, mock_get_messages, mock_get_convo
    ):
        """Test exporting conversation to JSON."""
        from session_controller.database import Conversation, Message

        mock_convo = Conversation(
            id="05abc123",
            type="private",
            display_name="Test User",
            nickname=None,
            last_message="Hello",
            active_at=1640000000000,
            unread_count=0,
            raw={},
        )
        mock_get_convo.return_value = mock_convo

        mock_msg = Message(
            id="msg1",
            conversation_id="05abc123",
            source="05abc123",
            body="Test message",
            timestamp=1640000000000,
            received_at=1640000000000,
            type="outgoing",
            attachments=[],
            quote=None,
            raw={},
        )
        mock_get_messages.return_value = [mock_msg]

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        from session_controller.database import SessionDatabase
        from session_controller.config import SessionConfig

        config = SessionConfig()
        db = SessionDatabase(config)

        db.export_conversation_to_json("05abc123", "output.json")

        mock_open.assert_called_with("output.json", "w", encoding="utf-8")

        written = mock_file.write.call_args[0][0]
        data = json.loads(written)

        assert data["conversation"]["id"] == "05abc123"
        assert data["conversation"]["name"] == "Test User"
        assert len(data["messages"]) == 1
        assert data["messages"][0]["body"] == "Test message"

    @patch("session_controller.database.SessionDatabase.get_conversation")
    @patch("session_controller.database.SessionDatabase.get_messages")
    @patch("builtins.open")
    def test_export_conversation_to_csv(
        self, mock_open, mock_get_messages, mock_get_convo
    ):
        """Test exporting conversation to CSV."""
        from session_controller.database import Conversation, Message

        mock_convo = Conversation(
            id="05abc123",
            type="private",
            display_name="Test User",
            nickname=None,
            last_message="Hello",
            active_at=1640000000000,
            unread_count=0,
            raw={},
        )
        mock_get_convo.return_value = mock_convo

        mock_msg = Message(
            id="msg1",
            conversation_id="05abc123",
            source="05abc123",
            body="Test message",
            timestamp=1640000000000,
            received_at=1640000000000,
            type="outgoing",
            attachments=[],
            quote=None,
            raw={},
        )
        mock_get_messages.return_value = [mock_msg]

        mock_file = MagicMock()
        csv_output = StringIO()
        mock_open.return_value.__enter__.return_value = csv_output
        mock_open.return_value.__exit__.return_value = None

        from session_controller.database import SessionDatabase
        from session_controller.config import SessionConfig

        config = SessionConfig()
        db = SessionDatabase(config)

        db.export_conversation_to_csv("05abc123", "output.csv")

        reader = csv.reader(StringIO(csv_output.getvalue()))
        headers = next(reader)
        row = next(reader)

        assert "Timestamp" in headers
        assert "Sender" in headers
        assert "Direction" in headers
        assert "Body" in headers

    @patch("session_controller.database.SessionDatabase.get_conversations")
    @patch("session_controller.database.SessionDatabase.export_conversation_to_json")
    @patch("pathlib.Path.mkdir")
    def test_export_all_conversations(
        self, mock_mkdir, mock_export_json, mock_get_convos
    ):
        """Test exporting all conversations."""
        from session_controller.database import Conversation

        mock_convo = Conversation(
            id="05abc123",
            type="private",
            display_name="Test User",
            nickname=None,
            last_message="Hello",
            active_at=1640000000000,
            unread_count=0,
            raw={},
        )
        mock_get_convos.return_value = [mock_convo]

        from session_controller.database import SessionDatabase
        from session_controller.config import SessionConfig

        config = SessionConfig()
        db = SessionDatabase(config)

        db.export_all_conversations("./exports", format="json")

        mock_mkdir.assert_called_once()
        mock_export_json.assert_called_once()

    @patch("session_controller.database.SessionDatabase.get_conversation")
    @patch("session_controller.database.SessionDatabase.get_messages")
    @patch("builtins.open")
    def test_export_conversation_to_html(
        self, mock_open, mock_get_messages, mock_get_convo
    ):
        """Test exporting conversation to HTML."""
        from session_controller.database import Conversation, Message

        mock_convo = Conversation(
            id="05abc123",
            type="private",
            display_name="Test User",
            nickname=None,
            last_message="Hello",
            active_at=1640000000000,
            unread_count=0,
            raw={},
        )
        mock_get_convo.return_value = mock_convo

        mock_msg = Message(
            id="msg1",
            conversation_id="05abc123",
            source="05abc123",
            body="Test message",
            timestamp=1640000000000,
            received_at=1640000000000,
            type="outgoing",
            attachments=[],
            quote=None,
            raw={},
        )
        mock_get_messages.return_value = [mock_msg]

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        from session_controller.database import SessionDatabase
        from session_controller.config import SessionConfig

        config = SessionConfig()
        db = SessionDatabase(config)

        db.export_conversation_to_html("05abc123", "output.html")

        mock_open.assert_called_with("output.html", "w", encoding="utf-8")

        written = mock_file.write.call_args_list[0][0][0]
        assert "<!DOCTYPE html>" in written
        assert "Test User" in written
        assert "Test message" in written


class TestBackup:
    """Test backup methods."""

    @patch("session_controller.database.SessionDatabase._get_connection")
    @patch("shutil.copy2")
    @patch("pathlib.Path.exists")
    @patch("builtins.open")
    @patch("pathlib.Path.mkdir")
    def test_create_backup_no_password(
        self, mock_mkdir, mock_open, mock_exists, mock_copy, mock_conn
    ):
        """Test creating backup without password."""
        mock_exists.return_value = True
        mock_conn.return_value = MagicMock()

        from session_controller.database import SessionDatabase
        from session_controller.config import SessionConfig

        config = SessionConfig()
        db = SessionDatabase(config)
        db._conn = mock_conn.return_value

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        result = db.create_backup(
            "./backups", include_attachments=False, backup_password=None
        )

        assert result["is_encrypted"] is False
        assert result["includes_attachments"] is False

    @patch("session_controller.database.SessionDatabase._get_connection")
    @patch("shutil.copy2")
    @patch("shutil.copytree")
    @patch("shutil.rmtree")
    @patch("pathlib.Path.exists")
    @patch("builtins.open")
    @patch("pathlib.Path.mkdir")
    @patch("zipfile.ZipFile")
    @patch("pyaes.AESModeOfOperationECB")
    def test_create_backup_with_password(
        self,
        mock_aes,
        mock_zip,
        mock_mkdir,
        mock_open,
        mock_exists,
        mock_rmtree,
        mock_copytree,
        mock_copy,
        mock_conn,
    ):
        """Test creating encrypted backup."""
        mock_exists.return_value = True
        mock_conn.return_value = MagicMock()
        mock_conn.return_value.execute.return_value.fetchone.return_value = [
            mock_sqlite_row("05abc123")
        ]

        def mock_sqlite_row(val):
            row = MagicMock()
            row.__getitem__ = lambda self, key: val
            return row

        from session_controller.database import SessionDatabase
        from session_controller.config import SessionConfig

        config = SessionConfig()
        db = SessionDatabase(config)
        db._conn = mock_conn.return_value

        result = db.create_backup(
            "./backups", include_attachments=True, backup_password="test123"
        )

        assert result["is_encrypted"] is True

    @patch("session_controller.database.SessionDatabase.get_new_messages")
    @patch("shutil.copy2")
    @patch("pathlib.Path.exists")
    @patch("builtins.open")
    @patch("pathlib.Path.mkdir")
    def test_create_incremental_backup(
        self, mock_mkdir, mock_open, mock_exists, mock_copy, mock_new_msgs
    ):
        """Test creating incremental backup."""
        mock_exists.return_value = True
        from session_controller.database import Message

        mock_msg = Message(
            id="msg1",
            conversation_id="05abc123",
            source="05abc123",
            body="Test message",
            timestamp=1640000000000,
            received_at=1640000000000,
            type="outgoing",
            attachments=[],
            quote=None,
            raw={},
        )
        mock_new_msgs.return_value = [mock_msg]

        from session_controller.database import SessionDatabase
        from session_controller.config import SessionConfig

        config = SessionConfig()
        db = SessionDatabase(config)

        result = db.create_incremental_backup(
            "./backups", since_timestamp=1600000000000
        )

        assert result["backup_type"] == "incremental"
        assert result["message_count"] == 1
        assert result["new_attachments"] == 0

    @patch("builtins.input")
    @patch("shutil.move")
    @patch("shutil.copy2")
    @patch("pathlib.Path.exists")
    @patch("builtins.open")
    def test_restore_from_backup_encrypted(
        self, mock_open, mock_exists, mock_copy, mock_move, mock_input
    ):
        """Test restoring from encrypted backup."""
        mock_input.return_value = "yes"
        mock_exists.side_effect = [True, False]

        with open.__enter__.context as mock_ctx:
            mock_ctx.return_value.read.return_value = json.dumps(
                {
                    "version": "1.0.0",
                    "created_at": "2026-01-30T00:00:00",
                    "session_id": "05abc123",
                    "conversation_count": 10,
                }
            )

        from session_controller.database import SessionDatabase
        from session_controller.config import SessionConfig

        config = SessionConfig()
        db = SessionDatabase(config)

        with patch("zipfile.ZipFile"):
            db.restore_from_backup(
                "./backups/session-backup.enc", backup_password="test123"
            )
