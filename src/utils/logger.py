# -*- coding: utf-8 -*-
import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler

# Project root directory
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOG_DIR = os.path.join(ROOT_DIR, "logs")

# Ensure the logs directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Configure logger
logger = logging.getLogger("VantageMail")
logger.setLevel(logging.INFO)
logger.handlers.clear()

# Daily rotating file handler (keeps 7 days)
log_file = os.path.join(LOG_DIR, "app.log")
file_handler = TimedRotatingFileHandler(
    log_file,
    when="D",
    interval=1,
    backupCount=7,
    encoding="utf-8"
)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Stdout console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def log_info(msg: str):
    logger.info(msg)

def log_error(msg: str, exc_info=None):
    logger.error(msg, exc_info=exc_info)

def log_critical(msg: str, exc_info=None):
    logger.critical(msg, exc_info=exc_info)

def log_realtime_count(db):
    try:
        count = db.get_total_email_count()
        logger.info(f"STATS: Realtime total email count in cache: {count}")
    except Exception as e:
        logger.error(f"Failed to fetch realtime email count: {e}")

def log_app_start(db):
    logger.info("Application starting up...")
    log_realtime_count(db)

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Uncaught Exception / Application Crash:", exc_info=(exc_type, exc_value, exc_traceback))
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

def register_crash_hook():
    sys.excepthook = handle_exception
