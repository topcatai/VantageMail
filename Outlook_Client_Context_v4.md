# Vantage Mail — Session Context v4
**Hand this file to the next Claude session as the opening message.**
*Updated: 2026-05-27 — Version 1.0.0 released with SQLite FTS5 Full-Text Search. Standalone MSI packaged.*

---

## Project Location
```
C:\aiproject\Goose\outlook_client
```
- Virtual environment: `venv\Scripts\activate`
- Run app: `python src/main.py`
- Run tests: `pytest tests\ -v`
- Delete DB to reset accounts: `del %LOCALAPPDATA%\VantageMail\outlook_client.db` (and shm/wal files)

---

## Stack
- Python 3.13.5
- PyQt6 6.11 + PyQt6-WebEngine
- imapclient + smtplib — **active and working**
- SQLite (account + offline cache storage under AppData)
- SQLite FTS5 (Full-Text Search) — **active and working**
- win32cred (Windows credential storage)
- pytest 9.0.3

---

## Current Status
**Version 1.0.0 released. 32/32 tests passing. Standalone Windows MSI installer successfully generated and published to GitHub.**

### Known Issues & Feedback to Address (V1.0.0 Post-Release)

| Issue | Details | Status |
|---|---|---|
| 1 | **Batch Loading / UI Activity** | All 7,500 emails load at the same time on sync. Need to sync and download emails in batches of 100 to show activity and progress indicators to the user that downloads are happening. | 📝 Pending |
| 2 | **Search Window Re-launch** | Search window works once, but does not launch a second time (even after restarting the app). Need to investigate the `_on_search()` slot/window tracker in `main_window.py` or `SearchWindow` lifetime management. | 📝 Pending |
| 3 | **Start Menu Icon** | Application icon is missing in the Windows Start Menu shortcut after installation. Need to check how to embed standard BMP-based ICO files in the installer shortcut database without breaking `msilib`. | 📝 Pending |

---

## Technical Updates in V1.0.0

1. **SQLite FTS5 Integration**:
   - Schema virtual table `emails_fts` created at startup with auto-migration hooks.
   - Syncing hooks in `save_cached_email()`, `batch_save_emails()`, and `delete_cached_email()`.
   - `search_emails()` updated with FTS5 token sanitization (`word* AND word*` query format restricted to `{subject body}`) and automatic sequential fallback.

2. **AppData Redirection (Write Permission Fix)**:
   - The database path (`outlook_client.db`) and logs directory (`logs/`) are now resolved inside `%LOCALAPPDATA%\VantageMail` (or platform equivalent) rather than the project root folder. This prevents `PermissionError` access crashes when installed in `C:\Program Files`.

3. **MSI Rebuild Fix**:
   - Removed `icon` parameter from `Executable(...)` inside `setup_cx.py` to prevent `msilib` database compilation truncation (which was outputting a corrupt 128 KB MSI). Standard MSI size is **~173.5 MB**.

---

## Key Files to Edit Next

* **`src/storage/sync_utils.py` / `src/storage/sync_engine.py`**: Refactor syncing loop to download and save messages in batches of 100, emitting progress updates.
* **`src/ui/main_window.py`**: Check the `_on_search()` method. Ensure that if the search window is closed, its reference is cleared so it can be re-opened, or check if the window is hidden/garbage collected.
* **`setup_cx.py`**: Configure shortcuts with standard ICO references.
