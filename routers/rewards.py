from fastapi import APIRouter, Depends
from models.UserModel import User
from services.auth import get_current_user
from configs.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from configs.rewards import create_default_items
from sqlalchemy.future import select
from models.AvailableRewards import AvailableReward
from models.UserReward import UserReward
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
            "title": reward.AvailableReward.title,
            "reward": reward.AvailableReward.reward,
            "description": reward.AvailableReward.description,
            "mission_completed": reward.mission_completed
        }
        for reward in rewards
    ]

    return missions_list


@router.on_event("startup")
async def startup_event():
    await create_default_items()