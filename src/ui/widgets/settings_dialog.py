# -*- coding: utf-8 -*-
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox,
    QCheckBox, QTextEdit, QPushButton, QScrollArea, QWidget, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtGui import QFont, QIcon

class SettingsDialog(QDialog):
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(600, 700)
        self.setMinimumSize(500, 500)
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")

        # Window icon
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "icons_Vantage Mail", "Vantage white_Logo.png"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #1e1e1e; }")
        
        container = QWidget()
        container.setStyleSheet("background-color: #1e1e1e;")
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(15)
        container_layout.setContentsMargins(10, 10, 10, 10)

        self.settings = QSettings("TakshiqSoftLabs", "VantageMail")

        # ── SECTION 1: Appearance ──────────────────────────────────────────
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setCurrentText(self.settings.value("appearance/theme", "Dark", type=str))

        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["Vertical", "Horizontal"])
        self.layout_combo.setCurrentText(self.settings.value("appearance/reading_pane", "Vertical", type=str))

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(self.settings.value("appearance/font_size", 13, type=int))

        sec1 = self._create_section("Appearance", [
            ("Theme:", self.theme_combo),
            ("Reading Pane Layout:", self.layout_combo),
            ("Reading Pane Font Size (pt):", self.font_size_spin)
        ])
        container_layout.addWidget(sec1)

        # ── SECTION 2: Email Sync ─────────────────────────────────────────
        self.sync_interval_combo = QComboBox()
        self.sync_interval_combo.addItems(["10 s", "30 s", "1 min", "5 min", "10 min", "Manual"])
        self.sync_interval_combo.setCurrentText(self.settings.value("sync/interval", "1 min", type=str))

        self.sync_limit_combo = QComboBox()
        self.sync_limit_combo.addItems(["100", "200", "500", "All"])
        self.sync_limit_combo.setCurrentText(self.settings.value("sync/limit", "All", type=str))

        self.mark_read_spin = QSpinBox()
        self.mark_read_spin.setRange(0, 30)
        self.mark_read_spin.setSpecialValueText("Never")
        self.mark_read_spin.setValue(self.settings.value("sync/mark_read_delay", 3, type=int))

        sec2 = self._create_section("Email Sync", [
            ("Auto-refresh Interval:", self.sync_interval_combo),
            ("Max Messages to Fetch per Folder:", self.sync_limit_combo),
            ("Mark as Read after (seconds):", self.mark_read_spin)
        ])
        container_layout.addWidget(sec2)

        # ── SECTION 3: Notifications ─────────────────────────────────────
        self.tray_checkbox = QCheckBox("Enable system tray icon")
        self.tray_checkbox.setChecked(self.settings.value("notifications/tray_enabled", True, type=bool))

        self.notify_checkbox = QCheckBox("Show new-mail notification")
        self.notify_checkbox.setChecked(self.settings.value("notifications/new_mail_enabled", True, type=bool))

        self.notify_duration_spin = QSpinBox()
        self.notify_duration_spin.setRange(2, 30)
        self.notify_duration_spin.setValue(self.settings.value("notifications/duration", 5, type=int))

        sec3 = self._create_section("Notifications", [
            ("", self.tray_checkbox),
            ("", self.notify_checkbox),
            ("Notification Duration (sec):", self.notify_duration_spin)
        ])
        container_layout.addWidget(sec3)

        # ── SECTION 4: Signature ──────────────────────────────────────────
        sig_frame = QFrame()
        sig_frame.setStyleSheet("QFrame { background-color: #252526; border-radius: 6px; }")
        sig_layout = QVBoxLayout(sig_frame)
        sig_layout.setContentsMargins(12, 12, 12, 12)
        
        title_lbl = QLabel("Signature")
        title_lbl.setStyleSheet("color: #4fc3f7; font-weight: bold; font-size: 14px;")
        sig_layout.addWidget(title_lbl)

        self.sig_text = QTextEdit()
        self.sig_text.setPlaceholderText("Enter rich text signature here...")
        self.sig_text.setHtml(self.settings.value("signature/text", "", type=str))
        self.sig_text.setFixedHeight(100)
        self.sig_text.setStyleSheet("QTextEdit { background-color: #1e1e1e; color: white; border: 1px solid #3c3c3c; border-radius: 4px; }")
        sig_layout.addWidget(self.sig_text)

        self.sig_new_chk = QCheckBox("Use in New Email")
        self.sig_new_chk.setChecked(self.settings.value("signature/use_new", False, type=bool))
        self.sig_reply_chk = QCheckBox("Use in Reply")
        self.sig_reply_chk.setChecked(self.settings.value("signature/use_reply", False, type=bool))
        self.sig_forward_chk = QCheckBox("Use in Forward")
        self.sig_forward_chk.setChecked(self.settings.value("signature/use_forward", False, type=bool))

        sig_layout.addWidget(self.sig_new_chk)
        sig_layout.addWidget(self.sig_reply_chk)
        sig_layout.addWidget(self.sig_forward_chk)
        container_layout.addWidget(sig_frame)

        # ── SECTION 5: Composer Defaults ─────────────────────────────────
        self.comp_font_combo = QComboBox()
        self.comp_font_combo.addItems(["Arial", "Calibri", "Courier New", "Georgia", "Segoe UI", "Times New Roman", "Trebuchet MS", "Verdana"])
        self.comp_font_combo.setCurrentText(self.settings.value("composer/font_family", "Arial", type=str))

        self.comp_size_combo = QComboBox()
        self.comp_size_combo.addItems(["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "36", "48", "72"])
        self.comp_size_combo.setCurrentText(self.settings.value("composer/font_size", "11", type=str))

        self.reply_action_combo = QComboBox()
        self.reply_action_combo.addItems(["Reply", "Reply All"])
        self.reply_action_combo.setCurrentText(self.settings.value("composer/reply_action", "Reply", type=str))

        sec5 = self._create_section("Composer Defaults", [
            ("Default Font Family:", self.comp_font_combo),
            ("Default Font Size (pt):", self.comp_size_combo),
            ("Default Reply Action:", self.reply_action_combo)
        ])
        container_layout.addWidget(sec5)

        # ── SECTION 6: Startup ───────────────────────────────────────────
        self.splash_checkbox = QCheckBox("Show splash screen")
        self.splash_checkbox.setChecked(self.settings.value("startup/show_splash", True, type=bool))

        self.last_folder_checkbox = QCheckBox("Open last folder on start")
        self.last_folder_checkbox.setChecked(self.settings.value("startup/open_last_folder", True, type=bool))

        sec6 = self._create_section("Startup", [
            ("", self.splash_checkbox),
            ("", self.last_folder_checkbox)
        ])
        container_layout.addWidget(sec6)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        # ── Buttons ──────────────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0098ff;
            }
        """)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #3e3e42;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 15px;
            }
            QPushButton:hover {
                background-color: #505054;
            }
        """)

        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        main_layout.addLayout(btn_layout)

    def _create_section(self, title: str, fields: list) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("QFrame { background-color: #252526; border-radius: 6px; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #4fc3f7; font-weight: bold; font-size: 14px;")
        layout.addWidget(title_lbl)

        for label_text, widget in fields:
            row = QHBoxLayout()
            if label_text:
                lbl = QLabel(label_text)
                lbl.setStyleSheet("color: #dddddd;")
                row.addWidget(lbl)
            row.addWidget(widget)
            if isinstance(widget, QWidget) and not isinstance(widget, (QCheckBox, QTextEdit)):
                widget.setStyleSheet("""
                    QComboBox, QSpinBox {
                        background-color: #1e1e1e;
                        color: white;
                        border: 1px solid #3c3c3c;
                        border-radius: 4px;
                        padding: 3px;
                    }
                """)
            layout.addLayout(row)

        return frame

    def save_settings(self):
        # Appearance
        self.settings.setValue("appearance/theme", self.theme_combo.currentText())
        self.settings.setValue("appearance/reading_pane", self.layout_combo.currentText())
        self.settings.setValue("appearance/font_size", self.font_size_spin.value())

        # Sync
        self.settings.setValue("sync/interval", self.sync_interval_combo.currentText())
        self.settings.setValue("sync/limit", self.sync_limit_combo.currentText())
        self.settings.setValue("sync/mark_read_delay", self.mark_read_spin.value())

        # Notifications
        self.settings.setValue("notifications/tray_enabled", self.tray_checkbox.isChecked())
        self.settings.setValue("notifications/new_mail_enabled", self.notify_checkbox.isChecked())
        self.settings.setValue("notifications/duration", self.notify_duration_spin.value())

        # Signature
        self.settings.setValue("signature/text", self.sig_text.toHtml())
        self.settings.setValue("signature/use_new", self.sig_new_chk.isChecked())
        self.settings.setValue("signature/use_reply", self.sig_reply_chk.isChecked())
        self.settings.setValue("signature/use_forward", self.sig_forward_chk.isChecked())

        # Composer Defaults
        self.settings.setValue("composer/font_family", self.comp_font_combo.currentText())
        self.settings.setValue("composer/font_size", self.comp_size_combo.currentText())
        self.settings.setValue("composer/reply_action", self.reply_action_combo.currentText())

        # Startup
        self.settings.setValue("startup/show_splash", self.splash_checkbox.isChecked())
        self.settings.setValue("startup/open_last_folder", self.last_folder_checkbox.isChecked())

        self.settings.sync()
        self.settings_changed.emit()
        self.accept()
