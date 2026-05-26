from services.providers.base import MailProvider, ProviderError
from config import GMAIL_CREDENTIALS_PATH, GMAIL_SCOPES
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64, email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

class GmailProvider(MailProvider):
    def __init__(self, email_address: str):
        self._email = email_address
        self._service = None

    @property
    def provider_name(self) -> str:
        return 'Gmail'

    @property
    def account_email(self) -> str:
        return self._email

    def connect(self) -> None:
        flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_PATH, GMAIL_SCOPES)
        creds = flow.run_local_server(port=0)
        self._service = build('gmail', 'v1', credentials=creds)

    def disconnect(self) -> None:
        self._service = None

    def fetch_folders(self):
        return self._service.users().labels().list(userId='me').execute()

    def fetch_messages(self, folder_id, limit=50, **kwargs):
        result = self._service.users().messages().list(userId='me', labelIds=[folder_id], maxResults=limit).execute()
        return result.get('messages', [])

    def fetch_message_body(self, message_id):
        msg = self._service.users().messages().get(userId='me', id=message_id, format='raw').execute()
        raw = base64.urlsafe_b64decode(msg['raw'])
        email_msg = email.message_from_bytes(raw)
        if email_msg.is_multipart():
            for part in email_msg.walk():
                if part.get_content_type() == 'text/html':
                    return part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8')
                if part.get_content_type() == 'text/plain':
                    return part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8')
        else:
            return email_msg.get_payload(decode=True).decode(email_msg.get_content_charset() or 'utf-8')
        return ''

    def send_message(self, to, subject, body, cc=None, attachments=None):
        message = MIMEMultipart()
        message['to'] = ', '.join(to) if isinstance(to, (list, tuple)) else to
        if cc:
            message['cc'] = ', '.join(cc) if isinstance(cc, (list, tuple)) else cc
        message['subject'] = subject
        message.attach(MIMEText(body, 'html'))
        if attachments:
            for att in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(att['data'])
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename=\"{att['filename']}\"")
                message.attach(part)
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return self._service.users().messages().send(userId='me', body={'raw': raw}).execute()

    def delete_message(self, message_id):
        return self._service.users().messages().trash(userId='me', id=message_id).execute()

    def move_message(self, message_id, folder_id):
        return self._service.users().messages().modify(userId='me', id=message_id, body={'removeLabelIds': [], 'addLabelIds': [folder_id]}).execute()

    def mark_read(self, message_id):
        return self._service.users().messages().modify(userId='me', id=message_id, body={'removeLabelIds': ['UNREAD']}).execute()
