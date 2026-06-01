from audit.sanitize import sanitize_value


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
