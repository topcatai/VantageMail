# -*- coding: utf-8 -*-
import msal
import logging
from datetime import datetime, timedelta
import os

class AuthenticationService:
    def __init__(self, client_id: str = None, authority: str = None, scopes: list = None, use_device_flow: bool = False, username: str = None, password: str = None):
        # Read from environment variables if not provided
        self.client_id = client_id or os.environ.get('AZURE_CLIENT_ID')
        self.authority = authority or (os.environ.get('AZURE_TENANT_ID') and f"https://login.microsoftonline.com/{os.environ.get('AZURE_TENANT_ID')}")
        self.scopes = scopes or ["Mail.Read", "Mail.Send", "User.Read"]
        self.use_device_flow = use_device_flow
        self.username = username
        self.password = password
        self.msal_client = None
        if self.client_id and self.authority:
            self.msal_client = msal.PublicClientApplication(
                client_id=self.client_id,
                authority=self.authority,
            )
        self.account = None
        self.token = None
        self.token_expires = None

    def login(self):
        if not self.msal_client:
            raise ValueError("MSAL client not initialized. Check AZURE_CLIENT_ID and AZURE_TENANT_ID environment variables.")
        
        if self.use_device_flow:
            flow = self.msal_client.initiate_device_flow(scopes=self.scopes)
            if "user_code" not in flow:
                raise ValueError("Failed to create device flow")
            print(f"Please visit: {flow['verification_uri']}")
            print(f"Code: {flow['user_code']}")
            import time
            result = None
            while result is None:
                result = self.msal_client.acquire_token_by_device_flow(flow)
                if "access_token" in result:
                    self.account = result["account"]
                    self.token = result["access_token"]
                    self.token_expires = datetime.now() + timedelta(seconds=result['expires_in'])
                    print("Authentication successful.")
                    break
                elif "error" in result:
                    print(f"Error: {result['error']}")
                    break
                time.sleep(5)
        else:
            # Username/password flow (ROPC) - placeholder
            self._acquire_token_silent()
            if not self.token:
                print("Username/password interactive login not implemented in this example.")

    def _acquire_token_silent(self):
        accounts = self.msal_client.get_accounts()
        if accounts:
            self.account = accounts[0]
            result = self.msal_client.acquire_token_silent(self.scopes, account=self.account)
            if "access_token" in result:
                self.token = result["access_token"]
                self.token_expires = datetime.now() + timedelta(seconds=result['expires_in'])
                return True
        return False

    def acquire_token(self):
        if self.token and self.token_expires and datetime.now() < self.token_expires - timedelta(minutes=5):
            return self.token
        if self._acquire_token_silent():
            return self.token
        self.login()
        if not self.token:
            raise RuntimeError("Failed to acquire token")
        # Note: token_expires is already set in login or _acquire_token_silent
        return self.token

    def get_access_token(self) -> str:
        return self.acquire_token()

    def get_account_info(self):
        if self.account:
            return {"account_id": self.account["account_id"], "username": self.account.get("username", "N/A")}
        return None