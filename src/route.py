# route.py — 应用工厂：组装 Flask、JSON 提供者与 Blueprint（页面 / API 分离）
import os

from flask import Flask

from CustomJSONEncoder import CustomJSONProvider
from mysql_manager import MySQLManager
from routes.api_bp import create_api_blueprint
from routes.pages_bp import create_pages_blueprint


def create_app(mysql_manager: MySQLManager) -> Flask:
    _base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    app = Flask(
        __name__,
        template_folder=os.path.join(_base, "templates"),
        static_folder=os.path.join(_base, "static"),
    )
    app.json = CustomJSONProvider(app)

    app.register_blueprint(create_pages_blueprint())
    app.register_blueprint(create_api_blueprint(mysql_manager))

    return app
