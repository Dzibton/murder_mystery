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
