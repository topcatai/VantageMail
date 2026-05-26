def detect_provider(email: str) -> str:
    domain = email.split('@')[-1].lower()
    if domain in ('outlook.com', 'hotmail.com', 'live.com', 'msn.com'):
        return 'microsoft'
    if domain.endswith('gmail.com'):
        return 'gmail'
    if domain.endswith('yahoo.com'):
        return 'yahoo'
    if domain.endswith('icloud.com'):
        return 'icloud'
    return 'generic'

PROVIDER_CONFIGS = {
    'yahoo': {
        'imap': {'host': 'imap.mail.yahoo.com', 'port': 993},
        'smtp': {'host': 'smtp.mail.yahoo.com', 'port': 587},
    },
    'icloud': {
        'imap': {'host': 'imap.mail.me.com', 'port': 993},
        'smtp': {'host': 'smtp.mail.me.com', 'port': 587},
    },
}

def get_provider_config(provider_name: str) -> dict:
    return PROVIDER_CONFIGS.get(provider_name, {})

def create_provider(email: str, credentials=None, config=None):
    provider = detect_provider(email)
    if provider == 'gmail':
        from .gmail_provider import GmailProvider
        return GmailProvider(email)
    elif provider == 'microsoft':
        from .graph_provider import GraphProvider
        token = credentials.get('token') if credentials else None
        return GraphProvider(email, token)
    else:
        from .imap_provider import ImapProvider
        cfg = config or get_provider_config(provider)
        imap = cfg.get('imap', {})
        smtp = cfg.get('smtp', {})
        return ImapProvider(email, credentials.get('password') if credentials else '', imap.get('host'), imap.get('port'), smtp.get('host'), smtp.get('port'))
