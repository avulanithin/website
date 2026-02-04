from __future__ import annotations

from flask import Blueprint, current_app, flash, redirect, render_template, session, url_for

from database import models
from services.scoring import calculate_match_score
from services.completion import calculate_profile_completion


bp = Blueprint("match", __name__, url_prefix="")


def _require_login():
    if not session.get("user_id"):
        flash("Please login to continue.", "error")
        return redirect(url_for("auth.login_get"))
    return None


@bp.get("/")
def home():
    if session.get("user_id"):
        return redirect(url_for("match.dashboard"))
    return redirect(url_for("auth.login_get"))


@bp.get("/dashboard")
def dashboard():
    guard = _require_login()
    if guard:
        return guard

    db_path = current_app.config["DB_PATH"]
    current_profile = models.get_profile_by_user_id(db_path, int(session["user_id"]))
    if not current_profile:
        flash("Please complete your profile first.", "error")
        return redirect(url_for("profile.edit_profile"))

    candidates = models.list_other_profiles(db_path, int(session["user_id"]))

    # IMPORTANT: Scores are NEVER stored/cached.
    # They are recalculated on every request using the latest profile data.
    completion_percent = calculate_profile_completion(current_profile)

    suggestions = []
    for cand in candidates:
        score, breakdown = calculate_match_score(current_profile, cand)
        me_id = int(session["user_id"])
        cand_user_id = int(cand["user_id"])

        interest_row = models.get_interest_between_users(db_path, me_id, cand_user_id)
        interest_status = interest_row["status"] if interest_row else None
        interest_id = interest_row["id"] if interest_row else None

        # Direction is always evaluated from *my* perspective.
        # If I am the sender => outgoing, else incoming.
        interest_direction = None
        if interest_row:
            interest_direction = "outgoing" if int(interest_row["from_user_id"]) == me_id else "incoming"

        messaging_unlocked = bool(score >= 90 and interest_status == "accepted")
        suggestions.append(
            {
                "profile": cand,
                "score": score,
                "breakdown": breakdown,
                "can_view": score >= 90,
                "interest_status": interest_status,
                "interest_direction": interest_direction,
                "interest_id": interest_id,
                "messaging_unlocked": messaging_unlocked,
            }
        )

    suggestions.sort(key=lambda x: x["score"], reverse=True)

    return render_template(
        "dashboard.html",
        me=current_profile,
        completion_percent=completion_percent,
        suggestions=suggestions,
    )
