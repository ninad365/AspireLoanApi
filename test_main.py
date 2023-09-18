import os
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from test_helper import cleanup_database, create_test_user, login_user

# Import app and models
from main import app, get_db
from app.models.model import User, Loan

load_dotenv()
SQLALCHEMY_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

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
    try:
        db = TestingSessionLocal()

        # Register a test user
        create_test_user(db, "testuser", "testpassword", "test@example.com")

        # Query the database to check if the user has been created
        created_user = db.query(User).filter_by(username="testuser").first()
        db.close()

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
        access_token = response_data["access_token"]

        # Create a new loan
        loan_data = {
            "amount": 1000,
            "terms": 6,
        }
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post("/loans/create", json=loan_data, headers=headers)
        assert response.status_code == 200
        assert response.json() == {"Message": "Loan was created. Waiting for approval."}

        # Query the database to check if the loan has been created
        db = TestingSessionLocal()
        created_loan = db.query(Loan).filter_by(user_id=created_user.id).first()
        db.close()

        # Assert that the loan exists in the database
        assert created_loan is not None
        assert created_loan.amount == 1000
        assert created_loan.terms == 6
        assert created_loan.status == "Waiting for approval"

    finally:
        cleanup_database(TestingSessionLocal())

def test_register_endpoint():
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

    finally:
        cleanup_database(TestingSessionLocal())

def test_login_endpoint():
    try:
        db = TestingSessionLocal()

        create_test_user(db, "testuser", "testpassword", "test@example.com")
        # Test a successful login
        login_data = {
            "username": "testuser",
            "password": "testpassword",
        }

        wrong_login_data = {
            "username": "testuser",
            "password": "wrongpassword",
        }

        response = client.post("/user/login/", data=wrong_login_data)
        assert response.status_code == 401

        response = client.post("/user/login/", data=login_data)
        assert response.status_code == 200
        response_data = response.json()
        assert "access_token" in response_data
        assert response_data["token_type"] == "bearer"
    finally:
        cleanup_database(TestingSessionLocal())

def test_create_loan():
    try:
        # Create a test user
        create_test_user(TestingSessionLocal(), "testuser", "testpassword", "test@example.com")

        # Log in the test user to get an access token (You can use your login_user helper here)
        login_response_data = login_user(client, "testuser", "testpassword")
        access_token = login_response_data["access_token"]

        # Define loan data
        loan_data = {
            "amount": 1000,
            "terms": 6,
        }

        # Set the authorization header with the access token
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        # Send a POST request to create a new loan
        response = client.post("/loans/create", json=loan_data, headers=headers)

        # Check the response status code and content
        assert response.status_code == 200
        response_data = response.json()
        assert "Message" in response_data
        assert response_data["Message"] == "Loan was created. Waiting for approval."

    finally:
        # Clean up the database
        db = TestingSessionLocal()
        cleanup_database(db)

def test_get_loans_for_user():
    try:
        # Create a test user
        create_test_user(TestingSessionLocal(), "testuser", "testpassword", "test@example.com", True)

        # Log in the test user to get an access token (You can use your login_user helper here)
        login_response_data = login_user(client, "testuser", "testpassword")
        access_token = login_response_data["access_token"]

        # Set the authorization header with the access token
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        # Send a GET request to retrieve loans for the logged-in user
        response = client.get("/loans/", headers=headers)

        # Check the response status code and content
        assert response.status_code == 200
        loans_response = response.json()

        # Assuming LoanView has the same structure as Loan in your model
        assert isinstance(loans_response, list)
        assert len(loans_response) == 1

    finally:
        # Clean up the database
        db = TestingSessionLocal()
        cleanup_database(db)