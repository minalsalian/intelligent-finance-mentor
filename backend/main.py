from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session
import models
from database import engine, get_db
from security import hash_password, verify_password
from datetime import date
from fastapi.middleware.cors import CORSMiddleware
from schemas import (
    UserRegister,
    UserLogin,
    ExpenseCreate,
    ExpenseResponse,
    SimulationRequest,
    SimulationResponse,
    TradeCreate,
    TradeResponse
)
from schemas import TradeCreate, TradeResponse
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from sqlalchemy import func
import models
from schemas import PortfolioResponse
import yfinance as yf




app = FastAPI(title="Intelligent Finance Mentor")
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



models.Base.metadata.create_all(bind=engine)


class FinanceProfileCreate(BaseModel):
    monthly_income: float = Field(ge=0)
    monthly_expenses: float = Field(ge=0)
    savings_goal: float = Field(ge=0)
    risk_level: str = Field(min_length=3, max_length=20)


class FinanceProfileResponse(BaseModel):
    id: int
    user_id: int
    monthly_income: float
    monthly_expenses: float
    savings_goal: float
    risk_level: str

    class Config:
        orm_mode = True


@app.get("/")
def root():
    return {"message": "Backend & Database connected"}


@app.post("/register")
def register_user(user: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pwd = hash_password(user.password)

    new_user = models.User(
        email=user.email,
        password=hashed_pwd
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user_id": new_user.id
    }


@app.post("/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    return {
        "message": "Login successful",
        "user_id": db_user.id
    }


@app.post("/finance/profile/{user_id}", response_model=FinanceProfileResponse)
def save_finance_profile(
    user_id: int,
    profile: FinanceProfileCreate,
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    finance = db.query(models.FinanceProfile).filter(
        models.FinanceProfile.user_id == user_id
    ).first()

    if finance:
        finance.monthly_income = profile.monthly_income
        finance.monthly_expenses = profile.monthly_expenses
        finance.savings_goal = profile.savings_goal
        finance.risk_level = profile.risk_level
    else:
        finance = models.FinanceProfile(
            user_id=user_id,
            monthly_income=profile.monthly_income,
            monthly_expenses=profile.monthly_expenses,
            savings_goal=profile.savings_goal,
            risk_level=profile.risk_level,
        )
        db.add(finance)

    db.commit()
    db.refresh(finance)
    return finance


@app.get("/finance/profile/{user_id}", response_model=FinanceProfileResponse)
def get_finance_profile(
    user_id: int,
    db: Session = Depends(get_db),
):
    finance = db.query(models.FinanceProfile).filter(
        models.FinanceProfile.user_id == user_id
    ).first()

    if not finance:
        raise HTTPException(status_code=404, detail="Finance profile not found")

    return finance

@app.post("/expenses/{user_id}", response_model=ExpenseResponse)
def add_expense(
    user_id: int,
    expense: ExpenseCreate,
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_expense = models.Expense(
        user_id=user_id,
        category=expense.category,
        amount=expense.amount,
        expense_date=expense.expense_date
    )

    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    return new_expense


@app.get("/expenses/summary/{user_id}")
def expense_summary(user_id: int, db: Session = Depends(get_db)):
    expenses = (
        db.query(models.Expense.category, func.sum(models.Expense.amount))
        .filter(models.Expense.user_id == user_id)
        .group_by(models.Expense.category)
        .all()
    )

    return {
        "summary": [
            {"category": cat, "total": total}
            for cat, total in expenses
        ]
    }


@app.get("/expenses/behavior/{user_id}")
def expense_behavior(user_id: int, db: Session = Depends(get_db)):
    finance = db.query(models.FinanceProfile).filter(
        models.FinanceProfile.user_id == user_id
    ).first()

    if not finance:
        raise HTTPException(status_code=404, detail="Finance profile not found")

    total_expenses = (
        db.query(func.sum(models.Expense.amount))
        .filter(models.Expense.user_id == user_id)
        .scalar()
    ) or 0

    income = finance.monthly_income
    savings = income - total_expenses
    savings_rate = savings / income if income > 0 else 0

    overspending = total_expenses > (0.8 * income)

    return {
        "income": income,
        "total_expenses": total_expenses,
        "savings": savings,
        "savings_rate": round(savings_rate, 2),
        "overspending": overspending
    }

@app.get("/simulation/basic/{user_id}")
def basic_simulation(user_id: int, months: int, db: Session = Depends(get_db)):
    finance = db.query(models.FinanceProfile).filter(
        models.FinanceProfile.user_id == user_id
    ).first()

    if not finance:
        raise HTTPException(status_code=404, detail="Finance profile not found")

    monthly_savings = finance.monthly_income - finance.monthly_expenses
    projected_balance = monthly_savings * months

    return {
        "months": months,
        "monthly_savings": monthly_savings,
        "projected_balance": projected_balance
    }

@app.post("/simulation/whatif/{user_id}", response_model=SimulationResponse)
def what_if_simulation(
    user_id: int,
    request: SimulationRequest,
    db: Session = Depends(get_db)
):
    finance = db.query(models.FinanceProfile).filter(
        models.FinanceProfile.user_id == user_id
    ).first()

    if not finance:
        raise HTTPException(status_code=404, detail="Finance profile not found")

    base_savings = finance.monthly_income - finance.monthly_expenses
    adjusted_savings = base_savings + request.extra_savings

    total_saved = (adjusted_savings * request.months) - request.emergency_expense

    goal_reached = total_saved >= finance.savings_goal

    return {
        "months": request.months,
        "monthly_savings": adjusted_savings,
        "projected_balance": round(total_saved, 2),
        "goal_reached": goal_reached
    }

@app.get("/health/score/{user_id}")
def financial_health_score(user_id: int, db: Session = Depends(get_db)):
    finance = db.query(models.FinanceProfile).filter(
        models.FinanceProfile.user_id == user_id
    ).first()

    if not finance:
        raise HTTPException(status_code=404, detail="Finance profile not found")

    total_expenses = (
        db.query(func.sum(models.Expense.amount))
        .filter(models.Expense.user_id == user_id)
        .scalar()
    ) or 0

    income = finance.monthly_income
    savings = income - total_expenses

    # -----------------------
    # Emergency Score
    # -----------------------
    emergency_fund_required = 6 * total_expenses

    if savings >= emergency_fund_required:
        emergency_score = 100
    elif savings >= 3 * total_expenses:
        emergency_score = 70
    else:
        emergency_score = 40

    # -----------------------
    # Savings Discipline Score
    # -----------------------
    savings_rate = savings / income if income > 0 else 0

    if savings_rate >= 0.4:
        savings_score = 100
    elif savings_rate >= 0.2:
        savings_score = 70
    elif savings_rate >= 0.1:
        savings_score = 50
    else:
        savings_score = 30

    # -----------------------
    # Overspending Risk
    # -----------------------
    overspending = total_expenses > (0.8 * income)

    behavior_bonus = 100 if not overspending else 50

    # -----------------------
    # Final Score
    # -----------------------
    overall_score = (
        0.4 * savings_score +
        0.4 * emergency_score +
        0.2 * behavior_bonus
    )

    return {
        "income": income,
        "total_expenses": total_expenses,
        "savings": savings,
        "savings_rate": round(savings_rate, 2),
        "emergency_score": emergency_score,
        "savings_score": savings_score,
        "overspending": overspending,
        "overall_financial_health_score": round(overall_score, 2)
    }
@app.get("/health/recommendations/{user_id}")
def financial_recommendations(user_id: int, db: Session = Depends(get_db)):
    finance = db.query(models.FinanceProfile).filter(
        models.FinanceProfile.user_id == user_id
    ).first()

    if not finance:
        raise HTTPException(status_code=404, detail="Finance profile not found")

    total_expenses = (
        db.query(func.sum(models.Expense.amount))
        .filter(models.Expense.user_id == user_id)
        .scalar()
    ) or 0

    income = finance.monthly_income
    savings = income - total_expenses
    savings_rate = savings / income if income > 0 else 0

    recommendations = []

    # Savings rate analysis
    if savings_rate < 0.1:
        recommendations.append("Your savings rate is critically low. Focus on reducing non-essential expenses.")
    elif savings_rate < 0.2:
        recommendations.append("Try increasing your monthly savings to at least 20% of income.")
    elif savings_rate >= 0.4:
        recommendations.append("Excellent savings discipline. Keep maintaining this consistency.")

    # Emergency fund analysis
    emergency_required = 6 * total_expenses

    if savings < emergency_required:
        recommendations.append("Build an emergency fund covering at least 6 months of expenses.")

    # Overspending check
    if total_expenses > (0.8 * income):
        recommendations.append("You are spending more than 80% of your income. Control discretionary spending.")

    # Priority level
    if len(recommendations) >= 3:
        priority = "High Improvement Needed"
    elif len(recommendations) == 2:
        priority = "Moderate Improvement Needed"
    elif len(recommendations) == 1:
        priority = "Stable but Can Improve"
    else:
        priority = "Financially Healthy"

    return {
        "income": income,
        "total_expenses": total_expenses,
        "savings_rate": round(savings_rate, 2),
        "recommendations": recommendations,
        "priority_level": priority
    }
@app.get("/health/explain/{user_id}")
def explain_financial_status(user_id: int, db: Session = Depends(get_db)):
    finance = db.query(models.FinanceProfile).filter(
        models.FinanceProfile.user_id == user_id
    ).first()

    if not finance:
        raise HTTPException(status_code=404, detail="Finance profile not found")

    total_expenses = (
        db.query(func.sum(models.Expense.amount))
        .filter(models.Expense.user_id == user_id)
        .scalar()
    ) or 0

    income = finance.monthly_income
    savings = income - total_expenses
    savings_rate = savings / income if income > 0 else 0

    strengths = []
    weaknesses = []
    summary = ""

    if savings_rate >= 0.4:
        strengths.append("Excellent savings discipline")
    elif savings_rate < 0.2:
        weaknesses.append("Low savings rate")

    if total_expenses > 0.8 * income:
        weaknesses.append("High spending relative to income")

    emergency_required = 6 * total_expenses
    if savings >= emergency_required:
        strengths.append("Strong emergency readiness")
    else:
        weaknesses.append("Insufficient emergency fund")

    if len(weaknesses) == 0:
        summary = "You are financially healthy with stable savings and controlled spending."
    else:
        summary = "Your financial condition is stable but requires improvement in key areas."

    next_action = "Increase savings or reduce discretionary expenses to strengthen financial stability."

    return {
        "summary": summary,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "next_best_action": next_action
    }

import requests

@app.get("/market/quote/{symbol}")
def get_quote(symbol: str):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch data")

    data = response.json()

    if "chart" not in data or not data["chart"]["result"]:
        raise HTTPException(status_code=404, detail="Stock not found")

    result = data["chart"]["result"][0]

    meta = result["meta"]
    quote = result["indicators"]["quote"][0]

    latest_close = quote["close"][-1]

    return {
        "symbol": symbol.upper(),
        "price": meta.get("regularMarketPrice"),
        "previous_close": meta.get("previousClose"),
        "latest_close": latest_close
    }


@app.get("/market/chart/{symbol}")
def get_intraday_chart(symbol: str):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch chart")

    try:
        data = response.json()
    except:
        raise HTTPException(status_code=500, detail="Invalid chart response")

    if "chart" not in data or not data["chart"]["result"]:
        raise HTTPException(status_code=404, detail="No chart data")

    result = data["chart"]["result"][0]
    timestamps = result["timestamp"]
    quote = result["indicators"]["quote"][0]

    ohlc = []

    for i in range(len(timestamps)):
        if quote["close"][i] is None:
            continue

        ohlc.append({
            "time": timestamps[i],
            "open": quote["open"][i],
            "high": quote["high"][i],
            "low": quote["low"][i],
            "close": quote["close"][i]
        })

    return {
        "symbol": symbol.upper(),
        "data": ohlc
    }
import yfinance as yf
from fastapi import HTTPException

@app.get("/market/candles/{symbol}")
def get_candles(symbol: str):

    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period="3mo")

        if data.empty:
            raise HTTPException(status_code=400, detail="Invalid symbol")

        candles = []

        for index, row in data.iterrows():
            candles.append({
                "time": index.strftime("%Y-%m-%d"),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"])
            })

        return {"candles": candles}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))





# --- Trades API ---
@app.post("/trades/{user_id}", response_model=TradeResponse)
def create_trade(user_id: int, trade: TradeCreate, db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_trade = models.Trade(
        user_id=user_id,
        symbol=trade.symbol,
        type=trade.type,
        price=trade.price,
        quantity=trade.quantity,
        pnl=0
    )

    db.add(new_trade)
    db.commit()
    db.refresh(new_trade)

    return new_trade

@app.get("/trades/{user_id}")
def get_trades(user_id: int, db: Session = Depends(get_db)):

    trades = db.query(models.Trade).filter(
        models.Trade.user_id == user_id
    ).all()

    result = []

    for trade in trades:

        # Fetch latest market price
        stock = yf.Ticker(trade.symbol)
        data = stock.history(period="1d")

        if data.empty:
            current_price = float(trade.price)
        else:
            current_price = float(data["Close"].iloc[-1])

        entry_price = float(trade.price)
        quantity = int(trade.quantity)

        # Calculate unrealized PnL
        if trade.type == "BUY":
            unrealized_pnl = (current_price - entry_price) * quantity
        else:
            unrealized_pnl = (entry_price - current_price) * quantity

        result.append({
            "id": trade.id,
            "symbol": trade.symbol,
            "type": trade.type,
            "entry_price": round(entry_price, 2),
            "current_price": round(current_price, 2),
            "quantity": quantity,
            "unrealized_pnl": round(unrealized_pnl, 2)
        })

    return result

@app.get("/portfolio/{user_id}")
def get_portfolio(user_id: int, db: Session = Depends(get_db)):

    trades = db.query(models.Trade).filter(
        models.Trade.user_id == user_id
    ).all()

    total_unrealized = 0
    total_realized = 0
    invested_amount = 0

    for trade in trades:

        stock = yf.Ticker(trade.symbol)
        data = stock.history(period="1d")

        if data.empty:
            current_price = float(trade.price)
        else:
            current_price = float(data["Close"].iloc[-1])

        entry_price = float(trade.price)
        quantity = int(trade.quantity)

        if trade.type == "BUY":
            total_unrealized += (current_price - entry_price) * quantity
            invested_amount += entry_price * quantity
        else:
            total_realized += (entry_price - current_price) * quantity

    total_equity = invested_amount + total_unrealized

    return {
        "invested_amount": round(invested_amount, 2),
        "total_unrealized_pnl": round(total_unrealized, 2),
        "total_realized_pnl": round(total_realized, 2),
        "total_equity": round(total_equity, 2)
    }


    # Get current market price
    unrealized_pnl = 0
    if position > 0:
        latest_trade = trades[-1] if trades else None
        symbol = latest_trade.symbol if latest_trade else None

        if symbol:
            stock = yf.Ticker(symbol)
            data = stock.history(period="1d")
            if not data.empty:
                current_price = float(data["Close"].iloc[-1])
                unrealized_pnl = (current_price - avg_price) * position

    total_equity = balance + unrealized_pnl

    return {
        "balance": balance,
        "position": position,
        "avg_price": avg_price,
        "realized_pnl": realized_pnl,
        "unrealized_pnl": unrealized_pnl,
        "total_equity": total_equity
    }

@app.get("/portfolio/{user_id}")
def get_portfolio(user_id: int, db: Session = Depends(get_db)):

    trades = db.query(models.Trade).filter(
        models.Trade.user_id == user_id
    ).all()

    if not trades:
        return {
            "total_invested": 0,
            "unrealized_pnl": 0,
            "net_equity": 0
        }

    total_invested = 0
    total_unrealized = 0

    for trade in trades:

        stock = yf.Ticker(trade.symbol)
        data = stock.history(period="1d")

        if data.empty:
            current_price = trade.price
        else:
            current_price = float(data["Close"].iloc[-1])

        if trade.type == "BUY":
            total_invested += trade.price * trade.quantity
            total_unrealized += (current_price - trade.price) * trade.quantity

        elif trade.type == "SELL":
            total_invested -= trade.price * trade.quantity
            total_unrealized += (trade.price - current_price) * trade.quantity

    net_equity = total_invested + total_unrealized

    return {
        "total_invested": round(total_invested, 2),
        "unrealized_pnl": round(total_unrealized, 2),
        "net_equity": round(net_equity, 2)
    }
@app.get("/portfolio/history/{user_id}")
def portfolio_history(user_id: int, db: Session = Depends(get_db)):

    trades = db.query(models.Trade).filter(
        models.Trade.user_id == user_id
    ).order_by(models.Trade.created_at).all()

    equity = 100000  # starting balance
    history = []

    for trade in trades:
        trade_value = trade.price * trade.quantity

        if trade.type == "BUY":
            equity -= trade_value
        else:
            equity += trade_value

        history.append({
            "time": trade.created_at.isoformat(),
            "equity": round(equity, 2)
        })

    return {"history": history}

# ============================================
# AI TRADING MENTOR ENDPOINTS (Option 3)
# ============================================

import pickle
import pandas as pd
import numpy as np
from ml.feature_engineering import add_features

_model_cache = None
_model_threshold = None
_model_metadata = None

def load_model():
    global _model_cache, _model_threshold, _model_metadata
    if _model_cache is None:
        try:
            with open("ml/model.pkl", "rb") as f:
                model_data = pickle.load(f)
                if isinstance(model_data, dict):
                    _model_cache = model_data['model']
                    _model_threshold = model_data.get('threshold', 0.5)
                    _model_metadata = model_data
                else:
                    _model_cache = model_data
                    _model_threshold = 0.5
                    _model_metadata = {}
        except Exception as e:
            print(f"⚠️ Model load error: {e}")
            return None, 0.5, {}
    return _model_cache, _model_threshold, _model_metadata


@app.get("/mentor/predict/{symbol}")
def predict_next_day(symbol: str):
    """
    🤖 INTELLIGENT TRADING MENTOR
    
    Predicts next-day price direction with confidence breakdown.
    Shows WHY the model makes its prediction.
    
    ⚠️ IMPORTANT:
    - Model accuracy: 56% on AAPL, 51% on TSLA, 48% on NFLX
    - NOT financial advice
    - Use with other analysis
    """
    try:
        model, threshold, metadata = load_model()
        if model is None:
            raise HTTPException(status_code=500, detail="Model not loaded")
        
        # Fetch 3 months of data
        stock = yf.Ticker(symbol)
        df = stock.history(period="3mo")
        
        if df.empty:
            raise HTTPException(status_code=400, detail=f"No data for {symbol}")
        
        df = df.reset_index()
        df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]
        df = add_features(df)
        
        feature_cols = [
            "EMA_10", "EMA_20", "MA_5", "MA_10", "MA_20",
            "RSI", "Body", "High_Low_Range", "Volume",
            "MACD", "MACD_Signal", "ATR", "Momentum", "Volume_Change"
        ]
        
        valid_data = df[feature_cols].dropna()
        if valid_data.empty:
            raise HTTPException(status_code=400, detail="Insufficient data")
        
        # Get latest row and predict
        X_latest = valid_data.iloc[-1:].values
        prob_up = float(model.predict_proba(X_latest)[0, 1])
        prediction = int(prob_up >= threshold)
        
        latest = df.iloc[-1]
        current_price = float(latest['Close'])
        
        # Determine confidence
        abs_prob = abs(prob_up - 0.5)
        if abs_prob < 0.05:
            confidence = "Very Low"
            confidence_pct = 50
        elif abs_prob < 0.10:
            confidence = "Low"
            confidence_pct = 55
        elif abs_prob < 0.15:
            confidence = "Moderate"
            confidence_pct = 60
        else:
            confidence = "High"
            confidence_pct = 70
        
        # Build response
        return {
            "symbol": symbol,
            "current_price": round(current_price, 2),
            "prediction": "UP" if prediction == 1 else "DOWN",
            "probability_up": round(prob_up * 100, 1),
            "probability_down": round((1 - prob_up) * 100, 1),
            "confidence_level": confidence,
            "confidence_percentage": confidence_pct,
            "model_accuracy_range": "48-56% depending on stock volatility",
            "action": "Consider as ONE input. Combine with other analysis.",
            "disclaimer": "Educational only. Not investment advice."
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/mentor/analysis/{symbol}")
def detailed_analysis(symbol: str):
    """
    🧠 DETAILED AI ANALYSIS
    
    Shows:
    1. What the model predicts
    2. WHY it predicts that (technical indicators)
    3. Model confidence
    4. Risk warnings
    """
    try:
        model, threshold, metadata = load_model()
        if model is None:
            raise HTTPException(status_code=500, detail="Model not loaded")
        
        stock = yf.Ticker(symbol)
        df = stock.history(period="3mo")
        
        if df.empty:
            raise HTTPException(status_code=400, detail=f"No data for {symbol}")
        
        df = df.reset_index()
        df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]
        df = add_features(df)
        
        feature_cols = [
            "EMA_10", "EMA_20", "MA_5", "MA_10", "MA_20",
            "RSI", "Body", "High_Low_Range", "Volume",
            "MACD", "MACD_Signal", "ATR", "Momentum", "Volume_Change"
        ]
        
        valid_data = df[feature_cols].dropna()
        if valid_data.empty:
            raise HTTPException(status_code=400, detail="Insufficient data")
        
        X_latest = valid_data.iloc[-1:].values
        prob_up = float(model.predict_proba(X_latest)[0, 1])
        prediction = int(prob_up >= threshold)
        
        latest = df.iloc[-1]
        
        # Extract indicators
        ema10 = float(latest['EMA_10'])
        ema20 = float(latest['EMA_20'])
        macd = float(latest['MACD'])
        macd_signal = float(latest['MACD_Signal'])
        rsi = float(latest['RSI'])
        momentum = float(latest['Momentum'])
        volume_change = float(latest['Volume_Change']) if not np.isnan(latest['Volume_Change']) else 0
        
        # Build explanation
        explanations = []
        bullish_signals = 0
        total_signals = 0
        
        # Trend Analysis
        if ema10 > ema20:
            explanations.append({
                "indicator": "Trend (EMA10 > EMA20)",
                "status": "Bullish",
                "value": f"{ema10:.2f} > {ema20:.2f}",
                "interpretation": "Shot-term trend is UP"
            })
            bullish_signals += 1
        else:
            explanations.append({
                "indicator": "Trend (EMA10 < EMA20)",
                "status": "Bearish",
                "value": f"{ema10:.2f} < {ema20:.2f}",
                "interpretation": "Short-term trend is DOWN"
            })
        total_signals += 1
        
        # MACD Analysis
        if macd > macd_signal:
            explanations.append({
                "indicator": "MACD Momentum",
                "status": "Bullish",
                "value": f"MACD: {macd:.4f}, Signal: {macd_signal:.4f}",
                "interpretation": "Momentum is positive"
            })
            bullish_signals += 1
        else:
            explanations.append({
                "indicator": "MACD Momentum",
                "status": "Bearish",
                "value": f"MACD: {macd:.4f}, Signal: {macd_signal:.4f}",
                "interpretation": "Momentum is negative"
            })
        total_signals += 1
        
        # RSI Analysis
        if rsi > 70:
            explanations.append({
                "indicator": "RSI (Momentum)",
                "status": "Overbought ⚠️",
                "value": f"{rsi:.1f}",
                "interpretation": "Price may pull back (caution on BUY)"
            })
        elif rsi < 30:
            explanations.append({
                "indicator": "RSI (Momentum)",
                "status": "Oversold ⚠️",
                "value": f"{rsi:.1f}",
                "interpretation": "Price may bounce (watch for reversal)"
            })
            bullish_signals += 1
        else:
            explanations.append({
                "indicator": "RSI (Momentum)",
                "status": "Neutral",
                "value": f"{rsi:.1f}",
                "interpretation": "Momentum is balanced"
            })
        total_signals += 1
        
        # Momentum Analysis
        if momentum > 0:
            explanations.append({
                "indicator": "10-Day Momentum",
                "status": "Positive",
                "value": f"{momentum:.2f}",
                "interpretation": "Price gaining strength"
            })
            bullish_signals += 1
        else:
            explanations.append({
                "indicator": "10-Day Momentum",
                "status": "Negative",
                "value": f"{momentum:.2f}",
                "interpretation": "Price losing strength"
            })
        total_signals += 1
        
        # Volume Analysis
        if volume_change > 0:
            explanations.append({
                "indicator": "Volume Trend",
                "status": "Increasing",
                "value": f"{volume_change*100:.1f}%",
                "interpretation": "Trading activity is rising"
            })
        else:
            explanations.append({
                "indicator": "Volume Trend",
                "status": "Decreasing",
                "value": f"{volume_change*100:.1f}%",
                "interpretation": "Trading activity is declining"
            })
        
        # Model confidence
        signal_ratio = bullish_signals / total_signals
        
        if signal_ratio > 0.75:
            model_confidence = "Strong"
        elif signal_ratio > 0.5:
            model_confidence = "Moderate"
        else:
            model_confidence = "Weak"
        
        return {
            "symbol": symbol,
            "current_price": round(float(latest['Close']), 2),
            "date": latest['Date'].strftime("%Y-%m-%d") if hasattr(latest['Date'], 'strftime') else str(latest['Date']),
            "ai_prediction": "UP" if prediction == 1 else "DOWN",
            "probability_up": round(prob_up * 100, 1),
            "ai_confidence": model_confidence,
            "signals_bullish": f"{bullish_signals}/{total_signals}",
            "technical_analysis": explanations,
            "model_accuracy_on_similar_stocks": "AAPL: 56%, TSLA: 51%, NFLX: 48%",
            "recommendation": "🎓 This is an AI-assisted insight. Combine with:\n- Fundamental analysis\n- Risk management\n- Your investment goals",
            "risk_warnings": [
                "No model predicts 100%",
                "Past patterns may not repeat",
                "Always use stop losses",
                "Diversify your portfolio",
                "Markets can be irrational"
            ],
            "disclaimer": "For educational purposes only. Not investment advice."
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/mentor/backtest")
def backtest_results():
    """
    📊 MODEL BACKTEST RESULTS
    
    Shows model performance on different stocks.
    Helps you understand when it works and doesn't.
    """
    return {
        "model_type": "Random Forest (multi-stock trained)",
        "training_data": {
            "stocks": ["AAPL", "MSFT", "GOOGL", "AMZN"],
            "period": "~2 years",
            "total_samples": 1984,
            "target": "Next-day price direction"
        },
        "backtest_results": {
            "AAPL": {
                "accuracy": "56.60%",
                "baseline": "51.89%",
                "improvement": "+4.71%",
                "status": "✅ Works (in-distribution)",
                "roc_auc": 0.9961
            },
            "TSLA": {
                "accuracy": "51.52%",
                "baseline": "51.52%",
                "improvement": "+0.00%",
                "status": "⚠️ Struggles (high volatility)",
                "roc_auc": 0.4857
            },
            "NFLX": {
                "accuracy": "47.62%",
                "baseline": "52.38%",
                "improvement": "-4.76%",
                "status": "❌ Fails (too volatile)",
                "roc_auc": 0.5412
            }
        },
        "key_learnings": [
            "Model works best on large-cap tech (AAPL-like)",
            "Struggles on high-volatility stocks (NFLX, TSLA)",
            "Stock personality matters - volatility is key factor",
            "Daily price direction is inherently hard (~50% random)"
        ],
        "when_to_use": "Use for large-cap blue chips, not growth stocks",
        "when_not_to_use": "Avoid volatility plays (biotech, small-cap, crypto)",
        "academic_takeaway": "Model generalizes modestly - shows real ML limitations"
    }