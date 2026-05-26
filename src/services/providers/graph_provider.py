from .base import MailProvider, ProviderError

# Assuming GraphMailService is defined elsewhere in the project
from services.mail.graph import GraphMailService

class GraphProvider(MailProvider):
    def __init__(self, account_email: str, token: str):
        self._email = account_email
        self._service = GraphMailService(token)

    @property
    def provider_name(self) -> str:
        return 'microsoft'

    @property
    def account_email(self) -> str:
        return self._email

    def connect(self) -> None:
        try:
            self._service.authenticate()
        except Exception as e:
            raise ProviderError(str(e))

    def disconnect(self) -> None:
        self._service.close()

    def fetch_folders(self):
        return self._service.list_folders()

    def fetch_messages(self, folder: str, **kwargs):
        return self._service.get_messages(folder)

    def fetch_message_body(self, msg_id: str):
        return self._service.get_message_body(msg_id)

    def send_message(self, to, subject, body, **kwargs):
        return self._service.send_email(to, subject, body, **kwargs)

    def delete_message(self, msg_id: str):
        self._service.delete_email(msg_id)

    def move_message(self, msg_id: str, folder: str):
        self._service.move_email(msg_id, folder)

    def mark_read(self, msg_id: str, read: bool = True):
        self._service.set_read_status(msg_id, read)
