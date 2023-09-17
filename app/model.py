from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True)
    password = Column(String(255), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    items = relationship("Item", back_populates="user")

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="items")

class ItemCreate(BaseModel):
    name: str

class UserCreate(BaseModel):
    username: str
    password: str
    email: str

class UserLogin(BaseModel):
    username: str
    password: str
