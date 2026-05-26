from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class ProviderError(Exception):
    """Custom exception for provider errors"""
    pass

class MailProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the mail service provider"""
        ...

    @property
    @abstractmethod
    def account_email(self) -> str:
        """Email address of the account"""
        ...

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the mail service"""
        ...

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the mail service"""
        ...

    @abstractmethod
    def fetch_folders(self) -> List[str]:
        """Return a list of folder names"""
        ...

    @abstractmethod
    def fetch_messages(self, folder: str) -> List[Dict]:
        """Fetch messages metadata from a folder"""
        ...

    @abstractmethod
    def fetch_message_body(self, msg_id: str) -> str:
        """Retrieve full body of a specific message"""
        ...

    @abstractmethod
    def send_message(self, to: List[str], subject: str, body: str, **kwargs) -> str:
        """Send an email and return its message ID"""
        ...

    @abstractmethod
    def delete_message(self, msg_id: str) -> None:
        """Delete a message by ID"""
        ...

    @abstractmethod
    def move_message(self, msg_id: str, folder: str) -> None:
        """Move a message to another folder"""
        ...

    @abstractmethod
    def mark_read(self, msg_id: str, read: bool = True) -> None:
        """Mark a message as read/unread"""
        ...
