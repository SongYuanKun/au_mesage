"""页面路由：旧版 Jinja 首页与 React SPA 独立入口。"""

from pathlib import Path

from flask import Blueprint, abort, current_app, render_template, send_from_directory


def _spa_directory() -> Path:
    return Path(current_app.static_folder) / "spa"


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

    @bp.route("/app", defaults={"spa_path": ""}, methods=["GET"])
    @bp.route("/app/", defaults={"spa_path": ""}, methods=["GET"])
    @bp.route("/app/<path:spa_path>", methods=["GET"])
    def react_spa(spa_path: str):
        """托管 Vite 构建物；仅 /app 范围内回退，绝不吞掉 /api 404。"""
        spa_dir = _spa_directory()
        if not (spa_dir / "index.html").is_file():
            abort(404)
        if spa_path:
            candidate = spa_dir / spa_path
            if candidate.is_file():
                return send_from_directory(spa_dir, spa_path)
            # 带扩展名的资源缺失不回退给 HTML，便于浏览器正确报告资源错误。
            if Path(spa_path).suffix:
                abort(404)
        return send_from_directory(spa_dir, "index.html")

    return bp
