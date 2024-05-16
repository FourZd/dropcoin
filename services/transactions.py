from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .entities import EntityMeta, User, AvailableReward
from datetime import datetime, timezone
from models.UserReward import UserReward
from models.UserTransaction import UserTransaction
async def add_reward_and_transaction(user_id: str, mission_id: int, session: AsyncSession):
    # Fetch the reward amount for the given mission_id
    reward_amount_query = await session.execute(
        select(AvailableReward.reward).filter_by(id=mission_id)
    )
    reward_amount = reward_amount_query.scalar()

    if reward_amount is None:
        raise ValueError("Invalid mission_id or reward not found")

    # Create the UserReward instance
    new_reward = UserReward(
        user_id=user_id,
        reward_type_id=mission_id,
        timestamp=datetime.now(timezone.utc)
    )
    session.add(new_reward)

    # Create the corresponding UserTransaction instance
    new_transaction = UserTransaction(
        user_id=user_id,
        profit=reward_amount,  # Using the fetched reward amount as the profit
        timestamp=datetime.now(timezone.utc)
    )
    session.add(new_transaction)

    # Commit both additions in one transaction to maintain atomicity
    await session.commit()

