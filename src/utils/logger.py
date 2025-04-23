import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from flask import Flask


def setup_logger(app: Flask) -> logging.Logger:  # pragma: no cover
    if not os.path.exists("../../logs"):
        os.makedirs("../../logs")

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    file_handler = RotatingFileHandler("../../logs/app.log", maxBytes=5000, backupCount=5)
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
