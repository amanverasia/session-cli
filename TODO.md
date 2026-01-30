# Session CLI - TODO

This document tracks planned features, improvements, and known issues.

## High Priority

- [ ] Rename package from `session_controller` to `session_cli`
- [ ] Add Windows platform support in `config.py`
- [ ] Implement comprehensive test suite
- [ ] Add CI/CD with GitHub Actions
- [ ] Publish to PyPI

## Medium Priority

### Testing
- [ ] Add unit tests for `config.py`
- [ ] Add unit tests for `database.py`
- [ ] Add unit tests for `cdp.py` (with mocked WebSocket)
- [ ] Add integration tests for CLI commands
- [ ] Add test fixtures for Session database (sample data)
- [ ] Test coverage to >80%

### Documentation
- [ ] Add API documentation (Sphinx or MkDocs)
- [ ] Add troubleshooting section to README
- [ ] Add video tutorials/gifs for common tasks
- [ ] Document database schema in detail
- [ ] Add Windows-specific setup instructions

### Features
- [ ] Implement `cdp.py:send_attachment()` method
- [ ] Add message export functionality (JSON, CSV, HTML)
- [ ] Add conversation export with messages
- [ ] Add batch operations (mark all as read, delete messages)
- [ ] Add message reaction support
- [ ] Add group management via CDP
- [ ] Add attachment sending via CDP
- [ ] Add message editing support
- [ ] Add message deletion support
- [ ] Add contact management (add, remove, block)
- [ ] Add profile management via CLI

### CLI Improvements
- [ ] Add `--version` flag
- [ ] Add interactive mode (REPL)
- [ ] Add tab completion for commands
- [ ] Add color output (opt-in with `--color`)
- [ ] Add progress bars for long operations
- [ ] Add `--quiet` flag for automation
- [ ] Add fuzzy search for conversation IDs
- [ ] Add `--format` option (table, json, csv)
- [ ] Add pagination for message listing

## Low Priority

### Enhancements
- [ ] Add configuration file support (`~/.session-cli/config.yaml`)
- [ ] Add aliases for common commands
- [ ] Add shell integration (bash/zsh/fish completion)
- [ ] Add Docker container for development
- [ ] Add web UI (optional feature)
- [ ] Add server mode (REST API wrapper)
- [ ] Add message forwarding between conversations
- [ ] Add auto-reply bot framework
- [ ] Add webhook integration (POST on new message)
- [ ] Add scheduled message sending
- [ ] Add message templates
- [ ] Add media preview in CLI
- [ ] Add message threading support

### Code Quality
- [ ] Add type hints throughout codebase
- [ ] Add mypy strict mode
- [ ] Refactor CLI to use `click` instead of `argparse`
- [ ] Add better error messages
- [ ] Add logging configuration
- [ ] Add performance benchmarks
- [ ] Add memory usage optimization
- [ ] Code duplication cleanup

### Internationalization
- [ ] Add multi-language support
- [ ] Add timezone handling
- [ ] Add locale-aware formatting

## Known Issues

### Bugs
- [ ] `launch_session.sh` needs Linux support
- [ ] Attachment decryption may fail with very large files
- [ ] CDP connection can timeout on slow networks
- [ ] Database polling in `watch` mode may miss rapid messages

### Limitations
- [ ] No Windows support (paths differ)
- [ ] CDP attachment sending not implemented
- [ ] Database is read-only (writes not supported)
- [ ] No multi-threading for concurrent operations
- [ ] Limited error recovery from database corruption

## Future Ideas (Not Prioritized)

### Advanced Features
- [ ] Message encryption/decryption outside of Session
- [ ] Backup and restore Session data
- [ ] Session account migration
- [ ] Multi-account management
- [ ] Message filtering by date range
- [ ] Attachment organization by type
- [ ] Statistics and analytics dashboard
- [ ] AI-powered message summarization
- [ ] Natural language message search

### Integrations
- [ ] Email gateway
- [ ] SMS gateway (via Session)
- [ ] Calendar integration
- [ ] Task manager integration
- [ ] Note-taking app integration
- [ ] IFTTT/Zapier webhook support

### Developer Tools
- [ ] VS Code extension
- [ ] Browser extension
- [ ] Desktop GUI wrapper (Electron/Tauri)
- [ ] Mobile companion app
- [ ] Plugin system for extensions

## Completed Tasks

### v1.0.0 (Initial Release)
- [x] Core database access (`SessionDatabase`)
- [x] CDP client (`SessionCDP`)
- [x] CLI with basic commands
- [x] Message listing and search
- [x] Conversation listing
- [x] Message sending via CDP
- [x] Real-time message watching
- [x] Attachment decryption
- [x] Media download
- [x] Session profile support
- [x] Python API
- [x] Basic documentation
- [x] Setup and packaging
- [x] MIT License

### Repository Setup
- [x] Create README.md
- [x] Add LICENSE (MIT)
- [x] Add .gitignore
- [x] Add setup.py
- [x] Add pyproject.toml
- [x] Add requirements.txt
- [x] Add CHANGELOG.md
- [x] Add CONTRIBUTING.md
- [x] Add AGENTS.md
- [x] Add usage examples
- [x] Clean up temporary files

## Backlog

Items to be prioritized later:

- [ ] Research Windows path handling
- [ ] Investigate SQLCipher 4.x compatibility
- [ ] Evaluate alternative to `sqlcipher3` (pure Python)
- [ ] Research WebSocket reconnection strategy
- [ ] Investigate attachment encryption variants
- [ ] Research Session protocol documentation
- [ ] Evaluate libsession_util_nodejs integration
- [ ] Investigate message deduplication in watch mode
- [ ] Research multi-platform GUI framework

## Contribution Wishlist

These are features we'd love help with:

1. **Windows Support**: Someone with Windows knowledge to implement platform-specific paths
2. **Test Suite**: Comprehensive test coverage for reliability
3. **Documentation**: Better user guides and API documentation
4. **Click CLI**: Migration from argparse to click for better UX
5. **Webhook Integration**: POST notifications on new messages
6. **Attachment Sending**: Implement file upload via CDP
7. **Performance**: Optimize large database queries
8. **Examples**: More real-world usage examples

---

Want to contribute? See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
