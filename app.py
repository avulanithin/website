from __future__ import annotations

import os

from flask import Flask
from flask_cors import CORS   # ✅ ADD THIS
from werkzeug.exceptions import RequestEntityTooLarge

from config import Config
from database import models
from routes import admin, auth, interest, match, messages, profile


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # ✅ ENABLE CORS (required for Netlify frontend → Railway backend)
    CORS(app, supports_credentials=True)

    # Ensure upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Init DB tables safely (CREATE TABLE IF NOT EXISTS).
    # IMPORTANT: Do not seed/reset the database.
    models.init_db(app.config["DB_PATH"])

    # Optional lightweight migration hook
    if hasattr(models, "migrate_db"):
        models.migrate_db(app.config["DB_PATH"])

    # Blueprints
    app.register_blueprint(auth.bp)
    app.register_blueprint(profile.bp)
    app.register_blueprint(match.bp)
    app.register_blueprint(interest.bp)
    app.register_blueprint(messages.bp)
    app.register_blueprint(admin.bp)

    @app.context_processor
    def inject_is_admin():
        """Expose `is_admin` to templates."""
        try:
            from flask import session

            user_id = session.get("user_id")
            if not user_id:
                return {"is_admin": False}

            user = models.get_user_by_id(
                app.config["DB_PATH"],
                int(user_id)
            )
            return {
                "is_admin": bool(
                    user and user.get("email") == app.config.get("ADMIN_EMAIL")
                )
            }
        except Exception:
            return {"is_admin": False}

    # Basic security headers
    @app.after_request
    def add_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        return resp

    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_too_large(e):
        from flask import flash, redirect, request, url_for

        max_mb = int(app.config.get("MAX_CONTENT_LENGTH", 0) or 0) // (1024 * 1024)
        flash(f"Upload too large. Please choose a smaller image (max {max_mb}MB).", "error")
        return redirect(request.referrer or url_for("profile.edit_profile"))

    # ✅ HEALTH CHECK ENDPOINT (VERY IMPORTANT)
    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    return app


# ✅ CREATE APP INSTANCE FOR GUNICORN
app = create_app()


# ✅ RAILWAY ENTRYPOINT
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
#test
