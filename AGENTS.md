# AGENTS.md - Claude Code Assistant Guidelines

This file contains guidelines for AI assistants working on the Session CLI project.

## Project Overview

Session CLI is a Python command-line tool and library for programmatic control of Session Desktop. It provides two modes of operation:

1. **Database Mode**: Read-only direct access to Session's SQLCipher database
2. **CDP Mode**: Full control via Chrome DevTools Protocol when Session is running

## Repository Structure

```
session-cli/
├── session_controller/          # Main package (to be renamed to session_cli)
│   ├── __init__.py
│   ├── cli.py                  # CLI implementation
│   ├── config.py               # Session configuration & path handling
│   ├── database.py             # SQLCipher database access
│   └── cdp.py                  # Chrome DevTools Protocol client
├── examples/                   # Usage examples
├── tests/                      # Test suite (to be added)
├── README.md                   # Main documentation
├── LICENSE                     # MIT License
├── setup.py                    # setuptools configuration
├── pyproject.toml             # Modern Python project config
├── requirements.txt           # Core dependencies
├── AGENTS.md                  # This file
└── TODO.md                    # Task list
```

## Code Conventions

### Python Style
- Follow PEP 8
- Use 4 spaces for indentation
- Line length: 100 characters (configured in pyproject.toml)
- Type hints are encouraged but not required
- Add docstrings to all public functions and classes

### Import Order
```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
import sqlcipher3
import nacl.bindings

# Local
from .config import SessionConfig
```

### Naming
- Classes: `PascalCase`
- Functions/Variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`

## Testing

### Running Tests
```bash
pytest
pytest --cov=session_controller --cov-report=html
pytest tests/test_database.py
```

### Test Structure
```
tests/
├── __init__.py
├── conftest.py                # Shared fixtures
├── test_config.py            # Configuration tests
├── test_database.py           # Database access tests
├── test_cdp.py               # CDP client tests
└── test_cli.py               # CLI command tests
```

### Testing Guidelines
- Use `pytest` as the test framework
- Mock external dependencies (CDP, filesystem, database)
- Use fixtures for shared test data
- Test both success and error cases
- Aim for >80% code coverage

## Build & Development

### Installation
```bash
pip install -e .
pip install -e ".[dev]"
```

### Code Quality
```bash
# Format code
black .

# Check style
flake8 session_controller

# Type checking
mypy session_controller
```

### Common Commands
```bash
# Run CLI
session-cli list
session-cli messages <id>
session-cli send <id> "message"

# Run test connection
python test_connection.py

# Run examples
python examples/basic_usage.py
python examples/message_watcher.py
```

## Known Issues & Limitations

### Current Limitations
- **Platform support**: macOS and Linux only (Windows not implemented)
- **CDP attachment sending**: Not implemented yet (see `cdp.py:send_attachment`)
- **Database writes**: Read-only access to prevent data corruption
- **Multi-platform paths**: Need to verify Windows path handling

### Common Pitfalls

1. **CDP Connection Issues**
   - Session must be running with `--remote-debugging-port=9222`
   - Check firewall settings if connection fails
   - Verify Session is actually listening on the port

2. **Database Access Issues**
   - Ensure Session has been run at least once
   - Check if database password is set (user-set vs auto-generated)
   - Verify sqlcipher3 is properly installed

3. **Path Issues**
   - Paths differ between macOS and Linux
   - Profile naming affects data directory location
   - Attachment paths include subdirectory (e.g., `ab/cd/filename`)

## Adding New Features

### Database Features
1. Add method to `SessionDatabase` class in `database.py`
2. Write docstring with example
3. Add CLI command in `cli.py` if needed
4. Write unit tests in `tests/test_database.py`
5. Update README.md if user-facing

### CDP Features
1. Add method to `SessionCDP` class in `cdp.py`
2. Use `evaluate()` method to execute JavaScript
3. Handle errors and return values appropriately
4. Write unit tests (mock WebSocket)
5. Update README.md if user-facing

### CLI Commands
1. Add subparser in `cli.py:main()`
2. Implement handler function
3. Add help text and examples
4. Update README.md command list
5. Add integration tests

## Architecture

### SessionConfig (`config.py`)
- Handles Session data paths (platform-specific)
- Loads `config.json` for database encryption key
- Manages profile switching
- No external dependencies

### SessionDatabase (`database.py`)
- Direct SQLCipher database access
- Context manager for connection handling
- Decrypts attachments using PyNaCl
- Provides generators for streaming results
- Dependencies: `sqlcipher3`, `pynacl`

### SessionCDP (`cdp.py`)
- Chrome DevTools Protocol via WebSocket
- Executes JavaScript in renderer context
- Manages connection lifecycle
- Dependencies: `websocket-client`

### CLI (`cli.py`)
- Argument parsing with `argparse`
- JSON output option for all commands
- Error handling and user feedback
- Orchestrates Database/CDP usage

## Dependencies

### Core
- `sqlcipher3>=0.5.0` - SQLCipher database access
- `pynacl>=1.5.0` - Attachment decryption (libsodium)
- `websocket-client>=1.0.0` - CDP WebSocket client

### Development
- `pytest>=7.0.0` - Testing framework
- `pytest-cov>=4.0.0` - Coverage reports
- `black>=23.0.0` - Code formatting
- `flake8>=6.0.0` - Linting
- `mypy>=1.0.0` - Type checking

## Session Desktop Integration

### Data Storage
- **macOS**: `~/Library/Application Support/Session/`
- **Linux**: `~/.config/Session/`
- **Database**: `sql/db.sqlite` (SQLCipher encrypted)
- **Attachments**: `attachments.noindex/` (encrypted files)

### Database Schema (Key Tables)
- `conversations` - Chat conversations
- `messages` - Messages (JSON in `json` column)
- `items` - Key-value settings
- `messages_fts` - Full-text search index

### CDP API (Window globals)
- `window.getConversationController()` - Conversation management
- `window.inboxStore` - Redux store
- `window.getSettingValue(key)` - Settings access
- `window.clipboard` - Electron clipboard

## Debugging

### Enable Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Database Debugging
```bash
# Open database manually
sqlite3 ~/Library/Application Support/Session/sql/db.sqlite

# Check key
cat ~/Library/Application Support/Session/config.json | grep key
```

### CDP Debugging
```bash
# Test WebSocket connection
wscat -c ws://localhost:9222/devtools/page/...
```

## Release Process

1. Update version in `setup.py` and `pyproject.toml`
2. Update `CHANGELOG.md`
3. Tag release: `git tag v1.0.0`
4. Push: `git push origin v1.0.0`
5. Create GitHub release
6. Optionally publish to PyPI

## Resources

- **Session Desktop**: https://getsession.org/
- **Session Protocol**: https://docs.session.org/
- **SQLCipher**: https://www.zetetic.net/sqlcipher/
- **CDP Protocol**: https://chromedevtools.github.io/devtools-protocol/
- **Python Packaging**: https://packaging.python.org/

## Contact & Support

- GitHub Issues: https://github.com/amanverasia/session-cli/issues
- Documentation: See README.md
- Examples: See `examples/` directory
