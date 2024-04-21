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
        select(
            AvailableReward.title,
            AvailableReward.reward,
            AvailableReward.description,
            UserReward.user_id.isnot(None).label('mission_completed')
        )
        .outerjoin(
            UserReward, 
            (UserReward.reward_type_id == AvailableReward.id) & (UserReward.user_id == user.id)
        )
        .order_by(AvailableReward.id)  # Сортировать по ID награды, если необходимо
    )
    results = await session.execute(stmt)
    
    # Формируем список словарей для ответа
    missions_list = [
        {
            "title": result.title,
            "reward": result.reward,
            "description": result.description,
            "mission_completed": bool(result.mission_completed)
        }
        for result in results.scalars()
    ]

    return missions_list


@router.on_event("startup")
async def startup_event():
    await create_default_items()