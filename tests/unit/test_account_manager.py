# -*- coding: utf-8 -*-
import json
import pytest
from storage.database import Database
from services.accounts.account_manager import AccountManager

def test_account_manager_load_flat_string_config():
    db = Database(db_path=":memory:")
    # Insert raw flat string config directly into accounts table
    cursor = db.conn.cursor()
    config_dict = {"imap": {"host": "imap.example.com", "port": 993}, "smtp": {"host": "smtp.example.com", "port": 465}}
    cursor.execute(
        "INSERT INTO accounts (email, provider, config, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("test@example.com", "generic", json.dumps(config_dict))
    )
    db.conn.commit()

    # Load account manager
    am = AccountManager(db)
    accounts = am.get_accounts()
    assert len(accounts) == 1
    assert accounts[0]["email"] == "test@example.com"
    # Ensure config was parsed as a dictionary and is tolerant of flat config
    assert isinstance(accounts[0]["config"], dict)
    assert accounts[0]["config"].get("imap", {}).get("host") == "imap.example.com"

def test_account_manager_load_nested_dict_config():
    db = Database(db_path=":memory:")
    # Insert nested config (containing config and credentials) directly
    cursor = db.conn.cursor()
    nested_dict = {
        "config": {"imap": {"host": "imap.example.com", "port": 993}, "smtp": {"host": "smtp.example.com", "port": 465}},
        "credentials": {"password": "testpassword"}
    }
    cursor.execute(
        "INSERT INTO accounts (email, provider, config, created_at) VALUES (?, ?, ?, datetime('now'))",
        ("test@example.com", "generic", json.dumps(nested_dict))
    )
    db.conn.commit()

    # Load account manager
    am = AccountManager(db)
    accounts = am.get_accounts()
    assert len(accounts) == 1
    assert accounts[0]["email"] == "test@example.com"
    # config attribute in account manager points to the nested config dict
    assert isinstance(accounts[0]["config"], dict)
    assert "config" in accounts[0]["config"]
    assert "credentials" in accounts[0]["config"]

    # Test get_provider loads it correctly with credentials and config
    from unittest.mock import patch
    with patch('services.providers.imap_provider.ImapProvider.connect') as mock_connect:
        provider = am.get_provider("test@example.com")
        assert provider is not None
        assert provider._email == "test@example.com"
        assert provider._password == "testpassword"
        assert provider._imap_host == "imap.example.com"
        assert provider._imap_port == 993
