# -*- coding: utf-8 -*-
import requests
from typing import Any, List, Dict, Optional
from services.token_manager import TokenManager

class GraphMailService:
    """Service for interacting with Microsoft Graph Mail endpoints."""

    base_url = "https://graph.microsoft.com/v1.0"

    def __init__(self, token_manager: TokenManager):
        self.token_manager = token_manager

    def _headers(self) -> Dict[str, str]:
        """Return HTTP headers with the Bearer token.

        Raises:
            ValueError: If no valid access token is available.
        """
        token = self.token_manager.get_token()
        if not token:
            raise ValueError("Unable to obtain access token for Graph API")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def fetch(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Generic GET request to a Graph endpoint.

        Args:
            endpoint: Relative endpoint, e.g. "/me/messages".
            params: Optional query parameters.
        Returns:
            Parsed JSON response.
        Raises:
            requests.HTTPError: For non‑2xx responses.
        """
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, headers=self._headers(), params=params)
        response.raise_for_status()
        return response.json()

    def get_folders(self) -> List[Dict[str, Any]]:
        """Return a list of mail folders for the authenticated user."""
        data = self.fetch("/me/mailFolders")
        return data.get("value", [])

    def send(self, subject: str, body: str, to: List[str], cc: Optional[List[str]] = None,
             bcc: Optional[List[str]] = None, **kwargs) -> Any:
        """Send an email via Graph.

        Args:
            subject: Email subject.
            body: Plain‑text or HTML body.
            to: List of recipient email addresses.
            cc: Optional list of CC addresses.
            bcc: Optional list of BCC addresses.
            **kwargs: Additional message fields (e.g., importance).
        Returns:
            JSON response from Graph.
        Raises:
            requests.HTTPError: If the send request fails.
        """
        message: Dict[str, Any] = {
            "message": {
                "subject": subject,
                "body": {"contentType": "Text", "content": body},
                "toRecipients": [{"emailAddress": {"address": addr}} for addr in to],
            },
            "saveToSentItems": "true",
        }
        if cc:
            message["message"]["ccRecipients"] = [{"emailAddress": {"address": addr}} for addr in cc]
        if bcc:
            message["message"]["bccRecipients"] = [{"emailAddress": {"address": addr}} for addr in bcc]
        message["message"].update(kwargs)
        url = f"{self.base_url}/me/sendMail"
        response = requests.post(url, headers=self._headers(), json=message)
        response.raise_for_status()
        return response.json() if response.content else {}

    def delete(self, mail_id: str) -> None:
        """Delete a message by its ID."""
        url = f"{self.base_url}/me/messages/{mail_id}"
        response = requests.delete(url, headers=self._headers())
        response.raise_for_status()

    def move(self, mail_id: str, destination_folder_id: str) -> Any:
        """Move a message to another folder.

        Returns the moved message JSON.
        """
        url = f"{self.base_url}/me/messages/{mail_id}/move"
        payload = {"destinationId": destination_folder_id}
        response = requests.post(url, headers=self._headers(), json=payload)
        response.raise_for_status()
        return response.json()

    def mark_read(self, mail_id: str) -> None:
        """Mark a message as read."""
        url = f"{self.base_url}/me/messages/{mail_id}"
        payload = {"isRead": True}
        response = requests.patch(url, headers=self._headers(), json=payload)
        response.raise_for_status()

    def mark_unread(self, mail_id: str) -> None:
        """Mark a message as unread."""
        url = f"{self.base_url}/me/messages/{mail_id}"
        payload = {"isRead": False}
        response = requests.patch(url, headers=self._headers(), json=payload)
        response.raise_for_status()
