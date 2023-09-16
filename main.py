from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import ForeignKey, create_engine, Column, Integer, String, or_
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
import jwt

app = FastAPI()

# Database Configuration
DATABASE_URL = "mysql+mysqlconnector://root:ninad1234@localhost/mydatabase"
SECRET_KEY = "ahrdkos1b5j3bs9o"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# Model Definition
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="items")

class ItemCreate(BaseModel):
    name: str

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True)
    password = Column(String(255), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    items = relationship("Item", back_populates="user")

class UserCreate(BaseModel):
    username: str
    password: str
    email: str

class UserLogin(BaseModel):
    username: str
    password: str

Base.metadata.create_all(bind=engine)

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
    return jwt.encode(data, SECRET_KEY, algorithm="HS256")

@app.post("/register/")
async def register_user(user_data: UserCreate):
    # Check if the username or email is already in use
    db = SessionLocal()
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

    return new_user

@app.post("/login/", response_model=dict)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Check the username and password
    db = SessionLocal()
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    # Generate an access token for the user
    access_token = create_access_token({"sub": user.username, "id": user.id})

    return {"access_token": access_token, "token_type": "bearer"}

def authenticate_user(db: Session, username: str, password: str):
    # Find the user by username in the database
    user = db.query(User).filter(User.username == username).first()
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
    
# Endpoint to get all items mapped to the logged-in user
@app.get("/items/", response_model=list[ItemCreate])
async def get_items_for_user(current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    # Query the database to get all items associated with the current user
    items = db.query(Item).filter(Item.user_id == current_user["id"]).all()
    
    # Convert the items to a list of ItemResponse models for the response
    items_response = [ItemCreate(name=item.name) for item in items]
    
    return items_response