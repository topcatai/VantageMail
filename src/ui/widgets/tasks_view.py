"""
widgets/tasks_view.py

Provides a simple UI view for the tasks service.
Integrates tasks (graph) functionality.
"""

# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime
# Import graph functions from services.tasks.graph (assuming module exists)
from services.tasks.graph import (
    load_and_sync_tasks,
    get_folders_with_tasks,
    reminder_status,
    completion_tracking,
    task_folder_sync,
)


@dataclass
class TaskWidget:
    task_id: str | int
    description: str
    due: datetime | None
    completed: bool
    folder: str
    reminder: str
    status: str


def build_widget(task: Dict) -> TaskWidget:
    task_id = task["id"]
    description = task.get("description", "")
    due = task["due"]
    if not isinstance(due, (int, str)):
        due = None
    completed = task["completed"]
    folder = task.get("folder", "root")
    reminder = reminder_status(task)
    return TaskWidget(
        task_id=task_id,
        description=description,
        due=due,
        completed=completed,
        folder=folder,
        reminder=reminder,
        # placeholder status, will be set later
        status="working",
    )


def sync_and_render(
    files: List[Dict[str, Any]],
    folder: str = "root",
) -> List[TaskWidget]:
    """
    Load tasks, sync them to folder, and build UI widgets.
    """
    # Initial empty tasks list
    task_list: List[Dict] = []
    for f in files:
        task_list.extend(f.get("tasks", []) if isinstance(f.get("tasks"), list) else [])
    load_and_sync_tasks(task_list, folder)  # type: ignore [arg-type]

    # Get folder list
    folders = get_folders_with_tasks(task_list)  # type: ignore [arg-type]
    # Actually we'll compute:
    _ = get_folders_from_file(task_list)  # dummy, use function imported from graph

    render_list = [build_widget(t) for t in task_list]

    return render_list

# UI widget for displaying tasks
from PyQt6.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout
from PyQt6.QtCore import Qt

class TasksViewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tasks")
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Task ID", "Description", "Due", "Folder", "Status"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

    def load_tasks(self, tasks: List[TaskWidget]):
        self.table.setRowCount(len(tasks))
        for row, task in enumerate(tasks):
            self.table.setItem(row, 0, QTableWidgetItem(str(task.task_id)))
            self.table.setItem(row, 1, QTableWidgetItem(task.description))
            due_str = task.due.isoformat() if isinstance(task.due, datetime) else str(task.due) if task.due else ""
            self.table.setItem(row, 2, QTableWidgetItem(due_str))
            self.table.setItem(row, 3, QTableWidgetItem(task.folder))
            self.table.setItem(row, 4, QTableWidgetItem(task.status))
        self.table.resizeColumnsToContents()


def display_widget(widget: TaskWidget) -> None:
    """
    Simple display function.
    """
    # Placeholder: print state
    pass