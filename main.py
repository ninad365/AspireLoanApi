from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import ForeignKey, create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError

app = FastAPI()

# Database Configuration
DATABASE_URL = "mysql+mysqlconnector://root:ninad1234@localhost/mydatabase"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

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
    email = Column(String(255), unique=True, index=True)
    items = relationship("Item", back_populates="user")

class UserCreate(BaseModel):
    username: str
    email: str

Base.metadata.create_all(bind=engine)

# Route to retrieve items
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    try:
        db = SessionLocal()
        item = db.query(Item).filter(Item.id == item_id).first()
        db.close()
        if item is None:
            return {"message": "Item not found"}
        return {"id": item.id, "name": item.name}

    except SQLAlchemyError as e:
        # Handle database-related exceptions here
        # You can log the error or return an appropriate error response
        return {"message": "Database error: " + str(e)}

@app.post("/items/")
async def create_item(item: ItemCreate, user_id: int):
    try:
        db = SessionLocal()
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user is None:
            db.close()
            return {"message": "User not found"}

        db_item = Item(name=item.name, user=db_user)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        db.close()
        return {"Message": "Item saved"}
    except SQLAlchemyError as e:
        return {"message": "Database error: " + str(e)}

@app.post("/users/")
async def create_user(user: UserCreate):
    db = SessionLocal()
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    db.close()
    return db_user
