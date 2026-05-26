# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class Email:
    id: str
    subject: str
    sender: str
    to: List[str]
    cc: List[str]
    body_html: Optional[str]
    body_text: Optional[str]
    date: str
    is_read: bool
    folder_id: str
    has_attachments: bool

    @classmethod
    def from_graph_response(cls, data: Dict[str, Any]) -> Email:
        # Extract common fields with safe defaults
        return cls(
            id=data.get("id", ""),
            subject=data.get("subject", ""),
            sender=data.get("sender", {}).get("emailAddress", {}).get("address", ""),
            to=[addr.get("emailAddress", {}).get("address", "") for addr in data.get("toRecipients", [])],
            cc=[addr.get("emailAddress", {}).get("address", "") for addr in data.get("ccRecipients", [])],
            body_html=data.get("body", {}).get("content", "") if data.get("body", {}).get("contentType") == "HTML" else None,
            body_text=data.get("body", {}).get("content", "") if data.get("body", {}).get("contentType") == "Text" else None,
            date=data.get("receivedDateTime", ""),
            is_read=data.get("isRead", False),
            folder_id=data.get("parentFolderId", ""),
            has_attachments=data.get("hasAttachments", False),
        )

@dataclass
class Folder:
    id: str
    display_name: str
    total_count: int
    unread_count: int
    parent_id: Optional[str]

    @classmethod
    def from_graph_response(cls, data: Dict[str, Any]) -> Folder:
        return cls(
            id=data.get("id", ""),
            display_name=data.get("displayName", ""),
            total_count=data.get("totalItemCount", 0),
            unread_count=data.get("unreadItemCount", 0),
            parent_id=data.get("parentFolderId"),
        )
