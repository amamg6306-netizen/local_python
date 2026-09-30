from __future__ import annotations

import re
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

from flask import current_app, request
from sqlalchemy import func, select, update
from werkzeug.datastructures import FileStorage

from extensions import db
from models.billing import FeaturedListing, LeadWallet, Subscription, SubscriptionPlan
from models.core import User
from models.marketplace import Favorite, Notification, Review
from services.auth_service import clean_text
from services.storage_service import delete_managed_file, store_image

PHONE_RE = re.compile(r"^[0-9+() .-]{7,25}$")
PINCODE_RE = re.compile(r"^[A-Za-z0-9 -]{3,12}$")
ICON_RE = re.compile(r"^[a-z0-9-]+$", re.I)
PLACEMENT_RE = re.compile(r"^[a-z0-9_-]+$", re.I)
UPI_RE = re.compile(r"^[A-Za-z0-9._-]{2,128}@[A-Za-z0-9._-]{2,64}$")


def page_window(default_per: int = 20, max_per: int = 50) -> tuple[int, int, int]:
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (TypeError, ValueError):
        page = 1
    page = min(page, int(current_app.config.get("PAGINATION_MAX_PAGE", 1000)))
    try:
        per = int(request.args.get("per", default_per))
    except (TypeError, ValueError):
        per = default_per
    per = max(1, min(max_per, per))
    return page, per, (page - 1) * per


def decimal_or_none(value: object, label: str = "Amount", maximum: Decimal = Decimal("100000000")) -> Decimal | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        amount = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"{label} is invalid.") from exc
    if amount < 0 or amount > maximum or amount.as_tuple().exponent < -2:
        raise ValueError(f"{label} is invalid.")
    return amount.quantize(Decimal("0.01"))


def date_or_none(value: object, *, allow_past: bool = True, label: str = "Date") -> date | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = date.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"{label} is invalid.") from exc
    if not allow_past and parsed < date.today():
        raise ValueError(f"{label} cannot be in the past.")
    return parsed


def time_or_none(value: object, label: str = "Time") -> time | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return time.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"{label} is invalid.") from exc


def datetime_or_none(value: object, label: str = "Date/time") -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"{label} is invalid.") from exc


def valid_phone_or_empty(value: str) -> bool:
    return not value or bool(PHONE_RE.fullmatch(value))


def valid_pincode_or_empty(value: str) -> bool:
    return not value or bool(PINCODE_RE.fullmatch(value))


def validated_http_url(value: object, max_length: int = 255) -> str | None:
    raw = clean_text(value, max_length, False, "URL")
    if not raw:
        return None
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("URL must be a valid http/https address.")
    return raw


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:180] or "item"


def create_notification(user_id: int, kind: str, title: str, message: str, link: str | None = None) -> Notification:
    row = Notification(
        user_id=user_id,
        type=clean_text(kind, 80, True, "Notification type"),
        title=clean_text(title, 180, True, "Notification title"),
        message=clean_text(message, 500, True, "Notification message"),
        link=(clean_text(link, 255, False, "Notification link") or None),
    )
    db.session.add(row)
    return row


def rating_summary(user_id: int) -> dict[str, float | int]:
    avg, total = db.session.execute(
        select(func.coalesce(func.avg(Review.rating), 0), func.count(Review.id)).where(
            Review.target_user_id == user_id, Review.status == "published"
        )
    ).one()
    return {"avg_rating": float(avg or 0), "total": int(total or 0)}


def is_favorite(customer_id: int, target_user_id: int) -> bool:
    return bool(db.session.scalar(select(Favorite.id).where(Favorite.customer_id == customer_id, Favorite.target_user_id == target_user_id).limit(1)))


def _refresh_current_subscription_locked(user_id: int) -> Subscription | None:
    """Refresh one user's entitlement while holding the user row lock.

    The legacy PHP implementation serializes subscription rollover on the user
    row.  Keep that invariant here so concurrent requests cannot activate two
    scheduled plans or apply lead/featured benefits twice.
    """
    now = datetime.now()
    user = db.session.scalar(select(User).where(User.id == user_id).with_for_update())
    if not user:
        return None

    # Expiry is a set operation; do not materialize every historical
    # subscription row into Python memory.  The user row lock above preserves
    # the legacy rollover serialization guarantee.
    db.session.execute(
        update(Subscription)
        .where(
            Subscription.user_id == user_id,
            Subscription.status == "active",
            Subscription.ends_at.is_not(None),
            Subscription.ends_at < now,
        )
        .values(status="expired")
    )

    active = db.session.scalar(
        select(Subscription)
        .where(
            Subscription.user_id == user_id,
            Subscription.status == "active",
            (Subscription.ends_at.is_(None) | (Subscription.ends_at >= now)),
        )
        .order_by(Subscription.id.desc())
        .limit(1)
    )
    if active:
        return active

    scheduled = db.session.scalar(
        select(Subscription)
        .where(
            Subscription.user_id == user_id,
            Subscription.status == "scheduled",
            Subscription.starts_at.is_not(None),
            Subscription.starts_at <= now,
        )
        .order_by(Subscription.starts_at.asc(), Subscription.id.asc())
        .with_for_update()
        .limit(1)
    )
    if not scheduled:
        return None

    scheduled.status = "active"
    plan = db.session.scalar(select(SubscriptionPlan).where(SubscriptionPlan.code == scheduled.plan).limit(1))
    if scheduled.benefits_applied_at is None:
        listings = db.session.scalars(
            select(FeaturedListing).where(
                FeaturedListing.subscription_id == scheduled.id,
                FeaturedListing.status == "pending",
                FeaturedListing.starts_at.is_not(None),
                FeaturedListing.starts_at <= now,
            )
        ).all()
        for listing in listings:
            listing.status = "active"

        if plan is not None and plan.lead_limit is not None:
            wallet = db.session.scalar(select(LeadWallet).where(LeadWallet.user_id == user_id).with_for_update())
            if wallet is None:
                wallet = LeadWallet(user_id=user_id, credits=int(plan.lead_limit or 0))
                db.session.add(wallet)
            else:
                wallet.credits = int(wallet.credits or 0) + int(plan.lead_limit or 0)
        scheduled.benefits_applied_at = now

    db.session.flush()
    return scheduled


def current_subscription(user_id: int) -> Subscription | None:
    session = db.session()
    owns_transaction = not session.in_transaction()
    try:
        current = _refresh_current_subscription_locked(user_id)
        if owns_transaction:
            session.commit()
        return current
    except Exception:
        if owns_transaction:
            session.rollback()
        raise


def ensure_free_subscription(user_id: int) -> Subscription:
    existing = current_subscription(user_id)
    if existing:
        return existing

    session = db.session()
    owns_transaction = not session.in_transaction()
    try:
        # Re-acquire the same serialization lock and re-check after the first
        # lookup, matching the legacy double-check that prevents duplicate free
        # subscriptions under concurrent dashboard requests.
        existing = _refresh_current_subscription_locked(user_id)
        if existing:
            if owns_transaction:
                session.commit()
            return existing
        user = session.get(User, user_id)
        if user is None:
            raise RuntimeError("User not found.")
        free_plan = session.scalar(
            select(SubscriptionPlan).where(SubscriptionPlan.code == "free", SubscriptionPlan.is_active == 1).limit(1)
        )
        sub = Subscription(
            user_id=user_id,
            plan="free",
            plan_id=free_plan.id if free_plan else None,
            status="active",
            starts_at=datetime.now(),
            price=Decimal("0.00"),
            billing_period_months=1,
        )
        session.add(sub)
        session.flush()
        if owns_transaction:
            session.commit()
        return sub
    except Exception:
        if owns_transaction:
            session.rollback()
        raise


def upload_image(file: FileStorage | None, folder: str, max_bytes: int = 3 * 1024 * 1024) -> str | None:
    """Compatibility wrapper preserving the legacy uploads/... database path contract."""
    return store_image(file, folder, max_bytes=max_bytes)


def delete_managed_upload(path: str | None) -> None:
    delete_managed_file(path)

def money_minor(amount: Decimal | str | int | float) -> int:
    parsed = decimal_or_none(amount, "Money amount", Decimal("100000000"))
    if parsed is None:
        raise ValueError("Invalid money amount.")
    return int(parsed * 100)


def money_decimal(minor: int) -> Decimal:
    if minor < 0:
        raise ValueError("Invalid money amount.")
    return (Decimal(minor) / Decimal(100)).quantize(Decimal("0.01"))
