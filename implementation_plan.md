# Implementation Plan — SQLite FTS5 Full-Text Search Indexing

This plan specifies the implementation of SQLite FTS5 Full-Text Search (FTS5) to index email subjects and bodies. This will enable instant search results on large mailboxes and include automatic migration of existing cached emails and a fallback query system in case the system's SQLite lacks the FTS5 module.

## Proposed Changes

### 1. Database Schema & Migration

#### [MODIFY] [database.py](file:///C:/aiproject/Goose/outlook_client/src/storage/database.py)
- **Table Creation**:
  - In `_create_tables()`, attempt to create the FTS5 virtual table:
    ```sql
    CREATE VIRTUAL TABLE IF NOT EXISTS emails_fts USING fts5(
        id,
        account_email,
        folder_id,
        subject,
        body
    );
    ```
  - Store `self.fts_available = True` if successful; if it raises `sqlite3.OperationalError` (e.g. FTS5 missing), catch it, log a warning, and set `self.fts_available = False`.
- **Startup Migration**:
  - If `self.fts_available` is `True`, check if `emails_fts` is empty but the main `emails` table contains records.
  - If so, run a one-time migration query to index all existing emails:
    ```sql
    INSERT INTO emails_fts (id, account_email, folder_id, subject, body)
    SELECT id, account_email, folder_id,
           json_extract(data, '$.subject'),
           json_extract(data, '$.body')
    FROM emails;
    ```
- **FTS5 Syncing**:
  - In `save_cached_email()`, if FTS5 is available:
    - Delete any old entry from `emails_fts` matching `account_email`, `folder_id`, and `id`.
    - Insert the new entry into `emails_fts` extracting the subject and body.
  - In `batch_save_emails()`, execute the same delete-and-insert sequence for each message in the batch (grouped under the single transaction).
  - In `delete_cached_email()`, if FTS5 is available:
    - Delete matching row from `emails_fts`.
- **Search Query Update**:
  - In `search_emails()`, check `self.fts_available`:
    - If `True`, sanitize/format the query (e.g. convert `"urgent review"` to `"urgent* AND review*"` for prefix queries) and execute a fast `JOIN` query on `emails_fts` using `MATCH`.
    - If `False`, fallback to the previous `json_extract` sequential query.

---

## Verification Plan

### Automated Tests
- Run `python -m py_compile src/storage/database.py` to check syntax.
- Run `python -m pytest tests\ -v` to verify existing tests pass.
- Add a new unit test `test_fts_indexing` to verify:
  1. FTS5 virtual table is created and populated on email saves.
  2. Deleted emails are removed from the FTS5 index.
  3. FTS5 search query returns correct results including prefix matches.
  4. Fallback search logic functions correctly if FTS5 is simulated to be disabled.

### Manual Verification
1. Open Vantage Mail. Verify startup completes successfully (migrating any existing cache to `emails_fts`).
2. Open Search Window. Enter search keywords and verify results populate instantly.
3. Verify that prefix queries (e.g. searching `"revi"` matches `"review"`) and multi-word searches return correct results.
