from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from extensions import db
from models.billing import SubscriptionPlan
from models.core import Category, User
from models.marketplace import PortfolioImage, ProviderProfile, ProviderService, Service, ServiceRequest
from services.auth_service import clean_text, security_log
from services.billing_service import price_breakdown
from services.marketplace_service import delete_managed_upload, decimal_or_none, ensure_free_subscription, page_window, upload_image, valid_pincode_or_empty
from utils.auth import current_user, require_roles

bp = Blueprint("provider", __name__)


@bp.get("/provider/dashboard.php")
@require_roles("provider")
def dashboard():
    user = current_user(); assert user is not None
    profile = db.session.scalar(select(ProviderProfile).where(ProviderProfile.user_id == user.id).limit(1))
    if not profile:
        profile = ProviderProfile(user_id=user.id, verification_status="pending"); db.session.add(profile); db.session.commit()
    service_count = db.session.scalar(select(func.count(ProviderService.id)).where(ProviderService.provider_user_id == user.id)) or 0
    portfolio_count = db.session.scalar(select(func.count(PortfolioImage.id)).where(PortfolioImage.user_id == user.id)) or 0
    return render_template("provider/dashboard.html", page_title="Provider Dashboard — LocalConnect", profile=profile, service_count=int(service_count), portfolio_count=int(portfolio_count))


@bp.route("/provider/profile.php", methods=["GET", "POST"])
@require_roles("provider")
def profile():
    user = current_user(); assert user is not None
    row = db.session.scalar(select(ProviderProfile).where(ProviderProfile.user_id == user.id).limit(1))
    if not row:
        row = ProviderProfile(user_id=user.id, verification_status="pending"); db.session.add(row); db.session.commit()
    error = ""
    if request.method == "POST":
        new_image = None
        try:
            headline = clean_text(request.form.get("headline", ""), 180, True, "Headline")
            about = clean_text(request.form.get("about", ""), 10000, True, "About")
            exp = int(request.form.get("experience_years", 0))
            if exp < 0 or exp > 80: raise ValueError("Experience years are outside the allowed range.")
            service_area = clean_text(request.form.get("service_area", ""), 255, True, "Service area")
            pmin = decimal_or_none(request.form.get("price_min"), "Minimum price"); pmax = decimal_or_none(request.form.get("price_max"), "Maximum price")
            if pmin is not None and pmax is not None and pmax < pmin: raise ValueError("Maximum price cannot be lower than minimum price.")
            availability = request.form.get("availability_status", "available")
            if availability not in {"available", "busy", "unavailable"}: raise ValueError("Availability value is invalid.")
            hours = clean_text(request.form.get("working_hours", ""), 255, False, "Working hours")
            city = clean_text(request.form.get("city", ""), 100, True, "City"); state = clean_text(request.form.get("state", ""), 100, True, "State")
            area = clean_text(request.form.get("area", ""), 150, False, "Area"); pincode = clean_text(request.form.get("pincode", ""), 12, False, "Pincode")
            if not valid_pincode_or_empty(pincode): raise ValueError("Pincode is invalid.")
            new_image = upload_image(request.files.get("profile_image"), "profiles")
            old_image = user.profile_image
            user.city, user.state, user.area, user.pincode = city, state, area or None, pincode or None
            if new_image: user.profile_image = new_image
            row.headline, row.about, row.experience_years, row.service_area = headline, about, exp, service_area
            row.price_min, row.price_max, row.availability_status, row.working_hours = pmin, pmax, availability, hours or None
            db.session.commit()
            if new_image and old_image and old_image != new_image: delete_managed_upload(old_image)
            flash("Provider profile updated successfully.", "success"); return redirect("/provider/profile.php", code=303)
        except (ValueError, TypeError) as exc:
            db.session.rollback();
            if new_image: delete_managed_upload(new_image)
            error = str(exc)
        except Exception as exc:
            db.session.rollback();
            if new_image: delete_managed_upload(new_image)
            security_log("provider_profile_update_failed", error_class=type(exc).__name__); error = "Could not update profile."
    return render_template("provider/profile.html", page_title="My Provider Profile — LocalConnect", profile=row, user=user, error=error)


@bp.route("/provider/services.php", methods=["GET", "POST"])
@require_roles("provider")
def services():
    return _services_page("provider")


def _services_page(role: str):
    user = current_user(); assert user is not None
    error = ""
    redirect_path = f"/{role}/services.php"
    if request.method == "POST":
        try:
            action = request.form.get("action", "add")
            if action == "delete":
                item_id = int(request.form.get("id", 0)); row = db.session.scalar(select(ProviderService).where(ProviderService.id == item_id, ProviderService.provider_user_id == user.id).limit(1))
                if row: db.session.delete(row); db.session.commit(); flash("Service removed.", "success")
                return redirect(redirect_path, code=303)
            service_id = int(request.form.get("service_id", 0)); service = db.session.scalar(select(Service).where(Service.id == service_id, Service.is_active == 1).limit(1))
            if not service: raise ValueError("Please select an active service.")
            title = clean_text(request.form.get("title", ""), 180, False, "Service title"); description = clean_text(request.form.get("description", ""), 5000, False, "Service description")
            pfrom = decimal_or_none(request.form.get("price_from"), "Starting price"); pto = decimal_or_none(request.form.get("price_to"), "Maximum price")
            if pfrom is not None and pto is not None and pto < pfrom: raise ValueError("Maximum price cannot be lower than minimum price.")
            db.session.add(ProviderService(provider_user_id=user.id, service_id=service_id, title=title or None, description=description or None, price_from=pfrom, price_to=pto, is_active=1))
            db.session.commit(); flash("Service added successfully.", "success"); return redirect(redirect_path, code=303)
        except IntegrityError:
            db.session.rollback(); error = "This service is already on your profile."
        except (ValueError, TypeError) as exc:
            db.session.rollback(); error = str(exc)
    page, per, offset = page_window(20, 40)
    catalogue = db.session.execute(select(Service.id, Service.name, Category.name.label("category")).join(Category, Category.id == Service.category_id).where(Service.is_active == 1).order_by(Category.name, Service.name).limit(500)).mappings().all()
    mine = db.session.execute(select(ProviderService.id, ProviderService.service_id, ProviderService.title, ProviderService.description, ProviderService.price_from, ProviderService.price_to, ProviderService.is_active, ProviderService.created_at, Service.name, Category.name.label("category")).join(Service, Service.id == ProviderService.service_id).join(Category, Category.id == Service.category_id).where(ProviderService.provider_user_id == user.id).order_by(ProviderService.created_at.desc(), ProviderService.id.desc()).limit(per + 1).offset(offset)).mappings().all()
    has_next = len(mine) > per; mine = mine[:per]
    template = "business/services.html" if role == "business" else "provider/services.html"
    return render_template(template, page_title=("Business services" if role == "business" else "My Services") + " — LocalConnect", role=role, catalogue=catalogue, mine=mine, page=page, has_next=has_next, error=error)


@bp.route("/provider/portfolio.php", methods=["GET", "POST"])
@require_roles("provider")
def portfolio():
    user = current_user(); assert user is not None; error = ""
    if request.method == "POST":
        path = None
        try:
            path = upload_image(request.files.get("image"), "portfolio")
            if not path: raise ValueError("Please choose an image.")
            caption = clean_text(request.form.get("caption", ""), 255, False, "Caption")
            db.session.add(PortfolioImage(user_id=user.id, image_path=path, caption=caption or None)); db.session.commit(); flash("Work image uploaded.", "success"); return redirect("/provider/portfolio.php", code=303)
        except ValueError as exc:
            db.session.rollback();
            if path: delete_managed_upload(path)
            error = str(exc)
        except Exception as exc:
            db.session.rollback();
            if path: delete_managed_upload(path)
            security_log("portfolio_upload_failed", error_class=type(exc).__name__); error = "Could not save the portfolio image."
    page, per, offset = page_window(24, 48)
    images = db.session.scalars(select(PortfolioImage).where(PortfolioImage.user_id == user.id).order_by(PortfolioImage.created_at.desc(), PortfolioImage.id.desc()).limit(per + 1).offset(offset)).all()
    has_next = len(images) > per; images = images[:per]
    return render_template("provider/portfolio.html", page_title="Portfolio — LocalConnect", images=images, page=page, has_next=has_next, error=error)


@bp.get("/provider/requests.php")
@require_roles("provider")
def requests_list():
    return _requests_page("provider")


def _requests_page(role: str):
    user = current_user(); assert user is not None
    if user.role != role:
        return redirect(f"/{user.role}/dashboard.php", code=303)
    page, per, offset = page_window(20, 40)
    filter_col = ServiceRequest.provider_id if role == "provider" else ServiceRequest.business_id
    rows = db.session.execute(select(ServiceRequest.id, ServiceRequest.request_type, ServiceRequest.title, ServiceRequest.location_text, ServiceRequest.preferred_date, ServiceRequest.status, ServiceRequest.created_at, User.name.label("customer_name"), Category.name.label("category_name"), Service.name.label("service_name")).join(User, User.id == ServiceRequest.customer_id).join(Category, Category.id == ServiceRequest.category_id).outerjoin(Service, Service.id == ServiceRequest.service_id).where(filter_col == user.id).order_by(ServiceRequest.created_at.desc(), ServiceRequest.id.desc()).limit(per + 1).offset(offset)).mappings().all()
    has_next = len(rows) > per; rows = rows[:per]
    return render_template("provider/requests.html", page_title="Service Requests — LocalConnect", role=role, rows=rows, page=page, has_next=has_next)


@bp.get("/provider/available-requirements.php")
@require_roles("provider", "business")
def available_requirements():
    user = current_user(); assert user is not None
    page, per, offset = page_window(20, 40)
    offered = select(ProviderService.service_id).where(ProviderService.provider_user_id == user.id, ProviderService.is_active == 1)
    rows = db.session.execute(select(ServiceRequest.id, ServiceRequest.title, ServiceRequest.description, ServiceRequest.location_text, ServiceRequest.preferred_date, ServiceRequest.preferred_time, ServiceRequest.budget_min, ServiceRequest.budget_max, ServiceRequest.status, ServiceRequest.created_at, User.name.label("customer_name"), Category.name.label("category_name"), Service.name.label("service_name")).join(User, User.id == ServiceRequest.customer_id).join(Category, Category.id == ServiceRequest.category_id).outerjoin(Service, Service.id == ServiceRequest.service_id).where(ServiceRequest.request_type == "requirement", ServiceRequest.status == "pending", ServiceRequest.provider_id.is_(None), ServiceRequest.business_id.is_(None), ServiceRequest.service_id.in_(offered)).order_by(ServiceRequest.created_at.desc(), ServiceRequest.id.desc()).limit(per + 1).offset(offset)).mappings().all()
    has_next = len(rows) > per; rows = rows[:per]
    return render_template("provider/available_requirements.html", page_title="Available Requirements — LocalConnect", rows=rows, page=page, has_next=has_next)


@bp.get("/provider/subscription.php")
@require_roles("provider")
def subscription():
    return _subscription_page("provider")


def _subscription_page(role: str):
    user = current_user(); assert user is not None
    sub = ensure_free_subscription(user.id); db.session.commit()
    plans = db.session.scalars(select(SubscriptionPlan).where(SubscriptionPlan.is_active == 1, SubscriptionPlan.audience.in_([role, "both"])).order_by(SubscriptionPlan.price_monthly, SubscriptionPlan.id)).all()
    priced = [(p, price_breakdown(p)) for p in plans]
    template = "business/subscription.html" if role == "business" else "provider/subscription.html"
    return render_template(template, page_title="Subscription — LocalConnect", role=role, subscription=sub, plans=priced)
