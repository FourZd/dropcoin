from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


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