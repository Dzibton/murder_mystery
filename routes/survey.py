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
