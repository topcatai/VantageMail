# -*- coding: utf-8 -*-
import pytest
from storage.database import Database

def test_drafts_database_operations_no_duplication():
    db = Database(db_path=":memory:")
    email = "user@example.com"
    folder = "Drafts"
    draft_id = "draft-12345"
    
    # Initial save of draft
    draft_msg = {
        "id": draft_id,
        "subject": "Hello Draft",
        "body": "<p>Initial body</p>",
        "to": ["rec@example.com"],
        "cc": []
    }
    db.save_cached_email(email, folder, draft_id, draft_msg)
    
    # Retrieve and check
    cached = db.get_cached_emails(email, folder)
    assert len(cached) == 1
    assert cached[0]["id"] == draft_id
    assert cached[0]["subject"] == "Hello Draft"
    
    # Modify draft and save (should overwrite, no duplication)
    updated_msg = dict(draft_msg)
    updated_msg["subject"] = "Updated Draft"
    updated_msg["body"] = "<p>Updated body</p>"
    db.save_cached_email(email, folder, draft_id, updated_msg)
    
    cached = db.get_cached_emails(email, folder)
    assert len(cached) == 1  # Verify count is still 1 (no duplication)
    assert cached[0]["subject"] == "Updated Draft"
    
    # Send draft and delete it
    db.delete_cached_email(email, folder, draft_id)
    assert len(db.get_cached_emails(email, folder)) == 0

def test_workers_execution():
    from PyQt6.QtCore import QCoreApplication
    from ui.main_window import MainWindowWorker
    from ui.widgets.email_composer import ComposerWorker

    app = QCoreApplication.instance() or QCoreApplication([])
    
    # Test MainWindowWorker
    test_workers_execution.mw_res = None
    def fn_mw():
        return "mw_success"
    worker_mw = MainWindowWorker(fn_mw)
    worker_mw.finished.connect(lambda r: setattr(test_workers_execution, "mw_res", r))
    worker_mw.run()
    assert test_workers_execution.mw_res == "mw_success"
    
    # Test ComposerWorker
    test_workers_execution.comp_res = None
    def fn_comp():
        return "comp_success"
    worker_comp = ComposerWorker(fn_comp)
    worker_comp.finished.connect(lambda r: setattr(test_workers_execution, "comp_res", r))
    worker_comp.run()
    assert test_workers_execution.comp_res == "comp_success"

def test_drafts_badge_updating():
    from PyQt6.QtWidgets import QApplication, QTreeWidgetItem
    from PyQt6.QtCore import Qt
    from unittest.mock import MagicMock
    from ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])

    # Mock the minimum attributes needed for MainWindow
    window = MagicMock(spec=MainWindow)
    window._current_account_email = "test@example.com"
    window.account_manager = MagicMock()
    
    # Setup mock DB returning 3 drafts
    db = MagicMock()
    db.get_cached_emails.return_value = [{"id": "d1"}, {"id": "d2"}, {"id": "d3"}]
    window.account_manager._db = db

    # Setup tree item
    header_item = QTreeWidgetItem(["test@example.com"])
    drafts_item = QTreeWidgetItem(["Drafts"])
    drafts_item.setData(0, Qt.ItemDataRole.UserRole, "Drafts")
    header_item.addChild(drafts_item)

    window._account_tree_items = {"test@example.com": header_item}

    # Call the actual badge refresh logic from MainWindow
    MainWindow._refresh_folder_badge(window, "Drafts")

    # Assert that the text is updated to "Drafts  (3)"
    assert drafts_item.text(0) == "Drafts  (3)"

def test_keypress_delete_and_close():
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QKeyEvent, QCloseEvent
    from PyQt6.QtCore import Qt, QEvent
    from unittest.mock import MagicMock
    from ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])

    class MockMainWindow(MainWindow):
        def __init__(self):
            from PyQt6.QtWidgets import QMainWindow
            QMainWindow.__init__(self)
            self._open_windows = [MagicMock(), MagicMock()]
            self._delete_selected = MagicMock()
            self.message_table = MagicMock()

    window = MockMainWindow()

    # Call closeEvent
    window.closeEvent(QCloseEvent())
    # Verify that tracked windows closed
    for w in window._open_windows:
        w.close.assert_called_once()

    # Setup table mock with focus
    window.message_table.hasFocus.return_value = True

    # Simulate key event for Delete
    key_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Delete, Qt.KeyboardModifier.NoModifier)
    window.keyPressEvent(key_event)
    
    # Assert delete was called
    window._delete_selected.assert_called_once()

def test_window_tracker_pruning():
    from unittest.mock import MagicMock
    from ui.main_window import MainWindow
    
    # We will instantiate a mock MainWindow instance
    window = MagicMock(spec=MainWindow)
    window._open_windows = []
    
    # 1. Valid visible window
    w_visible = MagicMock()
    w_visible.isVisible.return_value = True
    
    # 2. Valid invisible window (e.g. hidden)
    w_hidden = MagicMock()
    w_hidden.isVisible.return_value = False
    
    # 3. Destroyed window (raising RuntimeError)
    w_destroyed = MagicMock()
    w_destroyed.isVisible.side_effect = RuntimeError("wrapped C/C++ object of type SearchWindow has been deleted")
    
    window._open_windows = [w_visible, w_hidden, w_destroyed]
    
    # Call the actual pruning code on the mock object
    MainWindow._prune_open_windows(window)
    
    # Verify that:
    # - w_visible is kept because it's visible (isVisible() returns True)
    # - w_hidden is NOT kept because isVisible() returns False
    # - w_destroyed is pruned because it raised RuntimeError
    assert window._open_windows == [w_visible]
    
    # Let's test safe removal as well
    # Reset
    window._open_windows = [w_visible, w_destroyed]
    
    # Map mock method to the real one so _safe_remove_window can call it
    window._prune_open_windows = lambda: MainWindow._prune_open_windows(window)
    
    # Call safe removal of w_visible
    MainWindow._safe_remove_window(window, w_visible)
    assert window._open_windows == [] # w_destroyed is pruned, w_visible is removed
    
    # Call safe removal of already destroyed window (should prune and do nothing else)
    window._open_windows = [w_destroyed]
    MainWindow._safe_remove_window(window, w_destroyed)
    assert window._open_windows == []



