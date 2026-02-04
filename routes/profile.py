from __future__ import annotations

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from database import models
from services.image_upload import save_profile_image


bp = Blueprint("profile", __name__, url_prefix="/profile")


def _require_login():
    if not session.get("user_id"):
        flash("Please login to continue.", "error")
        return redirect(url_for("auth.login_get"))
    return None


@bp.get("/edit")
def edit_profile():
    guard = _require_login()
    if guard:
        return guard

    db_path = current_app.config["DB_PATH"]
    profile = models.get_profile_by_user_id(db_path, int(session["user_id"]))
    return render_template("profile_form.html", profile=profile)


@bp.post("/edit")
def save_profile():
    guard = _require_login()
    if guard:
        return guard

    db_path = current_app.config["DB_PATH"]
    user_id = int(session["user_id"])

    def get_int(name: str, default: int = 0) -> int:
        try:
            return int(request.form.get(name) or default)
        except Exception:
            return default

    # Basic validation
    full_name = (request.form.get("full_name") or "").strip()
    age = get_int("age")
    gender = (request.form.get("gender") or "").strip()

    if not full_name:
        flash("Full name is required.", "error")
        return redirect(url_for("profile.edit_profile"))
    if age < 18 or age > 80:
        flash("Age must be between 18 and 80.", "error")
        return redirect(url_for("profile.edit_profile"))
    if gender not in {"Male", "Female", "Other"}:
        flash("Please select a valid gender.", "error")
        return redirect(url_for("profile.edit_profile"))

    existing = models.get_profile_by_user_id(db_path, user_id) or {}

    image_filename = existing.get("image_filename")
    try:
        uploaded = save_profile_image(
            request.files.get("profile_image"),
            upload_folder=current_app.config["UPLOAD_FOLDER"],
            allowed_exts=current_app.config["ALLOWED_IMAGE_EXTENSIONS"],
        )
        if uploaded:
            image_filename = uploaded
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("profile.edit_profile"))

    profile_data = {
        "full_name": full_name,
        "age": age,
        "gender": gender,
        "height_cm": get_int("height_cm", 0) or None,
        "marital_status": (request.form.get("marital_status") or "").strip(),
        "location": (request.form.get("location") or "").strip(),
        "highest_education": (request.form.get("highest_education") or "").strip(),
        "occupation": (request.form.get("occupation") or "").strip(),
        "income_range": (request.form.get("income_range") or "").strip(),
        "smoking": (request.form.get("smoking") or "").strip(),
        "drinking": (request.form.get("drinking") or "").strip(),
        "medical_conditions": (request.form.get("medical_conditions") or "").strip(),
        "fitness_level": (request.form.get("fitness_level") or "").strip(),
        "pref_age_min": get_int("pref_age_min", 18),
        "pref_age_max": get_int("pref_age_max", 80),
        "pref_location": (request.form.get("pref_location") or "").strip(),
        "pref_education_level": (request.form.get("pref_education_level") or "").strip(),
        "image_filename": image_filename,
    }

    if profile_data["pref_age_min"] > profile_data["pref_age_max"]:
        flash("Preferred age min cannot exceed max.", "error")
        return redirect(url_for("profile.edit_profile"))

    required_fields = [
        "marital_status",
        "location",
        "highest_education",
        "occupation",
        "income_range",
        "smoking",
        "drinking",
        "medical_conditions",
        "fitness_level",
        "pref_location",
        "pref_education_level",
    ]
    for f in required_fields:
        if not profile_data[f]:
            flash("Please fill all required fields.", "error")
            return redirect(url_for("profile.edit_profile"))

    models.upsert_profile(db_path, user_id, profile_data)
    flash("Profile saved.", "success")
    return redirect(url_for("match.dashboard"))


@bp.get("/<int:profile_id>")
def view_profile(profile_id: int):
    """Profile view route.

    This page should only show full details if a match score >= 90
    between current user and the profile owner.

    The actual gating is implemented in `routes/match.py` where we compute score.
    Here we keep it simple and let the template decide based on `can_view`.
    """
    guard = _require_login()
    if guard:
        return guard

    db_path = current_app.config["DB_PATH"]
    current = models.get_profile_by_user_id(db_path, int(session["user_id"]))
    target = models.get_profile_by_id(db_path, profile_id)

    if not current or not target:
        flash("Profile not found (or your profile is incomplete).", "error")
        return redirect(url_for("match.dashboard"))

    # Match score is computed in dashboard; recompute here to avoid trusting client.
    from services.scoring import calculate_match_score

    score, breakdown = calculate_match_score(current, target)
    can_view = score >= 90

    # Interest state (fresh DB read). Messaging requires accepted.
    me_id = int(session["user_id"])
    target_user_id = int(target["user_id"])
    interest_row = models.get_interest_between_users(db_path, me_id, target_user_id)
    interest_status = interest_row["status"] if interest_row else None
    interest_id = interest_row["id"] if interest_row else None
    interest_direction = None
    if interest_row:
        interest_direction = "outgoing" if int(interest_row["from_user_id"]) == me_id else "incoming"
    messaging_unlocked = bool(score >= 90 and interest_status == "accepted")

    # STRICT 90% RULE (server-side):
    # If score is below threshold, do not expose full profile details.
    if not can_view:
        limited = {
            "id": target.get("id"),
            "user_id": target.get("user_id"),
            "full_name": target.get("full_name"),
            "location": target.get("location"),
            "image_filename": None,
        }
        return render_template(
            "profile_view.html",
            target=limited,
            score=score,
            breakdown=breakdown,
            can_view=False,
            interest_status=interest_status,
            interest_direction=interest_direction,
            interest_id=interest_id,
            messaging_unlocked=messaging_unlocked,
        )

    return render_template(
        "profile_view.html",
        target=target,
        score=score,
        breakdown=breakdown,
        can_view=True,
        interest_status=interest_status,
        interest_direction=interest_direction,
        interest_id=interest_id,
        messaging_unlocked=messaging_unlocked,
    )
