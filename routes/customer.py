from __future__ import annotations

from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request
from sqlalchemy import select

from extensions import db
from models.core import Category, User
from models.marketplace import BusinessProfile, Favorite, ProviderProfile, ProviderService, RequestStatusHistory, Service, ServiceRequest
from services.auth_service import clean_text
from services.marketplace_service import create_notification, date_or_none, decimal_or_none, page_window, time_or_none
from utils.auth import current_user, require_roles

bp = Blueprint("customer", __name__)


@bp.get("/customer/dashboard.php")
@require_roles("customer")
def dashboard():
    return render_template("customer/dashboard.html", page_title="Customer Dashboard — LocalConnect", user=current_user())


@bp.get("/customer/requests.php")
@require_roles("customer")
def requests_list():
    user = current_user(); assert user is not None
    page, per, offset = page_window(20, 40)
    target_p = User.__table__.alias("target_p"); target_b = User.__table__.alias("target_b")
    rows = db.session.execute(
        select(
            ServiceRequest.id, ServiceRequest.request_type, ServiceRequest.title, ServiceRequest.location_text,
            ServiceRequest.preferred_date, ServiceRequest.status, ServiceRequest.created_at,
            Category.name.label("category_name"), Service.name.label("service_name"),
            db.func.coalesce(target_p.c.name, target_b.c.name, "Open requirement").label("target_name"),
        )
        .join(Category, Category.id == ServiceRequest.category_id)
        .outerjoin(Service, Service.id == ServiceRequest.service_id)
        .outerjoin(target_p, target_p.c.id == ServiceRequest.provider_id)
        .outerjoin(target_b, target_b.c.id == ServiceRequest.business_id)
        .where(ServiceRequest.customer_id == user.id)
        .order_by(ServiceRequest.created_at.desc(), ServiceRequest.id.desc())
        .limit(per + 1).offset(offset)
    ).mappings().all()
    has_next = len(rows) > per; rows = rows[:per]
    return render_template("customer/requests.html", page_title="My Service Requests — LocalConnect", rows=rows, page=page, has_next=has_next)


@bp.route("/post-requirement.php", methods=["GET", "POST"])
@require_roles("customer")
def post_requirement():
    user = current_user(); assert user is not None
    categories = db.session.scalars(select(Category).where(Category.is_active == 1).order_by(Category.name)).all()
    services = db.session.scalars(select(Service).where(Service.is_active == 1).order_by(Service.name)).all()
    errors: list[str] = []
    if request.method == "POST":
        try:
            category_id = int(request.form.get("category_id", 0)); service_id = int(request.form.get("service_id", 0))
            title = clean_text(request.form.get("title", ""), 180, True, "Requirement title")
            description = clean_text(request.form.get("description", ""), 10000, True, "Requirement description")
            location = clean_text(request.form.get("location_text", ""), 255, True, "Service location")
            preferred_date = date_or_none(request.form.get("preferred_date"), allow_past=False, label="Preferred date")
            preferred_time = time_or_none(request.form.get("preferred_time"), "Preferred time")
            budget_min = decimal_or_none(request.form.get("budget_min"), "Minimum budget")
            budget_max = decimal_or_none(request.form.get("budget_max"), "Maximum budget")
            service = db.session.scalar(select(Service).where(Service.id == service_id, Service.category_id == category_id, Service.is_active == 1).limit(1))
            if not service or not db.session.get(Category, category_id) or not db.session.get(Category, category_id).is_active:
                raise ValueError("Please select a valid service for this category.")
            if budget_min is not None and budget_max is not None and budget_min > budget_max:
                raise ValueError("Minimum budget cannot exceed maximum budget.")
            row = ServiceRequest(customer_id=user.id, category_id=category_id, service_id=service_id, request_type="requirement", title=title, description=description, location_text=location, preferred_date=preferred_date, preferred_time=preferred_time, budget_min=budget_min, budget_max=budget_max, status="pending")
            db.session.add(row); db.session.flush()
            db.session.add(RequestStatusHistory(request_id=row.id, status="pending", changed_by=user.id, note="Requirement posted"))
            db.session.commit(); flash("Requirement posted successfully. Matching providers can now find it.", "success")
            return redirect("/customer/requests.php", code=303)
        except (ValueError, TypeError) as exc:
            db.session.rollback(); errors.append(str(exc))
        except Exception:
            db.session.rollback(); errors.append("Could not post your requirement. Please try again.")
    return render_template("customer/post_requirement.html", page_title="Post a Requirement — LocalConnect", categories=categories, services=services, errors=errors, user=user, today=date.today().isoformat())


@bp.route("/request-service.php", methods=["GET", "POST"])
@require_roles("customer")
def request_service():
    user = current_user(); assert user is not None
    try: target_id = int(request.args.get("provider") or request.form.get("target_id") or 0)
    except ValueError: target_id = 0
    kind = (request.args.get("type") or request.form.get("target_type") or "provider").strip()
    if kind not in {"provider", "business"}: kind = "provider"
    target = db.session.scalar(select(User).where(User.id == target_id, User.role == kind, User.status == "active").limit(1))
    if not target:
        flash("The selected provider or business is unavailable.", "error"); return redirect("/search.php", code=303)
    categories = db.session.scalars(select(Category).where(Category.is_active == 1).order_by(Category.name)).all()
    services = db.session.execute(
        select(Service).join(ProviderService, ProviderService.service_id == Service.id)
        .where(ProviderService.provider_user_id == target_id, ProviderService.is_active == 1, Service.is_active == 1)
        .order_by(Service.name)
    ).scalars().all()
    errors: list[str] = []
    if request.method == "POST":
        try:
            category_id = int(request.form.get("category_id", 0)); service_id = int(request.form.get("service_id", 0))
            title = clean_text(request.form.get("title", ""), 180, True, "Service title")
            description = clean_text(request.form.get("description", ""), 10000, True, "Description")
            location = clean_text(request.form.get("location_text", ""), 255, True, "Service location")
            notes = clean_text(request.form.get("additional_notes", ""), 5000, False, "Additional notes")
            preferred_date = date_or_none(request.form.get("preferred_date"), allow_past=False, label="Preferred date")
            preferred_time = time_or_none(request.form.get("preferred_time"), "Preferred time")
            budget_min = decimal_or_none(request.form.get("budget_min"), "Minimum budget")
            budget_max = decimal_or_none(request.form.get("budget_max"), "Maximum budget")
            offered = db.session.scalar(select(ProviderService.id).join(Service, Service.id == ProviderService.service_id).where(ProviderService.provider_user_id == target_id, ProviderService.service_id == service_id, ProviderService.is_active == 1, Service.is_active == 1, Service.category_id == category_id).limit(1))
            if not offered: raise ValueError("That service is not offered by this provider.")
            if budget_min is not None and budget_max is not None and budget_min > budget_max: raise ValueError("Minimum budget cannot exceed maximum budget.")
            row = ServiceRequest(customer_id=user.id, provider_id=target_id if kind == "provider" else None, business_id=target_id if kind == "business" else None, category_id=category_id, service_id=service_id, request_type="direct", title=title, description=description, location_text=location, preferred_date=preferred_date, preferred_time=preferred_time, budget_min=budget_min, budget_max=budget_max, additional_notes=notes or None, status="pending")
            db.session.add(row); db.session.flush(); db.session.add(RequestStatusHistory(request_id=row.id, status="pending", changed_by=user.id, note="Service request submitted"))
            create_notification(target_id, "service_request", "New service request", f"{user.name} sent you a service request.", f"request-details.php?id={row.id}")
            db.session.commit(); flash("Service request submitted successfully.", "success"); return redirect("/customer/requests.php", code=303)
        except (ValueError, TypeError) as exc:
            db.session.rollback(); errors.append(str(exc))
        except Exception:
            db.session.rollback(); errors.append("Could not submit the request. Please try again.")
    return render_template("customer/request_service.html", page_title="Request Service — LocalConnect", target=target, kind=kind, categories=categories, services=services, errors=errors, user=user)


@bp.get("/favorites.php")
@require_roles("customer")
def favorites():
    user = current_user(); assert user is not None
    page, per, offset = page_window(24, 48)
    rows = db.session.execute(
        select(Favorite.created_at, User.id, User.name, User.role, User.profile_image, User.city, User.area,
               ProviderProfile.headline, ProviderProfile.verification_status.label("provider_verified"),
               BusinessProfile.business_name, BusinessProfile.logo, BusinessProfile.verification_status.label("business_verified"))
        .join(User, User.id == Favorite.target_user_id)
        .outerjoin(ProviderProfile, ProviderProfile.user_id == User.id)
        .outerjoin(BusinessProfile, BusinessProfile.user_id == User.id)
        .where(Favorite.customer_id == user.id, User.status == "active")
        .order_by(Favorite.created_at.desc(), Favorite.id.desc()).limit(per + 1).offset(offset)
    ).mappings().all()
    has_next = len(rows) > per; rows = rows[:per]
    return render_template("customer/favorites.html", page_title="Favorites — LocalConnect", items=rows, page=page, has_next=has_next)
