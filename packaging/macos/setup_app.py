# -*- coding: utf-8 -*-
from setuptools import setup

APP = ['../../src/main.py']
DATA_FILES = [
    ('icons_Vantage Mail', [
        '../../icons_Vantage Mail/Vantage trans_Logo.png', 
        '../../icons_Vantage Mail/Vantage white_Logo.png',
        '../../icons_Vantage Mail/Vantage_Loading_Logo.mp4',
        '../../icons_Vantage Mail/paperclip.png',
        '../../icons_Vantage Mail/vm-logo-txt.jpg',
        '../../icons_Vantage Mail/vm-logo.jpg',
        '../../icons_Vantage Mail/vm-video.mp4',
        '../../icons_Vantage Mail/app_icon.icns'
    ])
]
OPTIONS = {
    'argv_emulation': False,
    'iconfile': '../../icons_Vantage Mail/app_icon.icns',
    'plist': {
        'CFBundleName': 'VantageMail',
        'CFBundleDisplayName': 'Vantage Mail',
        'CFBundleIdentifier': 'com.takshiq.vantagemail',
        'CFBundleVersion': '1.0.1',
        'CFBundleShortVersionString': '1.0.1',
        'NSHumanReadableCopyright': 'Copyright (c) 2026, All Rights Reserved',
    },
    'packages': ['PyQt6', 'sqlite3', 'json', 'logging', 'imapclient', 'smtplib', 'msal', 'icalendar', 'requests'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
