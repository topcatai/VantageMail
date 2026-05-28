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

def test_batch_sync_progress_and_chunking():
    db = Database(db_path=":memory:")
    email = "user@example.com"
    folder = "INBOX"
    
    # Pre-populate cache: 101 has body, 999 is obsolete (should be deleted)
    db.save_cached_email(email, folder, "101", {"id": "101", "sender": "a@a.com", "subject": "Old", "date": "2026-05-22", "is_read": True, "body": "Cached body"})
    db.save_cached_email(email, folder, "999", {"id": "999", "sender": "del@del.com", "subject": "Obsolete", "date": "2026-05-22", "is_read": True})
    
    provider = MagicMock()
    
    # We mock fetch_messages to emulate a chunked IMAP fetch
    def mock_fetch_messages(folder_id, limit=None, chunk_callback=None, uid_callback=None):
        if uid_callback:
            uid_callback(["101", "102", "103"])
            
        chunk1 = [
            {"id": "101", "sender": "a@a.com", "subject": "Old", "date": "2026-05-22", "is_read": False},
            {"id": "102", "sender": "b@b.com", "subject": "New 102", "date": "2026-05-23", "is_read": False}
        ]
        if chunk_callback:
            chunk_callback(chunk1)
            
        chunk2 = [
            {"id": "103", "sender": "c@c.com", "subject": "New 103", "date": "2026-05-24", "is_read": False}
        ]
        if chunk_callback:
            chunk_callback(chunk2)
            
        return chunk1 + chunk2

    provider.fetch_messages.side_effect = mock_fetch_messages
    
    progress_states = []
    def on_progress(state):
        progress_states.append(list(state))
        
    synced = sync_folder_messages(provider, db, email, folder, progress_callback=on_progress)
    
    # Verify that:
    # 1. Obsolete message 999 is deleted from DB
    assert db.get_cached_email(email, folder, "999") is None
    
    # 2. progress_callback was called 2 times
    assert len(progress_states) == 2
    
    # 3. First progress state contains 101 and 102, body of 101 is preserved, 999 is gone
    first_state = progress_states[0]
    first_dict = {m["id"]: m for m in first_state}
    assert "999" not in first_dict
    assert "101" in first_dict
    assert "102" in first_dict
    assert first_dict["101"]["body"] == "Cached body"
    assert first_dict["101"]["is_read"] is False
    
    # 4. Final synced state has 101, 102, 103
    final_dict = {m["id"]: m for m in synced}
    assert len(final_dict) == 3
    assert "103" in final_dict
    assert final_dict["103"]["subject"] == "New 103"
