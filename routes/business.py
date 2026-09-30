from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request
from sqlalchemy import func, select

from extensions import db
from models.core import Category
from models.marketplace import BusinessProfile, ProviderService
from routes.provider import _requests_page, _services_page, _subscription_page
from services.auth_service import clean_text, security_log
from services.marketplace_service import delete_managed_upload, decimal_or_none, time_or_none, upload_image, valid_phone_or_empty, valid_pincode_or_empty, validated_http_url, slugify
from utils.auth import current_user, require_roles

bp = Blueprint("business", __name__)


@bp.get("/business/dashboard.php")
@require_roles("business")
def dashboard():
    user = current_user(); assert user is not None
    profile = db.session.scalar(select(BusinessProfile).where(BusinessProfile.user_id == user.id).limit(1))
    if not profile:
        profile = BusinessProfile(user_id=user.id, verification_status="pending"); db.session.add(profile); db.session.commit()
    service_count = db.session.scalar(select(func.count(ProviderService.id)).where(ProviderService.provider_user_id == user.id)) or 0
    return render_template("business/dashboard.html", page_title="Business Dashboard — LocalConnect", profile=profile, service_count=int(service_count))


@bp.route("/business/profile.php", methods=["GET", "POST"])
@require_roles("business")
def profile():
    user = current_user(); assert user is not None
    categories = db.session.scalars(select(Category).where(Category.is_active == 1).order_by(Category.name)).all()
    row = db.session.scalar(select(BusinessProfile).where(BusinessProfile.user_id == user.id).limit(1))
    if not row:
        row = BusinessProfile(user_id=user.id, verification_status="pending"); db.session.add(row); db.session.commit()
    error = ""
    if request.method == "POST":
        new_logo = None
        try:
            name = clean_text(request.form.get("business_name", ""), 180, True, "Business name")
            category_id = int(request.form.get("category_id", 0))
            if not db.session.scalar(select(Category.id).where(Category.id == category_id, Category.is_active == 1).limit(1)): raise ValueError("Business category is invalid.")
            description = clean_text(request.form.get("description", ""), 10000, True, "Description")
            address = clean_text(request.form.get("address", ""), 255, True, "Address")
            phone = clean_text(request.form.get("phone", ""), 25, False, "Phone")
            city = clean_text(request.form.get("city", ""), 100, True, "City"); state = clean_text(request.form.get("state", ""), 100, True, "State")
            area = clean_text(request.form.get("area", ""), 150, False, "Area"); pincode = clean_text(request.form.get("pincode", ""), 12, False, "Pincode")
            if not valid_phone_or_empty(phone): raise ValueError("Phone number is invalid.")
            if not valid_pincode_or_empty(pincode): raise ValueError("Pincode is invalid.")
            opening = time_or_none(request.form.get("opening_time"), "Opening time"); closing = time_or_none(request.form.get("closing_time"), "Closing time")
            pmin = decimal_or_none(request.form.get("price_min"), "Minimum price"); pmax = decimal_or_none(request.form.get("price_max"), "Maximum price")
            if pmin is not None and pmax is not None and pmax < pmin: raise ValueError("Maximum price cannot be lower than minimum price.")
            website = validated_http_url(request.form.get("website", ""), 255)
            new_logo = upload_image(request.files.get("logo"), "businesses"); old_logo = row.logo
            user.phone, user.city, user.state, user.area, user.pincode = phone or None, city, state, area or None, pincode or None
            row.category_id, row.business_name, row.slug = category_id, name, f"{slugify(name)}-{user.id}"
            row.description, row.address, row.phone = description, address, phone or None
            row.opening_time, row.closing_time, row.price_min, row.price_max, row.website = opening, closing, pmin, pmax, website
            if new_logo: row.logo = new_logo
            db.session.commit()
            if new_logo and old_logo and old_logo != new_logo: delete_managed_upload(old_logo)
            flash("Business profile updated successfully.", "success"); return redirect("/business/profile.php", code=303)
        except (ValueError, TypeError) as exc:
            db.session.rollback();
            if new_logo: delete_managed_upload(new_logo)
            error = str(exc)
        except Exception as exc:
            db.session.rollback();
            if new_logo: delete_managed_upload(new_logo)
            security_log("business_profile_update_failed", error_class=type(exc).__name__); error = "Could not update business profile."
    return render_template("business/profile.html", page_title="Business Profile — LocalConnect", profile=row, categories=categories, user=user, error=error)


@bp.route("/business/services.php", methods=["GET", "POST"])
@require_roles("business")
def services():
    return _services_page("business")


@bp.get("/business/requests.php")
@require_roles("business")
def requests_alias():
    return _requests_page("business")


@bp.get("/business/subscription.php")
@require_roles("business")
def subscription():
    return _subscription_page("business")
