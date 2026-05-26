# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QDialog, QLineEdit, QTextEdit, QPushButton, QHBoxLayout, QVBoxLayout, QFileDialog, QLabel, QComboBox, QMessageBox, QColorDialog, QWidget
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QFont, QTextListFormat

class ComposerWorker(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
    def run(self):
        try:
            result = self._fn(*self._args, **self._kwargs)
            self.finished.emit(result)
        except Exception as e:
            from utils.logger import log_error
            log_error(f"Worker thread error running {self._fn.__name__ if hasattr(self._fn, '__name__') else str(self._fn)}: {e}", exc_info=True)
            self.error.emit(str(e))

class EmailComposerWidget(QWidget):
    finished = pyqtSignal(object)

    def __init__(self, mail_service, parent=None, account_manager=None, 
                 to='', subject='', body='', attachments=None, draft_id=None,
                 mode='new'):
        super().__init__(None)
        
        # Load signature settings and apply signature to body
        from PyQt6.QtCore import QSettings
        settings = QSettings("TakshiqSoftLabs", "VantageMail")
        sig_text = settings.value("signature/text", "", type=str)
        use_in_new = settings.value("signature/use_new", False, type=bool)
        use_in_reply = settings.value("signature/use_reply", False, type=bool)
        use_in_fwd = settings.value("signature/use_forward", False, type=bool)
        self._mode = mode

        if sig_text:
            if mode == 'new' and use_in_new and not body:
                body = "<br><br>--<br>" + sig_text
            elif mode == 'reply' and use_in_reply:
                body = body + "<br><br>--<br>" + sig_text
            elif mode == 'forward' and use_in_fwd:
                body = body + "<br><br>--<br>" + sig_text
        self._main_window = parent
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowSystemMenuHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowTitle("Compose Email")
        import os
        from PyQt6.QtGui import QIcon
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "icons_Vantage Mail", "Vantage white_Logo.png"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.resize(750, 600)
        self.mail_service = mail_service
        self.account_manager = account_manager
        self.attachments = attachments or []
        self._threads = []
        self._workers = []

        # Generate or assign draft ID
        import uuid
        self.draft_id = draft_id or f"draft-{uuid.uuid4()}"

        # Track last saved state
        self._last_saved_to = to
        self._last_saved_cc = ''
        self._last_saved_subject = subject
        self._last_saved_text = ''
        self._last_saved_attachments = list(self.attachments)
        
        # Fields
        self.to_edit = QLineEdit(to)
        self.cc_edit = QLineEdit()
        self.subject_edit = QLineEdit(subject)
        self.body_edit = QTextEdit()
        
        # Configure default font: Arial 11
        default_font = QFont("Arial", 11)
        self.body_edit.setFont(default_font)
        self.body_edit.setCurrentFont(default_font)
        self.body_edit.document().setDefaultFont(default_font)

        if body:
            self.body_edit.setHtml(body)
        
        # Formatting Toolbar
        formatting_bar = QHBoxLayout()
        formatting_bar.setContentsMargins(0, 0, 0, 0)
        formatting_bar.setSpacing(5)
        
        # Font Family
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Arial", "Calibri", "Courier New", "Georgia", "Segoe UI", "Times New Roman", "Trebuchet MS", "Verdana"])
        self.font_combo.setCurrentText("Arial")
        self.font_combo.currentTextChanged.connect(self.body_edit.setFontFamily)
        formatting_bar.addWidget(self.font_combo)
        
        # Font Size
        self.size_combo = QComboBox()
        self.size_combo.addItems(["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "36", "48", "72"])
        self.size_combo.setCurrentText("11")
        self.size_combo.currentTextChanged.connect(lambda s: self.body_edit.setFontPointSize(float(s)))
        formatting_bar.addWidget(self.size_combo)
        
        # Text Styles (text buttons for dark theme)
        btn_bold = QPushButton("Bold")
        btn_bold.setFixedWidth(50)
        btn_bold.clicked.connect(self.toggle_bold)
        formatting_bar.addWidget(btn_bold)
        
        btn_italic = QPushButton("Italic")
        btn_italic.setFixedWidth(50)
        btn_italic.clicked.connect(self.toggle_italic)
        formatting_bar.addWidget(btn_italic)
        
        btn_underline = QPushButton("Underline")
        btn_underline.setFixedWidth(70)
        btn_underline.clicked.connect(self.toggle_underline)
        formatting_bar.addWidget(btn_underline)

        btn_strike = QPushButton("Strike")
        btn_strike.setFixedWidth(50)
        btn_strike.clicked.connect(self.toggle_strike)
        formatting_bar.addWidget(btn_strike)

        btn_color = QPushButton("Color")
        btn_color.setFixedWidth(50)
        btn_color.clicked.connect(self.select_color)
        formatting_bar.addWidget(btn_color)

        # Alignments
        btn_left = QPushButton("Left")
        btn_left.setFixedWidth(40)
        btn_left.clicked.connect(lambda: self.body_edit.setAlignment(Qt.AlignmentFlag.AlignLeft))
        formatting_bar.addWidget(btn_left)

        btn_center = QPushButton("Center")
        btn_center.setFixedWidth(50)
        btn_center.clicked.connect(lambda: self.body_edit.setAlignment(Qt.AlignmentFlag.AlignCenter))
        formatting_bar.addWidget(btn_center)

        btn_right = QPushButton("Right")
        btn_right.setFixedWidth(45)
        btn_right.clicked.connect(lambda: self.body_edit.setAlignment(Qt.AlignmentFlag.AlignRight))
        formatting_bar.addWidget(btn_right)

        btn_justify = QPushButton("Justify")
        btn_justify.setFixedWidth(55)
        btn_justify.clicked.connect(lambda: self.body_edit.setAlignment(Qt.AlignmentFlag.AlignJustify))
        formatting_bar.addWidget(btn_justify)

        # Lists
        btn_bullet = QPushButton("• List")
        btn_bullet.setFixedWidth(50)
        btn_bullet.clicked.connect(self.insert_bullet_list)
        formatting_bar.addWidget(btn_bullet)

        btn_number = QPushButton("1. List")
        btn_number.setFixedWidth(50)
        btn_number.clicked.connect(self.insert_numbered_list)
        formatting_bar.addWidget(btn_number)
        
        formatting_bar.addStretch()

        # Visual attachments list container
        self.attachments_container = QWidget()
        self.attachments_container_layout = QVBoxLayout(self.attachments_container)
        self.attachments_container_layout.setContentsMargins(0, 0, 0, 0)
        self.attachments_container_layout.setSpacing(4)

        # Buttons
        attach_btn = QPushButton("Attach")
        send_btn = QPushButton("Send")
        discard_btn = QPushButton("Discard")
        attach_btn.clicked.connect(self.attach_files)
        send_btn.clicked.connect(self.send_email)
        discard_btn.clicked.connect(self.discard_email)
        
        # Layouts
        form_layout = QVBoxLayout()
        if self.account_manager:
            self.from_combo = QComboBox()
            accounts = self.account_manager.get_accounts()
            for acc in accounts:
                self.from_combo.addItem(acc["email"])
            active_email = getattr(self.account_manager, "_active_email", None)
            if active_email:
                idx = self.from_combo.findText(active_email)
                if idx >= 0:
                    self.from_combo.setCurrentIndex(idx)
            self.from_combo.currentTextChanged.connect(self._on_from_changed)
            form_layout.addWidget(QLabel("From:"))
            form_layout.addWidget(self.from_combo)
        form_layout.addWidget(QLabel("To:"))
        form_layout.addWidget(self.to_edit)
        form_layout.addWidget(QLabel("CC:"))
        form_layout.addWidget(self.cc_edit)
        form_layout.addWidget(QLabel("Subject:"))
        form_layout.addWidget(self.subject_edit)
        
        form_layout.addWidget(QLabel("Attachments:"))
        form_layout.addWidget(self.attachments_container)
        
        form_layout.addWidget(QLabel("Body:"))
        form_layout.addLayout(formatting_bar)
        form_layout.addWidget(self.body_edit)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(attach_btn)
        btn_layout.addWidget(send_btn)
        btn_layout.addWidget(discard_btn)
        form_layout.addLayout(btn_layout)
        self.setLayout(form_layout)

        # Update visual attachments listing
        self.update_attachments_list()

        # Update last saved text after body html/text is fully loaded
        self._last_saved_text = self.body_edit.toPlainText().strip()

        # Setup auto-save timer
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.setInterval(30000)
        self.auto_save_timer.timeout.connect(self.save_draft)
        self.auto_save_timer.start()

    def toggle_bold(self):
        weight = self.body_edit.fontWeight()
        new_weight = 700 if weight < 700 else 400
        self.body_edit.setFontWeight(new_weight)

    def toggle_italic(self):
        self.body_edit.setFontItalic(not self.body_edit.fontItalic())

    def toggle_underline(self):
        self.body_edit.setFontUnderline(not self.body_edit.fontUnderline())

    def toggle_strike(self):
        fmt = self.body_edit.currentCharFormat()
        fmt.setFontStrikeOut(not fmt.fontStrikeOut())
        self.body_edit.setCurrentCharFormat(fmt)

    def select_color(self):
        color = QColorDialog.getColor(self.body_edit.textColor(), self)
        if color.isValid():
            self.body_edit.setTextColor(color)

    def insert_bullet_list(self):
        cursor = self.body_edit.textCursor()
        cursor.insertList(QTextListFormat.Style.ListDisc)

    def insert_numbered_list(self):
        cursor = self.body_edit.textCursor()
        cursor.insertList(QTextListFormat.Style.ListDecimal)

    def update_attachments_list(self):
        for i in reversed(range(self.attachments_container_layout.count())):
            w = self.attachments_container_layout.itemAt(i).widget()
            if w:
                w.deleteLater()
                
        if not self.attachments:
            self.attachments_container.setVisible(False)
            return
            
        self.attachments_container.setVisible(True)
        for idx, item in enumerate(self.attachments):
            import os
            if isinstance(item, dict):
                filename = item.get('filename', 'Unknown')
                size_kb = item.get('size', 0) / 1024
                size_str = f"{size_kb:.1f} KB"
            else:
                try:
                    filename = os.path.basename(item)
                    size_kb = os.path.getsize(item) / 1024
                    size_str = f"{size_kb:.1f} KB"
                except Exception:
                    filename = str(item)
                    size_str = "Unknown size"
                
            item_widget = QWidget()
            item_widget.setStyleSheet("background-color: #2d2d2d; border-radius: 3px;")
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(8, 4, 8, 4)
            
            lbl = QLabel(f"📎 {filename} ({size_str})")
            lbl.setStyleSheet("color: #dddddd;")
            
            btn_remove = QPushButton("Remove")
            btn_remove.setFixedWidth(60)
            btn_remove.setStyleSheet("""
                QPushButton {
                    background-color: #aa3333;
                    color: white;
                    border: none;
                    border-radius: 2px;
                    padding: 2px 5px;
                }
                QPushButton:hover {
                    background-color: #cc4444;
                }
            """)
            btn_remove.clicked.connect(lambda checked, idx=idx: self.remove_attachment(idx))
            
            item_layout.addWidget(lbl)
            item_layout.addWidget(btn_remove)
            self.attachments_container_layout.addWidget(item_widget)

    def remove_attachment(self, idx):
        if 0 <= idx < len(self.attachments):
            self.attachments.pop(idx)
            self.update_attachments_list()

    def attach_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Attachments")
        if files:
            for f in files:
                if f not in self.attachments:
                    self.attachments.append(f)
            self.update_attachments_list()

    def is_modified(self) -> bool:
        current_to = self.to_edit.text().strip()
        current_cc = self.cc_edit.text().strip()
        current_subject = self.subject_edit.text().strip()
        current_text = self.body_edit.toPlainText().strip()
        return (current_to != self._last_saved_to or
                current_cc != self._last_saved_cc or
                current_subject != self._last_saved_subject or
                current_text != self._last_saved_text or
                self.attachments != self._last_saved_attachments)

    def _on_from_changed(self, selected_email):
        if self.account_manager:
            try:
                self.mail_service = self.account_manager.get_provider(selected_email)
            except Exception as e:
                from utils.logger import log_error
                log_error(f"Error switching mail service provider to {selected_email}: {e}")

    def save_draft(self, force=False):
        if getattr(self, 'is_sent', False):
            return
        if not force and not self.is_modified():
            return

        selected_email = self.from_combo.currentText() if (self.account_manager and hasattr(self, 'from_combo')) else (self.mail_service.account_email if hasattr(self.mail_service, 'account_email') else '')
        if not selected_email:
            return

        db = self.account_manager._db if (self.account_manager and hasattr(self.account_manager, '_db')) else None
        if not db:
            return

        # Convert path strings to base64 dicts
        import base64, os
        for i, item in enumerate(self.attachments):
            if isinstance(item, str):
                try:
                    filename = os.path.basename(item)
                    with open(item, 'rb') as f_att:
                        payload = f_att.read()
                        data_b64 = base64.b64encode(payload).decode('utf-8')
                        self.attachments[i] = {
                            'filename': filename,
                            'content_type': 'application/octet-stream',
                            'data': data_b64,
                            'size': len(payload)
                        }
                except Exception as e_att:
                    from utils.logger import log_error
                    log_error(f"Error reading attachment {item} to store in draft: {e_att}")
        
        self.update_attachments_list()

        from datetime import datetime
        draft_msg = {
            "id": self.draft_id,
            "subject": self.subject_edit.text(),
            "body": self.body_edit.toHtml(),
            "to": [addr.strip() for addr in self.to_edit.text().split(',') if addr.strip()],
            "cc": [addr.strip() for addr in self.cc_edit.text().split(',') if addr.strip()],
            "attachments": self.attachments,
            "sender": selected_email,
            "date": datetime.now().isoformat(),
            "is_read": True,
            "has_attachment": len(self.attachments) > 0
        }

        db.save_cached_email(selected_email, 'Drafts', self.draft_id, draft_msg)

        # Update last saved state
        self._last_saved_to = self.to_edit.text().strip()
        self._last_saved_cc = self.cc_edit.text().strip()
        self._last_saved_subject = self.subject_edit.text().strip()
        self._last_saved_text = self.body_edit.toPlainText().strip()
        self._last_saved_attachments = list(self.attachments)

        from utils.logger import log_info
        log_info(f"Draft {self.draft_id} saved/updated in database cache for {selected_email}.")
        
        if self._main_window and hasattr(self._main_window, '_refresh_folder_badge'):
            self._main_window._refresh_folder_badge('Drafts')

    def discard_email(self):
        self.is_sent = True
        selected_email = self.from_combo.currentText() if (self.account_manager and hasattr(self, 'from_combo')) else (self.mail_service.account_email if hasattr(self.mail_service, 'account_email') else '')
        db = self.account_manager._db if (self.account_manager and hasattr(self.account_manager, '_db')) else None
        if db and selected_email:
            db.delete_cached_email(selected_email, 'Drafts', self.draft_id)
            from utils.logger import log_info
            log_info(f"Draft {self.draft_id} discarded and deleted from database cache.")
            if self._main_window and hasattr(self._main_window, '_refresh_folder_badge'):
                self._main_window._refresh_folder_badge('Drafts')
        self.finished.emit(None)
        self.close()

    def closeEvent(self, event):
        if hasattr(self, 'auto_save_timer'):
            self.auto_save_timer.stop()
        self.save_draft()
        super().closeEvent(event)

    def send_email(self):
        import uuid
        from datetime import datetime
        if not hasattr(self, 'outbox_msg_id'):
            self.outbox_msg_id = f"local-{uuid.uuid4()}"

        selected_email = self.from_combo.currentText() if (self.account_manager and hasattr(self, 'from_combo')) else (self.mail_service.account_email if hasattr(self.mail_service, 'account_email') else '')
        
        message = {
            "id": self.outbox_msg_id,
            "subject": self.subject_edit.text(),
            "body": self.body_edit.toHtml(),
            "to": [addr.strip() for addr in self.to_edit.text().split(',') if addr.strip()],
            "cc": [addr.strip() for addr in self.cc_edit.text().split(',') if addr.strip()],
            "attachments": self.attachments,
            "sender": selected_email,
            "date": datetime.now().isoformat(),
            "is_read": True
        }

        db = self.account_manager._db if (self.account_manager and hasattr(self.account_manager, '_db')) else None
        if db:
            from utils.logger import log_info, log_realtime_count
            db.save_cached_email(selected_email, 'Outbox', self.outbox_msg_id, message)
            log_info(f"Email queued to Outbox database cache for {selected_email}.")
            log_realtime_count(db)

        if self.account_manager and hasattr(self, 'from_combo'):
            provider = self.account_manager.get_provider(selected_email)
        else:
            provider = self.mail_service

        def fn():
            prepared_attachments = []
            import base64
            for att in message["attachments"]:
                if isinstance(att, dict):
                    try:
                        filename = att.get('filename')
                        data_b64 = att.get('data')
                        payload = base64.b64decode(data_b64)
                        prepared_attachments.append({
                            'filename': filename,
                            'data': payload
                        })
                    except Exception as e_att:
                        from utils.logger import log_error
                        log_error(f"Error decoding attachment dict: {e_att}")
                else:
                    try:
                        import os
                        filename = os.path.basename(att)
                        with open(att, 'rb') as f_att:
                            prepared_attachments.append({
                                'filename': filename,
                                'data': f_att.read()
                            })
                    except Exception as e_att:
                        from utils.logger import log_error
                        log_error(f"Error reading attachment {att}: {e_att}")

            if hasattr(provider, 'send_message'):
                return provider.send_message(
                    to=message["to"],
                    subject=message["subject"],
                    body=message["body"],
                    cc=message["cc"],
                    attachments=prepared_attachments
                )
            else:
                return provider.send(**message)

        worker = ComposerWorker(fn)
        thread = QThread()
        self._workers.append(worker)
        self._threads.append(thread)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        
        def on_success():
            from utils.logger import log_info, log_realtime_count
            self.is_sent = True
            log_info(f"Email successfully sent from {selected_email} to {message['to']}")
            if db:
                db.delete_cached_email(selected_email, 'Outbox', self.outbox_msg_id)
                db.delete_cached_email(selected_email, 'Drafts', self.draft_id)
                log_realtime_count(db)
                if self._main_window and hasattr(self._main_window, '_refresh_folder_badge'):
                    self._main_window._refresh_folder_badge('Drafts')
                    self._main_window._refresh_folder_badge('Outbox')
            self.finished.emit(None)
            self.close()

        worker.finished.connect(on_success)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        worker.error.connect(lambda e: (QMessageBox.critical(self, "Send Error", f"Failed to send email:\n{e}"), thread.quit(), thread.deleteLater()))
        thread.start()
