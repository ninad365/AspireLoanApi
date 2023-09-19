from sqlalchemy import delete
from sqlalchemy.orm import Session
from ..app.models.model import User, Loan, PaymentTerm

def cleanup_database(db: Session):
    # Delete all records from the User and Loan tables to clean up the database
    db.execute(delete(PaymentTerm))
    db.execute(delete(Loan))
    db.execute(delete(User))
    db.commit()
    db.close()

def create_test_user(db, username, password, email, admin = False, addLoans = False):
    # Define test user data
    test_user_data = {
        "username": username,
        "password": password,
        "email": email,
    }

    if admin:
        test_user_data["admin"] = 1

    # Create a new user directly in the database
    new_user = User(**test_user_data)
    db.add(new_user)
    db.commit()

    if addLoans:
        # Define loan data
        loan_data = {
            "amount": 1000,
            "terms": 6,
            "user_id": new_user.id,
            "status": "Pending",
        }

        # Create a new loan directly in the database
        new_loan = Loan(**loan_data)
        db.add(new_loan)
        db.commit()

    db.close()

def login_user(client, username: str, password: str):
    login_data = {
        "username": username,
        "password": password,
    }
    
    response = client.post("/user/login/", data=login_data)
    return response.json()