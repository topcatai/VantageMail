# -*- coding: utf-8 -*-
import pytest
from unittest.mock import patch, MagicMock
from services.mail.graph import GraphMailService

@patch('services.mail.graph.requests')
def test_fetch_calls_correct_url(mock_requests):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {'value': []}
    mock_requests.get.return_value = mock_resp
    service = GraphMailService(token_manager=MagicMock())
    service.fetch('/me/messages')
    mock_requests.get.assert_called()
    args, _ = mock_requests.get.call_args
    assert '/me/messages' in args[0]

@patch('services.mail.graph.requests')
def test_send_posts_to_sendMail(mock_requests):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.content = b'{}'
    mock_resp.json.return_value = {}
    mock_requests.post.return_value = mock_resp
    service = GraphMailService(token_manager=MagicMock())
    service.send(subject='Test', body='Hello', to=['test@example.com'])
    mock_requests.post.assert_called()
    args, _ = mock_requests.post.call_args
    assert 'sendMail' in args[0]

@patch('services.mail.graph.requests')
def test_delete_sends_delete(mock_requests):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_requests.delete.return_value = mock_resp
    service = GraphMailService(token_manager=MagicMock())
    service.delete('123')
    mock_requests.delete.assert_called()
