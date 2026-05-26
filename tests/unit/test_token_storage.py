# -*- coding: utf-8 -*-
import pytest
from unittest.mock import patch, MagicMock

with patch('win32cred.CredWrite'), patch('win32cred.CredRead'), patch('win32cred.CredDelete'):
    from services.token_storage import TokenStorage

def test_save_calls_credwrite():
    with patch('services.token_storage.win32cred') as mock_cred:
        s = TokenStorage()
        s.save_token({'access_token': 'tok', 'expires_in': 3600, 'token_type': 'Bearer'})
        mock_cred.CredWrite.assert_called_once()

def test_load_calls_credread():
    with patch('services.token_storage.win32cred') as mock_cred:
        mock_cred.CredRead.return_value = {'CredentialBlob': '{"access_token": "tok"}'.encode('utf-16-le')}
        s = TokenStorage()
        result = s.load_token()
        mock_cred.CredRead.assert_called_once()
        assert result == {'access_token': 'tok'}

def test_delete_calls_creddelete():
    with patch('services.token_storage.win32cred') as mock_cred:
        s = TokenStorage()
        s.delete_token()
        mock_cred.CredDelete.assert_called_once()