from fastapi import APIRouter, Depends, HTTPException
from models.UserModel import User
from services.auth import get_current_user
from configs.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from configs.rewards import create_default_items
from sqlalchemy.future import select
from models.AvailableRewards import AvailableReward
from models.UserReward import UserReward
from schemas.rewards import CollectPointsRequest
from services.rewards import check_mission, check_user_reward
from datetime import datetime, timezone

router = APIRouter(
    prefix="/missions",
    tags=["missions"]
)

@router.get("/list")
async def get_list_of_missions(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    # Создаем запрос, который объединяет таблицы и проверяет статус для текущего пользователя
    stmt = (
        select(AvailableReward, UserReward.user_id.isnot(None).label('mission_completed'))
        .outerjoin(
            UserReward,
            (UserReward.reward_type_id == AvailableReward.id) & (UserReward.user_id == user.id)
        )
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
    mission_id = payload.mission_id
    if mission_id == 3:
        direct_referrals = user.referrals  # Первый уровень рефералов
        direct_referral_count = len(direct_referrals)
        
        second_level_referral_count = sum(len(referral.referrals) for referral in direct_referrals)
        
        return {
            "detail": f"Currently invited: Directly - {direct_referral_count}, By Referrals - {second_level_referral_count}"
        }
    reward_collected = await check_user_reward(session, user.id, mission_id)
    if reward_collected:
        raise HTTPException(status_code=400, detail="You've already collected the reward")
    completed = await check_mission(mission_id)
    
    if completed:
        new_reward = UserReward(user_id=user.id, reward_type_id=mission_id, timestamp=datetime.now(timezone.utc))
        session.add(new_reward)
        await session.commit()
        return {"detail": "Reward collected successfully", "mission_id": mission_id}
    else:
        raise HTTPException(status_code=400, detail="Mission is not completed or results are not processed yet")
@router.on_event("startup")
async def startup_event():
    await create_default_items()