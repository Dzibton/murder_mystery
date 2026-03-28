import os
from flask import Flask, redirect, url_for
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
        secret = os.environ.get("SECRET_KEY")
        if not secret:
            raise RuntimeError("SECRET_KEY environment variable must be set")
        app.config["SECRET_KEY"] = secret
        try:
            app.config["APP_CONFIG"] = load_config()
        except ConfigError as e:
            raise RuntimeError(f"Failed to load config: {e}")

    db.init_app(app)

    from routes.survey import survey_bp
    app.register_blueprint(survey_bp)

    from routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

    from routes.slideshow import slideshow_bp
    app.register_blueprint(slideshow_bp)

    @app.route("/")
    def root():
        return redirect(url_for("survey.survey"))

    return app


app = create_app(testing=os.environ.get("FLASK_TESTING") == "1")
with app.app_context():
    db.create_all()
