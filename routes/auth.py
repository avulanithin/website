from __future__ import annotations

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database import models


bp = Blueprint("auth", __name__, url_prefix="/auth")


def _is_logged_in() -> bool:
    return bool(session.get("user_id"))


@bp.get("/register")
def register_get():
    if _is_logged_in():
        return redirect(url_for("match.dashboard"))
    return render_template("register.html")


@bp.post("/register")
def register_post():
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    confirm = request.form.get("confirm") or ""

    if not email or "@" not in email:
        flash("Please enter a valid email.", "error")
        return redirect(url_for("auth.register_get"))
    if len(password) < 8:
        flash("Password must be at least 8 characters.", "error")
        return redirect(url_for("auth.register_get"))
    if password != confirm:
        flash("Passwords do not match.", "error")
        return redirect(url_for("auth.register_get"))

    db_path = current_app.config["DB_PATH"]
    existing = models.get_user_by_email(db_path, email)
    if existing:
        flash("Email already registered. Please login.", "error")
        return redirect(url_for("auth.login_get"))

    password_hash = generate_password_hash(password)
    models.create_user(db_path, email, password_hash)

    # Clean auth flow: after successful registration, redirect to login.
    # No hardcoded/admin credentials; everything is DB-driven.
    flash("Account created. Please sign in.", "success")
    return redirect(url_for("auth.login_get"))


@bp.get("/login")
def login_get():
    if _is_logged_in():
        return redirect(url_for("match.dashboard"))
    return render_template("login.html")


@bp.post("/login")
def login_post():
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    if not email or not password:
        flash("Email and password are required.", "error")
        return redirect(url_for("auth.login_get"))

    db_path = current_app.config["DB_PATH"]
    user = models.get_user_by_email(db_path, email)
    if not user or not check_password_hash(user["password_hash"], password):
        flash("Invalid credentials.", "error")
        return redirect(url_for("auth.login_get"))

    session.clear()
    session["user_id"] = user["id"]
    flash("Welcome back!", "success")
    return redirect(url_for("match.dashboard"))


@bp.get("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("auth.login_get"))
