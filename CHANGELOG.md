# Changelog

All notable changes to Vantage Mail will be documented in this file.

## [1.0.0] - 2026-05-26

### Added
- **Full-Text Search Indexing**: Implemented high-performance SQLite FTS5 matching query engine with query token sanitization and sequential fallback support.
- **Modeless Multi-Window Support**: Double-clicking an email launches independent read-only viewer windows or rich drafts composers with taskbar integration.
- **Auto-Save Drafts**: Interactive composers feature auto-saving drafts to local SQLite database with 5-second interval timer.
- **SMTP & Progressive Loading**: Support progressive cached item loading, increased connection timeouts, and SMTP handshake cleanup.
- **Auto-Mark-As-Read**: Selected unread messages automatically update to read state after a 3-second selection delay.
- **Rich Text Formatting Toolbar**: Built advanced rich text formatting controls for message composition including bold, italic, underline, alignments, lists, and color dialog.
- **Attachment Bar Widget**: Native attachment bar supporting downloading, saving, and launching default system applications.
- **QSystemTrayIcon Integration**: Embedded tray icon notifications with active sync state alerts.
- **Daily Timed Rotating Logs**: Active timed logs rotation with 7-day retention period.

### Fixed
- **Thread Worker Class Renaming**: Fixed class namespace conflicts inside main thread workers to prevent garbage collection crashes.
- **Drafts Node Normalization**: Consolidated multiple drafts folder names to a single local cache directory mapping.
