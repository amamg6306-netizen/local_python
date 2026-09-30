from __future__ import annotations

import secrets
import time
from functools import wraps
from urllib.parse import quote

from flask import abort, flash, g, redirect, request, session
from sqlalchemy import select

from extensions import db
from models.core import User
from services.auth_service import admin_mfa_needed, admin_mfa_record, dashboard_for, safe_admin_return


def clear_auth_session() -> None:
    session.clear()


def establish_session(user: User) -> None:
    session.clear()
    now = int(time.time())
    session["user_id"] = int(user.id)
    session["session_version"] = int(user.session_version or 1)
    session["_created_at"] = now
    session["_last_activity"] = now
    session["_rotated_at"] = now
    session["_nonce"] = secrets.token_hex(16)
    session.permanent = False


def current_user() -> User | None:
    if hasattr(g, "current_user"):
        return g.current_user
    user_id = session.get("user_id")
    if not user_id:
        g.current_user = None
        return None
    user = db.session.scalar(select(User).where(User.id == int(user_id)).limit(1))
    if not user or user.status == "blocked" or (int(session.get("session_version") or 0) > 0 and int(user.session_version or 0) != int(session.get("session_version") or 0)):
        clear_auth_session()
        g.current_user = None
        return None
    g.current_user = user
    return user


def admin_mfa_verified(user: User) -> bool:
    return int(session.get("admin_mfa_user_id") or 0) == int(user.id) and bool(session.get("admin_mfa_verified_at"))


def install_session_lifecycle(app) -> None:
    @app.before_request
    def _session_lifecycle():
        now = int(time.time())
        session.setdefault("_created_at", now)
        session.setdefault("_last_activity", now)
        session.setdefault("_rotated_at", now)
        if session.get("user_id"):
            idle = max(300, int(app.config["SESSION_IDLE_TIMEOUT"]))
            absolute = max(idle, int(app.config["SESSION_ABSOLUTE_TIMEOUT"]))
            rotate = max(300, int(app.config["SESSION_ROTATE_INTERVAL"]))
            if now - int(session["_last_activity"]) > idle or now - int(session["_created_at"]) > absolute:
                clear_auth_session()
                session["_created_at"] = now
                session["_last_activity"] = now
                session["_rotated_at"] = now
                flash("Your session expired. Please login again.", "error")
                return None
            if now - int(session["_rotated_at"]) > rotate:
                session["_rotated_at"] = now
                session["_nonce"] = secrets.token_hex(16)
        session["_last_activity"] = now
        return None


def require_guest(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if user:
            return redirect(dashboard_for(user.role), code=303)
        return view(*args, **kwargs)
    return wrapped


def require_login(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user:
            flash("Please login to continue.", "error")
            return redirect("/auth/login.php", code=303)
        g.user = user
        return view(*args, **kwargs)
    return wrapped


def require_roles(*roles: str):
    def decorator(view):
        @wraps(view)
        @require_login
        def wrapped(*args, **kwargs):
            user = g.user
            if user.role not in roles:
                abort(403)
            if user.role == "admin" and admin_mfa_needed(user) and not admin_mfa_verified(user) and request.path != "/admin/mfa.php":
                return redirect("/admin/mfa.php", code=303)
            return view(*args, **kwargs)
        return wrapped
    return decorator



def require_admin_mfa_for_sensitive():
    user = current_user()
    if not user or user.role != "admin":
        abort(403)
    if not admin_mfa_record(int(user.id)) or not admin_mfa_verified(user):
        flash("Enable and verify administrator MFA before changing payment configuration.", "error")
        return redirect("/admin/mfa.php", code=303)
    return None

def require_recent_admin_reauth(return_path: str, max_age: int = 600):
    user = current_user()
    if not user or user.role != "admin":
        abort(403)
    if admin_mfa_needed(user) and not admin_mfa_verified(user):
        return redirect("/admin/mfa.php", code=303)
    valid = int(session.get("admin_reauth_user_id") or 0) == int(user.id) and time.time() - int(session.get("admin_reauth_at") or 0) <= max_age
    if not valid:
        return redirect("/admin/reauth.php?return=" + quote(safe_admin_return(return_path), safe=""), code=303)
    return None
