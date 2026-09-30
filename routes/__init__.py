from .admin import bp as admin_bp
from .api import bp as api_bp
from .auth import bp as auth_bp
from .billing import bp as billing_bp
from .business import bp as business_bp
from .customer import bp as customer_bp
from .health import bp as health_bp
from .main import bp as main_bp
from .provider import bp as provider_bp
from .webhooks import bp as webhooks_bp


BLUEPRINTS = (
    health_bp,
    main_bp,
    auth_bp,
    customer_bp,
    provider_bp,
    business_bp,
    admin_bp,
    billing_bp,
    api_bp,
    webhooks_bp,
)
