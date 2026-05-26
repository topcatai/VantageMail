# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from services.token_storage import TokenStorage
import logging

class TokenManager:
    def __init__(self, auth_service, token_storage):
        self.auth_service = auth_service
        self.token_storage = token_storage
        self.token_data = None
        self.token_expires = None
        self.load_cached_token()

    def load_cached_token(self):
        self.token_data = self.token_storage.load_token()
        if self.token_data and 'expires_on' in self.token_data:
            try:
                self.token_expires = datetime.fromisoformat(self.token_data['expires_on'])
            except:
                self.token_expires = None
        else:
            self.token_data = None
            self.token_expires = None

    def save_token(self, token_data: dict):
        self.token_data = token_data
        if 'expires_in' in token_data:
            self.token_expires = datetime.now() + timedelta(seconds=token_data['expires_in'])
            token_data['expires_on'] = self.token_expires.isoformat()
        self.token_storage.save_token(token_data)

    def is_token_valid(self) -> bool:
        if not self.token_data or not self.token_expires:
            return False
        return self.token_expires > datetime.now() + timedelta(minutes=5)

    def get_token(self) -> str:
        if not self.is_token_valid():
            new_token = self.auth_service.get_access_token()
            self.save_token({
                'access_token': new_token,
                'expires_in': 3600
            })
        return self.token_data.get('access_token')