import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

client = TestClient(app)

def test_fetch_user_notifications():
    res = client.get("/api/v1/notifications/1")
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == 1
    assert "unread_count" in data
    assert "notifications" in data
    assert isinstance(data["notifications"], list)
    assert len(data["notifications"]) >= 1

def test_send_multi_channel_notification():
    req = {
        "user_id": 1,
        "type": "SOS_BROADCAST",
        "channel": "SMS",
        "title": "Emergency Alert Test",
        "message": "This is a simulated multi-channel SMS alert."
    }
    res = client.post("/api/v1/notifications/send", json=req)
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == 1
    assert data["channel"] == "SMS"
    assert data["title"] == "Emergency Alert Test"
    assert data["is_read"] == 0

def test_mark_notification_read():
    # Send a new notification first
    send_res = client.post("/api/v1/notifications/send", json={
        "user_id": 1,
        "type": "CHECK_IN",
        "channel": "PUSH",
        "title": "Check-in Alert",
        "message": "Caregiver checked in."
    })
    notif_id = send_res.json()["id"]

    read_res = client.post(f"/api/v1/notifications/{notif_id}/read")
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] == 1

def test_mark_all_notifications_read():
    res = client.post("/api/v1/notifications/read-all/1")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ALL_READ"

    # Verify unread_count is now 0
    fetch_res = client.get("/api/v1/notifications/1")
    assert fetch_res.json()["unread_count"] == 0
