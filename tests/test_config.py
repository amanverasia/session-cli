"""Unit tests for Session Controller config module."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from session_controller.config import SessionConfig


class TestSessionConfig:
    """Test SessionConfig class."""

    def test_default_initialization(self):
        """Test default initialization without profile."""
        config = SessionConfig()
        assert config.profile is None
        assert isinstance(config.data_path, Path)
        assert isinstance(config.db_path, Path)
        assert isinstance(config.attachments_path, Path)

    def test_custom_profile(self):
        """Test initialization with custom profile."""
        config = SessionConfig(profile="test_profile")
        assert config.profile == "test_profile"

    @patch("session_controller.config.Path.exists")
    def test_exists_method(self, mock_exists):
        """Test exists method."""
        mock_exists.return_value = True
        config = SessionConfig()
        assert config.exists() is True
        mock_exists.assert_called_once()

    @patch("session_controller.config.Path.exists")
    def test_has_password_method(self, mock_exists):
        """Test has_password method."""
        mock_exists.return_value = True

        with patch("builtins.open", MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = (
                '{"key": "test"}'
            )
            config = SessionConfig()
            assert config.has_password is True

    def test_get_attachment_path(self):
        """Test get_attachment_path method."""
        config = SessionConfig()
        attachment_path = config.get_attachment_path("ab/test.jpg")
        assert "ab" in str(attachment_path)
        assert "test.jpg" in str(attachment_path)
