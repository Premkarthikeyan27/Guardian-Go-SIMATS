import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

client = TestClient(app)

def test_admin_approval_and_rejection():
    # 1. Approve guardian #2
    approve_res = client.post("/api/v1/admin/guardians/2/approve", json={"reason": "Passed all background checks"})
    assert approve_res.status_code == 200
    assert approve_res.json()["overall_status"] == "VERIFIED"

    # 2. Reject guardian #2
    reject_res = client.post("/api/v1/admin/guardians/2/reject", json={"reason": "Document flag"})
    assert reject_res.status_code == 200
    assert reject_res.json()["overall_status"] == "REJECTED"

def test_admin_analytics_and_audit():
    # Analytics
    analytics_res = client.get("/api/v1/admin/analytics")
    assert analytics_res.status_code == 200
    data = analytics_res.json()
    assert "total_users" in data
    assert "verified_guardians" in data

    # Audit Logs
    audit_res = client.get("/api/v1/admin/audit")
    assert audit_res.status_code == 200
    assert isinstance(audit_res.json(), list)
