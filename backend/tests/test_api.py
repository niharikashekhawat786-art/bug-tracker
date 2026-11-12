import os
os.environ["DATABASE_URL"] = "sqlite:///./test_bug_tracker.db"
os.environ["SECRET_KEY"] = "test-secret-key"

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_register_and_login():
    response = client.post("/api/auth/register", json={
        "name": "Test Admin", "email": "admin@example.com", "password": "StrongPass123"
    })
    assert response.status_code == 201
    login = client.post("/api/auth/login", data={
        "username": "admin@example.com", "password": "StrongPass123"
    })
    assert login.status_code == 200
    assert "access_token" in login.json()
