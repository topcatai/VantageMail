# Vantage Mail — Agent Instructions

## Project
Python 3.13 desktop email client. PyQt6 UI. Windows only.
Working directory: C:\aiproject\Goose\outlook_client

## Critical Rules
- Never use && in PowerShell — one command per line
- Use findstr not grep
- All new .py files need # -*- coding: utf-8 -*- header
- No Unicode symbols in print/error strings (ASCII only)
- Never rewrite a working file from scratch — targeted edits only
- Run python -m py_compile <file> after every file change
- Run pytest tests\ -v after every phase
- QAction imports from PyQt6.QtGui not PyQt6.QtWidgets
- All network calls must use QThread — never on main thread
- Store Worker objects in self._workers to prevent garbage collection
- Import paths: from services.x import Y (no src. prefix)

## Current State
- All 7 phases complete
- 12/12 tests passing
- App runs with live IMAP (Hostinger)
- Read Outlook_Client_Context_v2.md for full details

## Stack
Python 3.13 · PyQt6 6.11 · imapclient · smtplib · MSAL · SQLite · pywin32