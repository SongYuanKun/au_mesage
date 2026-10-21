import json
from datetime import datetime
from unittest.mock import MagicMock

from audit.sanitize import sanitize_value
from audit.service import bind_audit_writer, log_audit


def test_sanitize_redacts_tokens():
    payload = {
        "wechat_webhook_url": "https://example.com/hook",
        "priority": 10,
        "nested": {"smtp_pass": "secret"},
    }
    out = sanitize_value(payload)
    assert out["wechat_webhook_url"] == "[REDACTED]"
    assert out["priority"] == 10
    assert out["nested"]["smtp_pass"] == "[REDACTED]"


def test_log_audit_serializes_datetime_values():
    writer = MagicMock()
    bind_audit_writer(writer)
    try:
        log_audit(
            action="admin.source.update",
            target="gold_api",
            after_value={"source_id": "gold_api", "updated_at": datetime(2026, 10, 19, 12, 0, 0)},
            actor="admin",
        )
    finally:
        bind_audit_writer(None)

    after_value = writer.insert_audit_log.call_args.kwargs["after_value"]
    assert json.loads(after_value)["updated_at"] == "2026-10-19 12:00:00"
