from models.AvailableRewards import AvailableReward
from models.UserReward import UserReward
from sqlalchemy.ext.asyncio import AsyncSession
from models.CrashBet import CrashBet
from sqlalchemy.future import select
from sqlalchemy import func

async def calculate_user_balance(user_id: str, session: AsyncSession) -> float:
    # Query to calculate the sum of reward points for the user
    rewards_query = (
        select(func.sum(AvailableReward.reward))
        .select_from(UserReward)
        .join(AvailableReward, UserReward.reward_type_id == AvailableReward.id)
        .where(UserReward.user_id == user_id)
    )
    total_rewards = await session.execute(rewards_query)
    total_reward_points = total_rewards.scalar() or 0

    # Query to calculate net money from CrashBets for the user
    bets_query = (
        select(
            func.sum(
                func.case(
                    [
                        (CrashBet.result == 'win', CrashBet.amount * CrashBet.cash_out_multiplier),
                        (CrashBet.result == 'lose', -CrashBet.amount)
                    ],
                    else_=0
                )
            )
        )
        .where(CrashBet.user_id == user_id)
    )
    total_bets = await session.execute(bets_query)
    net_money_from_bets = total_bets.scalar() or 0

    # Combine the results to get the user's current balance
    current_balance = total_reward_points + net_money_from_bets

    return current_balance