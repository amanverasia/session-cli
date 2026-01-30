"""Custom exceptions for Session Controller."""


class SessionError(Exception):
    """Base exception for Session Controller errors."""

    pass


class DatabaseError(SessionError):
    """Exception raised for database-related errors."""

    pass


class CDPError(SessionError):
    """Exception raised for CDP-related errors."""

    pass


class ConfigurationError(SessionError):
    """Exception raised for configuration errors."""

    pass


class AuthenticationError(SessionError):
    """Exception raised for authentication/encryption errors."""

    pass


class FileNotFoundError(SessionError):
    """Exception raised when required files are not found."""

    pass


class BackupError(SessionError):
    """Exception raised for backup/restore errors."""

    pass


class ExportError(SessionError):
    """Exception raised for export errors."""

    pass
