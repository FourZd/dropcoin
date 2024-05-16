from models.AvailableRewards import AvailableReward
from models.UserReward import UserReward
from sqlalchemy.ext.asyncio import AsyncSession
from models.CrashBet import CrashBet
from sqlalchemy.future import select
from sqlalchemy import func, case
from models.UserTransaction import UserTransaction

async def calculate_user_balance(user_id: str, session: AsyncSession) -> float:
    # Query to calculate the sum of reward points for the user
    result = await session.execute(
        select(func.coalesce(func.sum(UserTransaction.profit), 0.00)).filter(UserTransaction.user_id == user_id)
    )
    calculated_balance = result.scalar()  # Fetch the scalar result from the query
    return round(calculated_balance, 2)   # Return the balance rounded to two decimal places