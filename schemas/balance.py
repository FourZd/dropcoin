from pydantic import BaseModel
from decimal import Decimal

class GetBalanceResponse(BaseModel):
    balance: Decimal