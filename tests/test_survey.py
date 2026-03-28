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


def test_root_redirects_to_survey(client):
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/survey" in resp.headers["Location"]


def test_survey_get(client):
    response = client.get("/survey")
    assert response.status_code == 200
    assert b"Your name?" in response.data


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
    assert b"please select your name" in resp.data.lower()


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
