from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ApiError(Exception):
    code: str
    message: str
    http_status: int = 400
    details: Any | None = None

    @staticmethod
    def invalid_argument(message: str, *, details: Any | None = None) -> "ApiError":
        return ApiError("INVALID_ARGUMENT", message, 400, details)

    @staticmethod
    def not_found(message: str, *, details: Any | None = None) -> "ApiError":
        return ApiError("NOT_FOUND", message, 404, details)

    @staticmethod
    def rate_limited(message: str, *, details: Any | None = None) -> "ApiError":
        return ApiError("RATE_LIMITED", message, 429, details)

    @staticmethod
    def unauthorized(message: str = "未认证", *, details: Any | None = None) -> "ApiError":
        return ApiError("UNAUTHORIZED", message, 401, details)

    @staticmethod
    def forbidden(message: str = "无权限", *, details: Any | None = None) -> "ApiError":
        return ApiError("FORBIDDEN", message, 403, details)

    @staticmethod
    def internal(message: str = "服务器内部错误", *, details: Any | None = None) -> "ApiError":
        return ApiError("INTERNAL", message, 500, details)

    @staticmethod
    def method_not_allowed(message: str = "方法不允许", *, details: Any | None = None) -> "ApiError":
        return ApiError("METHOD_NOT_ALLOWED", message, 405, details)


def build_error_payload(err: ApiError) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "success": False,
        "error": {
            "code": err.code,
            "message": err.message,
        },
    }
    if err.details is not None:
        payload["error"]["details"] = err.details
    return payload
