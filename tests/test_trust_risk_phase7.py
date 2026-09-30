import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db, seed_db

client = TestClient(app)

def setup_module():
    init_db()
    seed_db()

def test_trust_score_calculation():
    res = client.get("/api/v1/trust/score/1")
    assert res.status_code == 200
    data = res.json()
    assert data["guardian_id"] == 1
    assert "trust_score" in data
    assert 0 <= data["trust_score"] <= 100
    assert "explainable_factors" in data
    assert isinstance(data["explainable_factors"], list)
    assert len(data["explainable_factors"]) > 0

def test_ai_risk_evaluation():
    res = client.post("/api/v1/admin/risk/evaluate/2")
    assert res.status_code == 200
    data = res.json()
    assert "alert_id" in data
    assert data["guardian_id"] == 2
    assert "action_policy" in data
    assert "Admin retains sole authority" in data["action_policy"]

def test_fetch_risk_alerts_list():
    res = client.get("/api/v1/admin/risk/alerts")
    assert res.status_code == 200
    alerts = res.json()
    assert isinstance(alerts, list)
    assert len(alerts) >= 1

def test_admin_resolve_risk_alert():
    # Fetch an open alert
    res_list = client.get("/api/v1/admin/risk/alerts?status=OPEN")
    assert res_list.status_code == 200
    alerts = res_list.json()
    assert len(alerts) >= 1
    alert_id = alerts[0]["id"]

    # Admin resolves alert
    res_res = client.post(f"/api/v1/admin/risk/alerts/{alert_id}/resolve", json={
        "action": "RESOLVE",
        "admin_notes": "Reviewed background verification documents; resolved."
    })
    assert res_res.status_code == 200
    assert res_res.json()["resolution_status"] == "RESOLVED"
