import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

client = TestClient(app)

def test_create_daily_care_report():
    report_data = {
        "booking_id": 1,
        "session_id": 1,
        "guardian_id": 1,
        "parent_id": 1,
        "child_name": "Leo Jenkins",
        "date": "2026-09-30",
        "meals": {
            "breakfast": "Pancakes with blueberries",
            "lunch": "Rice and vegetable soup",
            "snacks": "Fresh apple slices",
            "water_intake": "700 ml"
        },
        "naps": {
            "start": "13:00",
            "end": "14:15",
            "duration_mins": 75,
            "quality": "Deep sleep"
        },
        "activities": [
            "Lego tower building",
            "Preschool alphabet tracing",
            "Garden story walk"
        ],
        "mood": "Calm & Happy",
        "health_notes": "No temperature or symptoms. Drank water regularly.",
        "photos": [
            "https://images.unsplash.com/photo-1502086223501-7ea6ecd79368?w=300&auto=format&fit=crop&q=80"
        ]
    }

    res = client.post("/api/v1/reports", json=report_data)
    assert res.status_code == 200
    data = res.json()
    assert data["child_name"] == "Leo Jenkins"
    assert data["mood"] == "Calm & Happy"
    assert "ai_summary" in data
    assert len(data["ai_summary"]) > 0
    assert data["meals"]["breakfast"] == "Pancakes with blueberries"
    assert len(data["activities"]) == 3
    assert "ai_metadata" in data

def test_fetch_parent_reports():
    res = client.get("/api/v1/reports/parent/1")
    assert res.status_code == 200
    reports = res.json()
    assert isinstance(reports, list)
    assert len(reports) >= 1
    report = reports[0]
    assert "child_name" in report
    assert "guardian_name" in report

def test_fetch_guardian_reports():
    res = client.get("/api/v1/reports/guardian/1")
    assert res.status_code == 200
    reports = res.json()
    assert isinstance(reports, list)

def test_fetch_report_by_id():
    # Fetch seeded report
    res = client.get("/api/v1/reports/1")
    assert res.status_code == 200
    report = res.json()
    assert report["id"] == 1
    assert report["child_name"] == "Leo Jenkins"
    assert "ai_summary" in report

def test_regenerate_report_ai_summary():
    res = client.post("/api/v1/reports/1/ai-summary")
    assert res.status_code == 200
    data = res.json()
    assert "ai_summary" in data
    assert "ai_metadata" in data
