import os
from flask import Flask
from dotenv import load_dotenv
from models import db
from config_loader import load_config, ConfigError

load_dotenv()


def create_app(testing=False):
    app = Flask(__name__)

    if testing:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret"
        app.config["APP_CONFIG"] = {
            "characters": ["Lord Blackwood", "Miss Scarlet"],
            "questions": [
                {"id": "name", "text": "Your name?", "type": "dropdown"},
                {"id": "accuse", "text": "Who?", "type": "dropdown"},
                {"id": "why", "text": "Why?", "type": "text"},
                {"id": "best_dressed", "text": "Best dressed?", "type": "dropdown"},
                {"id": "best_actor", "text": "Best actor?", "type": "dropdown"},
                {"id": "money", "text": "Money?", "type": "text"},
                {"id": "how_money", "text": "How?", "type": "text"},
            ],
        }
    else:
        raw_url = os.environ.get("DATABASE_URL", "")
        if raw_url.startswith("postgres://"):
            raw_url = raw_url.replace("postgres://", "postgresql+psycopg2://", 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = raw_url
        app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", os.urandom(24))
        try:
            app.config["APP_CONFIG"] = load_config()
        except ConfigError as e:
            raise RuntimeError(f"Failed to load config: {e}")

    db.init_app(app)

    return app


# Only run at startup, not on test imports
if os.environ.get("FLASK_TESTING") != "1":
    app = create_app()
    with app.app_context():
        db.create_all()
else:
    app = None
