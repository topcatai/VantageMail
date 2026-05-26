# -*- coding: utf-8 -*-
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

with patch('msal.PublicClientApplication'):
    from services.authentication import AuthenticationService

def make_service():
    with patch('msal.PublicClientApplication'):
        return AuthenticationService(
            client_id='test-id',
            authority='https://login.microsoftonline.com/common',
            scopes=['Mail.Read'],
            use_device_flow=True
        )

def test_get_access_token_returns_cached():
    svc = make_service()
    svc.token = 'cached-token'
    svc.token_expires = datetime.now() + timedelta(minutes=10)
    assert svc.get_access_token() == 'cached-token'

def test_expires_in_uses_timedelta():
    svc = make_service()
    svc.token = 'tok'
    svc.token_expires = datetime.now() + timedelta(minutes=10)
    result = svc.acquire_token()
    assert result == 'tok'

def test_missing_token_triggers_login():
    svc = make_service()
    svc.token = None
    svc.token_expires = None
    svc.msal_client.get_accounts.return_value = []
    with pytest.raises(Exception):
        svc.acquire_token()