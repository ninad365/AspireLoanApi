from sqlalchemy import delete
from sqlalchemy.orm import Session
from app.models.model import User, Loan  # Import your User and Loan models

def cleanup_database(db: Session):
    # Delete all records from the User and Loan tables to clean up the database
    db.execute(delete(Loan))
    db.execute(delete(User))
    db.commit()
    db.close()

def create_test_user(db, username, password, email):
    # Define test user data
    test_user_data = {
        "username": username,
        "password": password,
        "email": email,
    }

    # Create a new user directly in the database
    new_user = User(**test_user_data)
    db.add(new_user)
    db.commit()
    db.close()