# route.py — 应用工厂：组装 Flask、JSON 提供者与 Blueprint（页面 / API 分离）
import os
import logging

from flask import Flask, jsonify, request

from CustomJSONEncoder import CustomJSONProvider
from api_errors import ApiError, build_error_payload
from db import DatabaseManager
from audit.service import bind_audit_writer
from routes.api import create_api_blueprint
from routes.pages_bp import create_pages_blueprint


def create_app(mysql_manager: DatabaseManager) -> Flask:
    _base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    app = Flask(
        __name__,
        template_folder=os.path.join(_base, "templates"),
        static_folder=os.path.join(_base, "static"),
    )
    app.json = CustomJSONProvider(app)
    bind_audit_writer(mysql_manager)

    app.register_blueprint(create_pages_blueprint())
    app.register_blueprint(create_api_blueprint(mysql_manager))

    @app.errorhandler(ApiError)
    def _handle_api_error(err: ApiError):
        return jsonify(build_error_payload(err)), err.http_status

    @app.errorhandler(404)
    def _handle_not_found(_err):
        if request.path.startswith("/api/"):
            return jsonify(build_error_payload(ApiError.not_found("资源不存在"))), 404
        return "Not Found", 404

    @app.errorhandler(405)
    def _handle_method_not_allowed(_err):
        if request.path.startswith("/api/"):
            return jsonify(build_error_payload(ApiError.method_not_allowed())), 405
        return "Method Not Allowed", 405

    @app.errorhandler(Exception)
    def _handle_unexpected(err: Exception):
        logging.exception("Unhandled exception")
        return jsonify(build_error_payload(ApiError.internal())), 500

    return app
