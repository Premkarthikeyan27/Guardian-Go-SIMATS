import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db, seed_db
from backend.services.auth_service import hash_password, verify_password, generate_user_token, get_session_by_token

client = TestClient(app)

def setup_module():
    init_db()
    seed_db()

def test_auth_service_hashing():
    pwd = "secretpassword123"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert ":" in hashed
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_token_generation():
    token = generate_user_token(1, "parent@demo.com", "parent")
    assert token.startswith("gg_token_parent_1_")
    session = get_session_by_token(token)
    assert session is not None
    assert session["user_id"] == 1
    assert session["role"] == "parent"

def test_parent_login_success():
    response = client.post("/api/v1/auth/login", json={"email": "parent@demo.com", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["user"]["role"] == "parent"
    assert "access_token" in data

def test_guardian_login_success():
    response = client.post("/api/v1/auth/guardian/login", json={"email": "guardian@demo.com", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["user"]["role"] == "guardian"

def test_admin_login_success():
    response = client.post("/api/v1/auth/admin/login", json={"email": "admin@demo.com", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["user"]["role"] == "admin"

def test_rbac_login_boundary():
    # Attempting to login to Parent endpoint with Guardian email must fail RBAC
    response = client.post("/api/v1/auth/login", json={"email": "guardian@demo.com", "password": "password123"})
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]

def test_parent_public_registration():
    import uuid
    email = f"parent_{uuid.uuid4().hex[:6]}@demo.com"
    response = client.post("/api/v1/auth/register/parent", json={
        "name": "New Parent",
        "email": email,
        "password": "password123",
        "phone": "+1 555-9999"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "parent"

def test_guardian_registration():
    import uuid
    email = f"guardian_{uuid.uuid4().hex[:6]}@demo.com"
    response = client.post("/api/v1/auth/register/guardian", json={
        "name": "New Guardian",
        "email": email,
        "password": "password123",
        "experience": "2 years",
        "skills": "First Aid"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "guardian"

def test_dependents_crud():
    # 1. List dependents
    res = client.get("/api/v1/parent/dependents?parent_id=1")
    assert res.status_code == 200
    deps = res.json()
    assert len(deps) >= 1
    assert deps[0]["name"] == "Leo Jenkins"

    # 2. Add dependent
    res_add = client.post("/api/v1/parent/dependents", json={
        "parent_id": 1,
        "name": "Maya Jenkins",
        "age": 3,
        "allergies": "Milk",
        "instructions": "Morning nap at 11 AM"
    })
    assert res_add.status_code == 200
    new_dep = res_add.json()
    assert new_dep["name"] == "Maya Jenkins"
    dep_id = new_dep["id"]

    # 3. Update dependent
    res_upd = client.put(f"/api/v1/parent/dependents/{dep_id}", json={
        "instructions": "Morning nap at 11:30 AM"
    })
    assert res_upd.status_code == 200
    assert res_upd.json()["instructions"] == "Morning nap at 11:30 AM"

    # 4. Delete dependent
    res_del = client.delete(f"/api/v1/parent/dependents/{dep_id}")
    assert res_del.status_code == 200
