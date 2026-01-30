# Changelog

All notable changes to the Session Controller project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2025-01-31

### Added
- Export conversations to JSON format with optional attachments
- Export conversations to CSV format
- Export conversations to HTML format with embedded base64 images and improved quote styling
- Export all conversations at once with batch operation
- Full backup functionality with optional AES-256 encryption (using pyaes)
- Incremental backup support to backup changes since timestamp
- Restore from backup with automatic rollback on failure
- Backup integrity verification with SHA256 checksums
- CLI commands: `export`, `export-all`, `backup`, `restore`

### Changed
- SessionDatabase now includes export and backup capabilities
- Enhanced HTML export with improved quote styling and readability
- Better handling of None values in attachment fields

### Fixed
- Fixed DateTime import order causing `'NoneType' object has no attribute 'replace'` in HTML export
- Fixed quote text being null in database exports - now fetches original message by ID
- Fixed NoneType errors when attachment fields exist but are None by adding proper parentheses
- Fixed HTML quote styling for better readability with background colors and borders

### Dependencies
- Added `pyaes>=1.6.0` for backup encryption

### Documentation
- Updated README.md with export and backup sections
- Added examples/export_conversation.py demonstrating export functionality
- Added examples/backup_session.py demonstrating backup/restore with encryption

## [1.0.0] - 2025-01-30

### Added
- Initial release of Session Controller
- Database mode for read-only access to Session's SQLCipher database
- CDP mode for full control when Session is running with remote debugging
- CLI tool with commands: list, messages, send, watch, search, media, info
- Full-text search across messages using FTS5
- Attachment decryption and download
- Real-time message watching with polling
- Support for multiple Session profiles
- Python API for programmatic access
- Comprehensive documentation and examples

### Features
- List conversations with metadata (name, type, last message, unread count)
- View messages from specific conversations
- Send text messages via CDP
- Watch for new messages in real-time
- Search messages by content
- Download and decrypt media attachments
- Display Session information
- JSON output option for all commands

### Platforms
- macOS support
- Linux support

### Dependencies
- sqlcipher3>=0.5.0
- pynacl>=1.5.0
- websocket-client>=1.0.0
