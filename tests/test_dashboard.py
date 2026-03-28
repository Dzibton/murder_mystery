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
