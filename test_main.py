import json
from fastapi.testclient import TestClient
import pytest
from main import app  # Import your FastAPI app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient
from main import get_db  # Import your get_db function
from app.models.model import User  # Import your User model (adjust the import path)

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

@pytest.fixture
def client():
    # Set up a test database and create a test FastAPI client
    test_db = override_get_db()
    
    # Use TestClient instead of AsyncClient
    client = TestClient(app)
    
    yield client

def test_register_user(client):
    # Define test user data
    test_user_data = {
        "username": "testuser",
        "password": "testpassword",
        "email": "test@example.com",
    }

    # Test a successful registration
    response = client.post("/user/register/", json=test_user_data)
    assert response.status_code == 200
    assert response.json() == {"Success": "New user is created"}
