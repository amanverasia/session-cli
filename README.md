# Session Controller

A Python CLI tool and library for programmatic control of [Session Desktop](https://getsession.org/), the privacy-focused messaging application.

## Features

- **Database Access**: Read messages, conversations, and attachments directly from Session's SQLCipher database
- **CDP Control**: Send messages and control Session via Chrome DevTools Protocol
- **Group Management**: Create groups, add/remove members, promote/demote admins
- **Real-time Monitoring**: Watch for new messages in real-time
- **Full-text Search**: Search across all messages using FTS5
- **Attachment Support**: Decrypt and download encrypted attachments
- **Interactive REPL**: Persistent session with tab completion
- **User Config**: Save defaults in `~/.config/session-cli/config.yaml`
- **Cross-platform**: Works on macOS and Linux

## Installation

```bash
pip install git+https://github.com/amanverasia/session-cli.git
```

This installs both the `session-cli` command and the `session_controller` Python library. All dependencies (sqlcipher3, PyNaCl, websocket-client) are installed automatically.

### Prerequisites

- **Python 3.10+**
- **Session Desktop** must be installed and run at least once (to create the database)

## Quick Start

### Check Version

```bash
session-cli --version
```

### List Conversations

```bash
session-cli list
```

### View Messages

```bash
session-cli messages 05abc123...
session-cli messages "friend name" --limit 10
```

### Send a Message

First, start Session with remote debugging enabled:

```bash
/Applications/Session.app/Contents/MacOS/Session --remote-debugging-port=9222 --remote-allow-origins="*"
```

Then send a message:

```bash
session-cli send 05abc123... "Hello from CLI!"
```

### Watch for New Messages

```bash
session-cli watch
session-cli watch --convo 05abc123... --save-media
```

### Search Messages

Basic search:
```bash
session-cli search "keyword"
```

Search with date filters:
```bash
# Messages from last 7 days
session-cli search --after 7d

# Messages between yesterday and today
session-cli search "meeting" --after yesterday --before today

# Messages in January 2025
session-cli search --after "2025-01-01" --before "2025-01-31"
```

Search by conversation:
```bash
# Search in specific conversation
session-cli search --conversation "John Doe"
session-cli search "important" --conversation "Work Group"
```

Filter by message type:
```bash
# Find all attachments
session-cli search --type attachment

# Find all quoted messages
session-cli search --type quote

# Text messages only
session-cli search "report" --type text
```

Filter by sender:
```bash
session-cli search --sender "Alice"
session-cli search "project" --sender "Bob"
```

Unread messages only:
```bash
session-cli search --unread-only
```

Combine multiple filters:
```bash
session-cli search "project" --after 30d --conversation "Team Chat" --type text --limit 50
```

### Group Management

List group members and admins:

```bash
session-cli group members <group_id>
```

Add a member to a group (requires admin):

```bash
session-cli group add <group_id> <session_id>
```

Remove a member from a group (requires admin):

```bash
session-cli group remove <group_id> <session_id>
```

Promote a member to admin:

```bash
session-cli group promote <group_id> <session_id>
```

Demote an admin to regular member:

```bash
session-cli group demote <group_id> <session_id>
```

Leave a group:

```bash
session-cli group leave <group_id>
session-cli group leave <group_id> --yes  # Skip confirmation
```

Rename a group (requires admin):

```bash
session-cli group rename <group_id> "New Group Name"
```

### Manage Requests

List pending requests:

```bash
# Show all pending requests
session-cli requests

# Show only message requests
session-cli requests --type message

# Show only contact requests
session-cli requests --type contact

# Filter by conversation type
session-cli requests --conversation-type private
session-cli requests --conversation-type group

# Show only unread requests
session-cli requests --unread

# Group requests by type for better organization
session-cli requests --group

# Combine filters
session-cli requests --type message --unread --group
```

Accept a request:

```bash
session-cli accept-request 05abc123...
```

Decline a request:

```bash
session-cli decline-request 05abc123...
```

Block a request:

```bash
session-cli block-request 05abc123...
```

### Download Media

```bash
session-cli media 05abc123... --output ./downloads
```

### Export Conversations

Export a single conversation to JSON:

```bash
session-cli export 05abc123... --format json --output convo.json
```

Export to CSV format:

```bash
session-cli export 05abc123... --format csv --output convo.csv
```

Export to HTML (with embedded images):

```bash
session-cli export 05abc123... --format html --output convo.html --include-attachments
```

Export all conversations at once:

```bash
session-cli export-all --format json --output ./exports
session-cli export-all --format html --output ./exports --include-attachments
```

### Backup and Restore

Create a full backup (unencrypted):

```bash
session-cli backup --output ./backups/session-backup
```

Create an encrypted backup:

```bash
session-cli backup --output ./backups/session-backup --encrypt
# Will prompt for password
```

Create backup with attachments:

```bash
session-cli backup --output ./backups/session-backup --include-attachments
```

Restore from backup:

```bash
session-cli restore ./backups/session-backup-20260130_123456
session-cli restore ./backups/session-backup-20260130.enc --password mypassword
```

**Backup Format:**
```
session-backup-20260130_123456/
├── db.sqlite                 # Session database
├── attachments/              # Encrypted attachments (optional)
├── metadata.json             # Backup information
└── checksum.txt              # File integrity checksums
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `--version`, `-v` | Show package version |
| `list` | List all conversations |
| `messages <id>` | Show messages from a conversation |
| `send <id> <msg>` | Send a message (requires CDP) |
| `watch` | Watch for new messages |
| `search <query>` | Search messages with filters (--after, --before, --conversation, --type, --sender, --unread-only) |
| `media <id>` | Download media from conversation |
| `export <id>` | Export a conversation to file |
| `export-all` | Export all conversations to directory |
| `backup` | Create a full backup of Session data |
| `restore` | Restore from backup |
| `requests` | List pending requests (optional: --type, --conversation-type, --unread, --group) |
| `accept-request <id>` | Accept a pending request (requires CDP) |
| `decline-request <id>` | Decline a pending request (requires CDP) |
| `block-request <id>` | Block and decline a request (requires CDP) |
| `group members <id>` | List group members and admins (requires CDP) |
| `group add <id> <sid>` | Add member to group (requires CDP) |
| `group remove <id> <sid>` | Remove member from group (requires CDP) |
| `group promote <id> <sid>` | Promote member to admin (requires CDP) |
| `group demote <id> <sid>` | Demote admin to member (requires CDP) |
| `group leave <id>` | Leave a group (requires CDP) |
| `group rename <id> <name>` | Rename a group (requires CDP) |
| `repl` | Start interactive REPL mode |
| `info` | Show Session information |

## Python API

Installing Session CLI also gives you the `session_controller` Python package for programmatic access. The library provides two modes of operation:

- **Database Mode**: Direct read-only access to Session's SQLCipher database (works offline)
- **CDP Mode**: Full control via Chrome DevTools Protocol (requires Session running with `--remote-debugging-port=9222`)

### Database Mode (Read-Only)

```python
from session_controller import SessionDatabase, SessionConfig

# Read messages (Session doesn't need to be running)
with SessionDatabase() as db:
    # List conversations
    for convo in db.get_conversations():
        print(f"{convo.name}: {convo.last_message}")

    # Get messages
    messages = db.get_messages(convo.id, limit=10)

    # Basic search
    results = db.search_messages("keyword")

    # Enhanced search with filters
    results = db.search_messages_enhanced(
        query="project",
        conversation_id=convo.id,
        after_timestamp=db.parse_date_filter("7d"),
        message_type="text",
        limit=50
    )

    # Find conversation by name or ID
    convo = db.find_conversation("John Doe")

    # Resolve contact name to Session ID
    session_id = db.resolve_contact("Alice")

    # Manage requests
    requests = db.get_pending_requests()
    for req in requests:
        print(f"{req.name}: {req.type}")
        if req.is_message_request:
            print("  Message request")
        if req.is_contact_request:
            print("  Contact request")

    # Get specific request
    request = db.get_request("05abc123...")
    if request:
        print(f"Found request: {request.name}")

    # Decrypt attachment
    decrypted = db.decrypt_attachment("ab/cd/abcd1234...")

    # Export conversation to JSON
    db.export_conversation_to_json(convo.id, "convo.json")

    # Export to HTML with embedded images
    db.export_conversation_to_html(convo.id, "convo.html", include_attachments=True)

    # Export all conversations
    db.export_all_conversations("./exports", format="html")

    # Create backup
    db.create_backup("./backups", include_attachments=True)

    # Create encrypted backup
    db.create_backup("./backups", include_attachments=True, backup_password="secret")

    # Create incremental backup
    db.create_incremental_backup("./backups", since_timestamp=1640000000000)

    # Restore from backup
    db.restore_from_backup("./backups/session-backup-20260130")
```

### CDP Mode (Full Control)

```python
from session_controller import SessionCDP

# Connect to running Session (must have --remote-debugging-port=9222)
with SessionCDP(port=9222) as cdp:
    # Get conversations
    convos = cdp.get_conversations()

    # Send message
    cdp.send_message("05abc123...", "Hello!")

    # Mark as read
    cdp.mark_conversation_read("05abc123...")

    # Manage requests
    cdp.accept_request("05abc123...")
    cdp.decline_request("05abc123...")
    cdp.block_request("05abc123...")

    # Group management
    members = cdp.get_group_members("group_id")  # Get members and admins
    cdp.add_group_member("group_id", "05abc...")  # Add member
    cdp.remove_group_member("group_id", "05abc...")  # Remove member
    cdp.promote_to_admin("group_id", "05abc...")  # Promote to admin
    cdp.demote_admin("group_id", "05abc...")  # Demote admin
    cdp.leave_group("group_id")  # Leave group
    cdp.rename_group("group_id", "New Name")  # Rename group
    # Note: Group creation is not supported via CDP (use Session GUI)

    # Get Redux state
    state = cdp.get_redux_state()
```

## Interactive REPL Mode

Start an interactive session with persistent database connection:

```bash
session-cli repl
# or
session-cli interactive
```

Available REPL commands:
```
session> list              # List conversations
session> messages <id> 20  # Show 20 messages
session> send <id> Hello!  # Send message (connects CDP)
session> search keyword    # Search messages
session> requests          # Show pending requests
session> accept <id>       # Accept request
session> group members <id>    # List group members
session> group add <id> <sid>  # Add member to group
session> info              # Show session info
session> json on           # Toggle JSON output
session> quit              # Exit
```

## User Configuration

Save your defaults in a config file:

**macOS**: `~/Library/Application Support/session-cli/config.yaml`
**Linux**: `~/.config/session-cli/config.yaml`

```yaml
# Example config
profile: null
port: 9222
json: false

commands:
  messages:
    limit: 50
  search:
    limit: 30
  watch:
    interval: 2.0
    media_dir: ./media
  export:
    format: json
```

Priority order: CLI args > config file > defaults

## Session Profiles

Work with multiple Session instances:

```bash
# Use development profile
session-cli --profile development list

# Use custom profile
session-cli --profile devprod1 send 05abc... "Hello"
```

## CDP Setup

To use CDP features (sending messages), Session must be started with remote debugging enabled. The `--remote-allow-origins="*"` flag is required for WebSocket connections.

### macOS
```bash
/Applications/Session.app/Contents/MacOS/Session --remote-debugging-port=9222 --remote-allow-origins="*"
```

### Linux
```bash
session-desktop --remote-debugging-port=9222 --remote-allow-origins="*"
```

### Start in Background (with tray)
```bash
/Applications/Session.app/Contents/MacOS/Session --remote-debugging-port=9222 --remote-allow-origins="*" --start-in-tray
```

## Database Access

Session stores data in:

- **macOS**: `~/Library/Application Support/Session/`
- **Linux**: `~/.config/Session/`

The database uses SQLCipher encryption. The tool automatically:
- Reads the encryption key from `config.json`
- Handles both auto-generated keys and user passwords
- Decrypts attachments using libsodium secretstream

## Examples

See the `examples/` directory for more usage examples:

```bash
python examples/verify_setup.py      # Verify your setup is working
python examples/basic_usage.py       # Basic database access
python examples/message_watcher.py   # Real-time message monitoring
```

## Data Storage

```
Session/
├── config.json              # DB encryption key
├── ephemeral.json           # Temporary settings
├── sql/
│   └── db.sqlite            # SQLCipher database
└── attachments.noindex/     # Encrypted attachments
```

## Limitations

- **Sending messages**: Requires Session running with CDP enabled
- **Database writes**: Read-only access prevents data corruption
- **Attachment uploads**: Use Session GUI for sending attachments
- **Group creation**: Not available via CDP, use Session GUI
- **Windows**: Not currently supported (macOS/Linux only)

## Security

- The database encryption key is stored in `config.json`
- Attachments are encrypted with separate keys
- CDP connections require explicit enabling
- No credentials or keys are transmitted externally

## Troubleshooting

### "Cannot connect to Session CDP"
Make sure Session is running with:
```bash
/Applications/Session.app/Contents/MacOS/Session --remote-debugging-port=9222
```

### "Database not found"
Ensure Session has been run at least once:
```bash
session-cli info
```

### "sqlcipher3 not installed"
```bash
pip install sqlcipher3
```

## Development

```bash
# Clone repository
git clone https://github.com/amanverasia/session-cli.git
cd session-cli

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
```

## License

[MIT License](LICENSE) - see LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Disclaimer

This tool is for educational and personal use. Respect user privacy and only use on your own Session instances.

## Related

- [Session Desktop](https://getsession.org/) - Privacy-focused messaging app
- [Session Protocol](https://docs.session.org/) - Technical documentation

## Credits

Built for the Session community. Not officially affiliated with Session or the Session Foundation.
