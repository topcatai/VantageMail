# -*- coding: utf-8 -*-
import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QTreeWidget, QTreeWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QIcon, QFont

class SearchWindow(QWidget):
    def __init__(self, account_manager, main_window, parent=None, initial_query=""):
        super().__init__(None)  # top-level independent window
        self.account_manager = account_manager
        self.main_window = main_window
        
        self.setWindowTitle("Vantage Mail — Search Messages")
        self.resize(900, 650)
        
        # Window Flags for separate taskbar entry and controls
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowSystemMenuHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        # Set Window Icon
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "icons_Vantage Mail", "Vantage white_Logo.png"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        # Main Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # Top Row: Search Input & Button
        top_layout = QHBoxLayout()
        self.search_input = QLineEdit(initial_query)
        self.search_input.setPlaceholderText("Type search query...")
        self.search_input.setMinimumHeight(30)
        self.search_input.returnPressed.connect(self.perform_search)
        
        self.search_btn = QPushButton("Search")
        self.search_btn.setMinimumHeight(30)
        self.search_btn.clicked.connect(self.perform_search)
        
        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.search_btn)
        layout.addLayout(top_layout)
        
        # Account Filters Row
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search in accounts:"))
        
        self.account_checkboxes = []
        accounts = self.account_manager.get_accounts()
        for acc in accounts:
            email = acc["email"]
            cb = QCheckBox(email)
            cb.setChecked(True)
            cb.stateChanged.connect(lambda state: self.perform_search())
            filter_layout.addWidget(cb)
            self.account_checkboxes.append(cb)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Results Tree Widget
        self.results_tree = QTreeWidget()
        self.results_tree.setColumnCount(5)
        self.results_tree.setHeaderLabels(["From", "Subject", "Date", "Folder", "Account"])
        self.results_tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.results_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.results_tree.setColumnWidth(0, 180)
        self.results_tree.setColumnWidth(2, 130)
        self.results_tree.setColumnWidth(3, 100)
        self.results_tree.setColumnWidth(4, 180)
        self.results_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.results_tree)
        
        # Setup Collapsible Root Nodes
        self.setup_root_nodes()
        
        # Apply Stylesheet
        self.apply_theme()
        
        # Run search if initial query is provided
        if initial_query:
            self.perform_search()

    def setup_root_nodes(self):
        self.root_subject = QTreeWidgetItem(["Matches in Subject (0)"])
        self.root_body = QTreeWidgetItem(["Matches in Body (0)"])
        
        bold_font = QFont()
        bold_font.setBold(True)
        self.root_subject.setFont(0, bold_font)
        self.root_body.setFont(0, bold_font)
        
        self.results_tree.addTopLevelItem(self.root_subject)
        self.results_tree.addTopLevelItem(self.root_body)
        
        self.root_subject.setExpanded(True)
        self.root_body.setExpanded(True)

    def apply_theme(self):
        # Retrieve themes from main_window dynamically to avoid circular import issues
        try:
            from ui.main_window import DARK_THEME, LIGHT_THEME
        except ImportError:
            DARK_THEME = ""
            LIGHT_THEME = ""

        settings = QSettings("TakshiqSoftLabs", "VantageMail")
        theme = settings.value("appearance/theme", "Dark", type=str)
        
        if theme == "Light" and LIGHT_THEME:
            self.setStyleSheet(LIGHT_THEME)
            self.results_tree.setStyleSheet("""
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
                QHeaderView::section {
                    background-color: #e6e6e6;
                    color: #333333;
                    border: 1px solid #cccccc;
                    padding: 4px;
                }
            """)
        else:
            if DARK_THEME:
                self.setStyleSheet(DARK_THEME)
            else:
                self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
            self.results_tree.setStyleSheet("""
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
                QHeaderView::section {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #3c3c3c;
                    padding: 4px;
                }
            """)

    def perform_search(self):
        query = self.search_input.text().strip().lower()
        
        # Clear children of the root nodes
        for i in reversed(range(self.root_subject.childCount())):
            self.root_subject.removeChild(self.root_subject.child(i))
        for i in reversed(range(self.root_body.childCount())):
            self.root_body.removeChild(self.root_body.child(i))
            
        self.root_subject.setText(0, "Matches in Subject (0)")
        self.root_body.setText(0, "Matches in Body (0)")
        
        if not query:
            return
            
        selected_accounts = [cb.text() for cb in self.account_checkboxes if cb.isChecked()]
        if not selected_accounts:
            return
            
        db = self.account_manager._db
        results = db.search_emails(selected_accounts, query)
        
        subject_matches = []
        body_matches = []
        
        for msg in results:
            subject = msg.get("subject", "").lower()
            body = msg.get("body", "").lower()
            
            # Grouping Logic:
            # - If match in subject, goes to subject matches
            # - If match in body, goes to body matches (and can be in both if matches both)
            in_subject = query in subject
            in_body = query in body
            
            item_data = {
                "id": msg.get("id"),
                "folder_id": msg.get("_folder_id"),
                "account_email": msg.get("_account_email")
            }
            
            if in_subject:
                child = QTreeWidgetItem([
                    msg.get("sender", "Unknown"),
                    msg.get("subject", ""),
                    msg.get("date", ""),
                    msg.get("_folder_id", ""),
                    msg.get("_account_email", "")
                ])
                child.setData(0, Qt.ItemDataRole.UserRole, item_data)
                subject_matches.append(child)
                
            if in_body:
                child = QTreeWidgetItem([
                    msg.get("sender", "Unknown"),
                    msg.get("subject", ""),
                    msg.get("date", ""),
                    msg.get("_folder_id", ""),
                    msg.get("_account_email", "")
                ])
                child.setData(0, Qt.ItemDataRole.UserRole, item_data)
                body_matches.append(child)
                
        # Append children
        self.root_subject.addChildren(subject_matches)
        self.root_body.addChildren(body_matches)
        
        # Update node counts
        self.root_subject.setText(0, f"Matches in Subject ({len(subject_matches)})")
        self.root_body.setText(0, f"Matches in Body ({len(body_matches)})")
        
        self.root_subject.setExpanded(len(subject_matches) > 0)
        self.root_body.setExpanded(len(body_matches) > 0)

    def on_item_double_clicked(self, item, column):
        # If it's a root node, do nothing
        if item.parent() is None:
            return
            
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data:
            return
            
        msg_id = item_data.get("id")
        folder_id = item_data.get("folder_id")
        account_email = item_data.get("account_email")
        
        db = self.account_manager._db
        email_data = db.get_cached_email(account_email, folder_id, msg_id)
        if not email_data:
            return
            
        # Launch viewer widget
        from ui.widgets.email_viewer import EmailViewerWidget
        provider = self.account_manager.get_provider(account_email)
        viewer = EmailViewerWidget(email_data, provider, parent=self.main_window)
        
        # Append to main_window's open windows so it isn't garbage collected
        if self.main_window:
            self.main_window._open_windows.append(viewer)
            viewer.show()
