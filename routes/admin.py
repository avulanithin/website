from __future__ import annotations

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from database import models
from services.scoring import calculate_match_score


bp = Blueprint("admin", __name__, url_prefix="/admin")


def _is_admin() -> bool:
    """Admin gate.

    IMPORTANT: This enforces server-side access control for `/admin/debug`.
    Only the user whose email equals `Config.ADMIN_EMAIL` may access.
    """
    user_id = session.get("user_id")
    if not user_id:
        return False

    user = models.get_user_by_id(current_app.config["DB_PATH"], int(user_id))
    admin_email = (current_app.config.get("ADMIN_EMAIL") or "").strip().lower()
    return bool(user and user.get("email", "").lower() == admin_email)


@bp.get("/debug")
def debug_view():
    if not _is_admin():
        flash("Admin access required.", "error")
        return redirect(url_for("match.dashboard"))

    db_path = current_app.config["DB_PATH"]
    users = models.list_users(db_path)
    profiles = models.list_profiles(db_path)

    # Quick match tool: select two profile IDs via query params
    a_id = request.args.get("a")
    b_id = request.args.get("b")
    match_result = None

    if a_id and b_id:
        try:
            pa = models.get_profile_by_id(db_path, int(a_id))
            pb = models.get_profile_by_id(db_path, int(b_id))
            if pa and pb:
                score, breakdown = calculate_match_score(pa, pb)
                match_result = {"a": pa, "b": pb, "score": score, "breakdown": breakdown}
        except Exception:
            match_result = None

    return render_template(
        "admin_debug.html",
        users=users,
        profiles=profiles,
        match_result=match_result,
    )


@bp.post("/set-verified")
def set_verified():
    if not _is_admin():
        flash("Admin access required.", "error")
        return redirect(url_for("match.dashboard"))

    db_path = current_app.config["DB_PATH"]
    try:
        profile_id = int((request.form.get("profile_id") or "0").strip())
        value = (request.form.get("value") or "0").strip()
        is_verified = bool(int(value))
    except Exception:
        flash("Invalid request.", "error")
        return redirect(url_for("admin.debug_view"))

    if not models.get_profile_by_id(db_path, profile_id):
        flash("Profile not found.", "error")
        return redirect(url_for("admin.debug_view"))

    models.set_profile_verified(db_path, profile_id=profile_id, value=is_verified)
    flash("Verification updated.", "success")
    return redirect(url_for("admin.debug_view"))
