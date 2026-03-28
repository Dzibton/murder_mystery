# Murder Mystery Survey App — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Flask web app where murder mystery guests fill out a survey on their phones, a PIN-protected dashboard shows attendance and exports responses, and a slideshow displays each character's answers for Chromecast casting.

**Architecture:** Flask app with a PostgreSQL backend (SQLAlchemy), deployed to Railway via GitHub push. `config.yaml` is the single source of truth for character names and questions. Three route blueprints (survey, dashboard, slideshow) keep responsibilities separated.

**Tech Stack:** Flask, Flask-SQLAlchemy, psycopg2-binary, qrcode[pil], PyYAML, gunicorn, python-dotenv, pytest

---

## File Map

| File | Responsibility |
|---|---|
| `app.py` | App factory — creates Flask app, loads config, inits DB, registers blueprints |
| `config_loader.py` | Loads and validates `config.yaml`, caches result, raises on missing/malformed |
| `models.py` | SQLAlchemy `Response` model |
| `routes/survey.py` | `GET/POST /survey`, `GET /thank-you` |
| `routes/dashboard.py` | `GET/POST /dashboard/login`, `GET /dashboard`, `GET /dashboard/export` |
| `routes/slideshow.py` | `GET /slideshow` |
| `templates/base.html` | Shared HTML shell, CSS variables, mobile viewport |
| `templates/survey.html` | Survey form — dynamic from config |
| `templates/thank_you.html` | Post-submit confirmation |
| `templates/dashboard/login.html` | PIN entry form |
| `templates/dashboard/index.html` | Dashboard: QR code, submitted/pending lists, buttons |
| `templates/slideshow.html` | Full-screen slideshow with prev/next |
| `static/style.css` | Shared styles (dark murder mystery theme) |
| `config.yaml` | Character names + question definitions |
| `Procfile` | `web: gunicorn app:app` |
| `.env.example` | Documents required env vars |
| `tests/conftest.py` | pytest fixtures: test app, test client, seeded DB |
| `tests/test_config_loader.py` | Config loading and validation |
| `tests/test_models.py` | Response model creation and duplicate detection |
| `tests/test_survey.py` | Survey form submission, duplicate flagging, thank-you redirect |
| `tests/test_dashboard.py` | PIN auth, dashboard content, CSV export format |
| `tests/test_slideshow.py` | Slideshow ordering, duplicate resolution, slide content |

---

## Task 1: Project Setup

**Files:**
- Modify: `requirements.txt`
- Create: `Procfile`
- Create: `.env.example`
- Create: `config.yaml`
- Create: `routes/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Update requirements.txt**

Replace the contents of `requirements.txt` with:

```
Flask==3.1.3
Flask-SQLAlchemy==3.1.1
psycopg2-binary==2.9.10
qrcode[pil]==8.0
PyYAML==6.0.2
gunicorn==23.0.0
python-dotenv==1.0.1
pytest==8.3.5
pytest-flask==1.3.0
```

- [ ] **Step 2: Install dependencies**

```bash
source venv/Scripts/activate
pip install -r requirements.txt
```

- [ ] **Step 3: Create Procfile**

```
web: gunicorn app:app
```

- [ ] **Step 4: Create .env.example**

```
DATABASE_URL=postgresql+psycopg2://localhost/murder_mystery
DASHBOARD_PIN=1234
PUBLIC_URL=http://localhost:5000
```

- [ ] **Step 5: Create config.yaml**

```yaml
characters:
  - Lord Blackwood
  - Lady Crimson
  - Col. Mustard
  - Miss Scarlet
  - Dr. Venom
  - Prof. Plum
  - Mrs. White
  - Rev. Green
  - Sgt. Grey
  - Baroness Blue
  - Countess Coral
  - Duke Diamond
  - Earl Emerald
  - Fiona Flame
  - Gus Gold
  - Harriet Haze
  - Ivan Ivory
  - Jade Jester
  - Kit Krimson
  - Luna Lace

questions:
  - id: name
    text: "What's your name?"
    type: dropdown
  - id: accuse
    text: "Who do you accuse of murder?"
    type: dropdown
  - id: why
    text: "Why do you accuse them?"
    type: text
  - id: best_dressed
    text: "Who was best dressed?"
    type: dropdown
  - id: best_actor
    text: "Who was the best actor/actress?"
    type: dropdown
  - id: money
    text: "How much money did you end with?"
    type: text
  - id: how_money
    text: "How did you get/lose your money?"
    type: text
```

- [ ] **Step 6: Create routes/__init__.py and tests/__init__.py (empty files)**

```bash
mkdir -p routes tests
touch routes/__init__.py tests/__init__.py
```

- [ ] **Step 7: Commit**

```bash
git add requirements.txt Procfile .env.example config.yaml routes/__init__.py tests/__init__.py
git commit -m "chore: project setup — deps, config, procfile"
```

---

## Task 2: Config Loader

**Files:**
- Create: `config_loader.py`
- Create: `tests/test_config_loader.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_config_loader.py`:

```python
import pytest
import yaml
from config_loader import load_config, ConfigError


def test_load_valid_config(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({
        "characters": ["Alice", "Bob"],
        "questions": [
            {"id": "name", "text": "Your name?", "type": "dropdown"},
            {"id": "why", "text": "Why?", "type": "text"},
        ]
    }))
    config = load_config(str(config_file))
    assert config["characters"] == ["Alice", "Bob"]
    assert len(config["questions"]) == 2


def test_missing_config_raises(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(str(tmp_path / "missing.yaml"))


def test_missing_characters_raises(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({"questions": []}))
    with pytest.raises(ConfigError, match="characters"):
        load_config(str(config_file))


def test_missing_questions_raises(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({"characters": ["Alice"]}))
    with pytest.raises(ConfigError, match="questions"):
        load_config(str(config_file))


def test_missing_name_question_raises(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({
        "characters": ["Alice"],
        "questions": [{"id": "why", "text": "Why?", "type": "text"}]
    }))
    with pytest.raises(ConfigError, match="name"):
        load_config(str(config_file))
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_config_loader.py -v
```

Expected: 5 errors — `config_loader` module not found.

- [ ] **Step 3: Implement config_loader.py**

```python
import yaml


class ConfigError(Exception):
    pass


def load_config(path="config.yaml"):
    try:
        with open(path, "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        raise ConfigError(f"config.yaml not found at {path}")
    except yaml.YAMLError as e:
        raise ConfigError(f"config.yaml is malformed: {e}")

    if not config.get("characters"):
        raise ConfigError("config.yaml must define a non-empty 'characters' list")
    if "questions" not in config:
        raise ConfigError("config.yaml must define a 'questions' list")

    ids = [q.get("id") for q in config["questions"]]
    if "name" not in ids:
        raise ConfigError("config.yaml questions must include a question with id 'name'")

    return config
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_config_loader.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add config_loader.py tests/test_config_loader.py
git commit -m "feat: config loader with validation"
```

---

## Task 3: Database Model

**Files:**
- Create: `models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_models.py`:

```python
import pytest
from datetime import datetime, timezone
from app import create_app
from models import db, Response


@pytest.fixture
def app():
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


def test_create_response(app):
    with app.app_context():
        r = Response(
            character_name="Lord Blackwood",
            answers={"name": "Lord Blackwood", "accuse": "Miss Scarlet", "why": "She did it"},
            is_duplicate=False,
        )
        db.session.add(r)
        db.session.commit()
        saved = Response.query.first()
        assert saved.character_name == "Lord Blackwood"
        assert saved.answers["accuse"] == "Miss Scarlet"
        assert saved.is_duplicate is False
        assert isinstance(saved.submitted_at, datetime)


def test_duplicate_flag(app):
    with app.app_context():
        r1 = Response(character_name="Alice", answers={"name": "Alice"}, is_duplicate=False)
        r2 = Response(character_name="Alice", answers={"name": "Alice"}, is_duplicate=True)
        db.session.add_all([r1, r2])
        db.session.commit()
        dupes = Response.query.filter_by(character_name="Alice", is_duplicate=True).all()
        assert len(dupes) == 1
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_models.py -v
```

Expected: errors — `app` and `models` modules not found.

- [ ] **Step 3: Create models.py**

```python
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
```

- [ ] **Step 4: Create app.py (minimal, enough for model tests)**

```python
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
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
pytest tests/test_models.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add models.py app.py tests/test_models.py
git commit -m "feat: Response model and app factory"
```

---

## Task 4: Survey Routes

**Files:**
- Create: `routes/survey.py`
- Create: `templates/base.html`
- Create: `templates/survey.html`
- Create: `templates/thank_you.html`
- Create: `static/style.css`
- Create: `tests/test_survey.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_survey.py`:

```python
import pytest
from app import create_app
from models import db, Response


@pytest.fixture
def app():
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_survey_get(client):
    response = client.get("/survey")
    assert response.status_code == 200
    assert b"What&#39;s your name?" in response.data or b"Your name?" in response.data


def test_survey_post_creates_response(client, app):
    data = {
        "name": "Lord Blackwood",
        "accuse": "Miss Scarlet",
        "why": "She was there",
        "best_dressed": "Lord Blackwood",
        "best_actor": "Miss Scarlet",
        "money": "1000",
        "how_money": "Won a bet",
    }
    resp = client.post("/survey", data=data, follow_redirects=False)
    assert resp.status_code == 302
    assert "/thank-you" in resp.headers["Location"]

    with app.app_context():
        saved = Response.query.first()
        assert saved.character_name == "Lord Blackwood"
        assert saved.is_duplicate is False


def test_survey_duplicate_flagged(client, app):
    data = {
        "name": "Lord Blackwood",
        "accuse": "Miss Scarlet",
        "why": "She was there",
        "best_dressed": "Lord Blackwood",
        "best_actor": "Miss Scarlet",
        "money": "1000",
        "how_money": "Won a bet",
    }
    client.post("/survey", data=data)
    client.post("/survey", data=data)

    with app.app_context():
        responses = Response.query.filter_by(character_name="Lord Blackwood").all()
        assert len(responses) == 2
        assert responses[0].is_duplicate is False
        assert responses[1].is_duplicate is True


def test_survey_requires_name(client):
    resp = client.post("/survey", data={"accuse": "Miss Scarlet"}, follow_redirects=False)
    assert resp.status_code == 200
    assert b"required" in resp.data.lower() or resp.status_code == 200


def test_thank_you_not_duplicate(client, app):
    with client.session_transaction() as sess:
        sess["last_submission"] = {"character_name": "Lord Blackwood", "is_duplicate": False}
    resp = client.get("/thank-you")
    assert resp.status_code == 200
    assert b"Lord Blackwood" in resp.data
    assert b"recorded" in resp.data


def test_thank_you_duplicate(client, app):
    with client.session_transaction() as sess:
        sess["last_submission"] = {"character_name": "Lord Blackwood", "is_duplicate": True}
    resp = client.get("/thank-you")
    assert resp.status_code == 200
    assert b"already submitted" in resp.data
```

- [ ] **Step 2: Run to confirm they fail**

```bash
pytest tests/test_survey.py -v
```

Expected: errors — blueprint not registered.

- [ ] **Step 3: Create routes/survey.py**

```python
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
from models import db, Response

survey_bp = Blueprint("survey", __name__)


@survey_bp.route("/survey", methods=["GET", "POST"])
def survey():
    config = current_app.config["APP_CONFIG"]
    if request.method == "POST":
        character_name = request.form.get("name", "").strip()
        if not character_name:
            return render_template("survey.html", config=config, error="Please select your name.")

        answers = {q["id"]: request.form.get(q["id"], "").strip() for q in config["questions"]}

        existing = Response.query.filter_by(character_name=character_name).first()
        is_duplicate = existing is not None

        response = Response(
            character_name=character_name,
            answers=answers,
            is_duplicate=is_duplicate,
        )
        db.session.add(response)
        db.session.commit()

        session["last_submission"] = {
            "character_name": character_name,
            "is_duplicate": is_duplicate,
        }
        return redirect(url_for("survey.thank_you"))

    return render_template("survey.html", config=config)


@survey_bp.route("/thank-you")
def thank_you():
    submission = session.get("last_submission")
    return render_template("thank_you.html", submission=submission)
```

- [ ] **Step 4: Register blueprint in app.py**

Add to `create_app()` before `return app`:

```python
from routes.survey import survey_bp
app.register_blueprint(survey_bp)
```

- [ ] **Step 5: Create templates/base.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Murder Mystery{% endblock %}</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
  <div class="container">
    {% block content %}{% endblock %}
  </div>
</body>
</html>
```

- [ ] **Step 6: Create static/style.css**

```css
:root {
  --bg: #1a1a2e;
  --surface: #16213e;
  --accent: #e94560;
  --green: #4ecca3;
  --yellow: #f6c90e;
  --text: #e0e0e0;
  --muted: #888;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: Georgia, serif;
  min-height: 100vh;
}

.container {
  max-width: 600px;
  margin: 0 auto;
  padding: 24px 16px;
}

h1 { color: var(--accent); font-size: 1.6rem; margin-bottom: 8px; }
h2 { color: var(--accent); font-size: 1.3rem; margin-bottom: 16px; }

.card {
  background: var(--surface);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}

label {
  display: block;
  font-size: 0.75rem;
  text-transform: uppercase;
  color: var(--accent);
  letter-spacing: 0.05em;
  margin-bottom: 6px;
}

select, input[type="text"], textarea {
  width: 100%;
  background: var(--bg);
  color: var(--text);
  border: 1px solid #333;
  border-radius: 6px;
  padding: 12px;
  font-size: 1rem;
  font-family: Georgia, serif;
  appearance: none;
}

select { cursor: pointer; }

textarea { min-height: 80px; resize: vertical; }

.btn {
  display: inline-block;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 14px 28px;
  font-size: 1rem;
  font-family: Georgia, serif;
  cursor: pointer;
  text-decoration: none;
  text-align: center;
}

.btn-secondary {
  background: var(--surface);
  border: 1px solid #444;
}

.btn-full { width: 100%; margin-top: 8px; }

.error { color: var(--accent); font-size: 0.9rem; margin-bottom: 12px; }

.dot-green::before { content: "● "; color: var(--green); }
.dot-grey::before  { content: "○ "; color: var(--muted); }
.warn::before      { content: "⚠ "; color: var(--yellow); }

.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.slide-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.slide-full { grid-column: 1 / -1; }

.slide-label {
  font-size: 0.7rem;
  text-transform: uppercase;
  color: var(--accent);
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}

.slide-value { font-size: 1rem; }

.nav-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.counter { color: var(--muted); font-size: 0.9rem; }

.qr-center { text-align: center; margin-bottom: 24px; }
.qr-center img { max-width: 200px; border-radius: 8px; }
.qr-center p { color: var(--muted); font-size: 0.85rem; margin-top: 8px; }

.button-row {
  display: flex;
  gap: 10px;
  margin-top: 20px;
  flex-wrap: wrap;
}

.col-heading {
  font-size: 0.75rem;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 8px;
  letter-spacing: 0.05em;
}

.character-list { list-style: none; line-height: 2; }
```

- [ ] **Step 7: Create templates/survey.html**

```html
{% extends "base.html" %}
{% block title %}Survey — Murder Mystery{% endblock %}
{% block content %}
<h1>🔪 Murder Mystery Survey</h1>
<p style="color: var(--muted); margin-bottom: 20px;">Fill in your answers below.</p>

{% if error %}
<p class="error">{{ error }}</p>
{% endif %}

<form method="post" action="/survey">
  {% for q in config.questions %}
  <div class="card">
    <label for="{{ q.id }}">{{ q.text }}</label>
    {% if q.type == "dropdown" %}
    <select name="{{ q.id }}" id="{{ q.id }}" {% if q.id == "name" %}required{% endif %}>
      <option value="">— select —</option>
      {% for char in config.characters %}
      <option value="{{ char }}">{{ char }}</option>
      {% endfor %}
    </select>
    {% else %}
    <textarea name="{{ q.id }}" id="{{ q.id }}" rows="3"></textarea>
    {% endif %}
  </div>
  {% endfor %}
  <button type="submit" class="btn btn-full">Submit</button>
</form>
{% endblock %}
```

- [ ] **Step 8: Create templates/thank_you.html**

```html
{% extends "base.html" %}
{% block title %}Thank You — Murder Mystery{% endblock %}
{% block content %}
<h1>🔪 Murder Mystery</h1>
{% if submission %}
  {% if submission.is_duplicate %}
  <div class="card">
    <p>Thanks <strong>{{ submission.character_name }}</strong> — looks like you may have already submitted. Your response was recorded but flagged for review.</p>
  </div>
  {% else %}
  <div class="card">
    <p>Thanks <strong>{{ submission.character_name }}</strong>! Your response has been recorded.</p>
  </div>
  {% endif %}
{% else %}
<div class="card"><p>Your response has been recorded.</p></div>
{% endif %}
{% endblock %}
```

- [ ] **Step 9: Run tests to confirm they pass**

```bash
pytest tests/test_survey.py -v
```

Expected: 6 passed.

- [ ] **Step 10: Commit**

```bash
git add routes/survey.py templates/ static/ tests/test_survey.py app.py
git commit -m "feat: survey form, thank-you page, base template and styles"
```

---

## Task 5: Dashboard Routes

**Files:**
- Create: `routes/dashboard.py`
- Create: `templates/dashboard/login.html`
- Create: `templates/dashboard/index.html`
- Create: `tests/test_dashboard.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_dashboard.py`:

```python
import csv
import io
import pytest
from app import create_app
from models import db, Response


@pytest.fixture
def app():
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    client.post("/dashboard/login", data={"pin": "1234"})
    return client


def test_dashboard_redirects_unauthenticated(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 302
    assert "/dashboard/login" in resp.headers["Location"]


def test_login_correct_pin(client):
    resp = client.post("/dashboard/login", data={"pin": "1234"}, follow_redirects=False)
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]


def test_login_wrong_pin(client):
    resp = client.post("/dashboard/login", data={"pin": "9999"})
    assert resp.status_code == 200
    assert b"Incorrect" in resp.data


def test_dashboard_shows_characters(auth_client, app):
    with app.app_context():
        db.session.add(Response(
            character_name="Lord Blackwood",
            answers={"name": "Lord Blackwood"},
            is_duplicate=False,
        ))
        db.session.commit()
    resp = auth_client.get("/dashboard")
    assert resp.status_code == 200
    assert b"Lord Blackwood" in resp.data
    assert b"Miss Scarlet" in resp.data  # pending character from test config


def test_dashboard_flags_duplicate(auth_client, app):
    with app.app_context():
        db.session.add(Response(
            character_name="Lord Blackwood",
            answers={"name": "Lord Blackwood"},
            is_duplicate=True,
        ))
        db.session.commit()
    resp = auth_client.get("/dashboard")
    assert b"\u26a0" in resp.data or b"duplicate" in resp.data.lower()


def test_csv_export_headers(auth_client, app):
    with app.app_context():
        db.session.add(Response(
            character_name="Lord Blackwood",
            answers={
                "name": "Lord Blackwood",
                "accuse": "Miss Scarlet",
                "why": "She did it",
                "best_dressed": "Lord Blackwood",
                "best_actor": "Miss Scarlet",
                "money": "500",
                "how_money": "Won",
            },
            is_duplicate=False,
        ))
        db.session.commit()
    resp = auth_client.get("/dashboard/export")
    assert resp.status_code == 200
    assert "text/csv" in resp.content_type
    reader = csv.DictReader(io.StringIO(resp.data.decode("utf-8")))
    rows = list(reader)
    assert len(rows) == 1
    assert "character_name" in reader.fieldnames
    assert "submitted_at" in reader.fieldnames
    assert "is_duplicate" in reader.fieldnames


def test_csv_export_requires_auth(client):
    resp = client.get("/dashboard/export")
    assert resp.status_code == 302
```

- [ ] **Step 2: Run to confirm they fail**

```bash
pytest tests/test_dashboard.py -v
```

Expected: errors — blueprint not registered.

- [ ] **Step 3: Create routes/dashboard.py**

```python
import csv
import io
import base64
import os
from datetime import timezone
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, current_app, Response as FlaskResponse)
import qrcode
import qrcode.image.svg
from models import db, Response

dashboard_bp = Blueprint("dashboard", __name__)


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("dashboard.login"))
        return f(*args, **kwargs)
    return decorated


def generate_qr_base64(url):
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


@dashboard_bp.route("/dashboard/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        pin = request.form.get("pin", "").strip()
        correct = os.environ.get("DASHBOARD_PIN", "1234")
        if pin == correct:
            session["authenticated"] = True
            return redirect(url_for("dashboard.index"))
        error = "Incorrect PIN. Try again."
    return render_template("dashboard/login.html", error=error)


@dashboard_bp.route("/dashboard")
@login_required
def index():
    config = current_app.config["APP_CONFIG"]
    characters = config["characters"]

    all_responses = Response.query.all()
    submitted_map = {}
    duplicate_counts = {}
    for r in all_responses:
        name = r.character_name
        if not r.is_duplicate:
            submitted_map[name] = True
        if r.is_duplicate:
            duplicate_counts[name] = duplicate_counts.get(name, 0) + 1

    submitted = [(c, duplicate_counts.get(c, 0)) for c in characters if c in submitted_map]
    pending = [c for c in characters if c not in submitted_map]

    public_url = os.environ.get("PUBLIC_URL", "http://localhost:5000")
    qr_data = generate_qr_base64(f"{public_url}/survey")

    return render_template(
        "dashboard/index.html",
        submitted=submitted,
        pending=pending,
        qr_data=qr_data,
    )


@dashboard_bp.route("/dashboard/export")
@login_required
def export():
    config = current_app.config["APP_CONFIG"]
    questions = config["questions"]

    responses = Response.query.order_by(Response.submitted_at).all()

    output = io.StringIO()
    fieldnames = (
        ["submitted_at", "character_name", "is_duplicate"]
        + [q["text"] for q in questions]
    )
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for r in responses:
        row = {
            "submitted_at": r.submitted_at.astimezone(timezone.utc).isoformat(),
            "character_name": r.character_name,
            "is_duplicate": r.is_duplicate,
        }
        for q in questions:
            row[q["text"]] = r.answers.get(q["id"], "")
        writer.writerow(row)

    return FlaskResponse(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=responses.csv"},
    )
```

- [ ] **Step 4: Register blueprint in app.py**

Add to `create_app()` before `return app`:

```python
from routes.dashboard import dashboard_bp
app.register_blueprint(dashboard_bp)
```

- [ ] **Step 5: Create templates/dashboard/login.html**

```bash
mkdir -p templates/dashboard
```

```html
{% extends "base.html" %}
{% block title %}Dashboard Login{% endblock %}
{% block content %}
<h1>🔪 Host Dashboard</h1>
<div class="card" style="margin-top: 32px;">
  <form method="post">
    <label for="pin">Enter PIN</label>
    <input type="password" name="pin" id="pin" autocomplete="off" autofocus
           style="font-size: 1.5rem; letter-spacing: 0.3em; text-align: center;">
    {% if error %}<p class="error" style="margin-top: 10px;">{{ error }}</p>{% endif %}
    <button type="submit" class="btn btn-full" style="margin-top: 16px;">Unlock</button>
  </form>
</div>
{% endblock %}
```

- [ ] **Step 6: Create templates/dashboard/index.html**

```html
{% extends "base.html" %}
{% block title %}Dashboard — Murder Mystery{% endblock %}
{% block content %}
<h1>🔪 Murder Mystery</h1>

<div class="qr-center">
  <img src="data:image/png;base64,{{ qr_data }}" alt="QR code for survey">
  <p>Scan to fill out the survey</p>
</div>

<div class="two-col">
  <div>
    <p class="col-heading">Submitted ({{ submitted|length }})</p>
    <ul class="character-list">
      {% for name, dupe_count in submitted %}
      <li>
        {% if dupe_count > 0 %}
        <span class="warn">{{ name }} ({{ dupe_count + 1 }} submissions)</span>
        {% else %}
        <span class="dot-green">{{ name }}</span>
        {% endif %}
      </li>
      {% endfor %}
    </ul>
  </div>
  <div>
    <p class="col-heading">Pending ({{ pending|length }})</p>
    <ul class="character-list">
      {% for name in pending %}
      <li><span class="dot-grey">{{ name }}</span></li>
      {% endfor %}
    </ul>
  </div>
</div>

<div class="button-row">
  <a href="/dashboard/export" class="btn btn-secondary">⬇ Export CSV</a>
  <a href="/slideshow" class="btn">▶ View Slideshow</a>
</div>
{% endblock %}
```

- [ ] **Step 7: Run tests to confirm they pass**

```bash
pytest tests/test_dashboard.py -v
```

Expected: 7 passed.

- [ ] **Step 8: Commit**

```bash
git add routes/dashboard.py templates/dashboard/ tests/test_dashboard.py app.py
git commit -m "feat: dashboard with PIN auth, QR code, attendance list, CSV export"
```

---

## Task 6: Slideshow Route

**Files:**
- Create: `routes/slideshow.py`
- Create: `templates/slideshow.html`
- Create: `tests/test_slideshow.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_slideshow.py`:

```python
import pytest
from app import create_app
from models import db, Response
from datetime import datetime, timezone, timedelta


@pytest.fixture
def app():
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_slideshow_empty(client):
    resp = client.get("/slideshow")
    assert resp.status_code == 200
    assert b"No responses" in resp.data or b"0" in resp.data


def test_slideshow_shows_submitted_characters(client, app):
    with app.app_context():
        db.session.add(Response(
            character_name="Lord Blackwood",
            answers={"name": "Lord Blackwood", "accuse": "Miss Scarlet",
                     "why": "Did it", "best_dressed": "Lord Blackwood",
                     "best_actor": "Miss Scarlet", "money": "500", "how_money": "Won"},
            is_duplicate=False,
        ))
        db.session.commit()
    resp = client.get("/slideshow")
    assert resp.status_code == 200
    assert b"Lord Blackwood" in resp.data
    assert b"Miss Scarlet" in resp.data


def test_slideshow_uses_latest_for_duplicate(client, app):
    with app.app_context():
        t1 = datetime.now(timezone.utc) - timedelta(minutes=5)
        t2 = datetime.now(timezone.utc)
        db.session.add(Response(
            character_name="Lord Blackwood",
            answers={"name": "Lord Blackwood", "accuse": "Miss Scarlet",
                     "why": "Old reason", "best_dressed": "Lord Blackwood",
                     "best_actor": "Miss Scarlet", "money": "100", "how_money": "old"},
            is_duplicate=False, submitted_at=t1,
        ))
        db.session.add(Response(
            character_name="Lord Blackwood",
            answers={"name": "Lord Blackwood", "accuse": "Miss Scarlet",
                     "why": "New reason", "best_dressed": "Lord Blackwood",
                     "best_actor": "Miss Scarlet", "money": "200", "how_money": "new"},
            is_duplicate=True, submitted_at=t2,
        ))
        db.session.commit()
    resp = client.get("/slideshow")
    assert b"New reason" in resp.data
    assert b"Old reason" not in resp.data


def test_slideshow_ordered_by_config(client, app):
    with app.app_context():
        # Miss Scarlet appears before Lord Blackwood in config? No — Lord Blackwood is first.
        # Just confirm both appear and Lord Blackwood is first.
        for name in ["Miss Scarlet", "Lord Blackwood"]:
            db.session.add(Response(
                character_name=name,
                answers={"name": name, "accuse": "Miss Scarlet", "why": "x",
                         "best_dressed": name, "best_actor": name, "money": "0", "how_money": "x"},
                is_duplicate=False,
            ))
        db.session.commit()
    resp = client.get("/slideshow")
    content = resp.data.decode()
    assert content.index("Lord Blackwood") < content.index("Miss Scarlet")
```

- [ ] **Step 2: Run to confirm they fail**

```bash
pytest tests/test_slideshow.py -v
```

Expected: errors — blueprint not registered.

- [ ] **Step 3: Create routes/slideshow.py**

```python
from flask import Blueprint, render_template, current_app
from models import Response

slideshow_bp = Blueprint("slideshow", __name__)


@slideshow_bp.route("/slideshow")
def slideshow():
    config = current_app.config["APP_CONFIG"]
    characters = config["characters"]

    all_responses = Response.query.order_by(Response.submitted_at).all()

    # Build a map: character_name -> most recent response
    latest = {}
    for r in all_responses:
        if r.character_name not in latest or r.submitted_at > latest[r.character_name].submitted_at:
            latest[r.character_name] = r

    # Order slides by position in config characters list
    slides = [latest[c] for c in characters if c in latest]

    return render_template("slideshow.html", slides=slides, total=len(slides))
```

- [ ] **Step 4: Register blueprint in app.py**

Add to `create_app()` before `return app`:

```python
from routes.slideshow import slideshow_bp
app.register_blueprint(slideshow_bp)
```

- [ ] **Step 5: Create templates/slideshow.html**

```html
{% extends "base.html" %}
{% block title %}Slideshow — Murder Mystery{% endblock %}
{% block content %}
<div id="slideshow">
{% if slides %}
  {% for slide in slides %}
  <div class="slide" id="slide-{{ loop.index }}" style="display: {% if loop.first %}block{% else %}none{% endif %};">
    <div class="nav-row">
      <button class="btn btn-secondary" onclick="changeSlide(-1)" {% if loop.first %}disabled{% endif %}>◀ Prev</button>
      <span class="counter">{{ loop.index }} / {{ total }}</span>
      <button class="btn btn-secondary" onclick="changeSlide(1)" {% if loop.last %}disabled{% endif %}>Next ▶</button>
    </div>

    <h2>{{ slide.character_name }}</h2>

    <div class="slide-grid" style="margin-top: 16px;">
      <div class="card slide-full">
        <p class="slide-label">Accuses</p>
        <p class="slide-value">{{ slide.answers.get('accuse', '—') }}</p>
      </div>
      <div class="card slide-full">
        <p class="slide-label">Because</p>
        <p class="slide-value">{{ slide.answers.get('why', '—') }}</p>
      </div>
      <div class="card">
        <p class="slide-label">Best Dressed</p>
        <p class="slide-value">{{ slide.answers.get('best_dressed', '—') }}</p>
      </div>
      <div class="card">
        <p class="slide-label">Best Actor/Actress</p>
        <p class="slide-value">{{ slide.answers.get('best_actor', '—') }}</p>
      </div>
      <div class="card">
        <p class="slide-label">Money</p>
        <p class="slide-value">{{ slide.answers.get('money', '—') }}</p>
      </div>
      <div class="card">
        <p class="slide-label">How</p>
        <p class="slide-value">{{ slide.answers.get('how_money', '—') }}</p>
      </div>
    </div>
  </div>
  {% endfor %}
{% else %}
  <div class="card" style="text-align:center; margin-top: 40px;">
    <p>No responses yet.</p>
  </div>
{% endif %}
</div>

<script>
  let current = 1;
  const total = {{ total }};

  function changeSlide(dir) {
    const oldSlide = document.getElementById('slide-' + current);
    current = Math.max(1, Math.min(total, current + dir));
    const newSlide = document.getElementById('slide-' + current);
    if (oldSlide) oldSlide.style.display = 'none';
    if (newSlide) newSlide.style.display = 'block';
  }
</script>
{% endblock %}
```

- [ ] **Step 6: Run tests to confirm they pass**

```bash
pytest tests/test_slideshow.py -v
```

Expected: 4 passed.

- [ ] **Step 7: Run full test suite**

```bash
pytest -v
```

Expected: all tests pass.

- [ ] **Step 8: Commit**

```bash
git add routes/slideshow.py templates/slideshow.html tests/test_slideshow.py app.py
git commit -m "feat: slideshow with per-character slides, duplicate resolution, config ordering"
```

---

## Task 7: Railway Deployment

**Files:**
- Modify: `app.py` (add redirect from `/` to `/survey`)
- Modify: `.gitignore` (add `.env`)

- [ ] **Step 1: Add root redirect to app.py**

In `app.py`, after registering blueprints, add:

```python
from flask import redirect, url_for as _url_for

@app.route("/")
def index():
    return redirect(_url_for("survey.survey"))
```

- [ ] **Step 2: Add .env to .gitignore**

Add to `.gitignore`:
```
.env
```

- [ ] **Step 3: Push to GitHub**

```bash
git add app.py .gitignore
git commit -m "chore: root redirect to survey, add .env to gitignore"
git push origin master
```

- [ ] **Step 4: Set up Railway**

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click **New Project** → **Deploy from GitHub repo** → select `murder_mystery`
3. In the project, click **+ New** → **Database** → **Add PostgreSQL**
4. Click the web service → **Variables** → add:
   - `DASHBOARD_PIN` = your chosen PIN
   - `PUBLIC_URL` = the Railway-generated URL for your app (found under **Settings → Domains**)
   - `SECRET_KEY` = any long random string
5. Railway will auto-deploy. Watch the deploy logs — if it fails, check the **Logs** tab.

- [ ] **Step 5: Verify deployment**

Visit `https://your-app.up.railway.app/survey` — you should see the survey form.
Visit `https://your-app.up.railway.app/dashboard/login` — you should see the PIN screen.

- [ ] **Step 6: Update PUBLIC_URL**

Once you have the final Railway domain, update the `PUBLIC_URL` env var in Railway settings so the QR code points to the correct URL. Redeploy by pushing an empty commit if needed:

```bash
git commit --allow-empty -m "chore: trigger redeploy"
git push origin master
```
