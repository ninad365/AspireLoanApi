import json
from fastapi.testclient import TestClient
from main import app  # Import your FastAPI app
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker, declarative_base
from main import get_db  # Import your get_db function
from app.models.model import User  # Import your User model (adjust the import path)

SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://root:ninad1234@localhost/mydatabasetest"

Base = declarative_base()

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False),
)

TestingSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_register_and_login():
    # Define test user data
    test_user_data = {
        "username": "testuser",
        "password": "testpassword",
        "email": "test@example.com",
    }

    try:
        # Test a successful registration
        response = client.post("/user/register/", json=test_user_data)
        assert response.status_code == 200
        assert response.json() == {"Success": "New user is created"}

        # Query the database to check if the user has been created
        db = TestingSessionLocal()
        created_user = db.query(User).filter_by(username="testuser").first()
        db.close()

        # Assert that the user exists in the database
        assert created_user is not None

        # Test a successful login
        login_data = {
            "username": "testuser",
            "password": "testpassword",
        }
        response = client.post("/user/login/", data=login_data)
        assert response.status_code == 200
        response_data = response.json()
        assert "access_token" in response_data
        assert response_data["token_type"] == "bearer"

    finally:
        # Delete all records from the User table to clean up the database
        db = TestingSessionLocal()
        db.execute(delete(User))
        db.commit()
        db.close()