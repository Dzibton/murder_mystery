import csv
import io
import base64
import os
from datetime import timezone
from functools import wraps
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, current_app, Response as FlaskResponse)
import qrcode
from models import db, Response

dashboard_bp = Blueprint("dashboard", __name__)


def login_required(f):
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
        correct = current_app.config.get("DASHBOARD_PIN") or os.environ.get("DASHBOARD_PIN", "1234")
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

    # Group responses by character name
    response_counts = {}   # character_name -> total count
    duplicate_counts = {}  # character_name -> duplicate count
    for r in all_responses:
        response_counts[r.character_name] = response_counts.get(r.character_name, 0) + 1
        if r.is_duplicate:
            duplicate_counts[r.character_name] = duplicate_counts.get(r.character_name, 0) + 1

    # dupe_count = extras beyond the first response; flag all-duplicate sets too
    def _dupe_count(c):
        total = response_counts[c]
        dupes = duplicate_counts.get(c, 0)
        # If every response is a duplicate (all-duplicate case), show 1 extra
        if dupes == total:
            return total
        return total - 1

    submitted = [(c, _dupe_count(c)) for c in characters if c in response_counts]
    pending = [c for c in characters if c not in response_counts]

    public_url = os.environ.get("PUBLIC_URL", "http://localhost:5000")
    qr_data = generate_qr_base64(f"{public_url}/survey")

    return render_template(
        "dashboard/index.html",
        submitted=submitted,
        pending=pending,
        qr_data=qr_data,
    )


@dashboard_bp.route("/dashboard/results")
@login_required
def results():
    all_responses = Response.query.order_by(Response.submitted_at).all()

    # Use most recent response per character (same logic as slideshow)
    latest = {}
    for r in all_responses:
        latest[r.character_name] = r

    tally_questions = [
        ("accuse", "Who do you accuse of murder?"),
        ("best_dressed", "Who was best dressed?"),
        ("best_actor", "Who was the best actor/actress?"),
    ]

    tallies = {}
    for qid, _ in tally_questions:
        counts = {}
        for r in latest.values():
            vote = r.answers.get(qid, "").strip()
            if vote:
                counts[vote] = counts.get(vote, 0) + 1
        tallies[qid] = sorted(counts.items(), key=lambda x: x[1], reverse=True)

    return render_template(
        "dashboard/results.html",
        tally_questions=tally_questions,
        tallies=tallies,
        total_votes=len(latest),
        reset_error=request.args.get("reset_error"),
        reset_success=request.args.get("reset_success"),
    )


@dashboard_bp.route("/dashboard/reset", methods=["POST"])
@login_required
def reset():
    pin = request.form.get("pin", "").strip()
    correct = current_app.config.get("DASHBOARD_PIN") or os.environ.get("DASHBOARD_PIN", "1234")
    if pin != correct:
        return redirect(url_for("dashboard.results", reset_error="1"))
    db.session.query(Response).delete()
    db.session.commit()
    return redirect(url_for("dashboard.results", reset_success="1"))


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
