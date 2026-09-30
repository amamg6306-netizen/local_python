from __future__ import annotations

from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from extensions import db
from models.core import User
from models.marketplace import Favorite
from utils.auth import current_user, require_roles

bp = Blueprint("api", __name__)


@bp.post("/ajax/favorite.php")
@require_roles("customer")
def favorite_toggle():
    user = current_user(); assert user is not None
    try:
        target_id = int(request.form.get("target_user_id", 0))
    except (TypeError, ValueError):
        return jsonify(ok=False, message="Provider not found."), 404
    target = db.session.scalar(select(User).where(User.id == target_id, User.role.in_(["provider", "business"]), User.status == "active").limit(1))
    if not target:
        return jsonify(ok=False, message="Provider not found."), 404
    favorite = db.session.scalar(select(Favorite).where(Favorite.customer_id == user.id, Favorite.target_user_id == target_id).limit(1))
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify(ok=True, favorite=False)
    try:
        db.session.add(Favorite(customer_id=user.id, target_user_id=target_id))
        db.session.commit()
    except IntegrityError:
        # Duplicate concurrent toggle is equivalent to an already-favorited state.
        db.session.rollback()
    return jsonify(ok=True, favorite=True)
