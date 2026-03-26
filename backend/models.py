from sqlalchemy import Column, Integer, Float, String, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


# =========================
# USER TABLE
# =========================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True)
    password = Column(String(255))

    finance_profile = relationship("FinanceProfile", back_populates="user")
    expenses = relationship("Expense", back_populates="user")
    trades = relationship("Trade", back_populates="user")


# =========================
# FINANCE PROFILE TABLE
# =========================

class FinanceProfile(Base):
    __tablename__ = "finance_profile"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    monthly_income = Column(Float)
    monthly_expenses = Column(Float)
    savings_goal = Column(Float)
    risk_level = Column(String(20))

    user = relationship("User", back_populates="finance_profile")


# =========================
# EXPENSE TABLE
# =========================

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    category = Column(String(50))
    amount = Column(Float)
    expense_date = Column(Date)

    user = relationship("User", back_populates="expenses")


# =========================
# TRADE TABLE
# =========================

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    symbol = Column(String(20), nullable=False)
    type = Column(String(10), nullable=False)  # BUY / SELL

    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    pnl = Column(Float, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="trades")
