import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

client = TestClient(app)

def test_landing_page_rendering():
    res = client.get("/")
    assert res.status_code == 200
    assert "Guardian Go" in res.text

def test_login_entry_points():
    res_parent = client.get("/login")
    assert res_parent.status_code == 200

    res_guardian = client.get("/guardian/login")
    assert res_guardian.status_code == 200

    res_admin = client.get("/admin/login")
    assert res_admin.status_code == 200

def test_portal_routes():
    res_user = client.get("/portals/user")
    assert res_user.status_code == 200

    res_g = client.get("/portals/guardian")
    assert res_g.status_code == 200

    res_a = client.get("/portals/admin")
    assert res_a.status_code == 200

def test_css_stylesheet_serving():
    res = client.get("/static/styles.css")
    assert res.status_code == 200
    assert "--primary-green" in res.text
