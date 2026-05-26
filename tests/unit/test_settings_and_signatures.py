# -*- coding: utf-8 -*-
import pytest
from PyQt6.QtCore import QSettings, QCoreApplication
from PyQt6.QtWidgets import QApplication
from ui.widgets.settings_dialog import SettingsDialog
from ui.widgets.email_composer import EmailComposerWidget
from unittest.mock import MagicMock

def test_settings_dialog_save():
    app = QApplication.instance() or QApplication([])
    settings = QSettings("TakshiqSoftLabs", "VantageMail")
    
    # Back up settings
    backup = {}
    keys = [
        "appearance/theme", "appearance/reading_pane", "appearance/font_size",
        "sync/interval", "sync/limit", "sync/mark_read_delay",
        "notifications/tray_enabled", "notifications/new_mail_enabled", "notifications/duration",
        "signature/text", "signature/use_new", "signature/use_reply", "signature/use_forward",
        "composer/font_family", "composer/font_size", "composer/reply_action",
        "startup/show_splash", "startup/open_last_folder"
    ]
    for key in keys:
        if settings.contains(key):
            backup[key] = settings.value(key)

    try:
        # Construct dialog
        dialog = SettingsDialog()
        
        # Modify some values in dialog controls
        dialog.theme_combo.setCurrentText("Light")
        dialog.layout_combo.setCurrentText("Horizontal")
        dialog.font_size_spin.setValue(18)
        dialog.sync_interval_combo.setCurrentText("30 s")
        dialog.sync_limit_combo.setCurrentText("200")
        dialog.mark_read_spin.setValue(10)
        dialog.tray_checkbox.setChecked(False)
        dialog.notify_checkbox.setChecked(False)
        dialog.notify_duration_spin.setValue(12)
        dialog.sig_text.setHtml("<p>My Custom Test Signature</p>")
        dialog.sig_new_chk.setChecked(True)
        dialog.sig_reply_chk.setChecked(False)
        dialog.sig_forward_chk.setChecked(True)
        dialog.comp_font_combo.setCurrentText("Courier New")
        dialog.comp_size_combo.setCurrentText("14")
        dialog.reply_action_combo.setCurrentText("Reply All")
        dialog.splash_checkbox.setChecked(False)
        dialog.last_folder_checkbox.setChecked(False)
        
        # Save settings
        dialog.save_settings()
        
        # Verify settings saved in QSettings
        assert settings.value("appearance/theme") == "Light"
        assert settings.value("appearance/reading_pane") == "Horizontal"
        assert int(settings.value("appearance/font_size")) == 18
        assert settings.value("sync/interval") == "30 s"
        assert settings.value("sync/limit") == "200"
        assert int(settings.value("sync/mark_read_delay")) == 10
        assert settings.value("notifications/tray_enabled", type=bool) is False
        assert settings.value("notifications/new_mail_enabled", type=bool) is False
        assert int(settings.value("notifications/duration")) == 12
        assert "My Custom Test Signature" in settings.value("signature/text")
        assert settings.value("signature/use_new", type=bool) is True
        assert settings.value("signature/use_reply", type=bool) is False
        assert settings.value("signature/use_forward", type=bool) is True
        assert settings.value("composer/font_family") == "Courier New"
        assert settings.value("composer/font_size") == "14"
        assert settings.value("composer/reply_action") == "Reply All"
        assert settings.value("startup/show_splash", type=bool) is False
        assert settings.value("startup/open_last_folder", type=bool) is False

    finally:
        # Restore settings
        settings.clear()
        for key, val in backup.items():
            settings.setValue(key, val)
        settings.sync()

def test_composer_signature_insertion():
    app = QApplication.instance() or QApplication([])
    settings = QSettings("TakshiqSoftLabs", "VantageMail")
    
    # Back up signature settings
    backup = {}
    keys = ["signature/text", "signature/use_new", "signature/use_reply", "signature/use_forward"]
    for key in keys:
        if settings.contains(key):
            backup[key] = settings.value(key)

    try:
        # Set test signature settings
        settings.setValue("signature/text", "Best regards, Tester")
        settings.setValue("signature/use_new", True)
        settings.setValue("signature/use_reply", True)
        settings.setValue("signature/use_forward", False)
        settings.sync()

        mock_provider = MagicMock()
        mock_provider.account_email = "test@example.com"
        mock_account_mgr = MagicMock()
        mock_account_mgr.get_accounts.return_value = [{"email": "test@example.com"}]
        mock_account_mgr._active_email = "test@example.com"
        mock_account_mgr._db = MagicMock()

        # Case 1: new email, use_new=True -> should append signature
        composer_new = EmailComposerWidget(
            mail_service=mock_provider,
            account_manager=mock_account_mgr,
            mode='new'
        )
        assert "Best regards, Tester" in composer_new.body_edit.toHtml()

        # Case 2: reply, use_reply=True -> should append signature
        composer_reply = EmailComposerWidget(
            mail_service=mock_provider,
            account_manager=mock_account_mgr,
            body="<div>Original Message</div>",
            mode='reply'
        )
        body_html = composer_reply.body_edit.toHtml()
        assert "Original Message" in body_html
        assert "Best regards, Tester" in body_html

        # Case 3: forward, use_forward=False -> should NOT append signature
        composer_fwd = EmailComposerWidget(
            mail_service=mock_provider,
            account_manager=mock_account_mgr,
            body="<div>Forwarded content</div>",
            mode='forward'
        )
        body_html = composer_fwd.body_edit.toHtml()
        assert "Forwarded content" in body_html
        assert "Best regards, Tester" not in body_html

    finally:
        # Restore signature settings
        settings.clear()
        for key, val in backup.items():
            settings.setValue(key, val)
        settings.sync()

def test_delete_message_bypasses_remote_for_local_folders():
    from PyQt6.QtWidgets import QApplication, QTableWidget, QTableWidgetItem
    from PyQt6.QtCore import Qt
    from unittest.mock import MagicMock
    from ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])

    class MockMainWindowForDelete(MainWindow):
        def __init__(self):
            from PyQt6.QtWidgets import QMainWindow
            QMainWindow.__init__(self)
            self._threads = []
            self._workers = []
            self.statusBar = MagicMock()
            
            # Setup table
            self.message_table = QTableWidget(1, 4)
            item = QTableWidgetItem("Draft Message")
            item.setData(Qt.ItemDataRole.UserRole, "draft-123")
            self.message_table.setItem(0, 1, item)
            self.message_table.selectRow(0)
            
            self._current_folder_id = "Drafts"
            self._current_account_email = "test@example.com"
            self.account_manager = MagicMock()
            self.account_manager._active_email = "test@example.com"
            self.account_manager._db = MagicMock()

    window = MockMainWindowForDelete()
    mock_provider = MagicMock()
    window.account_manager.get_active_provider.return_value = mock_provider

    # Mock _run_in_thread to execute synchronously
    def mock_run_in_thread(fn, callback, *args, **kwargs):
        res = fn()
        callback(res)
        return MagicMock(), MagicMock()

    window._run_in_thread = mock_run_in_thread

    # Test Drafts deletion (should NOT call provider.delete_message)
    window._current_folder_id = "Drafts"
    window._delete_selected()
    assert mock_provider.delete_message.call_count == 0
    window.account_manager._db.delete_cached_email.assert_called_once_with("test@example.com", "Drafts", "draft-123")

    # Test standard folder deletion (should call provider.delete_message)
    window.account_manager._db.delete_cached_email.reset_mock()
    mock_provider.delete_message.reset_mock()
    window._current_folder_id = "INBOX"
    
    # Re-insert row
    window.message_table.setRowCount(0)
    window.message_table.insertRow(0)
    item = QTableWidgetItem("Inbox Message")
    item.setData(Qt.ItemDataRole.UserRole, "msg-456")
    window.message_table.setItem(0, 1, item)
    window.message_table.selectRow(0)
    
    window._delete_selected()
    mock_provider.delete_message.assert_called_once_with("msg-456", "INBOX")
    window.account_manager._db.delete_cached_email.assert_called_once_with("test@example.com", "INBOX", "msg-456")

def test_search_window():
    from PyQt6.QtWidgets import QApplication
    from storage.database import Database
    from ui.widgets.search_window import SearchWindow
    from unittest.mock import MagicMock
    
    app = QApplication.instance() or QApplication([])
    
    # 1. Test database search functionality
    db = Database(db_path=":memory:")
    acc1 = "user1@test.com"
    acc2 = "user2@test.com"
    
    msg1 = {
        "id": "1",
        "subject": "Urgent review required",
        "body": "Hello, please review this draft before tomorrow.",
        "sender": "sender1@test.com",
        "date": "2026-05-26T12:00:00"
    }
    msg2 = {
        "id": "2",
        "subject": "Weekly meeting minutes",
        "body": "Meeting went well. Review attachment for notes.",
        "sender": "sender2@test.com",
        "date": "2026-05-26T13:00:00"
    }
    
    db.save_cached_email(acc1, "INBOX", "1", msg1)
    db.save_cached_email(acc2, "Inbox", "2", msg2)
    
    # Search for "Review" (should match msg1 in subject & body, and msg2 in body)
    res = db.search_emails([acc1, acc2], "review")
    assert len(res) == 2
    
    # Search in acc1 only for "meeting" (should be 0 matches)
    res_acc1 = db.search_emails([acc1], "meeting")
    assert len(res_acc1) == 0
    
    # Search for "Urgent" (should match msg1 only)
    res_urgent = db.search_emails([acc1, acc2], "urgent")
    assert len(res_urgent) == 1
    assert res_urgent[0]["id"] == "1"

    # 2. Test SearchWindow widget initialization
    mock_account_mgr = MagicMock()
    mock_account_mgr.get_accounts.return_value = [
        {"email": acc1, "provider": "IMAP"},
        {"email": acc2, "provider": "IMAP"}
    ]
    mock_account_mgr._db = db
    
    mock_main_window = MagicMock()
    mock_main_window._open_windows = []
    
    search_win = SearchWindow(mock_account_mgr, mock_main_window, initial_query="review")
    
    # Verify checkboxes populated
    assert len(search_win.account_checkboxes) == 2
    assert search_win.account_checkboxes[0].text() == acc1
    assert search_win.account_checkboxes[1].text() == acc2
    
    # Verify results populated in subject and body groups
    assert search_win.root_subject.childCount() == 1  # msg1 matches "review" in subject
    assert search_win.root_body.childCount() == 2     # msg1 & msg2 match "review" in body
    
    # Clean up
    search_win.close()

def test_fts_indexing():
    from storage.database import Database
    
    # Initialize in-memory database
    db = Database(db_path=":memory:")
    
    # 1. Verify FTS virtual table exists (if FTS is available)
    if not db.fts_available:
        pytest.skip("FTS5 is not available on this system's SQLite")
        
    acc = "test@example.com"
    folder = "INBOX"
    
    msg_fts1 = {
        "id": "101",
        "subject": "FTS5 Project Update",
        "body": "This is a message about full-text search indexing.",
        "sender": "boss@example.com",
        "date": "2026-05-26T12:00:00"
    }
    
    # Save email and verify index population
    db.save_cached_email(acc, folder, "101", msg_fts1)
    
    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM emails_fts WHERE id='101'")
    row = cursor.fetchone()
    assert row is not None
    # row cols: id, account_email, folder_id, subject, body
    assert row[0] == "101"
    assert row[1] == acc
    assert row[2] == folder
    assert row[3] == "FTS5 Project Update"
    assert row[4] == "This is a message about full-text search indexing."
    
    # Test FTS5 search (exact case-insensitive, prefix, multi-word)
    res = db.search_emails([acc], "fts5")
    assert len(res) == 1
    assert res[0]["id"] == "101"
    
    res = db.search_emails([acc], "proj")
    assert len(res) == 1
    
    res = db.search_emails([acc], "search index")
    assert len(res) == 1
    
    # 2. Test deletion
    db.delete_cached_email(acc, folder, "101")
    cursor.execute("SELECT * FROM emails_fts WHERE id='101'")
    assert cursor.fetchone() is None
    
    # Verify search no longer returns it
    res = db.search_emails([acc], "fts5")
    assert len(res) == 0
    
    # 3. Test fallback logic when fts_available is simulated as False
    db.fts_available = False
    # Re-save email (only goes to emails table, not emails_fts because fts_available is False)
    db.save_cached_email(acc, folder, "102", {
        "id": "102",
        "subject": "Fallback search test",
        "body": "Using json_extract now.",
        "sender": "boss@example.com",
        "date": "2026-05-26T12:00:00"
    })
    
    # Query should still find it using fallback json_extract
    res_fallback = db.search_emails([acc], "fallback")
    assert len(res_fallback) == 1
    assert res_fallback[0]["id"] == "102"

