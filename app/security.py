import re
from functools import wraps

from flask import flash, redirect, render_template, session, url_for
from sqlalchemy import text
from werkzeug.security import check_password_hash, generate_password_hash

from app.config import Config
from app.extensions import db
from app.models import Admin, User


EMAIL_PATTERN = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)
PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")


def hash_password(password: str) -> str:
    return generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)


def verify_password(password_hash: str, password: str) -> bool:
    if not password_hash:
        return False
    return check_password_hash(password_hash, password)


def validate_password(password: str) -> str | None:
    if not PASSWORD_PATTERN.match(password or ""):
        return "Password must be at least 8 characters and include uppercase, lowercase, number, and special character."
    return None


def validate_email(email: str) -> str | None:
    if not EMAIL_PATTERN.match(email or ""):
        return "Enter a valid email address."
    return None


def ensure_legacy_schema() -> None:
    """Adds required columns when upgrading an older local database."""
    rows = db.session.execute(text("PRAGMA table_info(users)")).mappings().all()
    existing = {row["name"] for row in rows}
    if rows and "password_hash" not in existing:
        db.session.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
    if rows and "role" not in existing:
        db.session.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user'"))
    if rows and "is_active" not in existing:
        db.session.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"))
    ticket_rows = db.session.execute(text("PRAGMA table_info(tickets)")).mappings().all()
    if ticket_rows:
        db.session.execute(text("UPDATE tickets SET status = 'NEEDS_ADMIN_REVIEW' WHERE status = 'Pending'"))
        db.session.execute(text("UPDATE tickets SET status = 'IN_PROGRESS' WHERE status = 'In Progress'"))
        db.session.execute(text("UPDATE tickets SET status = 'RESOLVED' WHERE status = 'Resolved'"))
    db.session.commit()


def seed_default_admin() -> None:
    ensure_legacy_schema()
    Admin.query.filter(Admin.username != Config.DEFAULT_ADMIN_USERNAME).delete()
    admin = Admin.query.filter_by(username=Config.DEFAULT_ADMIN_USERNAME).first()
    if admin is None:
        admin = Admin(
            username=Config.DEFAULT_ADMIN_USERNAME,
            password_hash=hash_password(Config.DEFAULT_ADMIN_PASSWORD),
        )
        db.session.add(admin)
    elif not verify_password(admin.password_hash, Config.DEFAULT_ADMIN_PASSWORD):
        admin.password_hash = hash_password(Config.DEFAULT_ADMIN_PASSWORD)
    db.session.commit()


def clear_auth_session() -> None:
    session.pop("user_id", None)
    session.pop("admin_id", None)
    session.pop("role", None)


def login_required(role: str):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if role == "admin":
                if session.get("role") != "admin" or not session.get("admin_id"):
                    return render_template("access_denied.html"), 403
            elif role == "user":
                if session.get("role") != "user" or not session.get("user_id"):
                    flash("Please log in to continue.", "warning")
                    return redirect(url_for("main.user_login"))
            return view(*args, **kwargs)

        return wrapped

    return decorator


def current_user() -> User | None:
    if session.get("role") != "user":
        return None
    return db.session.get(User, session.get("user_id"))


def current_admin() -> Admin | None:
    if session.get("role") != "admin":
        return None
    return db.session.get(Admin, session.get("admin_id"))
