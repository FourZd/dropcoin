from fastapi import APIRouter, Depends, HTTPException
from models.UserModel import User
from services.auth import get_current_user
from configs.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.AvailableRewards import AvailableReward
from models.UserReward import UserReward
from schemas.rewards import CollectPointsRequest
from services.rewards import check_mission, check_user_reward
from datetime import datetime, timezone
from services.transactions import add_reward_and_transaction
router = APIRouter(
    prefix="/missions",
    tags=["missions"]
)

@router.get("/list")
async def get_list_of_missions(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """
    Returns a list of available missions for the user. 
    Each mission has an id, title, reward, and description. 
    Use it for mission status tracking and to differentiate between missions.
    """
    exclude_tags = ["referrer_reward", "referrer_of_the_referrer_reward"]
    stmt = (
        select(AvailableReward, UserReward.user_id.isnot(None).label('mission_completed'))
        .outerjoin(
            UserReward,
            (UserReward.reward_type_id == AvailableReward.id) & (UserReward.user_id == user.id)
        )
        .filter(AvailableReward.tag.notin_(exclude_tags))
        .order_by(AvailableReward.id)  # Сортировать по ID награды, если необходимо
    )
    results = await session.execute(stmt)
    rewards = results.all()

    # Формируем список словарей для ответа
    missions_list = [
        {
            "id": reward.AvailableReward.id,
            "title": reward.AvailableReward.title,
            "reward": reward.AvailableReward.reward,
            "description": reward.AvailableReward.description,
            "mission_completed": reward.mission_completed
        }
        for reward in rewards
    ]

    return missions_list


@router.post("/collect")
async def collect_points(payload: CollectPointsRequest, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """
    Collects the reward for the mission. Use the mission_id from /list to specify the mission. Also provide any additional parameters if required.
    Additional parameters are required for some missions, such as the URL for a Twitter post, Telegram username. 
    If you have questions about missions and this endpoint's request/response, ask the employer.
    """
    mission_id = payload.mission_id
    result = await session.execute(select(AvailableReward).filter(AvailableReward.id == mission_id))
    mission = result.scalar()
    
    reward_collected = await check_user_reward(session, user.id, mission.tag)
    if reward_collected:
        raise HTTPException(status_code=400, detail="You've already collected the reward")
    completed = await check_mission(mission.tag, user, session)
    
    if completed:
        await add_reward_and_transaction(user.id, mission_id, session)
        return {"detail": "Reward collected successfully", "mission_id": mission_id}
    else:
        raise HTTPException(status_code=400, detail="Mission is not completed or results are not processed yet")