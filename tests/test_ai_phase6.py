import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db, seed_db

client = TestClient(app)

def setup_module():
    init_db()
    seed_db()

def test_ai_health():
    res = client.get("/api/v1/ai/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert data["status"] in ["AI_AVAILABLE", "AI_UNAVAILABLE", "AI_MODEL_MISSING"]
    assert "target_model" in data
    assert data["target_model"] == "qwen3:4b"

def test_ai_guardian_recommendation_request():
    res = client.post("/api/v1/ai/recommend-guardians", json={
        "parent_id": 1,
        "care_type": "Childcare"
    })
    assert res.status_code == 200
    data = res.json()
    assert "recommended_guardian" in data
    assert data["recommended_guardian"]["name"] is not None
    assert "explanation" in data
    assert "source" in data
    assert "model" in data
    assert data["model"] == "qwen3:4b"

def test_parent_ai_assistant():
    res = client.post("/api/v1/ai/assistant/user", json={
        "prompt": "How does the BLE beacon proximity tracking work?"
    })
    assert res.status_code == 200
    data = res.json()
    assert "response" in data
    assert len(data["response"]) > 0

def test_guardian_ai_assistant():
    res = client.post("/api/v1/ai/assistant/guardian", json={
        "prompt": "What is the procedure for logging care routines?"
    })
    assert res.status_code == 200
    data = res.json()
    assert "response" in data
    assert len(data["response"]) > 0

def test_admin_ai_assistant_and_summary():
    res_ast = client.post("/api/v1/ai/assistant/admin", json={
        "prompt": "Summarize safety events"
    })
    assert res_ast.status_code == 200
    assert "response" in res_ast.json()

    res_sum = client.get("/api/v1/ai/summary/admin")
    assert res_sum.status_code == 200
    data = res_sum.json()
    assert "summary" in data
    assert "metrics" in data
