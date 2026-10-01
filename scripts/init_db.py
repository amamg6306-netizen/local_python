from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import models  # noqa: F401
from database.connection import create_database_engine, connection_settings
from extensions import db
from models.billing import SubscriptionPlan
from models.core import Category
from models.marketplace import Service


CATEGORIES = [
    ("Home Services", "home-services", "fa-house"),
    ("Electrical", "electrical", "fa-bolt"),
    ("Plumbing", "plumbing", "fa-faucet-drip"),
    ("Carpenter", "carpenter", "fa-hammer"),
    ("Painting", "painting", "fa-paint-roller"),
    ("Cleaning", "cleaning", "fa-broom"),
    ("Appliance Repair", "appliance-repair", "fa-screwdriver-wrench"),
    ("AC & Cooling", "ac-cooling", "fa-snowflake"),
    ("Computer & Mobile Repair", "computer-mobile-repair", "fa-laptop"),
    ("Automotive", "automotive", "fa-car"),
    ("Beauty & Salon", "beauty-salon", "fa-scissors"),
    ("Education & Tutors", "education-tutors", "fa-graduation-cap"),
    ("Photography", "photography", "fa-camera"),
    ("Events", "events", "fa-calendar-days"),
    ("Construction", "construction", "fa-helmet-safety"),
    ("Tailoring", "tailoring", "fa-shirt"),
    ("Fitness", "fitness", "fa-dumbbell"),
    ("Other Services", "other-services", "fa-ellipsis"),
]

SERVICES = [
    ("electrician", "Electrician", "General electrical installation and repair", "electrical"),
    ("switchboard-repair", "Switchboard Repair", "Switchboard inspection and repair", "electrical"),
    ("plumber", "Plumber", "General plumbing work", "plumbing"),
    ("leak-repair", "Leak Repair", "Pipe and tap leak repair", "plumbing"),
    ("carpentry-work", "Carpentry Work", "General carpentry and furniture repair", "carpenter"),
    ("home-cleaning", "Home Cleaning", "Residential cleaning service", "cleaning"),
    ("washing-machine-repair", "Washing Machine Repair", "Washing machine diagnostics and repair", "appliance-repair"),
    ("ac-repair", "AC Repair", "Air conditioner diagnostics and repair", "ac-cooling"),
    ("ac-installation", "AC Installation", "Air conditioner installation", "ac-cooling"),
    ("computer-repair", "Computer Repair", "Desktop and laptop repair", "computer-mobile-repair"),
    ("mobile-repair", "Mobile Repair", "Mobile phone diagnostics and repair", "computer-mobile-repair"),
    ("car-mechanic", "Car Mechanic", "General car repair and maintenance", "automotive"),
    ("salon-services", "Salon Services", "Beauty and salon services", "beauty-salon"),
    ("home-tutor", "Home Tutor", "Private tutoring services", "education-tutors"),
    ("event-photography", "Event Photography", "Photography for local events", "photography"),
    ("masonry-work", "Masonry Work", "Construction and masonry work", "construction"),
    ("tailoring-alteration", "Tailoring & Alteration", "Clothing tailoring and alterations", "tailoring"),
    ("personal-fitness-training", "Personal Fitness Training", "Personal fitness coaching", "fitness"),
]

PLANS = [
    ("free", "Free", "both", 0, 1, 0, 5, "Basic local listing"),
    ("professional", "Professional", "provider", 499, 1, 0, 50, "For independent professionals"),
    ("business", "Business", "business", 999, 1, 0, None, "For local businesses"),
]


def seed_reference_data(session) -> None:
    existing_categories = {row.slug: row for row in session.scalars(select(Category)).all()}
    for name, slug, icon in CATEGORIES:
        if slug not in existing_categories:
            session.add(Category(name=name, slug=slug, icon=icon))
    session.flush()

    categories = {row.slug: row for row in session.scalars(select(Category)).all()}
    existing_services = {row.slug: row for row in session.scalars(select(Service)).all()}
    for slug, name, description, category_slug in SERVICES:
        if slug not in existing_services:
            session.add(Service(category_id=categories[category_slug].id, name=name, slug=slug, description=description))

    existing_plans = {row.code: row for row in session.scalars(select(SubscriptionPlan)).all()}
    for code, name, audience, price, period, tax, lead_limit, description in PLANS:
        if code not in existing_plans:
            session.add(
                SubscriptionPlan(
                    code=code,
                    name=name,
                    audience=audience,
                    price_monthly=price,
                    billing_period_months=period,
                    tax_rate_bps=tax,
                    featured_days={"free": 0, "professional": 7, "business": 15}[code],
                    lead_limit=lead_limit,
                    description=description,
                    is_active=1,
                )
            )
    session.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap the LocalConnect PostgreSQL schema safely.")
    parser.add_argument("--yes", action="store_true", help="Apply missing schema objects and reference data.")
    args = parser.parse_args()

    settings = connection_settings(migration=True)
    engine = create_database_engine(migration=True)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if not args.yes:
        print(f"PostgreSQL database {settings.database!r}: {len(tables)} table(s) currently present.")
        print("Re-run with --yes to create missing schema objects and seed reference data.")
        return 2

    # create_all is deliberately non-destructive and therefore safe to run on
    # every Render deploy. It creates missing tables/indexes without dropping data.
    db.metadata.create_all(engine)
    with Session(engine) as session:
        seed_reference_data(session)

    print(f"PostgreSQL bootstrap complete for {settings.database!r}; tables_before={len(tables)}; tables_after={len(inspect(engine).get_table_names())}.")
    engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
