# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Session CLI is a Python CLI tool and library for programmatic control of Session Desktop (privacy-focused messenger). It operates in two modes:

1. **Database Mode**: Read-only direct access to Session's SQLCipher database (offline)
2. **CDP Mode**: Full control via Chrome DevTools Protocol (requires Session running with `--remote-debugging-port=9222 --remote-allow-origins="*"`)

## Build & Development Commands

```bash
# Install in development mode
pip install -e .
pip install -e ".[dev]"

# Run tests
pytest
pytest --cov=session_controller --cov-report=html
pytest tests/test_config.py  # single test file

# Code quality
black .                                    # format (line-length: 100)
flake8 session_controller                  # lint
mypy session_controller --ignore-missing-imports  # type check

# CLI usage
session-cli list                           # list conversations
session-cli messages <id> --limit 10       # view messages
session-cli search "keyword" --after 7d    # search with filters
session-cli export <id> --format json      # export conversation
session-cli backup --encrypt               # create encrypted backup
session-cli group members <id>             # list group members
session-cli group add <id> <session_id>    # add member to group
session-cli group promote <id> <session_id> # promote to admin
session-cli stats                          # messaging statistics
session-cli stats --top 10 --period 30d    # top conversations in 30 days
session-cli repl                           # interactive REPL mode
```

## Architecture

### Core Modules

- **config.py**: Platform-specific Session path detection (macOS: `~/Library/Application Support/Session/`, Linux: `~/.config/Session/`), profile management, encryption key extraction from config.json
- **database.py**: SQLCipher database access, message/conversation retrieval, full-text search, attachment decryption (PyNaCl), export (JSON/CSV/HTML), backup/restore (AES-256)
- **cdp.py**: WebSocket-based Chrome DevTools Protocol client, JavaScript evaluation in Session's renderer, message sending, request management, group management (add/remove members, promote/demote admins, create/rename groups)
- **cli.py**: argparse-based CLI with JSON output option for all commands, includes `group` subcommand with nested commands
- **repl.py**: Interactive REPL mode using Python's `cmd` module, persistent database connection, lazy CDP connection, tab completion
- **user_config.py**: User configuration file support (`~/.config/session-cli/config.yaml`), loads defaults for profile, port, command limits
- **constants.py**: Centralized SQL queries and configuration values
- **exceptions.py**: Custom exception hierarchy (`SessionError` base class)

### Design Patterns

Context managers for resource cleanup:
```python
with SessionDatabase(config) as db:
    conversations = db.get_conversations()

with SessionCDP(port=9222) as cdp:
    cdp.send_message(conversation_id, text)
```

Dataclasses (`Message`, `Conversation`, `Request`) with `raw` dict for JSON access.

### Adding Features

- **New CLI command**: Add subparser in `cli.py:main()`, implement `cmd_*` handler function
- **New database query**: Add SQL to `constants.py`, implement method in `SessionDatabase`
- **New CDP operation**: Add method to `SessionCDP` using `evaluate()` for JavaScript execution
- **New REPL command**: Add `do_<command>` method to `SessionREPL` in `repl.py`
- **New group operation**: Add CDP method in `cdp.py`, CLI handler in `cli.py`, REPL method in `repl.py`

## Code Conventions

- Python 3.10+, PEP 8, line length 100
- Import order: stdlib, third-party, local (use isort with black profile)
- Type hints encouraged, docstrings for public API
- Conventional commits: `type(scope): subject` (feat, fix, docs, refactor, test, chore)

## Known Limitations

- **macOS and Linux only** (Windows not implemented)
- **Database is read-only** to prevent corruption
- **CDP attachment sending** not implemented
- **Group creation/rename** not supported via CDP (use Session GUI)
- **Version sync**: Update version in `pyproject.toml`, `__init__.py`, and `constants.py`

## Session Desktop Integration

- Database: `sql/db.sqlite` (SQLCipher encrypted)
- Attachments: `attachments.noindex/` (encrypted, decrypted via PyNaCl)
- Key tables: `conversations`, `messages` (JSON column), `messages_fts` (full-text search)
- Group fields: `members` (JSON array), `groupAdmins` (JSON array), `type` ("group" or "groupv2")
- CDP globals: `window.getConversationController()`, `window.inboxStore`
- CDP group methods: `convo.addMembers()`, `convo.removeMembers()`, `convo.addAdmin()`, `convo.removeAdmin()`, `convo.leaveGroup()`
- Note: `createGroup()` and `setGroupName()` don't sync to network - use Session GUI instead
