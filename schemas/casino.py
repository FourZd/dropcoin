from pydantic import BaseModel

class BetRequest(BaseModel):
    user_id: str
    amount: float

class CashOutRequest(BaseModel):
    user_id: str
    multiplier: float