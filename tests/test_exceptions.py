"""Unit tests for Session Controller exceptions module."""

import pytest
from session_controller.exceptions import (
    SessionError,
    DatabaseError,
    CDPError,
    ConfigurationError,
    AuthenticationError,
    FileNotFoundError,
    BackupError,
    ExportError,
)


class TestExceptions:
    """Test custom exceptions."""

    def test_session_error_base(self):
        """Test SessionError base exception."""
        with pytest.raises(SessionError):
            raise SessionError("Test error")

    def test_database_error_inheritance(self):
        """Test DatabaseError inherits from SessionError."""
        assert issubclass(DatabaseError, SessionError)
        with pytest.raises(SessionError):
            raise DatabaseError("Database error")

    def test_cdp_error_inheritance(self):
        """Test CDPError inherits from SessionError."""
        assert issubclass(CDPError, SessionError)
        with pytest.raises(SessionError):
            raise CDPError("CDP error")

    def test_configuration_error_inheritance(self):
        """Test ConfigurationError inherits from SessionError."""
        assert issubclass(ConfigurationError, SessionError)
        with pytest.raises(SessionError):
            raise ConfigurationError("Config error")

    def test_authentication_error_inheritance(self):
        """Test AuthenticationError inherits from SessionError."""
        assert issubclass(AuthenticationError, SessionError)
        with pytest.raises(SessionError):
            raise AuthenticationError("Auth error")

    def test_file_not_found_error_inheritance(self):
        """Test FileNotFoundError inherits from SessionError."""
        assert issubclass(FileNotFoundError, SessionError)
        with pytest.raises(SessionError):
            raise FileNotFoundError("File not found")

    def test_backup_error_inheritance(self):
        """Test BackupError inherits from SessionError."""
        assert issubclass(BackupError, SessionError)
        with pytest.raises(SessionError):
            raise BackupError("Backup error")

    def test_export_error_inheritance(self):
        """Test ExportError inherits from SessionError."""
        assert issubclass(ExportError, SessionError)
        with pytest.raises(SessionError):
            raise ExportError("Export error")

    def test_exception_messages(self):
        """Test exception messages are preserved."""
        msg = "Test message"
        try:
            raise SessionError(msg)
        except SessionError as e:
            assert str(e) == msg
