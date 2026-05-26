# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView

class EmailPreviewWidget(QWidget):
    reply_requested = pyqtSignal(str)   # emits message_id
    forward_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.message_id = None
        layout = QVBoxLayout()
        # Header bar
        header = QHBoxLayout()
        self.sender_label = QLabel()
        self.date_label = QLabel()
        self.subject_label = QLabel()
        header.addWidget(self.sender_label)
        header.addWidget(self.date_label)
        header.addStretch()
        header.addWidget(self.subject_label)
        # Reply/Forward buttons
        self.reply_btn = QPushButton("Reply")
        self.forward_btn = QPushButton("Forward")
        self.reply_btn.clicked.connect(self._emit_reply)
        self.forward_btn.clicked.connect(self._emit_forward)
        header.addWidget(self.reply_btn)
        header.addWidget(self.forward_btn)
        layout.addLayout(header)
        # Web view for body
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        self.setLayout(layout)

    def load_message(self, message_id: str, sender: str, date: str, subject: str, html_body: str):
        self.message_id = message_id
        self.sender_label.setText(sender)
        self.date_label.setText(date)
        self.subject_label.setText(subject)
        self.web_view.setHtml(html_body)

    def _emit_reply(self):
        if self.message_id:
            self.reply_requested.emit(self.message_id)

    def _emit_forward(self):
        if self.message_id:
            self.forward_requested.emit(self.message_id)
