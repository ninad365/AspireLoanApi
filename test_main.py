import json
from fastapi.testclient import TestClient
import pytest
from main import app, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

client = TestClient(app)

SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://root:ninad1234@localhost/mydatabasetest"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False),
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

def test_read_item():
    response = client.get("/items/1")
    assert response.status_code == 401

def test_create_item():
    response = client.post("/items/", json={"name": "new_item"})
    assert response.status_code == 401

def test_register_user():
    # Define test user data
    test_user_data = {
        "id":1,
        "username": "testuser",
        "password": "testpassword",
        "email": "test@example.com",
    }

    # Test a successful registration
    response = client.post("/register/", json=test_user_data)
    assert response.status_code == 200
    assert response.json() == {"Success":"New user is created"}