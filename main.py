from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import jwt
import os
from app.models.model import LoanCreate, User, Item, Loan, UserCreate, ItemCreate
from app.db import SessionLocal
from dotenv import load_dotenv
from datetime import datetime

app = FastAPI()

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

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
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
        return {"username":username,"id":user_id}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

def create_access_token(data: dict):
    try:
        return jwt.encode(data, SECRET_KEY, algorithm="HS256")
    except:
        print(SECRET_KEY)

@app.post("/register/")
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if the username or email is already in use
    existing_user = db.query(User).filter(
        or_(User.username == user_data.username, User.email == user_data.email)
    ).first()

    if existing_user:
        db.close()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already in use")

    # Create a new user
    new_user = User(**user_data.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()

    return {"Success":"New user is created"}

@app.post("/login/", response_model=dict)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Check the username and password
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    # Generate an access token for the user
    access_token = create_access_token({"sub": user.username, "id": user.id})

    return {"access_token": access_token, "token_type": "bearer"}

def authenticate_user(username: str, password: str, db):
    # Find the user by username in the database
    user = db.query(User).filter(
        or_(User.username == username)).first()
    if user is None:
        return None  # User not found
    if password != user.password:
        return None  # Password doesn't match
    return user  # Authentication successful

# Route to retrieve items
@app.get("/items/{item_id}")
async def read_item(item_id: int, current_user: dict = Depends(get_current_user)):
    try:
        db = SessionLocal()
        item = db.query(Item).filter(Item.id == item_id).first()
        db.close()
        if item is None:
            return {"message": "Item not found"}
        return {"id": item.id, "name": item.name, "current_user": current_user["username"], "user_id": current_user["id"]}
    except SQLAlchemyError as e:
        # Handle database-related exceptions here
        # You can log the error or return an appropriate error response
        return {"message": "Database error: " + str(e)}

# Endpoint to get all items mapped to the logged-in user
@app.get("/items/")
async def get_items_for_user(current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    # Query the database to get all items associated with the current user
    items = db.query(Item).filter(Item.user_id == current_user["id"]).all()
    
    # Convert the items to a list of ItemResponse models for the response
    items_response = [ItemCreate(name=item.name) for item in items]
    
    return items_response

@app.post("/items/")
async def create_item(item: ItemCreate, current_user: User = Depends(get_current_user)):
    try:
        db = SessionLocal()
        db_user = db.query(User).filter(User.id == current_user["id"]).first()
        if db_user is None:
            db.close()
            return {"message": "User not found"}

        db_item = Item(name=item.name, user=db_user)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        db.close()
        return {"message": "Item saved"}
    except SQLAlchemyError as e:
        return {"message": "Database error: " + str(e)}
    
# Route to create a new loan
@app.post("/loans/")
async def create_loan(loan_data: LoanCreate, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    try:
        # Create a new loan object
        new_loan = Loan(amount = loan_data.amount, 
                        terms = loan_data.terms, 
                        start_date = datetime.now(),
                        user_id=current_user["id"],
                        )

        # Add the new loan to the database
        db.add(new_loan)
        db.commit()
        db.refresh(new_loan)

        return {"Message":"Loan was created"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))