"""兼容旧导入路径 `from routes.api_bp import create_api_blueprint`。"""

from routes.api import create_api_blueprint

__all__ = ["create_api_blueprint"]
