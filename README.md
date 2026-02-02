# Session CLI

[![PyPI version](https://img.shields.io/pypi/v/session-cli.svg)](https://pypi.org/project/session-cli/)
[![Python versions](https://img.shields.io/pypi/pyversions/session-cli.svg)](https://pypi.org/project/session-cli/)
[![License](https://img.shields.io/pypi/l/session-cli.svg)](https://github.com/amanverasia/session-cli/blob/main/LICENSE)

A Python CLI tool and library for programmatic control of [Session Desktop](https://getsession.org/), the privacy-focused messenger.

## Features

- **Read-only database access** - Query messages, conversations, and attachments from Session's SQLCipher database
- **CDP control** - Send messages and manage groups via Chrome DevTools Protocol
- **MCP server** - Expose Session data to AI agents (Claude Desktop, Claude Code)
- **Full-text search** - Search messages with date, sender, and type filters
- **Export & backup** - Export to JSON/CSV/HTML, encrypted backups
- **Interactive REPL** - Persistent session with tab completion
- **Cross-platform** - macOS and Linux

## Installation

```bash
pip install session-cli
```

Requires **Python 3.10+** and **Session Desktop** (run at least once to create the database).

## Quick Start

```bash
# See all commands
session-cli -h

# List conversations
session-cli list

# View messages
session-cli messages <conversation_id>

# Search messages
session-cli search "keyword" --after 7d

# Interactive mode
session-cli repl
```

### Sending Messages (requires CDP)

Start Session with remote debugging:

```bash
# macOS
/Applications/Session.app/Contents/MacOS/Session --remote-debugging-port=9222 --remote-allow-origins="*"

# Linux
session-desktop --remote-debugging-port=9222 --remote-allow-origins="*"
```

Then send:

```bash
session-cli send <conversation_id> "Hello!"
```

## Python API

```python
from session_controller import SessionDatabase, SessionCDP

# Read messages (offline)
with SessionDatabase() as db:
    for convo in db.get_conversations():
        print(f"{convo.name}: {convo.last_message}")

    messages = db.get_messages(convo.id, limit=10)
    results = db.search_messages("keyword")

# Send messages (requires Session running with CDP)
with SessionCDP(port=9222) as cdp:
    cdp.send_message("05abc123...", "Hello!")
```

## MCP Server

Expose Session data to AI agents via [Model Context Protocol](https://modelcontextprotocol.io/).

```bash
session-mcp
```

### Claude Desktop / Claude Code

Add to your MCP config:

```json
{
  "mcpServers": {
    "session": {
      "command": "session-mcp"
    }
  }
}
```

Config locations:
- **Claude Desktop**: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `~/.config/Claude/claude_desktop_config.json` (Linux)
- **Claude Code**: `.claude/settings.json`

Once configured, ask Claude things like "List my Session conversations" or "Search my messages for 'meeting' from last week".

## Configuration

Save defaults in `~/.config/session-cli/config.yaml` (Linux) or `~/Library/Application Support/session-cli/config.yaml` (macOS):

```yaml
profile: null
port: 9222
json: false
commands:
  messages:
    limit: 50
```

## Data Locations

- **macOS**: `~/Library/Application Support/Session/`
- **Linux**: `~/.config/Session/`

## Limitations

- Database is read-only (prevents corruption)
- Sending messages/managing groups requires CDP
- Windows not supported yet

## License

[MIT](LICENSE)

## Links

- [Session Desktop](https://getsession.org/)
- [PyPI](https://pypi.org/project/session-cli/)
- [GitHub](https://github.com/amanverasia/session-cli)
