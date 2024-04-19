from pydantic import BaseModel

class BetRequest(BaseModel):
    amount: float

class CashOutRequest(BaseModel):
    multiplier: float