"""仅页面渲染：与 JSON API 分离，便于维护与测试。"""

from flask import Blueprint, render_template


def create_pages_blueprint() -> Blueprint:
    bp = Blueprint("pages", __name__)

    @bp.route("/", methods=["GET"])
    def index():
        return render_template("index.html")

    @bp.route("/history", methods=["GET"])
    def history_page():
        return render_template("history.html")

    @bp.route("/analysis", methods=["GET"])
    def analysis_page():
        return render_template("analysis.html")

    return bp
