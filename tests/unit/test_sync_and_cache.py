# -*- coding: utf-8 -*-
import json
import pytest
from unittest.mock import MagicMock
from storage.database import Database
from storage.sync_utils import sync_folder_messages

def test_sqlite_cache_methods():
    db = Database(db_path=":memory:")
    
    email = "user@example.com"
    folder = "INBOX"
    msg_id = "101"
    msg_data = {"id": "101", "sender": "test@test.com", "subject": "Hello", "date": "2026-05-23", "is_read": False}
    
    # Save cache
    db.save_cached_email(email, folder, msg_id, msg_data)
    
    # Load cache
    cached = db.get_cached_emails(email, folder)
    assert len(cached) == 1
    assert cached[0]["id"] == "101"
    assert cached[0]["subject"] == "Hello"
    
    # Load single cached message
    single = db.get_cached_email(email, folder, msg_id)
    assert single is not None
    assert single["sender"] == "test@test.com"
    
    # Delete cache
    db.delete_cached_email(email, folder, msg_id)
    assert len(db.get_cached_emails(email, folder)) == 0

def test_sync_folder_messages():
    db = Database(db_path=":memory:")
    
    email = "user@example.com"
    folder = "INBOX"
    
    # Pre-populate cache with an old message
    db.save_cached_email(email, folder, "101", {"id": "101", "sender": "a@a.com", "subject": "Old", "date": "2026-05-22", "is_read": True, "body": "Cached body"})
    
    # Mock IMAP provider
    provider = MagicMock()
    # Remote has "102" (new) and "101" (updated, is_read: False)
    provider.fetch_messages.return_value = [
        {"id": "101", "sender": "a@a.com", "subject": "Old", "date": "2026-05-22", "is_read": False},
        {"id": "102", "sender": "b@b.com", "subject": "New", "date": "2026-05-23", "is_read": False}
    ]
    
    synced = sync_folder_messages(provider, db, email, folder)
    assert len(synced) == 2
    
    # Verify new is cached
    msg_102 = db.get_cached_email(email, folder, "102")
    assert msg_102 is not None
    assert msg_102["subject"] == "New"
    
    # Verify updated is cached and body is preserved
    msg_101 = db.get_cached_email(email, folder, "101")
    assert msg_101 is not None
    assert msg_101["is_read"] is False
    assert msg_101["body"] == "Cached body"

def test_database_multithreaded_access():
    import threading
    db = Database(db_path=":memory:")
    errors = []
    def worker():
        try:
            db.save_cached_email("test@email.com", "INBOX", "1", {"id": "1"})
            email = db.get_cached_email("test@email.com", "INBOX", "1")
            assert email["id"] == "1"
        except Exception as e:
            errors.append(e)
    t = threading.Thread(target=worker)
    t.start()
    t.join()
    assert len(errors) == 0, f"Thread raised error: {errors}"
