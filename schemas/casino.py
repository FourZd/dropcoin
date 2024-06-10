from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional

class BetRequest(BaseModel):
    amount: float

class CashOutRequest(BaseModel):
    multiplier: float

class Bet(BaseModel):
    user_id: str
    amount: Decimal
    time: datetime
    hash: str

    
class BetResponse(BaseModel):
    detail: str
    bet: Bet

class CancelBetResponse(BaseModel):
    detail: str


class BetResultResponse(BaseModel):
    bet_id: int
    outcome: str
    win_amount: float


class LastGameResultResponse(BaseModel):
    result: float
    hash: str
    betting_close_time: datetime


class TimingResponse(BaseModel):
    current_time: datetime
    betting_close_time: datetime

class CurrentBet(BaseModel):
    user_id: str
    amount: float
    time: datetime
    cash_out_multiplier: Optional[float]
    cash_out_datetime: Optional[datetime]
    result: str = "pending"