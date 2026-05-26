# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (
    QWizard,
    QWizardPage,
    QLineEdit,
    QLabel,
    QVBoxLayout,
    QPushButton,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPalette, QColor
from services.providers.registry import detect_provider, create_provider

class ConnectionTester(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, provider):
        super().__init__()
        self.provider = provider

    def run(self):
        try:
            self.provider.connect()
            self.finished.emit(True, "Connection successful")
        except Exception as e:
            self.finished.emit(False, str(e))

class AddAccountWizard(QWizard):
    def __init__(self, account_manager, parent=None):
        super().__init__(parent)
        self.account_manager = account_manager
        self.email = ''
        self.provider_name = ''
        self.provider = None
        self.cfg = {}
        self.setWindowTitle("Add Account")
        self.setStyleSheet("""
            QWizard { background-color: #2b2b2b; color: #ffffff; }
            QWizard > QWidget { background-color: #2b2b2b; color: #ffffff; }
            QWizardPage { background-color: #2b2b2b; color: #ffffff; }
            QFrame { background-color: #2b2b2b; }
            QLabel { color: #ffffff; font-size: 13px; background-color: transparent; }
            QLineEdit { background-color: #3c3c3c; color: #ffffff; border: 1px solid #555555;
                        padding: 6px; border-radius: 3px; font-size: 13px; }
            QLineEdit:focus { border: 1px solid #0078d4; }
            QPushButton { background-color: #0078d4; color: #ffffff; border: none;
                          padding: 6px 16px; border-radius: 3px; font-size: 13px; }
            QPushButton:hover { background-color: #106ebe; }
            QPushButton:disabled { background-color: #555555; color: #999999; }
            QScrollArea { background-color: #2b2b2b; }
            QScrollArea > QWidget > QWidget { background-color: #2b2b2b; }
        """)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#2b2b2b"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#3c3c3c"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#ffffff"))
        self.setPalette(palette)
        self._build_pages()

    def _build_pages(self):
        # Page 0 - Email entry
        page1 = QWizardPage()
        page1.setTitle("Account Email")
        layout1 = QVBoxLayout()
        layout1.setSpacing(10)
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("user@example.com")
        self.provider_label = QLabel("Detected provider: unknown")
        self.provider_label.setStyleSheet("color: #aaaaaa; font-size: 12px;")
        layout1.addWidget(QLabel("Enter your email address:"))
        layout1.addWidget(self.email_edit)
        layout1.addWidget(self.provider_label)
        layout1.addStretch()
        page1.setLayout(layout1)
        self.addPage(page1)
        self.email_edit.textChanged.connect(self._on_email_changed)
        self.currentIdChanged.connect(self._on_page_changed)

        # Page 1 - Microsoft
        self.page2_ms = QWizardPage()
        self.page2_ms.setTitle("Microsoft Account")
        l_ms = QVBoxLayout()
        l_ms.setSpacing(10)
        l_ms.addWidget(QLabel("Open the following URL and enter the code:"))
        url_label = QLabel("https://microsoft.com/devicelogin")
        url_label.setStyleSheet("color: #4fc3f7;")
        l_ms.addWidget(url_label)
        l_ms.addStretch()
        self.page2_ms.setLayout(l_ms)

        # Page 2 - Gmail
        self.page2_gmail = QWizardPage()
        self.page2_gmail.setTitle("Gmail Account")
        l_gmail = QVBoxLayout()
        l_gmail.setSpacing(10)
        l_gmail.addWidget(QLabel("A browser window will open for Google OAuth."))
        l_gmail.addStretch()
        self.page2_gmail.setLayout(l_gmail)

        # Page 3 - IMAP/SMTP
        self.page2_imap = QWizardPage()
        self.page2_imap.setTitle("IMAP / SMTP Settings")
        l_imap = QVBoxLayout()
        l_imap.setSpacing(8)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.imap_host_edit = QLineEdit()
        self.imap_port_edit = QLineEdit()
        self.imap_port_edit.setText("993")
        self.smtp_host_edit = QLineEdit()
        self.smtp_port_edit = QLineEdit()
        self.smtp_port_edit.setText("465")
        for label_text, widget in [
            ("Password:", self.password_edit),
            ("IMAP Host:", self.imap_host_edit),
            ("IMAP Port:", self.imap_port_edit),
            ("SMTP Host:", self.smtp_host_edit),
            ("SMTP Port:", self.smtp_port_edit),
        ]:
            l_imap.addWidget(QLabel(label_text))
            l_imap.addWidget(widget)
        l_imap.addStretch()
        self.page2_imap.setLayout(l_imap)

        # Page 4 - Testing
        self.page3 = QWizardPage()
        self.page3.setTitle("Testing Connection")
        l3 = QVBoxLayout()
        self.test_label = QLabel("Testing connection...")
        self.test_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l3.addStretch()
        l3.addWidget(self.test_label)
        l3.addStretch()
        self.page3.setLayout(l3)

        # Page 5 - Success
        self.page4 = QWizardPage()
        self.page4.setTitle("Account Added")
        l4 = QVBoxLayout()
        self.success_label = QLabel("Account added successfully!")
        self.success_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.success_label.setStyleSheet(
            "color: #81c784; font-size: 15px; font-weight: bold;")
        l4.addStretch()
        l4.addWidget(self.success_label)
        l4.addStretch()
        self.page4.setLayout(l4)

        self.page2_ms_id    = self.addPage(self.page2_ms)
        self.page2_gmail_id = self.addPage(self.page2_gmail)
        self.page2_imap_id  = self.addPage(self.page2_imap)
        self.page3_id       = self.addPage(self.page3)
        self.page4_id       = self.addPage(self.page4)

    def nextId(self):
        current = self.currentId()
        if current == 0:
            if self.provider_name == 'microsoft':
                return self.page2_ms_id
            elif self.provider_name == 'gmail':
                return self.page2_gmail_id
            else:
                return self.page2_imap_id
        if current in (self.page2_ms_id, self.page2_gmail_id, self.page2_imap_id):
            return self.page3_id
        if current == self.page3_id:
            return self.page4_id
        return -1

    def _on_email_changed(self, text):
        self.email = text.strip()
        self.provider_name = detect_provider(self.email) if self.email else ''
        display = {
            'microsoft': 'Microsoft 365 / Outlook',
            'gmail':     'Gmail',
            'yahoo':     'Yahoo Mail (IMAP)',
            'icloud':    'iCloud Mail (IMAP)',
            'generic':   'Generic IMAP/SMTP',
        }.get(self.provider_name, 'unknown')
        self.provider_label.setText(f"Detected provider: {display}")

    def _on_page_changed(self, id_):
        if id_ == self.page3_id:
            if self.provider_name == 'gmail':
                self.provider = create_provider(self.email)
            elif self.provider_name == 'microsoft':
                self.provider = create_provider(
                    self.email, credentials={"token": None})
            else:
                self.cfg = {
                    'imap': {
                        'host': self.imap_host_edit.text(),
                        'port': int(self.imap_port_edit.text() or 993)
                    },
                    'smtp': {
                        'host': self.smtp_host_edit.text(),
                        'port': int(self.smtp_port_edit.text() or 465)
                    },
                }
                cred = {'password': self.password_edit.text()}
                self.provider = create_provider(
                    self.email, credentials=cred, config=self.cfg)

            self.test_label.setText("Testing connection...")
            self.tester = ConnectionTester(self.provider)
            self.tester.finished.connect(self._on_test_finished)
            self.tester.start()

    def _on_test_finished(self, success, message):
        if success:
            self.test_label.setText("Connection successful!")
            self.test_label.setStyleSheet("color: #81c784; font-size: 14px;")
            self.account_manager.add_account_with_provider(
                self.email, self.provider, self.cfg)
            QTimer.singleShot(800, self.next)
        else:
            self.test_label.setText(f"Failed: {message}")
            self.test_label.setStyleSheet("color: #e57373; font-size: 13px;")