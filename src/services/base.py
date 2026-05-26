"""
Base service classes for defining common interfaces.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict
from ..models import Email, Folder, CalendarEvent, Contact, Task

class BaseService(ABC):
    """Abstract base class for all services."""
    
    def __init__(self, auth_token: str):
        """
        Initialize the service with an authentication token.
        
        Args:
            auth_token: A valid access token for the service (e.g., Microsoft Graph).
        """
        self.auth_token = auth_token
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test the connection to the service.
        
        Returns:
            True if connection is successful, False otherwise.
        """
        pass

class MailService(BaseService):
    """Abstract base class for mail services."""
    
    @abstractmethod
    def get_folders(self) -> List[Folder]:
        """Get all mail folders.
        
        Returns:
            List of Folder objects.
        """
        pass
    
    @abstractmethod
    def get_messages(self, folder_id: str, 
                     limit: int = 50, 
                     offset: int = 0,
                     search_query: Optional[str] = None) -> List[Email]:
        """Get messages from a specific folder.
        
        Args:
            folder_id: The ID of the folder to fetch messages from.
            limit: Maximum number of messages to return.
            offset: Number of messages to skip (for pagination).
            search_query: Optional search query to filter messages.
            
        Returns:
            List of Email objects.
        """
        pass
    
    @abstractmethod
    def get_message(self, message_id: str) -> Email:
        """Get a specific message by ID.
        
        Args:
            message_id: The ID of the message to fetch.
            
        Returns:
            Email object.
        """
        pass
    
    @abstractmethod
    def send_message(self, email: Email) -> str:
        """Send an email message.
        
        Args:
            email: Email object to send.
            
        Returns:
            The ID of the sent message.
        """
        pass
    
    @abstractmethod
    def delete_message(self, message_id: str) -> bool:
        """Delete a message.
        
        Args:
            message_id: The ID of the message to delete.
            
        Returns:
            True if deletion was successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def move_message(self, message_id: str, destination_folder_id: str) -> bool:
        """Move a message to another folder.
        
        Args:
            message_id: The ID of the message to move.
            destination_folder_id: The ID of the destination folder.
            
        Returns:
            True if move was successful, False otherwise.
        """
        pass

class CalendarService(BaseService):
    """Abstract base class for calendar services."""
    
    @abstractmethod
    def get_events(self, calendar_id: str = "primary",
                   start_time: Optional[Any] = None,
                   end_time: Optional[Any] = None) -> List[CalendarEvent]:
        """Get calendar events.
        
        Args:
            calendar_id: The ID of the calendar (default is primary calendar).
            start_time: Start time for filtering events (inclusive).
            end_time: End time for filtering events (exclusive).
            
        Returns:
            List of CalendarEvent objects.
        """
        pass
    
    @abstractmethod
    def create_event(self, event: CalendarEvent) -> str:
        """Create a new calendar event.
        
        Args:
            event: CalendarEvent object to create.
            
        Returns:
            The ID of the created event.
        """
        pass
    
    @abstractmethod
    def update_event(self, event: CalendarEvent) -> bool:
        """Update an existing calendar event.
        
        Args:
            event: CalendarEvent object with updated information.
            
        Returns:
            True if update was successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def delete_event(self, event_id: str) -> bool:
        """Delete a calendar event.
        
        Args:
            event_id: The ID of the event to delete.
            
        Returns:
            True if deletion was successful, False otherwise.
        """
        pass

class ContactsService(BaseService):
    """Abstract base class for contacts services."""
    
    @abstractmethod
    def get_contacts(self, limit: int = 50, 
                     offset: int = 0,
                     search_query: Optional[str] = None) -> List[Contact]:
        """Get contacts.
        
        Args:
            limit: Maximum number of contacts to return.
            offset: Number of contacts to skip (for pagination).
            search_query: Optional search query to filter contacts.
            
        Returns:
            List of Contact objects.
        """
        pass
    
    @abstractmethod
    def get_contact(self, contact_id: str) -> Contact:
        """Get a specific contact by ID.
        
        Args:
            contact_id: The ID of the contact to fetch.
            
        Returns:
            Contact object.
        """
        pass
    
    @abstractmethod
    def create_contact(self, contact: Contact) -> str:
        """Create a new contact.
        
        Args:
            contact: Contact object to create.
            
        Returns:
            The ID of the created contact.
        """
        pass
    
    @abstractmethod
    def update_contact(self, contact: Contact) -> bool:
        """Update an existing contact.
        
        Args:
            contact: Contact object with updated information.
            
        Returns:
            True if update was successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def delete_contact(self, contact_id: str) -> bool:
        """Delete a contact.
        
        Args:
            contact_id: The ID of the contact to delete.
            
        Returns:
            True if deletion was successful, False otherwise.
        """
        pass

class TasksService(BaseService):
    """Abstract base class for tasks services."""
    
    @abstractmethod
    def get_tasks(self, limit: int = 50, 
                  offset: int = 0,
                  search_query: Optional[str] = None) -> List[Task]:
        """Get tasks.
        
        Args:
            limit: Maximum number of tasks to return.
            offset: Number of tasks to skip (for pagination).
            search_query: Optional search query to filter tasks.
            
        Returns:
            List of Task objects.
        """
        pass
    
    @abstractmethod
    def get_task(self, task_id: str) -> Task:
        """Get a specific task by ID.
        
        Args:
            task_id: The ID of the task to fetch.
            
        Returns:
            Task object.
        """
        pass
    
    @abstractmethod
    def create_task(self, task: Task) -> str:
        """Create a new task.
        
        Args:
            task: Task object to create.
            
        Returns:
            The ID of the created task.
        """
        pass
    
    @abstractmethod
    def update_task(self, task: Task) -> bool:
        """Update an existing task.
        
        Args:
            task: Task object with updated information.
            
        Returns:
            True if update was successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def delete_task(self, task_id: str) -> bool:
        """Delete a task.
        
        Args:
            task_id: The ID of the task to delete.
            
        Returns:
            True if deletion was successful, False otherwise.
        """
        pass