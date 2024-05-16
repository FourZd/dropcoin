from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from models.UserModel import User
from configs.db import get_session
from services.auth import get_current_user
from models.Farming import Farming
from sqlalchemy.future import select
from models.UserTransaction import UserTransaction
from datetime import datetime, timedelta, timezone
router = APIRouter(
    prefix="/farming",
    tags=["farming"],
)


@router.get("/farming")
async def get_farming_status(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """Возвращает оставшееся время до награды и текущий эквивалент полученной награды"""

    # Получаем последний запись о фермерстве для пользователя
    farming = await session.execute(select(Farming).filter(Farming.user_id == user.id))
    farming = farming.scalars().first()
    if not farming:
        return {"error": "Farming not found"}

    # Расчет общего времени работы
    total_duration = farming.end_time - farming.start_time
    # Определяем текущее время
    now = datetime.now(timezone.utc)

    # Расчет пройденного времени с начала работы
    elapsed_time = now - farming.start_time
    # Расчет оставшегося времени до окончания работы
    time_left = farming.end_time - now

    # Проверка на случай, если текущее время превышает время окончания
    if elapsed_time.total_seconds() > total_duration.total_seconds():
        earned_reward = farming.reward
    else:
        # Расчет пропорциональной части награды, на основе пройденного времени
        earned_reward = (elapsed_time.total_seconds() /
                         total_duration.total_seconds()) * farming.reward

    return {
        "time_left": time_left if time_left.total_seconds() > 0 else timedelta(seconds=0),
        "earned_reward": round(earned_reward, 3),
        "collectable": time_left.total_seconds() <= 0,
    }


@router.post("/start_farming")
async def start_farming(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """Начинает фермерство для пользователя"""

    # Проверка на наличие активного фермерства
    farming = await session.execute(select(Farming).filter(Farming.user_id == user.id))
    farming = farming.scalars().first()
    if farming:
        return {"error": "Farming already started"}

    # Создание новой записи о фермерстве
    new_farming = Farming(
        user_id=user.id,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc) + timedelta(hours=8),
        reward=57
    )
    session.add(new_farming)
    await session.commit()

    return {
        "message": "Farming started",
        "start_time": new_farming.start_time,
        "end_time": new_farming.end_time,
        "reward": new_farming.reward
    }


@router.post("/collect_reward")
async def collect_reward(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """Собирает награду за фермерство"""

    # Поиск активного фермерства
    farming = await session.execute(select(Farming).filter(Farming.user_id == user.id))
    farming = farming.scalars().first()
    if not farming:
        return {"error": "Farming not found"}

    # Проверка на возможность собрать награду
    if farming.end_time > datetime.now(timezone.utc):
        return {"error": "Farming not finished yet"}

    # Создание транзакции для пользователя с полученной наградой
    rewards = [
        UserTransaction(
            user_id=user.id,
            profit=farming.reward,
            timestamp=datetime.now(timezone.utc)
        ),
        UserTransaction(
            user_id=user.referrer_id,
            profit=farming.reward * 0.10,
            timestamp=datetime.now(timezone.utc)
        ),
        UserTransaction(
            user_id=user.referrer.referrer_id,
            profit=farming.reward * 0.025,
            timestamp=datetime.now(timezone.utc)
        )
    ]

    session.add_all(rewards)
    session.delete(farming)

    await session.commit()

    return {"message": "Reward collected"}
