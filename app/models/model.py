from pydantic import BaseModel
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ...app.db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True)
    password = Column(String(255), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    admin = Column(Integer)
    loans = relationship("Loan", back_populates="user")
    payment_status = relationship("PaymentTerm", back_populates="user")

class Loan(Base):
    __tablename__ = "loans"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Integer)
    terms = Column(Integer)
    start_date = Column(DateTime, default=func.now())
    status = Column(String(255))
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="loans")
    payment_status = relationship("PaymentTerm", back_populates="loan")

class PaymentTerm(Base):
    __tablename__ = "payment_status"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Integer)
    due_date = Column(DateTime)
    payment_status = Column(String(255))
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="payment_status")
    loan_id = Column(Integer, ForeignKey("loans.id"))
    loan = relationship("Loan", back_populates="payment_status")


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
    status: str
    user_id: int

class UserLogin(BaseModel):
    username: str
    password: str