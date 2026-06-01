"""REST API Blueprint：按领域拆分为 price / alert / misc。"""

from __future__ import annotations

from flask import Blueprint

from db import DatabaseManager

from .admin_routes import register_admin_routes
from .auth_routes import register_auth_routes
from .alert_routes import register_alert_routes
from .misc_routes import register_misc_routes
from .price_routes import register_price_routes


def create_api_blueprint(mysql_manager: DatabaseManager) -> Blueprint:
    bp = Blueprint("api", __name__)
    register_price_routes(bp, mysql_manager)
    register_alert_routes(bp, mysql_manager)
    register_misc_routes(bp, mysql_manager)
    register_admin_routes(bp, mysql_manager)
    register_auth_routes(bp)
    return bp
