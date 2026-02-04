from __future__ import annotations

from flask import Blueprint, current_app, flash, redirect, request, session, url_for

from database import models


bp = Blueprint("interest", __name__, url_prefix="/interest")


def _require_login():
    if not session.get("user_id"):
        flash("Please login to continue.", "error")
        return redirect(url_for("auth.login_get"))
    return None


@bp.post("/send/<int:user_id>")
def send_interest(user_id: int):
    """Send an interest from the logged-in user to the target user."""
    guard = _require_login()
    if guard:
        return guard

    from_user_id = int(session["user_id"])
    to_user_id = int(user_id)

    if from_user_id == to_user_id:
        flash("You cannot send interest to yourself.", "error")
        return redirect(url_for("match.dashboard"))

    db_path = current_app.config["DB_PATH"]

    # Ensure the target user exists before creating interest.
    if not models.get_user_by_id(db_path, to_user_id):
        flash("User not found.", "error")
        return redirect(url_for("match.dashboard"))

    existing = models.get_interest_between_users(db_path, from_user_id, to_user_id)
    if not existing:
        models.create_interest(db_path, from_user_id=from_user_id, to_user_id=to_user_id)
        flash("Interest sent.", "success")
    else:
        # One-interest-per-unordered-pair logic:
        # - If a reverse pending exists (they already sent you interest), auto-accept it
        #   instead of creating a new row.
        # - If any interest already exists (pending/accepted/rejected), block duplicates.
        status = (existing.get("status") or "").strip().lower()
        ex_from = int(existing.get("from_user_id"))
        ex_to = int(existing.get("to_user_id"))

        reverse_pending = status == "pending" and ex_from == to_user_id and ex_to == from_user_id
        if reverse_pending:
            models.respond_to_interest(db_path, interest_id=int(existing["id"]), action="accepted")
            flash("Interest accepted.", "success")
        else:
            if status == "pending":
                flash("Interest already pending.", "error")
            elif status == "accepted":
                flash("Interest already accepted.", "error")
            elif status == "rejected":
                flash("Interest already rejected.", "error")
            else:
                flash("Interest already exists.", "error")

    next_url = (request.form.get("next") or "").strip()
    return redirect(next_url or url_for("match.dashboard"))


@bp.post("/respond/<int:interest_id>/<action>")
def respond_interest(interest_id: int, action: str):
    """Respond to an incoming interest (accept/reject)."""
    guard = _require_login()
    if guard:
        return guard

    if action not in {"accepted", "rejected"}:
        flash("Invalid action.", "error")
        return redirect(url_for("match.dashboard"))

    db_path = current_app.config["DB_PATH"]
    me = int(session["user_id"])

    # Security: only the recipient (to_user_id) can respond.
    # Fresh DB read every request.
    conn = models.get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM interests WHERE id = ?", (interest_id,)).fetchone()
    finally:
        conn.close()

    if not row:
        flash("Interest not found.", "error")
        return redirect(url_for("match.dashboard"))

    # Only the receiver can respond.
    if int(row["to_user_id"]) != me:
        flash("Not allowed.", "error")
        return redirect(url_for("match.dashboard"))

    # Sender cannot respond to their own interest.
    if int(row["from_user_id"]) == me:
        flash("Not allowed.", "error")
        return redirect(url_for("match.dashboard"))

    if row.get("status") != "pending":
        flash("Interest already responded.", "error")
        return redirect(url_for("match.dashboard"))

    models.respond_to_interest(db_path, interest_id=interest_id, action=action)
    flash(f"Interest {action}.", "success")
    return redirect(url_for("match.dashboard"))
