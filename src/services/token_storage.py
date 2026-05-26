# -*- coding: utf-8 -*-
import json
import win32cred
import logging

class TokenStorage:
    def __init__(self, service_name: str = "VantageMail"):
        self.service_name = service_name

    def save_token(self, token_data: dict):
        """Save token data to Windows Credential Manager"""
        json_data = json.dumps(token_data)
        creds = {
            'Type': win32cred.CRED_TYPE_GENERIC,
            'TargetName': self.service_name,
            'CredentialBlob': json_data.encode('utf-16-le'),  # CredentialBlob must be bytes
            'Persist': win32cred.CRED_PERSIST_LOCAL_MACHINE,
        }
        win32cred.CredWrite(creds)
        logging.info(f"Token saved for service: {self.service_name}")

    def load_token(self):
        """Load token data from Windows Credential Manager"""
        try:
            cred = win32cred.CredRead(self.service_name, win32cred.CRED_TYPE_GENERIC)
            if cred and 'CredentialBlob' in cred:
                json_data = cred['CredentialBlob'].decode('utf-16-le')
                token_data = json.loads(json_data)
                logging.info(f"Token loaded for service: {self.service_name}")
                return token_data
        except Exception as e:
            logging.info(f"No cached token found for service: {self.service_name}")
            return None
        return None

    def delete_token(self):
        """Delete token data from Windows Credential Manager"""
        try:
            win32cred.CredDelete(self.service_name, win32cred.CRED_TYPE_GENERIC, 0)
            logging.info(f"Token deleted for service: {self.service_name}")
        except Exception as e:
            logging.info(f"No token to delete for service: {self.service_name}")
