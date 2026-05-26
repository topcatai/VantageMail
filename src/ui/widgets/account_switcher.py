# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import QComboBox
from PyQt6.QtCore import pyqtSignal

class AccountSwitcher(QComboBox):
    account_changed = pyqtSignal(str)

    def __init__(self, account_manager, parent=None):
        super().__init__(parent)
        self.account_manager = account_manager
        self.currentIndexChanged.connect(self._on_index_changed)
        self.refresh()

    def refresh(self):
        self.blockSignals(True)
        self.clear()
        accounts = self.account_manager.get_accounts()
        for acc in accounts:
            email = acc.get('email') if isinstance(acc, dict) else getattr(acc, 'email', None)
            if email:
                self.addItem(email)
        self.blockSignals(False)

    def _on_index_changed(self, index):
        email = self.itemText(index)
        if email:
            self.account_changed.emit(email)
