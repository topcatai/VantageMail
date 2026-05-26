# -*- coding: utf-8 -*-
import pytest
from storage.database import Database
from utils.logger import log_info, log_error, log_realtime_count

def test_database_get_total_email_count():
    db = Database(db_path=":memory:")
    
    # Empty count
    assert db.get_total_email_count() == 0
    
    # Save a couple emails
    db.save_cached_email("test@example.com", "Inbox", "1", {"id": "1", "subject": "Test 1"})
    db.save_cached_email("test@example.com", "Inbox", "2", {"id": "2", "subject": "Test 2"})
    db.save_cached_email("other@example.com", "Sent", "3", {"id": "3", "subject": "Test 3"})
    
    # Verify count
    assert db.get_total_email_count() == 3
    
    # Delete one
    db.delete_cached_email("test@example.com", "Inbox", "1")
    assert db.get_total_email_count() == 2

def test_logger_functions():
    # Test that logging calls do not throw exceptions
    log_info("Test log info message")
    log_error("Test log error message", exc_info=False)
    
    db = Database(db_path=":memory:")
    log_realtime_count(db)
