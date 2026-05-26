import json
from typing import Dict, List, Optional

from services.providers.registry import detect_provider, create_provider, get_provider_config
from storage.database import Database

class AccountManager:
    def __init__(self, db: Database):
        self._db = db
        self._accounts: Dict[str, Dict] = {}
        self._active_email: Optional[str] = None
        self._load_accounts()

    def _load_accounts(self):
        accounts = self._db.load_accounts()
        for acc in accounts:
            email = acc["email"]
            saved = acc["config"] if isinstance(acc["config"], dict) else json.loads(acc["config"] or "{}")
            self._accounts[email] = {
                "email": email,
                "provider": acc["provider"],
                "provider_instance": None,
                "config": saved,
            }
        if self._accounts:
            self._active_email = next(iter(self._accounts))

    def add_account(self, email: str, config: Optional[Dict] = None):
        provider_name = detect_provider(email)
        if isinstance(config, dict) and ("config" in config or "credentials" in config):
            saved_config = config
            inner_config = config.get("config", config)
            credentials = config.get("credentials", {})
        else:
            saved_config = {
                "config": config or {},
                "credentials": {}
            }
            inner_config = config or {}
            credentials = {}

        provider = create_provider(email, credentials=credentials, config=inner_config)
        if hasattr(provider, "_password") and provider._password:
            saved_config["credentials"]["password"] = provider._password

        self._accounts[email] = {
            "email": email,
            "provider": provider_name,
            "provider_instance": provider,
            "config": saved_config,
        }
        self._db.save_account(email, provider_name, saved_config)
        self._active_email = email

    # New method as requested
    def add_account_with_provider(self, email: str, provider, config: Optional[Dict] = None):
        """Add an account when a provider instance is already created.

        Args:
            email: Email address of the account.
            provider: The already‑instantiated provider (or provider name string).
            config: Optional configuration dictionary.
        """
        provider_name = detect_provider(email)
        if isinstance(config, dict) and ("config" in config or "credentials" in config):
            saved_config = config
            inner_config = config.get("config", config)
            credentials = config.get("credentials", {})
        else:
            inner_config = config or {}
            credentials = {}
            saved_config = None

        # Ensure we have a provider instance
        if isinstance(provider, str):
            # If only name passed, create instance
            provider_instance = create_provider(email, credentials=credentials, config=inner_config)
        else:
            provider_instance = provider
        # Reconnect if possible (ignore failures)
        try:
            provider_instance.connect()
        except Exception:
            pass

        if saved_config is None:
            saved_config = {
                "config": inner_config,
                "credentials": {}
            }
            if hasattr(provider_instance, "_password") and provider_instance._password:
                saved_config["credentials"]["password"] = provider_instance._password

        self._accounts[email] = {
            "email": email,
            "provider": provider_name,
            "provider_instance": provider_instance,
            "config": saved_config,
        }
        self._db.save_account(email, provider_name, saved_config)
        self._active_email = email

    def remove_account(self, email: str):
        if email in self._accounts:
            del self._accounts[email]
            self._db.delete_account(email)
            if self._active_email == email:
                self._active_email = next(iter(self._accounts), None)

    def get_accounts(self) -> List[Dict]:
        return list(self._accounts.values())

    def get_provider(self, email: Optional[str] = None):
        email = email or self._active_email
        if not email:
            return None
        acc = self._accounts.get(email)
        if not acc:
            raise KeyError(f"Account {email} not found")
        provider = acc.get("provider_instance")
        if provider is None:
            # lazily create provider if not loaded
            saved = acc["config"] if isinstance(acc["config"], dict) else json.loads(acc["config"] or "{}")
            config = saved.get("config", saved)
            credentials = saved.get("credentials", {})
            provider = create_provider(email, credentials=credentials, config=config)
            acc["provider_instance"] = provider
        return provider

    def set_active_account(self, email: str):
        if email in self._accounts:
            self._active_email = email

    def get_active_provider(self):
        return self.get_provider(self._active_email)

