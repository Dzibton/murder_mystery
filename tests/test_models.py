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
