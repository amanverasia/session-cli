# Session Controller

A Python CLI tool and library for programmatic control of [Session Desktop](https://getsession.org/), the privacy-focused messaging application.

## Features

- **Database Access**: Read messages, conversations, and attachments directly from Session's SQLCipher database
- **CDP Control**: Send messages and control Session via Chrome DevTools Protocol
- **Real-time Monitoring**: Watch for new messages in real-time
- **Full-text Search**: Search across all messages using FTS5
- **Attachment Support**: Decrypt and download encrypted attachments
- **Cross-platform**: Works on macOS and Linux

## Installation

### From GitHub

```bash
git clone https://github.com/amanverasia/session-cli.git
cd session-cli
pip install -e .
```

Or install directly with pip:

```bash
pip install git+https://github.com/amanverasia/session-cli.git
```

### Requirements

- Python 3.10 or higher
- Session Desktop installed
- [sqlcipher3](https://github.com/coleifer/sqlcipher3-python)
- [PyNaCl](https://pynacl.readthedocs.io/)
- [websocket-client](https://github.com/websocket-client/websocket-client)

## Quick Start

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
/Applications/Session.app/Contents/MacOS/Session --remote-debugging-port=9222
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
| `info` | Show Session information |

## Python API

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
    
    # Get Redux state
    state = cdp.get_redux_state()
```

## Session Profiles

Work with multiple Session instances:

```bash
# Use development profile
session-cli --profile development list

# Use custom profile
session-cli --profile devprod1 send 05abc... "Hello"
```

## CDP Setup

To use CDP features (sending messages), Session must be started with remote debugging:

### macOS
```bash
/Applications/Session.app/Contents/MacOS/Session --remote-debugging-port=9222
```

### Linux
```bash
session-desktop --remote-debugging-port=9222
```

### Start in Background (with tray)
```bash
/Applications/Session.app/Contents/MacOS/Session --remote-debugging-port=9222 --start-in-tray
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
python examples/basic_usage.py
python examples/message_watcher.py
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
