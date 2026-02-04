from __future__ import annotations

from pathlib import Path

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from database import models
from services.image_upload import save_message_attachment
from services.permissions import can_message


bp = Blueprint("messages", __name__, url_prefix="")


def _require_login():
    if not session.get("user_id"):
        flash("Please login to continue.", "error")
        return redirect(url_for("auth.login_get"))
    return None


@bp.get("/messages/<int:user_id>")
def view_messages(user_id: int):
    guard = _require_login()
    if guard:
        return guard

    me = int(session["user_id"])
    other = int(user_id)

    if me == other:
        flash("Invalid chat target.", "error")
        return redirect(url_for("match.dashboard"))

    db_path = current_app.config["DB_PATH"]

    gate = can_message(db_path, from_user_id=me, to_user_id=other)
    if not gate.allowed:
        flash("Messaging is locked until match 90% and interest accepted.", "error")
        return redirect(url_for("match.dashboard"))

    other_user = models.get_user_by_id(db_path, other)
    other_profile = models.get_profile_by_user_id(db_path, other)
    if not other_user or not other_profile:
        flash("User not found.", "error")
        return redirect(url_for("match.dashboard"))

    messages = models.list_messages_between_users(db_path, me, other)

    return render_template(
        "messages.html",
        other_user=other_user,
        other_profile=other_profile,
        messages=messages,
        gate=gate,
    )


@bp.post("/messages/<int:user_id>")
def send_message(user_id: int):
    guard = _require_login()
    if guard:
        return guard

    me = int(session["user_id"])
    other = int(user_id)

    if me == other:
        flash("Invalid chat target.", "error")
        return redirect(url_for("match.dashboard"))

    db_path = current_app.config["DB_PATH"]

    gate = can_message(db_path, from_user_id=me, to_user_id=other)
    if not gate.allowed:
        flash("Messaging is locked until match 90% and interest accepted.", "error")
        return redirect(url_for("match.dashboard"))

    body = (request.form.get("body") or "").strip()
    if body and len(body) > 2000:
        flash("Message too long.", "error")
        return redirect(url_for("messages.view_messages", user_id=other))

    file = request.files.get("attachment")
    attachment_filename = None
    if file and file.filename:
        try:
            upload_folder = str(Path(current_app.root_path) / "static" / "uploads" / "messages")
            attachment_filename = save_message_attachment(
                file,
                upload_folder=upload_folder,
                allowed_exts={"jpg", "jpeg", "png", "webp"},
            )
        except ValueError as e:
            flash(str(e), "error")
            return redirect(url_for("messages.view_messages", user_id=other))

    if not body and not attachment_filename:
        flash("Message cannot be empty.", "error")
        return redirect(url_for("messages.view_messages", user_id=other))

    models.insert_message_v2(
        db_path,
        from_user_id=me,
        to_user_id=other,
        body=body or None,
        attachment_filename=attachment_filename,
    )
    return redirect(url_for("messages.view_messages", user_id=other))
