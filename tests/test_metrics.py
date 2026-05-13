from datetime import datetime
from application.metrics import build_quality_metrics_payload, _freshness_seconds, _data_status, _p95, _as_naive_datetime

def test_as_naive_datetime():
    assert _as_naive_datetime(None) is None
    assert _as_naive_datetime("2026-05-13 10:00:00") == datetime(2026, 5, 13, 10, 0)
    assert _as_naive_datetime("") is None
    assert _as_naive_datetime("invalid") is None

def test_freshness_seconds():
    now = datetime(2026, 5, 13, 10, 0, 10)
    assert _freshness_seconds(datetime(2026, 5, 13, 10, 0, 0), now) == 10
    assert _freshness_seconds(None, now) is None
    # negative
    assert _freshness_seconds(datetime(2026, 5, 13, 10, 0, 20), now) == 0

def test_data_status():
    assert _data_status(None) == "abnormal"
    assert _data_status(100) == "normal"
    assert _data_status(300) == "delayed"
    assert _data_status(1000) == "abnormal"

def test_p95():
    assert _p95([]) is None
    assert _p95([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) == 10
    assert _p95([100]) == 100

def test_build_quality_metrics_payload():
    now = datetime(2026, 5, 13, 10, 0, 0)
    latest = [
        {"data_type": "XAU", "source": "gold_api", "latest_at": "2026-05-13 09:59:00"}
    ]
    counts = [
        {"data_type": "XAU", "source": "gold_api", "cnt_last_hour": 50}
    ]
    
    payload = build_quality_metrics_payload(latest, counts, now, window_seconds=3600, expected_interval_seconds=60)
    assert payload["success"] is True
    assert payload["freshness_p95_seconds"] == 60
    assert len(payload["groups"]) == 1
    g = payload["groups"][0]
    assert g["data_type"] == "XAU"
    assert g["source"] == "gold_api"
    assert g["freshness_seconds"] == 60
    assert g["data_status"] == "normal"
    assert g["count_last_hour"] == 50
    assert g["expected_count_last_hour"] == 60
    # missing rate = 1 - (50/60) = 0.1667
    assert abs(g["missing_rate"] - 0.1667) < 0.001
    assert abs(g["collector_success_rate"] - (50/60)) < 0.001
