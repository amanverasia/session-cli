# Changelog

All notable changes to Session Controller project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.7.0] - 2026-02-02

### Added
- **MCP Write Tools**: CDP-based actions for AI agents
- New MCP tools requiring Session running with CDP:
  - `send_message` - Send text messages
  - `accept_request` - Accept pending requests
  - `decline_request` - Decline requests without blocking
  - `block_request` - Block and decline requests
  - `add_group_member` - Add member to group
  - `remove_group_member` - Remove member from group
  - `promote_to_admin` - Promote member to admin
  - `demote_admin` - Demote admin to member
  - `leave_group` - Leave a group
  - `mark_as_read` - Mark conversation as read
  - `export_conversation` - Export to JSON/CSV/HTML

### Documentation
- Streamlined README (removed verbose examples, use `session-cli -h`)

## [1.6.0] - 2026-02-02

### Added
- **MCP Server**: Model Context Protocol server for AI agent integration
- New `session_mcp` package exposing read-only Session data to AI agents
- `session-mcp` CLI command to run the MCP server
- Support for running as `python -m session_mcp`
- FastMCP-based server with stdio transport

### MCP Tools
- `list_conversations` - List all conversations with metadata
- `get_conversation` - Get details of a specific conversation
- `find_conversation` - Find conversation by name or partial ID
- `get_messages` - Get messages from a conversation with pagination
- `search_messages` - Search across messages with filters (date, conversation, sender)
- `get_message` - Get a specific message by ID
- `list_pending_requests` - List contact/message requests
- `get_request` - Get details of a specific request
- `get_stats` - Get messaging statistics
- `get_top_conversations` - Get most active conversations
- `get_activity` - Get activity breakdown by date
- `get_session_info` - Session ID, data path, status
- `list_profiles` - List available Session profiles

### Dependencies
- Added `fastmcp>=2.0.0` for MCP server implementation

### Documentation
- Added MCP Server section to README with configuration examples
- Updated CLAUDE.md with MCP module documentation
- Claude Desktop and Claude Code configuration examples

## [1.5.2] - 2026-02-02

### Documentation
- Added Linux instructions for launching Session with CDP in README Quick Start section
- Documented AppImage and system install methods for Linux users

## [1.5.1] - 2026-02-02

### Added
- Verified and documented Linux platform support (tested on Pop!_OS 22.04 LTS)
- Platform Support section in CLAUDE.md with explicit paths
- Linux CDP launch instructions for AppImage and system installations

### Documentation
- Updated CLAUDE.md with Linux-specific information
- Updated TODO.md to mark Linux support as completed
- Added Linux setup instructions for Session Desktop AppImage

## [1.5.0] - 2026-01-31

### Added
- Statistics command for messaging analytics
- `get_stats()` database method for overall statistics
- `get_top_conversations()` database method for most active conversations
- `get_activity_by_date()` database method for activity breakdown
- CLI `stats` command with filters: `--conversation`, `--period`, `--top`, `--activity`
- REPL `stats` command for interactive statistics

### Features
- Total messages count (sent/received breakdown)
- Messages with attachments count
- Conversation counts (private/group)
- Busiest hours and days of week
- Average messages per day
- Top N most active conversations
- Activity breakdown by day/week/month
- Filter by time period (7d, 30d, etc.)
- Filter by specific conversation

## [1.4.0] - 2026-01-31

### Added
- User configuration file support (`~/.config/session-cli/config.yaml` on Linux, `~/Library/Application Support/session-cli/config.yaml` on macOS)
- Interactive REPL mode with `session-cli repl` command
- Group management via CDP (add/remove members, promote/demote admins, leave group)
- `pyyaml>=6.0.0` dependency for configuration file parsing

### Features
- **User Config**: Save defaults for profile, port, JSON output, and per-command settings (limits, formats, intervals)
- **REPL Mode**: Persistent database connection, lazy CDP connection, tab completion for conversation IDs
- **REPL Commands**: list, messages, send, search, requests, accept, group, stats, info, json, refresh, quit
- **Group Management**: List members/admins, add members, remove members, promote to admin, demote admin, leave group

### CLI Usage Examples
```bash
# Interactive REPL
session-cli repl
session-cli interactive

# Group management
session-cli group members <group_id>
session-cli group add <group_id> <session_id>
session-cli group remove <group_id> <session_id>
session-cli group promote <group_id> <session_id>
session-cli group demote <group_id> <session_id>
session-cli group leave <group_id>
```

### Limitations
- Group creation not supported via CDP (use Session GUI)
- Group rename doesn't sync to network via CDP (use Session GUI)

## [1.3.0] - 2025-01-31

### Added
- Request management for contact and message requests
- Request dataclass with properties (is_contact_request, is_message_request, is_private, is_group)
- Database methods: `get_pending_requests()`, `get_request()`
- CDP methods: `accept_request()`, `decline_request()`, `block_request()`
- CLI commands: `requests`, `accept-request`, `decline-request`, `block-request`
- Filters for requests command: `--type`, `--conversation-type`, `--unread`
- Grouping option `--group` to organize requests by type
- Added AGENTS.md to .gitignore and removed from git tracking

### Features
- List all pending requests (contact and message requests)
- Accept pending requests via CLI
- Decline requests without blocking sender
- Block request sender and delete conversation
- Filter requests by type (message/contact/all)
- Filter requests by conversation type (private/group/all)
- Filter requests by unread status
- Group requests in output for better organization

### CLI Usage Examples
```bash
# List all pending requests
session-cli requests

# List only message requests
session-cli requests --type message

# List only private conversation requests
session-cli requests --conversation-type private

# List only unread requests
session-cli requests --unread

# Group requests by type
session-cli requests --group

# Combine filters
session-cli requests --type message --unread --group

# Accept a request
session-cli accept-request 05abc123...

# Decline a request
session-cli decline-request 05abc123...

# Block a request
session-cli block-request 05abc123...
```

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
