# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

with patch('win32cred.CredWrite'), patch('win32cred.CredRead'), patch('win32cred.CredDelete'):
    from services.token_manager import TokenManager

def make_manager():
    auth = MagicMock()
    auth.get_access_token.return_value = 'fresh-token'
    auth.token_expires = datetime.now() + timedelta(hours=1)
    storage = MagicMock()
    storage.load_token.return_value = None
    return TokenManager(auth, storage), auth, storage

def test_returns_cached_token():
    mgr, auth, storage = make_manager()
    mgr.token_data = {'access_token': 'cached'}
    mgr.token_expires = datetime.now() + timedelta(minutes=30)
    assert mgr.get_token() == 'cached'
    auth.get_access_token.assert_not_called()

def test_refreshes_expired_token():
    mgr, auth, storage = make_manager()
    mgr.token_data = None
    mgr.token_expires = None
    result = mgr.get_token()
    assert result == 'fresh-token'
    auth.get_access_token.assert_called_once()

def test_load_cached_called_on_init():
    auth = MagicMock()
    storage = MagicMock()
    storage.load_token.return_value = None
    TokenManager(auth, storage)
    storage.load_token.assert_called_once()