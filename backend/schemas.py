from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime


# =========================
# USER SCHEMAS
# =========================

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# =========================
# FINANCE / EXPENSE SCHEMAS
# =========================

class ExpenseCreate(BaseModel):
    category: str
    amount: float
    expense_date: date


class ExpenseResponse(BaseModel):
    id: int
    user_id: int
    category: str
    amount: float
    expense_date: date

    class Config:
        from_attributes = True


# =========================
# SIMULATION SCHEMAS
# =========================

class SimulationRequest(BaseModel):
    months: int
    extra_savings: float = 0
    emergency_expense: float = 0


class SimulationResponse(BaseModel):
    months: int
    monthly_savings: float
    projected_balance: float
    goal_reached: bool


# =========================
# TRADE SCHEMAS
# =========================

class TradeCreate(BaseModel):
    symbol: str
    type: str   # BUY / SELL
    price: float
    quantity: int


class TradeResponse(BaseModel):
    id: int
    user_id: int
    symbol: str
    type: str
    price: float
    quantity: int
    pnl: float
    created_at: datetime

    class Config:
        from_attributes = True

from pydantic import BaseModel

class PortfolioResponse(BaseModel):
    balance: float
    position: int
    avg_price: float
    realized_pnl: float
    unrealized_pnl: float
    total_equity: float

    class Config:
        from_attributes = True
