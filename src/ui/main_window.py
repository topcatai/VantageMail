# -*- coding: utf-8 -*-
from PyQt6.QtGui import QAction, QIcon, QColor, QBrush, QFont
from PyQt6.QtWidgets import (
    QMainWindow, QToolBar, QSplitter,
    QTreeWidget, QTreeWidgetItem, QTableWidget,
    QTableWidgetItem, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QHeaderView,
    QLineEdit, QPushButton, QMenu, QMessageBox
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal, QObject
from ui.widgets.account_switcher import AccountSwitcher
from ui.widgets.email_composer import EmailComposerWidget
from ui.widgets.add_account_wizard import AddAccountWizard
from storage.sync_utils import sync_folder_messages
from utils.logger import log_info, log_error
from ui.widgets.settings_dialog import SettingsDialog
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication

DARK_THEME = """
QMainWindow {
    background-color: #1e1e1e;
}
QToolBar {
    background-color: #2d2d2d;
    border-bottom: 1px solid #3c3c3c;
    spacing: 5px;
}
QToolButton {
    background-color: #3e3e42;
    color: #ffffff;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 4px 8px;
}
QToolButton:hover {
    background-color: #505054;
}
QTreeWidget {
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #3c3c3c;
}
QTreeWidget::item:hover {
    background-color: #2d2d2d;
}
QTreeWidget::item:selected {
    background-color: #007acc;
    color: #ffffff;
}
QTableWidget {
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #3c3c3c;
    gridline-color: #3c3c3c;
}
QTableWidget::item:hover {
    background-color: #2d2d2d;
}
QTableWidget::item:selected {
    background-color: #007acc;
    color: #ffffff;
}
QHeaderView::section {
    background-color: #2d2d2d;
    color: #ffffff;
    border: 1px solid #3c3c3c;
    padding: 4px;
}
QLineEdit {
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #3c3c3c;
    border-radius: 3px;
    padding: 3px;
}
QPushButton {
    background-color: #3e3e42;
    color: #ffffff;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 4px 8px;
}
QPushButton:hover {
    background-color: #505054;
}
QStatusBar {
    background-color: #007acc;
    color: #ffffff;
}
"""

LIGHT_THEME = """
QMainWindow {
    background-color: #f3f3f3;
}
QToolBar {
    background-color: #e6e6e6;
    border-bottom: 1px solid #cccccc;
    spacing: 5px;
}
QToolButton {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #cccccc;
    border-radius: 3px;
    padding: 4px 8px;
}
QToolButton:hover {
    background-color: #f0f0f0;
}
QTreeWidget {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #cccccc;
}
QTreeWidget::item:hover {
    background-color: #f0f0f0;
}
QTreeWidget::item:selected {
    background-color: #007acc;
    color: #ffffff;
}
QTableWidget {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #cccccc;
    gridline-color: #cccccc;
}
QTableWidget::item:hover {
    background-color: #f0f0f0;
}
QTableWidget::item:selected {
    background-color: #007acc;
    color: #ffffff;
}
QHeaderView::section {
    background-color: #e6e6e6;
    color: #333333;
    border: 1px solid #cccccc;
    padding: 4px;
}
QLineEdit {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #cccccc;
    border-radius: 3px;
    padding: 3px;
}
QPushButton {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #cccccc;
    border-radius: 3px;
    padding: 4px 8px;
}
QPushButton:hover {
    background-color: #f0f0f0;
}
QStatusBar {
    background-color: #007acc;
    color: #ffffff;
}
"""

class MainWindowWorker(QObject):
    finished = pyqtSignal(object)
    error    = pyqtSignal(str)
    progress = pyqtSignal(object)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            has_progress = False
            try:
                import inspect
                sig = inspect.signature(self._fn)
                if 'progress_callback' in sig.parameters:
                    has_progress = True
            except Exception:
                pass

            if has_progress:
                res = self._fn(*self._args, progress_callback=lambda data: self.progress.emit(data), **self._kwargs)
            else:
                res = self._fn(*self._args, **self._kwargs)
            self.finished.emit(res)
        except Exception as e:
            from utils.logger import log_error
            log_error(f"Worker thread error running {self._fn.__name__ if hasattr(self._fn, '__name__') else str(self._fn)}: {e}", exc_info=True)
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self, account_manager, parent=None, tray=None):
        super().__init__(parent)
        self.account_manager = account_manager
        self._tray = tray
        self.setWindowTitle("Vantage Mail")
        import os
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "icons_Vantage Mail", "Vantage white_Logo.png"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.resize(1280, 800)
        self._threads = []
        self._open_windows = []
        self._current_folder_id = None
        self._current_account_email = None
        self._badge_in_flight = set()
        self._sync_in_flight = set()
        self._folder_message_counts = {}

        # ── Auto-refresh timer ──────────────────────────────────────────
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._auto_refresh)

        # ── 3-second auto-mark-as-read timer ─────────────────────────────
        self._read_timer = QTimer(self)
        self._read_timer.setSingleShot(True)
        self._read_timer.timeout.connect(self._mark_current_message_as_read)
        self._pending_read_msg_id = None
        self._pending_read_row = -1
        self._pending_read_folder_id = None
        self._pending_read_account_email = None

        # ── Toolbar ──────────────────────────────────────────────────────
        toolbar = QToolBar("Main")
        self.addToolBar(toolbar)



        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search messages...")
        self.search_bar.setMinimumWidth(200)
        self.search_bar.returnPressed.connect(self._on_search)
        toolbar.addWidget(self.search_bar)
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._on_search)
        toolbar.addWidget(search_btn)
        toolbar.addSeparator()

        act_new     = QAction("New Email", self)
        act_reply   = QAction("Reply",     self)
        act_forward = QAction("Forward",   self)
        act_delete  = QAction("Delete",    self)
        act_add_acc = QAction("Add Account", self)
        act_export_eml = QAction("Export EML", self)
        act_export_csv = QAction("Export CSV", self)
        self.act_layout  = QAction("Vertical View", self)
        self.act_layout.setCheckable(True)
        act_logs    = QAction("Logs", self)
        act_settings = QAction("Settings", self)

        act_new.triggered.connect(self._compose_new)
        act_reply.triggered.connect(self._reply_selected)
        act_forward.triggered.connect(self._forward_selected)
        act_delete.triggered.connect(self._delete_selected)
        act_add_acc.triggered.connect(self._launch_add_account_wizard)
        act_export_eml.triggered.connect(self._export_selected_to_eml)
        act_export_csv.triggered.connect(self._export_to_csv)
        self.act_layout.toggled.connect(self._toggle_layout)
        act_logs.triggered.connect(self._open_logs)
        act_settings.triggered.connect(self._open_settings)

        toolbar.addActions([act_new, act_reply, act_forward, act_delete, act_add_acc, act_export_eml, act_export_csv, self.act_layout, act_logs, act_settings])

        # ── Three-pane layout ────────────────────────────────────────────
        outer = QSplitter(Qt.Orientation.Horizontal)

        # Folder pane
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderLabel("Folders")
        self.folder_tree.setMinimumWidth(180)
        self.folder_tree.itemClicked.connect(self._on_folder_clicked)

        # Message list + reading pane (vertical split)
        self.inner_splitter = QSplitter(Qt.Orientation.Vertical)

        self.message_table = QTableWidget(0, 4)
        self.message_table.setHorizontalHeaderLabels(["📎", "From", "Subject", "Date"])
        self.message_table.setColumnWidth(0, 24)
        self.message_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Fixed)
        self.message_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch)
        self.message_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self.message_table.setSelectionMode(
            QTableWidget.SelectionMode.ExtendedSelection)
        self.message_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        self.message_table.itemClicked.connect(self._on_message_clicked)
        self.message_table.itemDoubleClicked.connect(self._on_message_double_clicked)
        self.message_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.message_table.customContextMenuRequested.connect(self._show_context_menu)

        # Delete shortcut when message table has focus
        from PyQt6.QtGui import QShortcut, QKeySequence
        self._delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self.message_table)
        self._delete_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        self._delete_shortcut.activated.connect(self._delete_selected)

        # Container for reading pane and attachment bar
        self.reading_pane_container = QWidget()
        self.reading_pane_container.setStyleSheet("background-color: #1e1e1e;")
        reading_layout = QVBoxLayout(self.reading_pane_container)
        reading_layout.setContentsMargins(0, 0, 0, 0)
        reading_layout.setSpacing(0)
        
        # Attachment Bar (hidden by default)
        self.attachment_bar = QWidget()
        self.attachment_bar.setStyleSheet("background-color: #252526; border-bottom: 1px solid #3c3c3c;")
        self.attachment_bar.setVisible(False)
        self.attachment_bar_layout = QHBoxLayout(self.attachment_bar)
        self.attachment_bar_layout.setContentsMargins(10, 4, 10, 4)
        
        self.attachment_label = QLabel("📎 Attachments:")
        self.attachment_label.setStyleSheet("color: #cccccc; font-weight: bold;")
        self.attachment_bar_layout.addWidget(self.attachment_label)
        self.attachment_bar_layout.addStretch()
        
        self.attachments_buttons_container = QWidget()
        self.attachments_buttons_layout = QHBoxLayout(self.attachments_buttons_container)
        self.attachments_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.attachments_buttons_layout.setSpacing(5)
        self.attachment_bar_layout.addWidget(self.attachments_buttons_container)

        self.reading_pane = QWebEngineView()
        self.reading_pane.setStyleSheet("background-color: #1e1e1e;")
        self.reading_pane.setHtml("<body style='background:#1e1e1e;color:#ffffff;'><p>Select a message to read it.</p></body>")

        reading_layout.addWidget(self.attachment_bar)
        reading_layout.addWidget(self.reading_pane)

        self.inner_splitter.addWidget(self.message_table)
        self.inner_splitter.addWidget(self.reading_pane_container)
        self.inner_splitter.setSizes([250, 550])

        outer.addWidget(self.folder_tree)
        outer.addWidget(self.inner_splitter)
        outer.setSizes([200, 1080])

        self.main_layout = outer
        self._apply_settings()

        # ── Status bar ───────────────────────────────────────────────────
        self.statusBar().showMessage("Ready")

        # ── Check accounts on startup ───────────────────────────────────
        if not account_manager.get_accounts():
            self.no_accounts_label = QLabel("No accounts configured. Click 'Add Account' in the toolbar to get started.")
            self.no_accounts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.no_accounts_label.setStyleSheet("font-size: 14px; color: #888888; background-color: #1e1e1e;")
            self.setCentralWidget(self.no_accounts_label)
        else:
            self.setCentralWidget(self.main_layout)
            accounts = self.account_manager.get_accounts()
            if accounts:
                self._current_account_email = accounts[0]["email"]
            QTimer.singleShot(100, self._load_folders)

    # ── Slots ─────────────────────────────────────────────────────────────
    def _stop_read_timer(self):
        if hasattr(self, '_read_timer'):
            self._read_timer.stop()
        self._pending_read_msg_id = None
        self._pending_read_row = -1
        self._pending_read_folder_id = None
        self._pending_read_account_email = None

    def _mark_current_message_as_read(self):
        msg_id = self._pending_read_msg_id
        row = self._pending_read_row
        folder_id = self._pending_read_folder_id
        acc_email = self._pending_read_account_email

        self._stop_read_timer()

        if not msg_id or row < 0 or not folder_id or not acc_email:
            return

        found_row = -1
        for r in range(self.message_table.rowCount()):
            cell = self.message_table.item(r, 1)
            if cell and cell.data(Qt.ItemDataRole.UserRole) == msg_id:
                found_row = r
                break

        if found_row == -1:
            return

        first_cell = self.message_table.item(found_row, 1)
        if not (first_cell and first_cell.font().bold()):
            return

        provider = self.account_manager.get_provider(acc_email)
        db = self.account_manager._db
        if not provider:
            return

        def do_mark():
            try:
                provider.mark_read(msg_id, True, folder_id)
                cached_msg = db.get_cached_email(acc_email, folder_id, msg_id)
                if cached_msg:
                    cached_msg['is_read'] = True
                    db.save_cached_email(acc_email, folder_id, msg_id, cached_msg)
            except Exception as e:
                log_error(f"Error marking auto-read message {msg_id}: {e}")
            return True

        def on_complete(is_read):
            from PyQt6.QtGui import QFont, QColor, QBrush
            curr_row = -1
            for r in range(self.message_table.rowCount()):
                cell = self.message_table.item(r, 1)
                if cell and cell.data(Qt.ItemDataRole.UserRole) == msg_id:
                    curr_row = r
                    break
            if curr_row != -1:
                font = QFont()
                font.setBold(False)
                color = QColor('#aaaaaa')
                for col in range(1, 4):
                    cell = self.message_table.item(curr_row, col)
                    if cell:
                        cell.setFont(font)
                        cell.setForeground(QBrush(color))
            if self._current_folder_id == folder_id:
                self._refresh_folder_badge(folder_id)

        self._run_in_thread(do_mark, on_complete)

    def _prune_finished(self):
        alive_threads = []
        for t in self._threads:
            try:
                if t.isRunning():
                    alive_threads.append(t)
            except RuntimeError:
                pass
        self._threads = alive_threads

        alive_workers = []
        for w in getattr(self, '_workers', []):
            try:
                if hasattr(w, '_thread') and w._thread.isRunning():
                    alive_workers.append(w)
            except RuntimeError:
                pass
        self._workers = alive_workers

    def _run_in_thread(self, fn, callback, *args, **kwargs):
        worker = MainWindowWorker(fn, *args, **kwargs)
        thread = QThread()
        worker._thread = thread
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(callback)
        worker.finished.connect(thread.quit)
        worker.error.connect(lambda e: (self.statusBar().showMessage(f"Error: {e}"), log_error(f"THREAD ERROR: {e}")))
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._prune_finished)
        self._threads.append(thread)
        self._workers = getattr(self, '_workers', [])
        self._workers.append(worker)
        thread.start()
        log_info(f"Thread started for {fn.__name__ if hasattr(fn, '__name__') else str(fn)}")
        return thread, worker

    def _load_folders(self):
        log_info("_load_folders called")
        self.statusBar().showMessage("Loading folders...")
        self.folder_tree.clear()
        self._account_tree_items = {}

        accounts = self.account_manager.get_accounts()
        if not accounts:
            return

        # Pre-create all top-level items so they are in the tree in a consistent order
        for acc in accounts:
            email = acc["email"]
            header_item = QTreeWidgetItem([email])
            font = header_item.font(0)
            font.setBold(True)
            header_item.setFont(0, font)
            header_item.setForeground(0, QBrush(QColor("#4fc3f7")))
            self.folder_tree.addTopLevelItem(header_item)
            self._account_tree_items[email] = header_item

        # Launch thread for each account
        for acc in accounts:
            email = acc["email"]
            try:
                def load_task(e=email):
                    provider = self.account_manager.get_provider(e)
                    if provider:
                        return provider.fetch_folders()
                    return []

                self._run_in_thread(
                    load_task,
                    lambda folders, e=email: self._on_folders_loaded(e, folders)
                )
            except Exception as e:
                log_error(f"Error starting folder load for {email}: {e}")

    def _on_folders_loaded(self, email, folders):
        log_info(f"_on_folders_loaded: got {len(folders)} folders for {email}")
        header_item = self._account_tree_items.get(email)
        if not header_item:
            return

        # Clear existing children of this header
        for i in reversed(range(header_item.childCount())):
            header_item.removeChild(header_item.child(i))

        has_outbox = False
        has_drafts = False

        for f in folders:
            fid = f.get('id', '')
            name = f.get('display_name') or f.get('name', 'Unknown')
            unread = f.get('unread', 0)
            
            is_draft = fid.lower() == 'drafts' or fid.lower() == 'inbox.drafts' or 'draft' in fid.lower() or name.lower() == 'drafts' or 'draft' in name.lower()
            is_outbox = fid.lower() == 'outbox' or name.lower() == 'outbox'
            
            if is_draft:
                if has_drafts:
                    continue
                has_drafts = True
                fid = "Drafts"
                name = "Drafts"
            elif is_outbox:
                if has_outbox:
                    continue
                has_outbox = True
                fid = "Outbox"
                name = "Outbox"
                
            label = f"{name}  ({unread})" if unread > 0 else name
            child_item = QTreeWidgetItem([label])
            child_item.setData(0, Qt.ItemDataRole.UserRole, fid)
            header_item.addChild(child_item)

        # Add Outbox virtual folder if not present
        if not has_outbox:
            outbox_child = QTreeWidgetItem(["Outbox"])
            outbox_child.setData(0, Qt.ItemDataRole.UserRole, "Outbox")
            header_item.addChild(outbox_child)

        # Add Drafts virtual folder if not present
        if not has_drafts:
            drafts_child = QTreeWidgetItem(["Drafts"])
            drafts_child.setData(0, Qt.ItemDataRole.UserRole, "Drafts")
            header_item.addChild(drafts_child)

        self._refresh_folder_badge('Drafts', email)
        self._refresh_folder_badge('Outbox', email)

        # Only refresh the badge for the active inbox folder immediately.
        active_email = self.account_manager._active_email
        if email == active_email:
            for i in range(header_item.childCount()):
                child_item = header_item.child(i)
                fid = child_item.data(0, Qt.ItemDataRole.UserRole)
                if fid in ('INBOX', 'Inbox'):
                    self._refresh_folder_badge(fid, email)

        header_item.setExpanded(True)

        # Active account's Inbox/INBOX auto-expanded and selected
        active_email = self.account_manager._active_email
        if email == active_email:
            for i in range(header_item.childCount()):
                child_item = header_item.child(i)
                folder_id = child_item.data(0, Qt.ItemDataRole.UserRole)
                if folder_id == 'INBOX' or folder_id == 'Inbox':
                    self.folder_tree.setCurrentItem(child_item)
                    self._on_folder_clicked(child_item)
                    break

        self.statusBar().showMessage(f"Loaded folders for {email}")

    def _on_folder_clicked(self, item):
        self._stop_read_timer()
        parent = item.parent()
        if not parent:
            return  # clicked on account header node, not a folder

        acc_email = parent.text(0)
        folder_id = item.data(0, Qt.ItemDataRole.UserRole)
        if not folder_id:
            return

        self._current_folder_id = folder_id
        self._current_account_email = acc_email

        # Set active account in account_manager
        self.account_manager.set_active_account(acc_email)
        
        # Refresh folder badge on click
        self._refresh_folder_badge(folder_id, acc_email)


        self.search_bar.clear()

        # Clear reading pane (FIX 4)
        settings = QSettings("TakshiqSoftLabs", "VantageMail")
        theme = settings.value("appearance/theme", "Dark", type=str)
        bg = "#ffffff" if theme == "Light" else "#1e1e1e"
        fg = "#000000" if theme == "Light" else "#ffffff"
        font_size = settings.value("appearance/font_size", 13, type=int)
        self.reading_pane.setHtml(f"<body style='background:{bg};color:{fg};font-size:{font_size}pt;'><p>Select a message to read it.</p></body>")

        # Load first 100 from cache immediately (FIX 3)
        db = self.account_manager._db
        all_cached = db.get_cached_emails(acc_email, folder_id)
        self._folder_message_counts[(acc_email, folder_id)] = len(all_cached)
        first_batch = all_cached[:100]
        
        self._populate_message_table(first_batch)
        
        folder_display_name = item.text(0)
        if "  (" in folder_display_name:
            folder_display_name = folder_display_name.split("  (")[0]

        self.statusBar().showMessage(
            f"Showing {len(first_batch)} of {len(all_cached)} emails | Loading more...")

        # Step 2: After 2 second delay, append remaining (FIX 3)
        remaining = all_cached[100:]
        if remaining:
            QTimer.singleShot(2000, lambda: self._append_messages(remaining))
        else:
            self.statusBar().showMessage(f"{folder_display_name} — {len(first_batch)} emails (from cache) | Syncing...")

        # Step 3: After 3 second delay, sync with server (FIX 3)
        if folder_id not in ('Outbox', 'Drafts'):
            QTimer.singleShot(3000, lambda: self._sync_folder_background(acc_email, folder_id))
        else:
            folder_label = "local outbox" if folder_id == 'Outbox' else "local drafts"
            self.statusBar().showMessage(f"{folder_display_name} — {len(all_cached)} emails ({folder_label})")

    def _on_search(self):
        self._stop_read_timer()
        term = self.search_bar.text().strip()
        
        self._prune_open_windows()
        # Check if an existing SearchWindow is already open
        from ui.widgets.search_window import SearchWindow
        existing_search = None
        for w in self._open_windows:
            try:
                if isinstance(w, SearchWindow) and w.isVisible():
                    existing_search = w
                    break
            except RuntimeError:
                pass
                
        if existing_search:
            existing_search.search_input.setText(term)
            existing_search.perform_search()
            existing_search.raise_()
            existing_search.activateWindow()
        else:
            if not self._can_open_new_window():
                return
            window = SearchWindow(self.account_manager, self, initial_query=term)
            self._open_windows.append(window)
            window.destroyed.connect(lambda: self._safe_remove_window(window))
            window.show()

    def _sync_folder_background(self, acc_email, folder_id):
        if folder_id in ('Outbox', 'Drafts'):
            return
        if self._current_folder_id != folder_id or self._current_account_email != acc_email:
            return
        sync_key = (acc_email, folder_id)
        if sync_key in self._sync_in_flight:
            return
        self._sync_in_flight.add(sync_key)
        db = self.account_manager._db
        provider = self.account_manager.get_active_provider()
        
        def sync_task(progress_callback=None):
            wrapped_cb = None
            if progress_callback:
                wrapped_cb = lambda msgs: progress_callback((acc_email, folder_id, msgs))
            res = sync_folder_messages(provider, db, acc_email, folder_id, progress_callback=wrapped_cb)
            return (acc_email, folder_id, res)

        thread, worker = self._run_in_thread(
            sync_task,
            self._on_messages_loaded
        )
        worker.progress.connect(self._on_sync_progress)
        thread.finished.connect(lambda: self._sync_in_flight.discard(sync_key))

    def _on_sync_progress(self, data):
        acc_email, folder_id, messages = data
        if self._current_folder_id == folder_id and self._current_account_email == acc_email:
            self._populate_message_table(messages)
            self.statusBar().showMessage(f"Syncing folder: {folder_id} — {len(messages)} messages...")

    def _on_messages_loaded(self, data):
        acc_email, folder_id, messages = data
        if self._current_folder_id == folder_id and self._current_account_email == acc_email:
            self._populate_message_table(messages)
            self.statusBar().showMessage(f"Loaded {len(messages)} messages")
        if folder_id:
            self._refresh_folder_badge(folder_id, acc_email)
            count_key = (acc_email, folder_id)
            new_count = len(messages)
            prev_count = self._folder_message_counts.get(count_key)
            self._folder_message_counts[count_key] = new_count
            
            if prev_count is not None and new_count > prev_count:
                settings = QSettings("TakshiqSoftLabs", "VantageMail")
                tray_enabled = settings.value("notifications/tray_enabled", True, type=bool)
                new_mail_enabled = settings.value("notifications/new_mail_enabled", True, type=bool)
                if tray_enabled and new_mail_enabled and self._tray:
                    duration_sec = settings.value("notifications/duration", 5, type=int)
                    from PyQt6.QtWidgets import QSystemTrayIcon
                    
                    folder_name = folder_id
                    item = self.folder_tree.currentItem()
                    if item:
                        name = item.text(0)
                        if "  (" in name:
                            folder_name = name.split("  (")[0]
                        else:
                            folder_name = name
                    
                    self._tray.showMessage(
                        "Vantage Mail",
                        f"{new_count - prev_count} new message(s) in {folder_name}",
                        QSystemTrayIcon.MessageIcon.Information,
                        duration_sec * 1000
                    )

    def _populate_message_table(self, messages):
        self._stop_read_timer()
        self.message_table.setSortingEnabled(False)
        self.message_table.setRowCount(0)
        for msg in messages:
            self._insert_message_row(msg)
        self.message_table.setSortingEnabled(True)
        self.message_table.sortItems(3, Qt.SortOrder.DescendingOrder)
        self.message_table.horizontalHeader().setSortIndicator(3, Qt.SortOrder.DescendingOrder)

    def _append_messages(self, messages):
        self.message_table.setSortingEnabled(False)
        for msg in messages:
            self._insert_message_row(msg)
        self.message_table.setSortingEnabled(True)
        self.message_table.sortItems(3, Qt.SortOrder.DescendingOrder)
        self.message_table.horizontalHeader().setSortIndicator(3, Qt.SortOrder.DescendingOrder)
        self.statusBar().showMessage(
            f"Loaded {self.message_table.rowCount()} emails (from cache) | Syncing...")

    def _insert_message_row(self, msg):
        row = self.message_table.rowCount()
        self.message_table.insertRow(row)
        is_read = msg.get('is_read', True)
        font = QFont()
        font.setBold(not is_read)
        color = QColor('#ffffff') if not is_read else QColor('#aaaaaa')

        # Attachment icon
        has_att = msg.get('has_attachment', False)
        att_item = QTableWidgetItem()
        if has_att:
            import os
            icon_path = "icons_Vantage Mail/paperclip.png"
            if os.path.exists(icon_path):
                att_item.setIcon(QIcon(icon_path))
            else:
                att_item.setText("📎")
        att_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_table.setItem(row, 0, att_item)

        for col_offset, key in enumerate(['sender', 'subject', 'date']):
            col = col_offset + 1
            item = QTableWidgetItem(str(msg.get(key, '')))
            item.setFont(font)
            item.setForeground(QBrush(color))
            if col == 1:
                item.setData(Qt.ItemDataRole.UserRole, msg.get('id'))
            self.message_table.setItem(row, col, item)

    def _refresh_folder_badge(self, folder_id, account_email=None):
        email = account_email or self._current_account_email or self.account_manager._active_email
        if not email or not hasattr(self, '_account_tree_items'):
            return
        header_item = self._account_tree_items.get(email)
        if not header_item:
            return
        
        target_item = None
        for i in range(header_item.childCount()):
            child = header_item.child(i)
            if child.data(0, Qt.ItemDataRole.UserRole) == folder_id:
                target_item = child
                break
        
        if not target_item:
            return

        if folder_id == 'Drafts':
            db = self.account_manager._db
            count = len(db.get_cached_emails(email, 'Drafts'))
            name = target_item.text(0)
            if "  (" in name:
                name = name.split("  (")[0]
            label = f"{name}  ({count})" if count > 0 else name
            target_item.setText(0, label)
            return

        if folder_id == 'Outbox':
            db = self.account_manager._db
            count = len(db.get_cached_emails(email, 'Outbox'))
            name = target_item.text(0)
            if "  (" in name:
                name = name.split("  (")[0]
            label = f"{name}  ({count})" if count > 0 else name
            target_item.setText(0, label)
            return

        badge_key = (email, folder_id)
        if badge_key in self._badge_in_flight:
            return
        self._badge_in_flight.add(badge_key)

        def fetch_badge():
            provider = self.account_manager.get_provider(email)
            if hasattr(provider, 'get_folder_unread_count'):
                return provider.get_folder_unread_count(folder_id)
            return 0

        def update_badge(count):
            name = target_item.text(0)
            if "  (" in name:
                name = name.split("  (")[0]
            label = f"{name}  ({count})" if count > 0 else name
            target_item.setText(0, label)

        thread, worker = self._run_in_thread(fetch_badge, update_badge)
        thread.finished.connect(lambda: self._badge_in_flight.discard(badge_key))

    def _on_message_clicked(self, item):
        self._stop_read_timer()
        row = item.row()
        msg_id = self.message_table.item(row, 1).data(Qt.ItemDataRole.UserRole)
        if not msg_id:
            return

        first_cell = self.message_table.item(row, 1)
        if first_cell and first_cell.font().bold():
            self._pending_read_msg_id = msg_id
            self._pending_read_row = row
            self._pending_read_folder_id = self._current_folder_id
            self._pending_read_account_email = self._current_account_email or self.account_manager._active_email
            if getattr(self, '_mark_read_delay', 3) > 0:
                self._read_timer.start(self._mark_read_delay * 1000)

        db = self.account_manager._db
        acc_email = self._current_account_email or self.account_manager._active_email
        folder_id = self._current_folder_id
        
        cached_msg = db.get_cached_email(acc_email, folder_id, msg_id)
        
        # Decide if we need to download attachments/body
        needs_fetch = False
        if not cached_msg or not cached_msg.get('body'):
            needs_fetch = True
        elif cached_msg.get('has_attachment') and not cached_msg.get('attachments'):
            needs_fetch = True

        if not needs_fetch:
            self._on_body_loaded(cached_msg)
        else:
            self.statusBar().showMessage("Fetching message details...")
            provider = self.account_manager.get_active_provider()
            def fetch_and_cache():
                res = provider.fetch_message_body(msg_id, folder_id)
                body = res.get('body', '')
                attachments = res.get('attachments', [])
                if cached_msg:
                    cached_msg['body'] = body
                    cached_msg['attachments'] = attachments
                    db.save_cached_email(acc_email, folder_id, msg_id, cached_msg)
                else:
                    new_msg = {
                        'id': msg_id,
                        'body': body,
                        'attachments': attachments,
                        'has_attachment': len(attachments) > 0
                    }
                    db.save_cached_email(acc_email, folder_id, msg_id, new_msg)
                return res
            self._run_in_thread(
                fetch_and_cache,
                self._on_body_loaded
            )

    def _on_body_loaded(self, result):
        body = ""
        attachments = []
        if isinstance(result, dict):
            body = result.get('body', '')
            attachments = result.get('attachments', [])
        else:
            body = result or ""

        if body:
            import re
            body = re.sub(r'(<meta\s+[^>]*content="[^"]*);([^"]*")', r'\1,\2', body, flags=re.IGNORECASE)
        
        body_html = body or "<p>No content</p>"
        settings = QSettings("TakshiqSoftLabs", "VantageMail")
        theme = settings.value("appearance/theme", "Dark", type=str)
        bg = "#ffffff" if theme == "Light" else "#1e1e1e"
        fg = "#000000" if theme == "Light" else "#ffffff"
        font_size = settings.value("appearance/font_size", 13, type=int)

        style_header = f"<style>body {{ background-color: {bg}; color: {fg}; font-size: {font_size}pt; font-family: sans-serif; }}</style>"
        if "<body>" in body_html.lower():
            body_html = body_html.replace("<body>", f"<body>{style_header}")
            body_html = body_html.replace("<body ", f"<body style='background-color: {bg}; color: {fg};' ")
        else:
            body_html = f"<html><head>{style_header}</head><body>{body_html}</body></html>"

        self.reading_pane.setHtml(body_html)

        # Populate attachment bar
        for i in reversed(range(self.attachments_buttons_layout.count())):
            w = self.attachments_buttons_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        if attachments:
            self.attachment_bar.setVisible(True)
            for att in attachments:
                btn = QPushButton(att.get('filename', 'Attachment'))
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #333333;
                        color: #ffffff;
                        border: 1px solid #555555;
                        border-radius: 3px;
                        padding: 3px 8px;
                    }
                    QPushButton:hover {
                        background-color: #444444;
                        border-color: #666666;
                    }
                """)
                btn.clicked.connect(lambda checked, a=att: self._show_attachment_options(a))
                self.attachments_buttons_layout.addWidget(btn)
        else:
            self.attachment_bar.setVisible(False)

    def _show_attachment_options(self, att):
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        menu = QMenu(self)
        
        act_open = QAction("Open", self)
        act_save = QAction("Save As...", self)
        
        act_open.triggered.connect(lambda: self._open_attachment(att))
        act_save.triggered.connect(lambda: self._save_attachment(att))
        
        menu.addAction(act_open)
        menu.addAction(act_save)
        menu.exec(self.cursor().pos())

    def _open_attachment(self, att):
        import base64, tempfile, os
        try:
            filename = att.get('filename', 'attachment')
            data_b64 = att.get('data', '')
            payload = base64.b64decode(data_b64)
            
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, filename)
            with open(temp_path, 'wb') as f:
                f.write(payload)
                
            os.startfile(temp_path)
            self.statusBar().showMessage(f"Opened {filename}")
        except Exception as e:
            self.statusBar().showMessage(f"Failed to open attachment: {e}")

    def _save_attachment(self, att):
        import base64
        from PyQt6.QtWidgets import QFileDialog
        try:
            filename = att.get('filename', 'attachment')
            data_b64 = att.get('data', '')
            payload = base64.b64decode(data_b64)
            
            path, _ = QFileDialog.getSaveFileName(self, "Save Attachment", filename, "All Files (*)")
            if path:
                with open(path, 'wb') as f:
                    f.write(payload)
                self.statusBar().showMessage(f"Saved attachment to {path}")
        except Exception as e:
            self.statusBar().showMessage(f"Failed to save attachment: {e}")

    def _on_account_changed(self, email):
        self._stop_read_timer()
        self.account_manager.set_active_account(email)
        self._current_account_email = email
        self._load_folders()

    def _prune_open_windows(self):
        alive = []
        for w in self._open_windows:
            try:
                # If the C++ object was deleted, this will raise RuntimeError
                if w.isVisible():
                    alive.append(w)
            except RuntimeError:
                pass
        self._open_windows = alive

    def _safe_remove_window(self, window):
        self._prune_open_windows()
        try:
            if window in self._open_windows:
                self._open_windows.remove(window)
        except RuntimeError:
            pass

    def _can_open_new_window(self) -> bool:
        self._prune_open_windows()
        if len(self._open_windows) >= 10:
            reply = QMessageBox.warning(
                self,
                "Resource Warning",
                "You have 10 or more independent windows open. More windows will consume additional system resources and may lead to the application hanging or crashing.\n\nDo you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return False
        return True

    def _on_message_double_clicked(self, item):
        row = item.row()
        widget_item = self.message_table.item(row, 1)
        if not widget_item:
            return
        msg_id = widget_item.data(Qt.ItemDataRole.UserRole)
        if not msg_id:
            return
            
        if not self._can_open_new_window():
            return

        acc_email = self._current_account_email or self.account_manager._active_email
        folder_id = self._current_folder_id
        db = self.account_manager._db
        
        email_data = db.get_cached_email(acc_email, folder_id, msg_id)
        if not email_data:
            return

        if not email_data.get('body') and folder_id not in ('Drafts', 'Outbox'):
            provider = self.account_manager.get_active_provider()
            self.statusBar().showMessage("Loading message body...")
            
            def load_body():
                return provider.fetch_message_body(msg_id, folder_id)
                
            def on_loaded(result):
                self.statusBar().showMessage("Message loaded.")
                if isinstance(result, dict):
                    email_data['body'] = result.get('body', '')
                    email_data['attachments'] = result.get('attachments', [])
                else:
                    email_data['body'] = result
                db.save_cached_email(acc_email, folder_id, msg_id, email_data)
                self._open_message_window(email_data, folder_id)
                
            self._run_in_thread(load_body, on_loaded)
        else:
            self._open_message_window(email_data, folder_id)

    def _open_message_window(self, email_data, folder_id):
        if not self._can_open_new_window():
            return

        acc_email = self._current_account_email or self.account_manager._active_email
        provider = self.account_manager.get_active_provider()
        
        if folder_id == 'Drafts':
            composer = EmailComposerWidget(
                provider, 
                parent=self, 
                account_manager=self.account_manager,
                to=','.join(email_data.get('to', [])),
                subject=email_data.get('subject', ''),
                body=email_data.get('body', ''),
                attachments=email_data.get('attachments', []),
                draft_id=email_data.get('id')
            )
            self._open_windows.append(composer)
            composer.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            composer.destroyed.connect(lambda: self._safe_remove_window(composer))
            composer.finished.connect(self._on_composer_finished)
            composer.show()
        else:
            from ui.widgets.email_viewer import EmailViewerWidget
            viewer = EmailViewerWidget(email_data, provider, parent=self)
            self._open_windows.append(viewer)
            viewer.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            viewer.destroyed.connect(lambda: self._safe_remove_window(viewer))
            viewer.show()

    def _compose_new(self):
        if not self._can_open_new_window():
            return
        provider = self.account_manager.get_active_provider()
        composer = EmailComposerWidget(provider, parent=self, account_manager=self.account_manager, mode='new')
        self._open_windows.append(composer)
        composer.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        composer.destroyed.connect(lambda: self._safe_remove_window(composer))
        composer.finished.connect(self._on_composer_finished)
        composer.show()

    def _reply_selected(self):
        row = self.message_table.currentRow()
        if row < 0:
            return
        msg_id = self.message_table.item(row, 1).data(Qt.ItemDataRole.UserRole)
        if not msg_id:
            return
        sender = self.message_table.item(row, 1).text()
        subject = self.message_table.item(row, 2).text()
        if subject.lower().startswith('re: '):
            reply_subject = subject
        else:
            reply_subject = 'Re: ' + subject
        self._reply_meta = {'to': sender, 'subject': reply_subject}
        self._run_in_thread(
            self.account_manager.get_active_provider().fetch_message_body,
            self._on_reply_body_loaded,
            msg_id,
            self._current_folder_id
        )

    def _on_reply_body_loaded(self, html):
        meta = getattr(self, '_reply_meta', {})
        quoted = ''
        if isinstance(html, dict):
            quoted = html.get('body', '')
        else:
            quoted = html or ''
        body = '<br><br><blockquote style="border-left:2px solid #888;padding-left:8px;color:#aaa;">' + quoted + '</blockquote>'
        if not self._can_open_new_window():
            return
        provider = self.account_manager.get_active_provider()
        composer = EmailComposerWidget(
            provider, 
            parent=self, 
            account_manager=self.account_manager,
            to=meta.get('to', ''),
            subject=meta.get('subject', ''),
            body=body,
            mode='reply'
        )
        self._open_windows.append(composer)
        composer.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        composer.destroyed.connect(lambda: self._safe_remove_window(composer))
        composer.finished.connect(self._on_composer_finished)
        composer.save_draft(force=True)
        composer.show()

    def _forward_selected(self):
        row = self.message_table.currentRow()
        if row < 0:
            return
        msg_id = self.message_table.item(row, 1).data(Qt.ItemDataRole.UserRole)
        if not msg_id:
            return
        sender = self.message_table.item(row, 1).text()
        subject = self.message_table.item(row, 2).text()
        date = self.message_table.item(row, 3).text()
        if subject.lower().startswith('fwd: '):
            fwd_subject = subject
        else:
            fwd_subject = 'Fwd: ' + subject
        self._forward_meta = {
            'subject': fwd_subject,
            'orig_subject': subject,
            'sender': sender,
            'date': date,
        }
        self._run_in_thread(
            self.account_manager.get_active_provider().fetch_message_body,
            self._on_forward_body_loaded,
            msg_id,
            self._current_folder_id
        )

    def _on_forward_body_loaded(self, html):
        meta = getattr(self, '_forward_meta', {})
        quoted = ''
        if isinstance(html, dict):
            quoted = html.get('body', '')
        else:
            quoted = html or ''
        body = (
            '<p>---------- Forwarded message ----------<br>'
            'From: ' + meta.get('sender', '') + '<br>'
            'Subject: ' + meta.get('orig_subject', '') + '<br>'
            'Date: ' + meta.get('date', '') + '</p>'
            '<blockquote style="border-left:2px solid #aaa;margin:0;padding-left:10px;">'
            + quoted + '</blockquote>'
        )
        if not self._can_open_new_window():
            return
        provider = self.account_manager.get_active_provider()
        composer = EmailComposerWidget(
            provider, 
            parent=self, 
            account_manager=self.account_manager,
            to='',
            subject=meta.get('subject', ''),
            body=body,
            mode='forward'
        )
        self._open_windows.append(composer)
        composer.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        composer.destroyed.connect(lambda: self._safe_remove_window(composer))
        composer.finished.connect(self._on_composer_finished)
        composer.save_draft(force=True)
        composer.show()

    def _show_context_menu(self, pos):
        item = self.message_table.itemAt(pos)
        if not item:
            return
        selected_ranges = self.message_table.selectedRanges()
        if not selected_ranges:
            return
        menu = QMenu(self)
        act_reply = QAction("Reply", self)
        act_reply_all = QAction("Reply All", self)
        act_forward = QAction("Forward", self)
        act_mark_read = QAction("Mark as Read", self)
        act_mark_unread = QAction("Mark as Unread", self)
        act_delete = QAction("Delete", self)
        act_export_eml = QAction("Export EML", self)
        act_reply.triggered.connect(self._reply_selected)
        act_reply_all.triggered.connect(self._reply_all_selected)
        act_forward.triggered.connect(self._forward_selected)
        act_mark_read.triggered.connect(lambda: self._mark_selected_read_status(True))
        act_mark_unread.triggered.connect(lambda: self._mark_selected_read_status(False))
        act_delete.triggered.connect(self._delete_selected)
        act_export_eml.triggered.connect(self._export_selected_to_eml)
        menu.addAction(act_reply)
        menu.addAction(act_reply_all)
        menu.addAction(act_forward)
        menu.addSeparator()
        menu.addAction(act_mark_read)
        menu.addAction(act_mark_unread)
        menu.addSeparator()
        menu.addAction(act_delete)
        menu.addAction(act_export_eml)
        menu.exec(self.message_table.viewport().mapToGlobal(pos))

    def _reply_all_selected(self):
        row = self.message_table.currentRow()
        if row < 0:
            return
        msg_id = self.message_table.item(row, 1).data(Qt.ItemDataRole.UserRole)
        if not msg_id:
            return
        sender = self.message_table.item(row, 1).text()
        subject = self.message_table.item(row, 2).text()
        if subject.lower().startswith('re: '):
            reply_subject = subject
        else:
            reply_subject = 'Re: ' + subject
        self._reply_meta = {'to': sender, 'subject': reply_subject}
        self._run_in_thread(
            self.account_manager.get_active_provider().fetch_message_body,
            self._on_reply_all_body_loaded,
            msg_id,
            self._current_folder_id
        )

    def _on_reply_all_body_loaded(self, html):
        meta = getattr(self, '_reply_meta', {})
        quoted = ''
        if isinstance(html, dict):
            quoted = html.get('body', '')
        else:
            quoted = html or ''
        body = '<br><br><blockquote style="border-left:2px solid #888;padding-left:8px;color:#aaa;">' + quoted + '</blockquote>'
        if not self._can_open_new_window():
            return
        provider = self.account_manager.get_active_provider()
        composer = EmailComposerWidget(
            provider,
            parent=self,
            account_manager=self.account_manager,
            to=meta.get('to', ''),
            subject=meta.get('subject', ''),
            body=body,
            mode='reply'
        )
        self._open_windows.append(composer)
        composer.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        composer.destroyed.connect(lambda: self._safe_remove_window(composer))
        composer.finished.connect(self._on_composer_finished)
        composer.save_draft(force=True)
        composer.show()

    def _mark_selected_read_status(self, read: bool):
        selected_ranges = self.message_table.selectedRanges()
        if not selected_ranges:
            return
        selected_rows = set()
        for r in selected_ranges:
            for row in range(r.topRow(), r.bottomRow() + 1):
                selected_rows.add(row)
        if not selected_rows:
            return
        provider = self.account_manager.get_active_provider()
        db = self.account_manager._db
        acc_email = self._current_account_email or self.account_manager._active_email
        folder_id = self._current_folder_id
        msg_ids_and_rows = []
        for row in selected_rows:
            item = self.message_table.item(row, 1)
            if item:
                msg_id = item.data(Qt.ItemDataRole.UserRole)
                if msg_id:
                    msg_ids_and_rows.append((msg_id, row))
        def do_mark():
            for msg_id, row in msg_ids_and_rows:
                provider.mark_read(msg_id, read, folder_id)
                cached_msg = db.get_cached_email(acc_email, folder_id, msg_id)
                if cached_msg:
                    cached_msg['is_read'] = read
                    db.save_cached_email(acc_email, folder_id, msg_id, cached_msg)
            return read
        def on_complete(is_read):
            from PyQt6.QtGui import QFont, QColor, QBrush
            font = QFont()
            font.setBold(not is_read)
            color = QColor('#ffffff') if not is_read else QColor('#aaaaaa')
            for msg_id, row in msg_ids_and_rows:
                for col in range(1, 4):
                    cell = self.message_table.item(row, col)
                    if cell:
                        cell.setFont(font)
                        cell.setForeground(QBrush(color))
            if self._current_folder_id:
                self._refresh_folder_badge(self._current_folder_id)
        self._run_in_thread(do_mark, on_complete)

    def _on_composer_finished(self, result=None):
        self._refresh_current_folder()

    def _refresh_current_folder(self):
        if not self._current_folder_id or not self._current_account_email:
            return
        db = self.account_manager._db
        cached = db.get_cached_emails(self._current_account_email, self._current_folder_id)
        self._on_messages_loaded(cached)

    def _toggle_layout(self, checked: bool):
        if checked:
            self.inner_splitter.setOrientation(Qt.Orientation.Horizontal)
            self.inner_splitter.setSizes([400, 860])
        else:
            self.inner_splitter.setOrientation(Qt.Orientation.Vertical)
            self.inner_splitter.setSizes([250, 550])

        settings = QSettings("TakshiqSoftLabs", "VantageMail")
        val = "Vertical" if checked else "Horizontal"
        if settings.value("appearance/reading_pane", "") != val:
            settings.setValue("appearance/reading_pane", val)
            settings.sync()

    def _open_logs(self):
        import os
        from utils.logger import LOG_DIR, log_info, log_error
        try:
            log_info("User requested to open logs folder.")
            os.startfile(LOG_DIR)
        except Exception as e:
            log_error(f"Failed to open logs directory: {e}", exc_info=True)
            self.statusBar().showMessage(f"Failed to open logs directory: {e}")

    def _delete_selected(self):
        self._stop_read_timer()
        selected_ranges = self.message_table.selectedRanges()
        if not selected_ranges:
            self.statusBar().showMessage("Select messages to delete")
            return
        rows_to_delete = set()
        for r in selected_ranges:
            for row in range(r.topRow(), r.bottomRow() + 1):
                rows_to_delete.add(row)
        if not rows_to_delete:
            return
        targets = []
        for r in rows_to_delete:
            item = self.message_table.item(r, 1)
            if item:
                msg_id = item.data(Qt.ItemDataRole.UserRole)
                if msg_id:
                    targets.append((r, msg_id))
        if not targets:
            return
        targets.sort(key=lambda x: x[0], reverse=True)
        self.statusBar().showMessage(f"Deleting {len(targets)} messages...")
        provider = self.account_manager.get_active_provider()
        acc_email = self._current_account_email or self.account_manager._active_email
        folder_id = self._current_folder_id
        db = self.account_manager._db
        
        def run_deletion():
            deleted_ids = []
            for row, msg_id in targets:
                try:
                    if folder_id not in ('Drafts', 'Outbox'):
                        provider.delete_message(msg_id, folder_id)
                    db.delete_cached_email(acc_email, folder_id, msg_id)
                    deleted_ids.append(msg_id)
                except Exception as e:
                    log_error(f"Error deleting message {msg_id}: {e}")
            return deleted_ids

        def on_deletion_complete(deleted_ids):
            from utils.logger import log_info, log_realtime_count
            log_info(f"Deleted {len(deleted_ids)} messages from folder '{folder_id}' on account '{acc_email}'.")
            for msg_id in deleted_ids:
                for r in reversed(range(self.message_table.rowCount())):
                    item = self.message_table.item(r, 1)
                    if item and item.data(Qt.ItemDataRole.UserRole) == msg_id:
                        self.message_table.removeRow(r)
                        break
            self.statusBar().showMessage("Deletion complete")
            self._refresh_folder_badge(folder_id)
            log_realtime_count(db)
        self._run_in_thread(run_deletion, on_deletion_complete)

    def _launch_add_account_wizard(self):
        wizard = AddAccountWizard(self.account_manager, parent=self)
        wizard.finished.connect(self._on_wizard_finished)
        wizard.exec()

    def _on_wizard_finished(self, result):
        accounts = self.account_manager.get_accounts()
        if accounts:
            email = accounts[0]['email']
            self.account_manager.set_active_account(email)
            self._current_account_email = email

            if self.centralWidget() != self.main_layout:
                self.setCentralWidget(self.main_layout)
            self._load_folders()
        else:
            self.statusBar().showMessage("No account added.")

    def _export_selected_to_eml(self):
        row = self.message_table.currentRow()
        if row < 0:
            self.statusBar().showMessage("Select an email to export first")
            return
        item = self.message_table.item(row, 1)
        if not item:
            return
        msg_id = item.data(Qt.ItemDataRole.UserRole)
        if not msg_id:
            return
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "Export Email to EML", f"email_{msg_id}.eml", "EML Files (*.eml);;All Files (*)")
        if not path:
            return
        self.statusBar().showMessage("Exporting email as EML...")
        provider = self.account_manager.get_active_provider()
        def do_export():
            if hasattr(provider, 'fetch_raw_email'):
                return provider.fetch_raw_email(msg_id, self._current_folder_id)
            else:
                raise NotImplementedError("This provider does not support raw EML export")
        def on_exported(raw_bytes):
            try:
                with open(path, 'wb') as f:
                    f.write(raw_bytes)
                self.statusBar().showMessage(f"Email exported to {path}")
            except Exception as e:
                self.statusBar().showMessage(f"Failed to write EML: {e}")
        self._run_in_thread(do_export, on_exported)

    def _export_to_csv(self):
        if not self._current_folder_id:
            self.statusBar().showMessage("Select a folder first")
            return
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "Export All Emails to CSV", "", "CSV Files (*.csv);;All Files (*)")
        if not path:
            return
        self.statusBar().showMessage("Exporting emails to CSV...")
        try:
            import csv
            db = self.account_manager._db
            acc_email = self._current_account_email or self.account_manager._active_email
            emails = db.get_cached_emails(acc_email, self._current_folder_id)
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerow(["ID", "From", "Subject", "Date", "Body"])
                for msg in emails:
                    body = msg.get('body', '')
                    writer.writerow([
                        msg.get('id', ''),
                        msg.get('sender', ''),
                        msg.get('subject', ''),
                        msg.get('date', ''),
                        body
                    ])
            self.statusBar().showMessage(f"Successfully exported {len(emails)} emails to CSV")
        except Exception as e:
            self.statusBar().showMessage(f"Export failed: {e}")

    def _open_settings(self):
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self._apply_settings)
        dialog.exec()

    def _apply_settings(self):
        settings = QSettings("TakshiqSoftLabs", "VantageMail")
        # Apply theme
        theme = settings.value("appearance/theme", "Dark", type=str)
        self._apply_theme(theme)

        # Apply layout
        layout_mode = settings.value("appearance/reading_pane", "Vertical", type=str)
        is_vertical = (layout_mode == "Vertical")
        if hasattr(self, 'act_layout'):
            self.act_layout.blockSignals(True)
            self.act_layout.setChecked(is_vertical)
            self.act_layout.blockSignals(False)
        self._toggle_layout(is_vertical)

        # Apply mark-as-read delay
        self._mark_read_delay = settings.value("sync/mark_read_delay", 3, type=int)

        # Apply tray visibility
        if self._tray:
            tray_enabled = settings.value("notifications/tray_enabled", True, type=bool)
            if tray_enabled:
                self._tray.show()
            else:
                self._tray.hide()

        # Apply refresh timer if exists
        if hasattr(self, '_refresh_timer'):
            self._apply_refresh_interval()

    def _apply_refresh_interval(self):
        settings = QSettings("TakshiqSoftLabs", "VantageMail")
        interval_str = settings.value("sync/interval", "10 s", type=str)
        if interval_str == "Manual":
            self._refresh_timer.stop()
            return
        
        secs = 10
        try:
            parts = interval_str.split()
            if len(parts) == 2:
                val = int(parts[0])
                unit = parts[1]
                if unit.startswith('s'):
                    secs = val
                elif unit.startswith('min'):
                    secs = val * 60
        except Exception as e:
            from utils.logger import log_error
            log_error(f"Error parsing sync interval '{interval_str}': {e}")
            
        self._refresh_timer.setInterval(secs * 1000)
        if not self._refresh_timer.isActive():
            self._refresh_timer.start()

    def _auto_refresh(self):
        if self._current_account_email and self._current_folder_id:
            if self._current_folder_id not in ('Outbox', 'Drafts'):
                self._sync_folder_background(self._current_account_email, self._current_folder_id)

    def _apply_theme(self, theme):
        settings = QSettings("TakshiqSoftLabs", "VantageMail")
        bg = "#ffffff" if theme == "Light" else "#1e1e1e"
        fg = "#000000" if theme == "Light" else "#ffffff"
        font_size = settings.value("appearance/font_size", 13, type=int)

        if theme == "Light":
            QApplication.instance().setStyleSheet(LIGHT_THEME)
            self.reading_pane_container.setStyleSheet("background-color: #ffffff; color: #000000;")
            self.reading_pane.setStyleSheet("background-color: #ffffff; color: #000000;")
        else:
            QApplication.instance().setStyleSheet(DARK_THEME)
            self.reading_pane_container.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
            self.reading_pane.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
            
        # Refresh placeholder text style if no email is selected (i.e. row is -1)
        if self.message_table.currentRow() < 0:
            self.reading_pane.setHtml(f"<body style='background:{bg};color:{fg};font-size:{font_size}pt;'><p>Select a message to read it.</p></body>")

    def closeEvent(self, event):
        for w in list(self._open_windows):
            w.close()
        super().closeEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            if self.message_table.hasFocus():
                self._delete_selected()
                event.accept()
                return
        super().keyPressEvent(event)