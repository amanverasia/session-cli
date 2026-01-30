# Changelog

All notable changes to the Session Controller project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

## [1.0.0] - 2025-01-30

### Added
- Initial public release
