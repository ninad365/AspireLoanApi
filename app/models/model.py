from pydantic import BaseModel
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True)
    password = Column(String(255), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    admin = Column(Integer)
    items = relationship("Item", back_populates="user")
    loans = relationship("Loan", back_populates="user")
    payment_status = relationship("PaymentTerm", back_populates="user")


class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="items")

class Loan(Base):
    __tablename__ = "loans"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Integer)
    terms = Column(Integer)
    start_date = Column(DateTime, default=func.now())
    approved = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="loans")

class PaymentTerm(Base):
    __tablename__ = "payment_status"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Integer)
    due_date = Column(DateTime)
    payment_status = Column(String(255))
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="payment_status")

class ItemCreate(BaseModel):
    name: str

class UserCreate(BaseModel):
    username: str
    password: str
    email: str

class LoanCreate(BaseModel):
    amount: int
    terms: int

class LoanApprove(BaseModel):
    id: int
    decision: int

class LoanView(BaseModel):
    id: int
    amount: int
    terms: int
    approved: int
    user_id: int

class UserLogin(BaseModel):
    username: str
    password: str
