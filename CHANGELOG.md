# Changelog

All notable changes to the Session Controller project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2025-01-31

### Added
- Enhanced search with advanced filtering options
- Date range filtering (after/before) with relative date support (today, yesterday, 7d, 30d, etc.)
- Filter by conversation ID or name
- Filter by message type (text, attachment, quote, all)
- Filter by sender (Session ID or name)
- Filter unread messages only
- Search without query text to apply filters only
- Helper methods: `find_conversation()` and `resolve_contact()` for name/ID resolution
- Date parsing utility supporting multiple formats (ISO, relative, Unix timestamp)

### Changed
- Search command now supports optional query text (can be omitted to filter only)
- Improved search result display showing message type indicators

### Features
- Search messages from specific conversations
- Search by date range (e.g., "messages from last 7 days")
- Find all attachments or quotes
- Find messages from specific senders
- Find unread messages across all conversations

### CLI Usage Examples
```bash
# Basic search (unchanged)
session-cli search "keyword"

# Date range filtering
session-cli search --after 7d
session-cli search "meeting" --after yesterday --before today
session-cli search --after "2025-01-01" --before "2025-01-31"

# Filter by conversation
session-cli search --conversation "John Doe"
session-cli search "important" --conversation "Work Group"

# Filter by message type
session-cli search --type attachment
session-cli search --type quote
session-cli search "report" --type text

# Filter by sender
session-cli search --sender "Alice"

# Unread messages only
session-cli search --unread-only

# Combine filters
session-cli search "project" --after 30d --conversation "Team Chat" --type text --limit 50
```

## [1.1.0] - 2025-01-30

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
