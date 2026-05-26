# -*- coding: utf-8 -*-
import base64
import os
import tempfile
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QWidget, QFileDialog, QMenu, QSizePolicy
)
from PyQt6.QtGui import QAction
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt

class EmailViewerWidget(QWidget):
    def __init__(self, email_data, provider, parent=None):
        super().__init__(None)
        self._main_window = parent
        self.provider = provider
        self.email_data = email_data
        
        self.setWindowTitle(email_data.get('subject', 'View Email'))
        self.resize(800, 600)
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        
        # Modeless window behavior
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowSystemMenuHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        import os
        from PyQt6.QtGui import QIcon
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "icons_Vantage Mail", "Vantage white_Logo.png"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Metadata headers
        meta_widget = QWidget()
        meta_widget.setStyleSheet("background-color: #252526; border-radius: 4px; padding: 10px;")
        meta_layout = QVBoxLayout(meta_widget)
        meta_layout.setSpacing(4)
        
        sender_lbl = QLabel(f"<b>From:</b> {email_data.get('sender', '')}")
        sender_lbl.setStyleSheet("color: #dddddd; font-size: 12px;")
        to_data = email_data.get('to', [])
        to_str = ', '.join(to_data) if isinstance(to_data, list) else str(to_data)
        to_lbl = QLabel(f"<b>To:</b> {to_str}")
        to_lbl.setStyleSheet("color: #dddddd; font-size: 12px;")
        subject_lbl = QLabel(f"<b>Subject:</b> {email_data.get('subject', '')}")
        subject_lbl.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: bold;")
        date_lbl = QLabel(f"<b>Date:</b> {email_data.get('date', '')}")
        date_lbl.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        
        meta_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        meta_layout.addWidget(sender_lbl)
        meta_layout.addWidget(to_lbl)
        meta_layout.addWidget(subject_lbl)
        meta_layout.addWidget(date_lbl)
        layout.addWidget(meta_widget, 0)
        
        # Attachment bar (hidden by default)
        self.attachment_bar = QWidget()
        self.attachment_bar.setStyleSheet("background-color: #252526; border: 1px solid #3c3c3c; border-radius: 4px;")
        self.attachment_bar.setVisible(False)
        self.attachment_bar_layout = QHBoxLayout(self.attachment_bar)
        self.attachment_bar_layout.setContentsMargins(10, 5, 10, 5)
        
        self.attachment_label = QLabel("📎 Attachments:")
        self.attachment_label.setStyleSheet("color: #cccccc; font-weight: bold;")
        self.attachment_bar_layout.addWidget(self.attachment_label)
        
        self.attachments_buttons_container = QWidget()
        self.attachments_buttons_layout = QHBoxLayout(self.attachments_buttons_container)
        self.attachments_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.attachments_buttons_layout.setSpacing(5)
        self.attachment_bar_layout.addWidget(self.attachments_buttons_container)
        self.attachment_bar_layout.addStretch()
        
        layout.addWidget(self.attachment_bar, 0)
        
        # WebEngine reading pane
        self.web_view = QWebEngineView()
        self.web_view.setStyleSheet("background-color: #1e1e1e;")
        layout.addWidget(self.web_view, 1)
        
        # Load email body content
        body = email_data.get('body', '')
        if isinstance(body, dict):
            body_html = body.get('body', '')
        else:
            body_html = body or ''
            
        if not body_html:
            body_html = "<body style='background:#1e1e1e;color:#ffffff;'><p>No body content</p></body>"
        elif "background" not in body_html:
            body_html = f"<body style='background:#1e1e1e;color:#ffffff;'>{body_html}</body>"
            
        self.web_view.setHtml(body_html)
        
        # Populate attachments
        attachments = email_data.get('attachments', [])
        if attachments:
            self.attachment_bar.setVisible(True)
            for att in attachments:
                filename = att.get('filename', 'Unnamed')
                btn = QPushButton(filename)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3e3e42;
                        color: #ffffff;
                        border: 1px solid #555555;
                        border-radius: 3px;
                        padding: 3px 8px;
                    }
                    QPushButton:hover {
                        background-color: #505054;
                    }
                """)
                btn.clicked.connect(lambda checked, a=att: self.handle_attachment_click(a))
                self.attachments_buttons_layout.addWidget(btn)
                
    def handle_attachment_click(self, attachment):
        menu = QMenu(self)
        act_open = QAction("Open", self)
        act_save = QAction("Save As...", self)
        menu.addAction(act_open)
        menu.addAction(act_save)
        
        def do_open():
            try:
                data_b64 = attachment.get('data', '')
                if isinstance(data_b64, str):
                    data_bytes = base64.b64decode(data_b64)
                else:
                    data_bytes = data_b64
                
                temp_dir = tempfile.gettempdir()
                filename = attachment.get('filename', 'attachment')
                temp_path = os.path.join(temp_dir, filename)
                with open(temp_path, 'wb') as f:
                    f.write(data_bytes)
                os.startfile(temp_path)
            except Exception as e:
                from utils.logger import log_error
                log_error(f"Failed to open attachment in viewer: {e}", exc_info=True)
                
        def do_save():
            try:
                filename = attachment.get('filename', 'attachment')
                save_path, _ = QFileDialog.getSaveFileName(self, "Save Attachment", filename)
                if save_path:
                    data_b64 = attachment.get('data', '')
                    if isinstance(data_b64, str):
                        data_bytes = base64.b64decode(data_b64)
                    else:
                        data_bytes = data_b64
                    with open(save_path, 'wb') as f:
                        f.write(data_bytes)
            except Exception as e:
                from utils.logger import log_error
                log_error(f"Failed to save attachment in viewer: {e}", exc_info=True)
                
        act_open.triggered.connect(do_open)
        act_save.triggered.connect(do_save)
        
        menu.exec(self.cursor().pos())
