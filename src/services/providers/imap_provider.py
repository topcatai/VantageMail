# -*- coding: utf-8 -*-

import imapclient
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email import message_from_bytes
from email.header import decode_header, make_header

from services.providers.base import MailProvider, ProviderError
from utils.logger import log_info, log_error


def _has_attachments_from_structure(structure) -> bool:
    if not structure:
        return False
    if isinstance(structure[0], (list, tuple)):
        for part in structure:
            if isinstance(part, (list, tuple)):
                if _has_attachments_from_structure(part):
                    return True
        return False
    else:
        if len(structure) > 2:
            params = structure[2]
            if isinstance(params, (list, tuple)):
                for i in range(0, len(params) - 1, 2):
                    key = params[i]
                    if isinstance(key, bytes):
                        key = key.upper()
                    if isinstance(key, str):
                        key = key.upper()
                    if key in (b'NAME', 'NAME', b'FILENAME', 'FILENAME'):
                        return True
        for item in structure:
            if isinstance(item, bytes):
                item_str = item.decode('utf-8', errors='replace').upper()
                if 'ATTACHMENT' in item_str:
                    return True
            elif isinstance(item, str):
                if 'ATTACHMENT' in item.upper():
                    return True
            elif isinstance(item, (list, tuple)):
                if _has_attachments_from_structure(item):
                    return True
        return False


class ImapProvider(MailProvider):
    def __init__(self, email: str, password: str, imap_host: str, imap_port: int,
                 smtp_host: str, smtp_port: int):
        self._email = email
        self._password = password
        self._imap_host = imap_host
        self._imap_port = imap_port
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._imap = None
        self._smtp = None
        self._lock = threading.Lock()

    @property
    def provider_name(self) -> str:
        return 'IMAP'

    @property
    def account_email(self) -> str:
        return self._email

    def _ensure_connected(self):
        need_connect = False
        if self._imap is None:
            need_connect = True
        else:
            try:
                self._imap.noop()
            except Exception:
                need_connect = True
                try:
                    self._imap.logout()
                except Exception:
                    pass
                self._imap = None
                
        if need_connect:
            try:
                self._imap = imapclient.IMAPClient(
                    self._imap_host,
                    port=self._imap_port,
                    ssl=True,
                    timeout=10
                )
                self._imap.login(self._email, self._password)
            except Exception as e:
                self._imap = None
                raise ProviderError(f"IMAP connection failed: {e}")

    def connect(self):
        with self._lock:
            self._ensure_connected()

    def disconnect(self) -> None:
        with self._lock:
            try:
                if self._imap:
                    self._imap.logout()
                    self._imap = None
                if self._smtp:
                    self._smtp.quit()
                    self._smtp = None
            except Exception:
                pass

    def fetch_folders(self):
        with self._lock:
            self._ensure_connected()
            try:
                log_info("fetch_folders: calling list_folders")
                raw = self._imap.list_folders()
                log_info(f"fetch_folders: got {len(raw)} folders")
                folders = []
                for flags, delim, name in raw:
                    display = name
                    if isinstance(name, str):
                        display = name.replace('INBOX.', '', 1) if name.startswith('INBOX.') else name
                    elif isinstance(name, bytes):
                        name = name.decode('utf-8', errors='replace')
                        display = name.replace('INBOX.', '', 1) if name.startswith('INBOX.') else name
                    if display.upper() == 'INBOX':
                        display = 'Inbox'
                    unread = 0
                    folders.append({
                        'id': name,
                        'display_name': display,
                        'unread': unread
                    })
                log_info(f"fetch_folders: returning {len(folders)} folders")
                return folders
            except Exception as e:
                log_error(f"fetch_folders ERROR: {e}")
                raise ProviderError(f"fetch_folders failed: {e}")

    def get_folder_unread_count(self, folder_id: str) -> int:
        with self._lock:
            self._ensure_connected()
            try:
                status = self._imap.folder_status(folder_id, ['UNSEEN'])
                return status.get(b'UNSEEN', 0)
            except Exception:
                return 0

    def fetch_messages(self, folder_id, limit: int = None, search_term=None):
        with self._lock:
            self._ensure_connected()
            try:
                self._imap.select_folder(folder_id)
                if search_term:
                    uids = self._imap.search(['TEXT', search_term])
                else:
                    uids = self._imap.search(['ALL'])
                if limit is not None:
                    latest_uids = uids[-limit:] if len(uids) > limit else uids
                else:
                    latest_uids = uids
                messages = []
                if latest_uids:
                    data = self._imap.fetch(latest_uids, ['ENVELOPE', 'FLAGS', 'BODYSTRUCTURE'])
                else:
                    data = {}
                for uid in reversed(latest_uids):
                    msg_data = data.get(uid)
                    if not msg_data:
                        continue
                    env = msg_data.get(b'ENVELOPE')
                    flags = msg_data.get(b'FLAGS', [])
                    if not env:
                        continue
                    subject = ''
                    sender = ''
                    date = ''
                    try:
                        if env.subject:
                            raw_subj = env.subject
                            if isinstance(raw_subj, bytes):
                                raw_subj = raw_subj.decode('utf-8', errors='replace')
                            subject = str(make_header(decode_header(raw_subj)))
                        else:
                            subject = ''
                    except Exception:
                        subject = str(env.subject) if env.subject else ''
                    try:
                        if env.from_:
                            mb = env.from_[0].mailbox
                            host = env.from_[0].host
                            mb = mb.decode('utf-8', errors='replace') if isinstance(mb, bytes) else str(mb)
                            host = host.decode('utf-8', errors='replace') if isinstance(host, bytes) else str(host)
                            sender = f"{mb}@{host}"
                    except Exception:
                        sender = ''
                    try:
                        date = env.date.isoformat() if env.date else ''
                    except Exception:
                        date = ''
                    has_attachment = False
                    bodystructure = msg_data.get(b'BODYSTRUCTURE')
                    if bodystructure:
                        has_attachment = _has_attachments_from_structure(bodystructure)
                    messages.append({
                        'id': uid,
                        'subject': subject,
                        'sender': sender,
                        'date': date,
                        'is_read': b'\\Seen' in flags,
                        'has_attachment': has_attachment
                    })
                return messages
            except Exception as e:
                raise ProviderError(f"fetch_messages failed: {e}")

    def fetch_message_body(self, message_id, folder_id=None):
        with self._lock:
            self._ensure_connected()
            try:
                try:
                    msg_id_val = int(message_id)
                except ValueError:
                    msg_id_val = message_id

                if folder_id:
                    self._imap.select_folder(folder_id)
                raw = self._imap.fetch([msg_id_val], ['RFC822'])
                
                key = msg_id_val
                if key not in raw:
                    try:
                        key = int(msg_id_val)
                    except ValueError:
                        pass
                if key not in raw:
                    try:
                        key = str(msg_id_val)
                    except ValueError:
                        pass
                if key not in raw and raw:
                    key = list(raw.keys())[0]
                
                if key not in raw:
                    return {
                        'body': "<p style='color:#ff5555;font-weight:bold;'>Error: Unable to fetch message body from server.</p><p>The message may have been deleted on the server, or the folder structure may have changed. Please try refreshing the folder.</p>",
                        'attachments': []
                    }
                msg_bytes = raw[key].get(b'RFC822') or raw[key].get(b'BODY[]')
                if not msg_bytes:
                    return {
                        'body': "<p style='color:#ff5555;font-weight:bold;'>Error: Unable to fetch message body from server.</p><p>The message may have been deleted on the server, or the folder structure may have changed. Please try refreshing the folder.</p>",
                        'attachments': []
                    }
                msg = message_from_bytes(msg_bytes)
                
                body_html = ''
                body_text = ''
                attachments = []
                
                for part in msg.walk():
                    filename = part.get_filename()
                    if filename:
                        try:
                            decoded = decode_header(filename)
                            filename = str(make_header(decoded))
                        except Exception:
                            pass
                        
                        payload = part.get_payload(decode=True)
                        if payload is not None:
                            import base64
                            data_b64 = base64.b64encode(payload).decode('utf-8')
                            attachments.append({
                                'filename': filename,
                                'content_type': part.get_content_type(),
                                'data': data_b64,
                                'size': len(payload)
                            })
                    else:
                        content_type = part.get_content_type()
                        disposition = str(part.get('content-disposition') or '')
                        if content_type == 'text/html' and 'attachment' not in disposition:
                            charset = part.get_content_charset() or 'utf-8'
                            body_html = part.get_payload(decode=True).decode(charset, errors='replace')
                        elif content_type == 'text/plain' and 'attachment' not in disposition:
                            charset = part.get_content_charset() or 'utf-8'
                            body_text = part.get_payload(decode=True).decode(charset, errors='replace')
                
                if not msg.is_multipart():
                    charset = msg.get_content_charset() or 'utf-8'
                    body_html = msg.get_payload(decode=True).decode(charset, errors='replace')
                    
                body = body_html or body_text
                return {
                    'body': body,
                    'attachments': attachments
                }
            except Exception as e:
                raise ProviderError(f"fetch_message_body failed: {e}")

    def send_message(self, to, subject, body, cc=None, attachments=None):
        try:
            smtp = smtplib.SMTP_SSL(self._smtp_host, self._smtp_port, timeout=30)
            smtp.login(self._email, self._password)
            msg = MIMEMultipart()
            msg['From'] = self._email
            msg['To'] = ', '.join(to) if isinstance(to, (list, tuple)) else to
            if cc:
                msg['Cc'] = ', '.join(cc) if isinstance(cc, (list, tuple)) else cc
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))
            if attachments:
                for att in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(att['data'])
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition',
                                    f"attachment; filename=\"{att['filename']}\"")
                    msg.attach(part)
            all_recipients = (to if isinstance(to, list) else [to]) + (cc or [])
            smtp.sendmail(self._email, all_recipients, msg.as_string())
            try:
                smtp.quit()
            except Exception:
                pass  # ignore cleanup timeout — email was sent successfully
        except Exception as e:
            raise ProviderError(f"send_message failed: {e}")

    def delete_message(self, message_id, folder_id=None):
        with self._lock:
            self._ensure_connected()
            try:
                if folder_id:
                    self._imap.select_folder(folder_id)
                self._imap.delete_messages([message_id])
                self._imap.expunge()
            except Exception as e:
                raise ProviderError(f"delete_message failed: {e}")

    def move_message(self, message_id, folder_id, from_folder_id=None):
        with self._lock:
            self._ensure_connected()
            try:
                if from_folder_id:
                    self._imap.select_folder(from_folder_id)
                self._imap.move([message_id], folder_id)
            except Exception:
                try:
                    self._imap.copy([message_id], folder_id)
                    self._imap.delete_messages([message_id])
                    self._imap.expunge()
                except Exception as e:
                    raise ProviderError(f"move_message failed: {e}")

    def mark_read(self, message_id, read: bool = True, folder_id=None):
        with self._lock:
            self._ensure_connected()
            try:
                if folder_id:
                    self._imap.select_folder(folder_id)
                flag = b'\\Seen'
                if read:
                    self._imap.add_flags([message_id], [flag])
                else:
                    self._imap.remove_flags([message_id], [flag])
            except Exception as e:
                raise ProviderError(f"mark_read failed: {e}")

    def fetch_raw_email(self, message_id, folder_id=None) -> bytes:
        with self._lock:
            self._ensure_connected()
            try:
                if folder_id:
                    self._imap.select_folder(folder_id)
                raw = self._imap.fetch([message_id], ['RFC822'])
                return raw[message_id][b'RFC822']
            except Exception as e:
                raise ProviderError(f"fetch_raw_email failed: {e}")