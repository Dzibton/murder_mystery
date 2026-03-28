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
    # Check that Lord Blackwood's slide heading appears before Miss Scarlet's slide heading
    lord_heading = content.index('<h2>Lord Blackwood</h2>')
    scarlet_heading = content.index('<h2>Miss Scarlet</h2>')
    assert lord_heading < scarlet_heading
