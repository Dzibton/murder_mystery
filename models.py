from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Response(db.Model):
    __tablename__ = "responses"

    id = db.Column(db.Integer, primary_key=True)
    character_name = db.Column(db.String(100), nullable=False)
    answers = db.Column(db.JSON, nullable=False)
    submitted_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    is_duplicate = db.Column(db.Boolean, nullable=False, default=False)
