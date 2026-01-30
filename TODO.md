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
- [x] Add message export functionality (JSON, CSV, HTML) - COMPLETED
- [x] Add conversation export with messages - COMPLETED
- [ ] Add batch operations (mark all as read, delete messages)
- [ ] Add message reaction support
- [ ] Add group management via CDP
- [ ] Add attachment sending via CDP
- [ ] Add message editing support
- [ ] Add message deletion support
- [ ] Add contact management (add, remove, block)
- [ ] Add profile management via CLI
- [x] Backup and restore Session data (full and incremental) - COMPLETED
- [ ] Statistics and analytics dashboard
- [x] Enhanced search with filters (date range, sender, attachments) - COMPLETED
- [x] Message filtering by type (text, attachment, quote) - COMPLETED
- [ ] Configuration file support (`~/.session-cli/config.yaml`)
- [ ] Webhook integration for automation
- [ ] Auto-reply bot framework
- [ ] Interactive REPL mode
- [ ] Contact management via CDP
- [ ] Group management via CDP
- [ ] Message thread view
- [ ] Message templates
- [ ] Scheduled message sending

### CLI Improvements
- [ ] Add `--version` flag
- [ ] Add interactive mode (REPL)
- [ ] Add tab completion for commands
- [ ] Add color output (opt-in with `--color`)
- [ ] Add progress bars for long operations
- [ ] Add `--quiet` flag for automation
- [ ] Add fuzzy search for conversation IDs
- [x] Add `--format` option (table, json, csv) - COMPLETED (export formats)
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

### Resolved Bugs
- [x] DateTime import causing `'NoneType' object has no attribute 'replace'` in HTML export
- [x] Quote text null in database when exporting - fixed by fetching original message
- [x] NoneType errors when attachment fields exist but are None - fixed with proper parentheses
- [x] HTML quote styling was broken - improved CSS styling

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

### v1.1.0 (Export & Backup)
- [x] Export conversations to JSON format
- [x] Export conversations to CSV format
- [x] Export conversations to HTML format with embedded images
- [x] Export all conversations at once
- [x] Full backup with optional encryption
- [x] Incremental backup support
- [x] Restore from backup
- [x] Include attachments in exports
- [x] Added pyaes dependency for backup encryption

### Bug Fixes (v1.1.x)
- [x] Fixed DateTime import order error in HTML export
- [x] Fixed HTML quote styling for better readability
- [x] Fixed NoneType errors when attachment fields are None
- [x] Fixed quote text handling in JSON export - fetches original message by ID when null

### v1.2.0 (Enhanced Search & Filtering)
- [x] Added search_messages_enhanced() with advanced filtering
- [x] Date range filtering with relative date support (today, yesterday, 7d, 30d, etc.)
- [x] Filter by conversation ID or name
- [x] Filter by message type (text, attachment, quote, all)
- [x] Filter by sender (Session ID or name)
- [x] Filter unread messages only
- [x] Search without query text to apply filters only
- [x] Added find_conversation() helper for name/ID resolution
- [x] Added resolve_contact() helper for contact lookup
- [x] Added parse_date_filter() for date parsing

### v1.3.0 (Request Management)
- [x] Added Request dataclass for pending requests
- [x] Added get_pending_requests() database method
- [x] Added get_request() database method
- [x] Added accept_request() CDP method
- [x] Added decline_request() CDP method
- [x] Added block_request() CDP method
- [x] Added requests CLI command to list pending requests
- [x] Added accept-request CLI command
- [x] Added decline-request CLI command
- [x] Added block-request CLI command
- [x] Added filters to requests command (--type, --conversation-type, --unread)
- [x] Added grouping in requests output (by request type)
- [x] Added is_private and is_group properties to Request
- [!] **Known Issue**: CDP request management methods need investigation - API methods may have changed in newer Session versions. Listing requests works, but accept/decline/block may not work correctly.

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
