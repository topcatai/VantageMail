# -*- coding: utf-8 -*-
import sys
import os
from cx_Freeze import setup, Executable

# Project root files/folders to include
include_files = [
    ("icons_Vantage Mail", "icons_Vantage Mail")
]

# cx_Freeze build options
build_exe_options = {
    "packages": [
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "PyQt6.QtWebEngineWidgets",
        "sqlite3",
        "json",
        "logging",
        "imapclient",
        "smtplib",
        "msal",
        "icalendar",
        "email"
    ],
    "includes": [
        "win32cred",
        "win32security",
        "win32api"
    ],
    "include_files": include_files,
    "excludes": ["tkinter"]
}

# MSI installer shortcut table config
# Columns: Shortcut, Directory_, Name, Component_, Target, Arguments, Description, Hotkey, Icon, IconIndex, ShowCmd, WkDir
shortcut_table = [
    (
        "DesktopShortcut",             # Shortcut identifier
        "DesktopFolder",               # Directory_ (Where to place it)
        "Vantage Mail",                # Name
        "TARGETDIR",                   # Component_
        "[TARGETDIR]VantageMail.exe",  # Target
        None,                          # Arguments
        "Vantage Mail Desktop Shortcut", # Description
        None,                          # Hotkey
        None,                          # Icon
        None,                          # IconIndex
        None,                          # ShowCmd
        "TARGETDIR"                    # WkDir (Working Directory)
    ),
    (
        "StartMenuShortcut",           # Shortcut identifier
        "ProgramMenuFolder",           # Directory_ (Where to place it)
        "Vantage Mail",                # Name
        "TARGETDIR",                   # Component_
        "[TARGETDIR]VantageMail.exe",  # Target
        None,                          # Arguments
        "Vantage Mail Start Menu Shortcut", # Description
        None,                          # Hotkey
        None,                          # Icon
        None,                          # IconIndex
        None,                          # ShowCmd
        "TARGETDIR"                    # WkDir (Working Directory)
    )
]

# Directory hierarchy for AppData Local
directory_table = [
    ("LocalAppDataFolder", "TARGETDIR", "."),
    ("VantageMailDataFolder", "LocalAppDataFolder", "VantageMail"),
    ("VantageMailLogsFolder", "VantageMailDataFolder", "logs"),
    ("VantageMailCacheFolder", "VantageMailDataFolder", "cache"),
    ("VantageMailQtCacheFolder", "VantageMailCacheFolder", "qtpipelinecache-x86_64-little_endian-llp64")
]

# Remove registry keys under HKCU on uninstall
remove_registry_table = [
    ("VantageMailRegCleanup", 1, r"Software\TakshiqSoftLabs\VantageMail", "-", "TARGETDIR"),
    ("VantageMailVendorRegCleanup", 1, r"Software\TakshiqSoftLabs", None, "TARGETDIR")
]

# Remove all database files and folders from AppData Local on uninstall
remove_file_table = [
    # 1. Clean files and folder for Qt Cache
    ("CleanQtCacheFiles", "TARGETDIR", "*", "VantageMailQtCacheFolder", 2),
    ("CleanQtCacheFolder", "TARGETDIR", None, "VantageMailQtCacheFolder", 2),

    # 2. Clean files and folder for Cache root
    ("CleanCacheFiles", "TARGETDIR", "*", "VantageMailCacheFolder", 2),
    ("CleanCacheFolder", "TARGETDIR", None, "VantageMailCacheFolder", 2),

    # 3. Clean files and folder for Logs
    ("CleanLogsFiles", "TARGETDIR", "*", "VantageMailLogsFolder", 2),
    ("CleanLogsFolder", "TARGETDIR", None, "VantageMailLogsFolder", 2),

    # 4. Clean files and folder for VantageMail root (database, wal, shm)
    ("CleanCachedFiles", "TARGETDIR", "*", "VantageMailDataFolder", 2),
    ("CleanCachedFolder", "TARGETDIR", None, "VantageMailDataFolder", 2)
]

msi_data = {
    "Shortcut": shortcut_table,
    "Directory": directory_table,
    "RemoveRegistry": remove_registry_table,
    "RemoveFile": remove_file_table
}

bdist_msi_options = {
    "upgrade_code": "{8A5D6B2C-7C4E-4A9B-9B2D-2F3D4E5F6A7B}",
    "add_to_path": False,
    "initial_target_dir": "[ProgramFilesFolder]\\VantageMail",
    "install_icon": "icons_Vantage Mail/app_icon.ico",
    "all_users": True,
    "data": msi_data
}

base = None
if sys.platform == "win32":
    base = "gui"  # Run GUI base to suppress command prompt window

executables = [
    Executable(
        script="src/main.py",
        base=base,
        target_name="VantageMail.exe",
        icon="icons_Vantage Mail/app_icon.ico"
    )
]

setup(
    name="VantageMail",
    version="1.0.1",
    description="Vantage Mail Email Client",
    author="Vantage Mail Developer",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options
    },
    executables=executables
)
