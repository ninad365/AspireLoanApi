from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import or_
from sqlalchemy.orm import Session
import jwt
import os
from .app.models.model import (
    LoanApprove,
    LoanCreate,
    LoanView,
    PaymentTerm,
    User,
    Loan,
    UserCreate,
)
from .app.db import SessionLocal
from dotenv import load_dotenv
from datetime import datetime, timedelta

app = FastAPI()

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login/")


def get_database_session():
    return SessionLocal()


def get_db():
    db = get_database_session()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # Get username and user id from the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")

        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        return {"username": username, "id": user_id}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


def create_access_token(data: dict):
    try:
        return jwt.encode(data, SECRET_KEY, algorithm="HS256")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@app.post("/user/register/")
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if the username or email is already in use
    existing_user = (
        db.query(User)
        .filter(or_(User.username == user_data.username, User.email == user_data.email))
        .first()
    )

    if existing_user:
        db.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already in use",
        )

    # Create a new user
    new_user = User(**user_data.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()

    return {"Success": "New user is created"}


@app.post("/user/login/", response_model=dict)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    # Check the username and password
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # Generate an access token for the user
    access_token = create_access_token({"sub": user.username, "id": user.id})

    return {"access_token": access_token, "token_type": "bearer"}


def authenticate_user(username: str, password: str, db):
    # Find the user by username in the database
    user = db.query(User).filter(or_(User.username == username)).first()
    if user is None:
        return None  # User not found
    if password != user.password:
        return None  # Password doesn't match
    return user  # Authentication successful


# Route to create a new loan
@app.post("/loans/create")
async def create_loan(
    loan_data: LoanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if loan_data.terms > 12:
        return {"Error": "Please select terms less than or equal to 12."}
    else:
        try:
            # Create a new loan object
            new_loan = Loan(
                amount=loan_data.amount,
                terms=loan_data.terms,
                start_date=datetime.now(),
                user_id=current_user["id"],
                status="Waiting for approval",
            )

            # Add the new loan to the database
            db.add(new_loan)
            db.commit()
            db.refresh(new_loan)

            return {"Message": "Loan was created. Waiting for approval."}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))


# Endpoint to get all loans mapped to the logged-in user
@app.get("/loans/")
async def get_loans_for_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)):

    # Query the database to get all loans associated with the current user

    user = db.query(User).filter(User.id == current_user["id"]).first()
    if user.admin == 1:
        loans = db.query(Loan).all()
    else:
        loans = db.query(Loan).filter(Loan.user_id == current_user["id"]).all()

    # Convert the items to a list of ItemResponse models for the response
    loans_response = [
        LoanView(id=loan.id, amount=loan.amount, terms=loan.terms, status=loan.status, user_id=loan.user_id)
        for loan in loans
    ]

    return loans_response

# Endpoint for approval/rejection
@app.post("/loans/decision")
async def get_loans_for_user(loan_data: LoanApprove,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):

    user = db.query(User).filter(User.id == current_user["id"]).first()
    if user.admin == 1:
        loan = db.query(Loan).filter(Loan.id == loan_data.id).first()
        if loan:
            # Update loan approval status
            loan.status = loan_data.decision

            # If approved, save the payment terms in the database
            if loan_data.decision == 1:
                amount_per_installment = loan.amount / loan.terms
                date = datetime.now()
                for i in range(loan.terms):
                    payment_status = PaymentTerm (
                        amount = amount_per_installment,
                        due_date = date + timedelta(days = 7 * (i+1)),
                        payment_status = "Pending",
                        user_id = loan.user_id,
                        loan_id = loan.id
                    )

                    db.add(payment_status)

            db.commit()
            return {"message": "Loan status updated successfully."}
    else:
        return {"error":"User is not permitted."}
    

# Endpoint to get pending payments with the earliest due date
@app.get("/payments/pending-earliest-due-date")
async def get_pending_payments_with_earliest_due_date(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get the current date and time
    current_datetime = datetime.now()

    # Query for pending payments with the earliest due date
    pending_payment = (
        db.query(PaymentTerm)
        .filter(PaymentTerm.user_id == current_user["id"])
        .filter(PaymentTerm.payment_status == "Pending")
        .filter(PaymentTerm.due_date > current_datetime)
        .order_by(PaymentTerm.due_date.asc())
        .first()
    )

    if pending_payment:
        return {
            "id": pending_payment.id,
            "amount": pending_payment.amount,
            "due_date": pending_payment.due_date,
            "user_id": pending_payment.user_id,
            "loan_id": pending_payment.loan_id
        }
    else:
        return {"message": "No pending payments with future due dates found."}
    
@app.post("/payments/make-payment/")
async def make_payment(
    payment_id: int,
    amount: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Retrieve the payment record from the database
    payment = db.query(PaymentTerm).filter(PaymentTerm.user_id == current_user["id"]).filter(PaymentTerm.id == payment_id).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Check if the payment amount is greater than or equal to the due amount
    if amount >= payment.amount:
        # Mark the payment as paid
        payment.payment_status = "Paid"
        db.commit()

        # Check if all payments related to the loan are paid
        check_loan_paid(db, payment.loan_id)

        return {"message": "Payment successful. Payment marked as Paid."}
    else:
        return {"message": "Transiction failed. Payment amount is less than the due amount."}
    
# Function to check if all payments related to a loan are paid
def check_loan_paid(db: Session, loan_id: int):
    # Query the payments related to the loan
    payments = db.query(PaymentTerm).filter(PaymentTerm.loan_id == loan_id).all()

    # Check if all payments are marked as "Paid"
    if all(payment.payment_status == "Paid" for payment in payments):
        # Update the loan as "Paid" if all payments are paid
        loan = db.query(Loan).filter(Loan.id == loan_id).first()
        if loan:
            loan.status = "Paid"
            db.commit()