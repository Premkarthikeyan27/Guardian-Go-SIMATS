import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db, seed_db

client = TestClient(app)

def setup_module():
    init_db()
    seed_db()

def test_get_membership_plans():
    res = client.get("/api/v1/membership/plans")
    assert res.status_code == 200
    plans = res.json()["plans"]
    assert len(plans) == 3
    plan_ids = [p["id"] for p in plans]
    assert "BASIC_CARE" in plan_ids
    assert "SAFECARE" in plan_ids
    assert "PREMIUM_CARE_PLUS" in plan_ids

def test_get_user_membership():
    res = client.get("/api/v1/membership?user_id=1")
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == 1
    assert data["status"] == "ACTIVE"

def test_subscribe_user_simulated_payment():
    res = client.post("/api/v1/membership/subscribe", json={
        "user_id": 1,
        "plan": "SAFECARE",
        "payment_method": "DEMO_VISA_4242"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["payment_status"] == "SIMULATED_SUCCESS"
    assert data["membership"]["plan"] == "SAFECARE"

def test_upgrade_membership():
    res = client.post("/api/v1/membership/upgrade", json={
        "user_id": 1,
        "new_plan": "PREMIUM_CARE_PLUS"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["membership"]["plan"] == "PREMIUM_CARE_PLUS"

def test_cancel_membership():
    res = client.post("/api/v1/membership/cancel", json={"user_id": 1})
    assert res.status_code == 200
    data = res.json()
    assert data["membership"]["status"] == "CANCELLED"

def test_backend_entitlement_enforcement():
    # Upgrade to PREMIUM_CARE_PLUS
    client.post("/api/v1/membership/subscribe", json={"user_id": 1, "plan": "PREMIUM_CARE_PLUS"})
    
    res = client.get("/api/v1/membership/check-entitlement?user_id=1&feature_key=ble_beacon_device")
    assert res.status_code == 200
    assert res.json()["allowed"] is True

    # Check for another user on default BASIC_CARE
    res_basic = client.get("/api/v1/membership/check-entitlement?user_id=999&feature_key=ble_beacon_device")
    assert res_basic.status_code == 200
    assert res_basic.json()["allowed"] is False

def test_admin_memberships_list():
    res = client.get("/api/v1/admin/memberships")
    assert res.status_code == 200
    m_list = res.json()
    assert isinstance(m_list, list)
    assert len(m_list) >= 1
