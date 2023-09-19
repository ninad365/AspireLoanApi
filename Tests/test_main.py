import datetime
import os
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from .test_helper import cleanup_database, create_test_user, login_user
from datetime import datetime, timedelta

# Import app and models
from ..main import app, get_db
from ..app.models.model import PaymentTerm, User, Loan

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
        create_test_user(TestingSessionLocal(), "testuser", "testpassword", "test@example.com", addLoans= True)

        # Log in the test user to get an access token
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

def test_approve_loans():
    try:
        # Create a test database session
        db = TestingSessionLocal()

        # Create a test user
        create_test_user(db, "testuser", "testpassword", "test@example.com", addLoans=True)

        # Log in the test user to get an access token
        login_response_data = login_user(client, "testuser", "testpassword")
        access_token = login_response_data["access_token"]

        # Set the authorization header with the access token
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        loan = db.query(Loan).order_by(Loan.id.desc()).first()

        # Define test loan approval data
        loan_approval_data = {
            "id": loan.id,
            "decision": 1
        }

        # Send a POST request to approve the loan
        response = client.post("/loans/decision", json=loan_approval_data, headers=headers)

        # Check the response status code and content
        assert response.status_code == 200
        response_data = response.json()
        assert "message" in response_data
        assert response_data["message"] == "User is not permitted."

        # Check if the payment terms were created
        payment_terms = db.query(PaymentTerm).filter(PaymentTerm.loan_id == 1).all()
        assert len(payment_terms) == 0

        # Create an admin user
        create_test_user(db, "admin", "adminpassword", "admin@example.com", admin=True)
        # Log in the admin user to get an access token
        login_response_data = login_user(client, "admin", "adminpassword")
        access_token = login_response_data["access_token"]

        # Set the authorization header with the access token
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        loan = db.query(Loan).order_by(Loan.id.desc()).first()

        # Define test loan approval data
        loan_approval_data = {
            "id": loan.id,
            "decision": 1
        }

        # Send a POST request to approve the loan
        response = client.post("/loans/decision", json=loan_approval_data, headers=headers)

        # Check the response status code and content
        assert response.status_code == 200
        response_data = response.json()
        assert "message" in response_data
        assert response_data["message"] == "Loan status updated successfully."

    finally:
        # Clean up the database
        db = TestingSessionLocal()
        cleanup_database(db)

# Test the make_payment endpoint
def test_make_payment():
    try:
        # Create a test database session
        db = TestingSessionLocal()

        # Create a test user
        create_test_user(db, "testuser", "testpassword", "test@example.com")

        user = db.query(User).order_by(User.id.desc()).first()

        loan_data = {
            "amount": 1000,
            "terms": 6,
            "user_id": user.id,
            "status": "Pending",
        }

        # Create a new loan directly in the database
        new_loan = Loan(**loan_data)
        db.add(new_loan)
        db.commit()

        loan = db.query(Loan).order_by(Loan.id.desc()).first()

        for i in range(loan_data["terms"]):
            # Create a test payment term for the loan
            test_payment_term_data = {
                "amount": 1000/6,  # Assuming the due amount is 1000
                "due_date": datetime.now() + timedelta(days = 7 * (i+1)),
                "payment_status": "Pending",
                "user_id": user.id,
                "loan_id": loan.id
            }

            new_payment_term = PaymentTerm(**test_payment_term_data)
            db.add(new_payment_term)

        db.commit()

        # Log in the test user to get an access token (You can use your login_user helper here)
        login_response_data = login_user(client, "testuser", "testpassword")
        access_token = login_response_data["access_token"]

        # Set the authorization header with the access token
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        paymentTerms = db.query(PaymentTerm).filter(PaymentTerm.loan_id == loan.id).all()

        # Define test payment data with amount less than the due amount
        payment_data = {
            "payment_id": paymentTerms[0].id,
            "amount": 100
        }

        # Send a POST request to make the payment
        response = client.post("/payments/make-payment/", json=payment_data, headers=headers)

        # Check the response status code and content
        assert response.status_code == 200
        response_data = response.json()
        assert "message" in response_data
        assert response_data["message"] == "Transiction failed. Payment amount is less than the due amount."

        updated_payment_term = db.query(PaymentTerm).filter(PaymentTerm.id == paymentTerms[0].id).first()
        assert updated_payment_term.payment_status == "Pending"
        db.close()

        # Define test payment data with amount equal to the due amount
        payment_data = {
            "payment_id": paymentTerms[0].id,
            "amount": 1000
        }

        # Send a POST request to make the payment
        response = client.post("/payments/make-payment/", json=payment_data, headers=headers)

        # Check the response status code and content
        assert response.status_code == 200
        response_data = response.json()
        assert "message" in response_data
        assert response_data["message"] == "Payment successful. Payment marked as Paid."

        print(paymentTerms[0].id)
        print(updated_payment_term.payment_status)
        # Check if the payment term is marked as "Paid"
        updated_payment_term = db.query(PaymentTerm).filter(PaymentTerm.id == paymentTerms[0].id).first()
        print(updated_payment_term.payment_status)
        assert updated_payment_term.payment_status == "Paid"

    finally:
        # Clean up the database
        db = TestingSessionLocal()
        cleanup_database(db)