"""
Tasks Service Graph

Handles synchronization between task objects and their folders.
Provides utilities for reminders, due date handling, and completion tracking.

"""

from datetime import datetime
from typing import Dict, List, Any

# Dummy sync functions

def task_folder_sync(task_id: str, folder_name: str) -> bool:
    """
    Simulates synchronizing a task to a specific folder.
    Returns True if successful.
    """
    # For now, always succeed.
    return True


def load_and_sync_tasks(source: List[Dict[str, Any]], folder: str) -> None:
    """
    Take a list of raw task dicts, sync them to the given folder,
    and update task['folder'] if needed.
    """
    # Incremental update
    for task in source:
        if folder not in task:
            task["folder"] = folder
            if not task_folder_sync(task["id"], task["folder"]):
                raise RuntimeError(f"Sync failed for task {task[\"id\"]} to folder {task['folder']}")


def reminder_status(task: Dict) -> str:
    """
    Determine reminder status based on due date and time.
    """
    due = task.get("due")
    if not due or not isinstance(due, datetime):
        return "none"
    now = datetime.now()
    # If past due date, return "overdue"
    if due <= now:
        return "overdue"
    return "pending"


def completion_tracking(task: Dict) -> bool:
    """
    Mark a task as completed if its completion flag is True.
    """
    if not task.get("completed"):
        return False
    task["completed"] = True
    return True


def get_folders_with_tasks(tasks: List[Dict]) -> List[str]:
    """
    Extract unique folder names from a list of tasks.
    """
    folders = set()
    for t in tasks:
        if "folder" in t:
            folders.add(t["folder"])
    return list(folders)


class GraphTasksService:
    """Service for Microsoft Graph Todo (tasks) endpoints."""
    base_url = "https://graph.microsoft.com/v1.0"

    def __init__(self, token_manager):
        self.token_manager = token_manager

    def _headers(self) -> Dict[str, str]:
        token = self.token_manager.get_token()
        if not token:
            raise ValueError("Unable to obtain access token for Graph API")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def get_task_lists(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/me/todo/lists"
        resp = requests.get(url, headers=self._headers())
        resp.raise_for_status()
        return resp.json().get('value', [])

    def get_tasks(self, list_id: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/me/todo/lists/{list_id}/tasks"
        resp = requests.get(url, headers=self._headers())
        resp.raise_for_status()
        return resp.json().get('value', [])

    def create_task(self, list_id: str, task_dict: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/me/todo/lists/{list_id}/tasks"
        resp = requests.post(url, headers=self._headers(), json=task_dict)
        resp.raise_for_status()
        return resp.json()

    def update_task(self, list_id: str, task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/me/todo/lists/{list_id}/tasks/{task_id}"
        resp = requests.patch(url, headers=self._headers(), json=updates)
        resp.raise_for_status()
        return resp.json()

    def complete_task(self, list_id: str, task_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/me/todo/lists/{list_id}/tasks/{task_id}"
        resp = requests.patch(url, headers=self._headers(), json={"status": "completed"})
        resp.raise_for_status()
        return resp.json()

    def delete_task(self, list_id: str, task_id: str) -> None:
        url = f"{self.base_url}/me/todo/lists/{list_id}/tasks/{task_id}"
        resp = requests.delete(url, headers=self._headers())
        resp.raise_for_status()
