import csv
import io
import base64
import os
from datetime import timezone
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, current_app, Response as FlaskResponse)
import qrcode
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
    any_response_map = {}
    for r in all_responses:
        name = r.character_name
        any_response_map[name] = True
        if not r.is_duplicate:
            submitted_map[name] = True
        if r.is_duplicate:
            duplicate_counts[name] = duplicate_counts.get(name, 0) + 1

    # Include characters who have any response (even all-duplicate) in submitted list
    submitted = [
        (c, duplicate_counts.get(c, 0))
        for c in characters
        if c in submitted_map or c in any_response_map
    ]
    pending = [c for c in characters if c not in any_response_map]

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
