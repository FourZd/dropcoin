from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from models.UserModel import User
from services.auth import get_current_user
from configs.db import get_session

from services.balance import calculate_user_balance
router = APIRouter(
    prefix="/user/balance",
    tags=["balance"]
)

@router.get("/") # This thing made by Chatgpt, god save us
async def get_balance(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    current_balance = await calculate_user_balance(user.id, session)
    return {"balance": current_balance}