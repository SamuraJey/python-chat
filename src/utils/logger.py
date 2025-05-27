import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask


def setup_logger(app: Flask) -> logging.Logger:  # pragma: no cover
    logs_dir = os.path.join(app.root_path, "logs")  # Папка logs рядом с Flask-приложением
    Path(logs_dir).mkdir(parents=True, exist_ok=True)  # Создаём папку, если её нет
    
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    log_file = os.path.join(logs_dir, "app.log")
    file_handler = RotatingFileHandler(log_file, maxBytes=5000, backupCount=5)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Clear existing handlers to prevent duplication
    app.logger.handlers.clear()

    # Add handlers to app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.DEBUG)

    return app.logger
