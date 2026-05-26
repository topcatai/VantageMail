# Vantage Mail — Session Context v2
**Hand this file to the next Claude session as the opening message.**
*Updated: 2026-05-21 — App fully functional with live IMAP mailbox, Reply/Forward/Search working*

---

## Project Location
```
C:\aiproject\Goose\outlook_client
```
- Virtual environment: `venv\Scripts\activate`
- Run app: `python src/main.py`
- Run tests: `pytest tests\ -v`
- Delete DB to reset accounts: `del outlook_client.db`

---

## Stack
- Python 3.13.5
- PyQt6 6.11 + PyQt6-WebEngine
- Microsoft Graph API (MSAL) — commented out, pending Azure credentials
- imapclient + smtplib — **active and working**
- Google Auth + Gmail REST API — commented out, pending credentials
- pywin32 (Windows credential storage)
- SQLite (account + offline cache storage)
- pytest 9.0.3

---

## Current Status
**All 7 phases complete. 12/12 tests passing. App name: Vantage Mail. Live tested with Hostinger IMAP.**

| Phase | Description | Status |
|---|---|---|
| 1 | Auth & Token (MSAL, win32cred) | ✅ Complete |
| 2 | Mail Service + Data Models | ✅ Complete |
| 3 | UI Rebuild (PyQt6 three-pane layout) | ✅ Complete |
| 4 | Calendar / Contacts / Tasks services | ✅ Complete |
| 5 | Offline Cache (SQLite) + Sync Engine | ✅ Complete |
| 6 | Test Suite (12 unit + integration tests) | ✅ Complete |
| 7 | Universal Provider Support (IMAP/Gmail/Graph) | ✅ Complete |

### Confirmed Working (live tested)
- App launches and shows three-pane layout
- Add Account Wizard detects provider from email domain
- IMAP connection tested and saved (Hostinger: imap.hostinger.com:993)
- Folders load in left pane (INBOX, Trash, Sent, Junk, Drafts)
- Messages load in middle pane (From, Subject, Date columns)
- Email body renders as HTML in reading pane
- Account email shows in toolbar dropdown
- Account persists across restarts (saved to SQLite)
- Subject lines decode UTF-8 MIME encoding correctly
- Reply opens composer pre-filled with To, Re: subject, quoted body
- Forward opens composer with Fwd: subject and forwarding header
- Search bar filters messages via IMAP TEXT search
- Dark theme consistent across main window and reading pane
- database.py uses json.loads/json.dumps (no eval)
- Reconnection logic automatically triggers on startup and on calling get_provider
- Folder names display clean values without INBOX. prefix
- Tree view displays unread badges on folders containing unseen mail
- INBOX is automatically selected and loaded on startup
- Composer widget has a From dropdown supporting multiple accounts
- Folder tree groups folder nodes under a styled, bold account header node
- SQLite caching loaded instantly, background IMAP synchronization
- Email bodies cached on first load for offline access
- Send/Reply/Forward crash fixed by referencing threads and workers
- Exporting individual emails as EML and folder emails as tabbed CSV
- Multiple row selection and deletion (descending index shift proof, offline synced)

---

## File Structure
```
src/
├── main.py                          # Entry point — IMAP active, MS/Gmail commented out
├── config.py                        # App config — AZURE_CLIENT_ID placeholder
├── models/__init__.py               # Email + Folder dataclasses
├── services/
│   ├── authentication.py            # MSAL device flow
│   ├── token_manager.py             # Token caching + refresh
│   ├── token_storage.py             # win32cred persistence
│   ├── base.py
│   ├── mail/graph.py                # Microsoft Graph mail service
│   ├── cal_service/                 # Renamed from calendar/ (avoids stdlib clash)
│   │   └── graph.py
│   ├── contacts/graph.py
│   ├── tasks/graph.py
│   ├── providers/
│   │   ├── base.py                  # Abstract MailProvider + ProviderError
│   │   ├── registry.py              # detect_provider() + create_provider()
│   │   ├── graph_provider.py        # Microsoft 365 wrapper
│   │   ├── imap_provider.py         # Generic IMAP/SMTP — ACTIVE
│   │   └── gmail_provider.py        # Gmail REST API + Google OAuth
│   └── accounts/
│       └── account_manager.py       # Multi-account manager
├── storage/
│   ├── database.py                  # SQLite
│   └── sync_engine.py               # QThread background sync
└── ui/
    ├── main_window.py               # QMainWindow — three-pane, QThread network calls
    └── widgets/
        ├── email_composer.py        # QDialog — compose/send
        ├── email_preview.py         # QWidget — QWebEngineView HTML render
        ├── tasks_view.py            # QWidget — task list
        ├── add_account_wizard.py    # QWizard — account setup
        └── account_switcher.py      # QComboBox — account switcher
tests/
├── unit/
│   ├── test_authentication.py
│   ├── test_token_manager.py
│   ├── test_token_storage.py
│   └── test_mail_graph.py
└── integration/
    └── test_auth_flow.py
```

---

## Critical Architecture Notes
These decisions must NOT be changed by any coding agent:

- `src/calendar/` renamed to `src/cal_service/` — avoids shadowing Python stdlib `calendar` module
- `QAction` is in `PyQt6.QtGui` not `PyQt6.QtWidgets`
- All network calls use `QThread` + `Worker` object — never call API on main thread
- Worker objects must be stored in `self._workers` list to prevent garbage collection
- Token stored in Windows Credential Manager via `win32cred.CredWrite/CredRead/CredDelete`
- `expires_in` is a duration in seconds: `datetime.now() + timedelta(seconds=expires_in)`
- No `sys.path.append('src')` — package installed via `pip install -e .`
- Import paths are `from services.x import Y` (no `src.` prefix)
- Use `findstr` not `grep` on Windows
- Never use `&&` in PowerShell — run one command per line
- `QTimer.singleShot(100, fn)` used to defer UI calls until after event loop starts

---

## Known Issues to Fix (priority order)

| # | File | Issue |
|---|---|---|
| 1 | `src/services/providers/imap_provider.py` | `b'\Seen'` should be `b'\\Seen'` -- SyntaxWarning (low priority, functional) |
| 2 | `src/services/token_manager.py` | `save_token()` hardcodes `expires_in: 3600` |

---

## Features Not Yet Built

- Attachment download UI -- flag exists in model, no UI
- Pagination -- fetch capped at 50, no "load more"
- New mail notification
- Calendar UI widget -- service exists, no panel
- Contacts UI widget -- service exists, no panel
- Search filters -- currently searches full TEXT only, no filter by From/Subject/Date range

---

## Account Manager — Key Methods
```python
account_manager.add_account_with_provider(email, provider, cfg)
# Use this — NOT add_account() — when provider instance already exists (e.g. after wizard test)

account_manager.get_active_provider()
# Returns connected MailProvider — auto-reconnects via noop() check

account_manager.set_active_account(email)
account_manager.get_accounts()  # returns list of dicts with 'email' key
```

---

## IMAP Provider — Key Details
```python
# Credentials saved format in DB (config column):
{
    "config": {"imap": {"host": "...", "port": 993}, "smtp": {"host": "...", "port": 465}},
    "credentials": {"password": "..."}
}

# fetch_folders() returns: [{'id': 'INBOX', 'display_name': 'INBOX'}, ...]
# fetch_messages(folder_id, limit=50) returns: [{'id': uid, 'subject': ..., 'sender': ..., 'date': ..., 'is_read': bool}]
# fetch_message_body(message_id) returns: HTML string
```

---

## Provider IMAP/SMTP Settings Reference
| Provider | IMAP Host | IMAP Port | SMTP Host | SMTP Port |
|---|---|---|---|---|
| Hostinger | imap.hostinger.com | 993 | smtp.hostinger.com | 465 |
| Yahoo | imap.mail.yahoo.com | 993 | smtp.mail.yahoo.com | 465 |
| iCloud | imap.mail.me.com | 993 | smtp.mail.me.com | 587 |
| Zoho | imap.zoho.com | 993 | smtp.zoho.com | 465 |
| Fastmail | imap.fastmail.com | 993 | smtp.fastmail.com | 465 |
| cPanel/generic | mail.yourdomain.com | 993 | mail.yourdomain.com | 465 |
| ProtonMail Bridge | 127.0.0.1 | 1143 | 127.0.0.1 | 1025 |

---

## Azure App Registration (Pending)
- Legal entity: Takshiq Soft Labs LLP — registration in progress
- Register at: portal.azure.com → App registrations
- Account type: Accounts in any organizational directory + personal Microsoft accounts
- Enable: Allow public client flows = Yes
- Required permissions (delegated): Mail.Read, Mail.Send, Mail.ReadWrite, Calendars.ReadWrite, Contacts.ReadWrite, Tasks.ReadWrite, User.Read
- After registration: add client ID to `src/config.py` → `AZURE_CLIENT_ID`
- Uncomment Microsoft block in `src/main.py`

## Gmail Credentials (Pending)
- Register at: console.cloud.google.com → New Project → Enable Gmail API
- Create OAuth 2.0 credentials → Desktop application
- Download `gmail_credentials.json` to project root
- Uncomment Gmail block in `src/main.py`

---

## Coding Agent Rules
- Working directory: `C:\aiproject\Goose\outlook_client`
- Always activate venv: `venv\Scripts\activate`
- Use `findstr` not `grep`
- Never use `&&` in PowerShell — one command per line
- Use Write file tool for file creation
- Run `python -m py_compile <file>` after every change
- Run `pytest tests\ -v` after every phase
- Do not use the code execution tool — shell commands only
- All new .py files: `# -*- coding: utf-8 -*-` header
- No Unicode symbols in print/error strings
- Never rewrite a working file from scratch — make targeted edits only
- Always upload the current file before editing if unsure of contents

---

## Previous Blueprint Documents
- `Outlook_Client_Blueprint_v2.docx` — Phases 1-6 spec + audit checklists
- `Outlook_Client_Phase7_Blueprint.docx` — Phase 7 universal provider spec
Both in: `C:\aiproject\Goose\outlook_client\`

---
*v2 — 2026-05-21 — Reply, Forward, Search, subject decode, dark theme, eval fix all complete*
