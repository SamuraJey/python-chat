from typing import TYPE_CHECKING

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# Type handling for mypy
if TYPE_CHECKING:
    from flask_sqlalchemy.model import Model

    BaseModel = Model
else:
    BaseModel = db.Model
