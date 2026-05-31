# -*- coding: utf-8 -*-
import sys
from PyQt6.QtWidgets import QApplication
from storage.database import Database
from services.accounts.account_manager import AccountManager
from ui.main_window import MainWindow
from ui.splash_screen import SplashScreen
from PyQt6.QtCore import QSettings

# ── Microsoft 365 / Exchange (enable when Azure credentials are ready) ──
# from config import AZURE_CLIENT_ID, AZURE_AUTHORITY, AZURE_SCOPES
# from services.authentication import AuthenticationService
# from services.token_storage import TokenStorage
# from services.token_manager import TokenManager
# from services.providers.graph_provider import GraphProvider

# ── Gmail (enable when gmail_credentials.json is ready) ──
# from services.providers.gmail_provider import GmailProvider

# ── IMAP/SMTP — active now ──
from services.providers.imap_provider import ImapProvider

def main():
    from utils.logger import log_app_start, register_crash_hook
    register_crash_hook()

    db = Database()
    log_app_start(db)

    account_manager = AccountManager(db)

    # Clean up orphaned Windows Credential Manager generic credentials if no accounts exist
    if not account_manager.get_accounts():
        try:
            from services.token_storage import TokenStorage
            TokenStorage().delete_token()
        except Exception:
            pass

    # ── Microsoft 365 block — uncomment when Azure is ready ──────────────
    # if not AZURE_CLIENT_ID or AZURE_CLIENT_ID == 'your-azure-client-id':
    #     raise ValueError("Set AZURE_CLIENT_ID in src/config.py before running")
    # auth_service = AuthenticationService(
    #     client_id=AZURE_CLIENT_ID,
    #     authority=AZURE_AUTHORITY,
    #     scopes=AZURE_SCOPES,
    #     use_device_flow=True
    # )
    # token_storage = TokenStorage()
    # token_manager = TokenManager(auth_service, token_storage)
    # if not account_manager.get_accounts():
    #     provider = GraphProvider(token_manager)
    #     account_manager._providers['default'] = provider
    #     account_manager._active_email = 'default'

    # ── Gmail block — uncomment when gmail_credentials.json is ready ─────
    # if not account_manager.get_accounts():
    #     provider = GmailProvider('your@gmail.com')
    #     account_manager._providers['your@gmail.com'] = provider
    #     account_manager._active_email = 'your@gmail.com'

    # ── IMAP/SMTP — active now ────────────────────────────────────────────
    # Wizard launches automatically if no accounts saved
    if sys.platform == "win32":
        import ctypes
        try:
            myappid = 'takshiqsoftlabs.vantagemail.client.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    app = QApplication(sys.argv)
    
    from PyQt6.QtGui import QIcon
    import os
    icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "icons_Vantage Mail", "Vantage white_Logo.png"))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    settings = QSettings("TakshiqSoftLabs", "VantageMail")
    if not settings.value("splash/skip", False, type=bool):
        splash = SplashScreen()
        splash.exec()

    from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
    tray = None
    if QSystemTrayIcon.isSystemTrayAvailable():
        tray = QSystemTrayIcon(parent=app)
        if os.path.exists(icon_path):
            tray.setIcon(QIcon(icon_path))
        
        tray_menu = QMenu()
        def show_action():
            window.show()
            window.raise_()
            window.activateWindow()
        
        tray_menu.addAction("Open Vantage Mail", show_action)
        tray_menu.addAction("Quit", app.quit)
        tray.setContextMenu(tray_menu)
        
        tray_enabled = settings.value("notifications/tray_enabled", True, type=bool)
        if tray_enabled:
            tray.show()

    window = MainWindow(account_manager, tray=tray)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()