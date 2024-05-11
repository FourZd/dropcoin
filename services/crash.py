import hashlib
from datetime import datetime, timedelta, timezone
import asyncio
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, or_, case, cast
from models.CrashHash import CrashHash
from models.CrashState import CrashState
from models.CrashBet import CrashBet
from models.UserTransaction import UserTransaction
from configs.db import get_session
import hashlib
from decimal import Decimal
from sqlalchemy.dialects.postgresql import ENUM

async def game_scheduler():

    await update_crash_state(session, state, finished_game_id, crash_point, next_hash_id=next_hash.id)
    await update_crash_bets(session=session, last_game_hash_id=finished_game_id, last_game_result=crash_point)
        

        
async def calculate_game_time_final(crash_point):
    initial_time = Decimal('0.2')
    time_decrease_factor = Decimal('0.995')  # Настроенный коэффициент

    time = Decimal('0.0')
    multiplier = Decimal('1.0')
    current_time = initial_time

    crash_point = Decimal(crash_point)

    while multiplier < crash_point:
        time += current_time
        multiplier += Decimal('0.01')  # Мелкий шаг мультиплаера
        current_time *= time_decrease_factor  # Адаптированное уменьшение времени

    return timedelta(seconds=float(time))

async def update_crash_state(session, state, finished_game_id, crash_point, next_hash_id):
    game_duration = await calculate_game_time_final(crash_point)
    betting_close_time = datetime.now(timezone.utc) + timedelta(seconds=10) + timedelta(seconds=2)
    state.last_game_hash_id = finished_game_id
    state.last_game_result = crash_point
    state.current_game_hash_id = next_hash_id
    state.next_game_time = betting_close_time + game_duration
    state.betting_close_time = betting_close_time # 2 seconds for crash animation

    await session.commit()


async def update_crash_bets(session: AsyncSession, last_game_hash_id, last_game_result):
    await session.execute(
        update(CrashBet)
        .where(CrashBet.game_id == last_game_hash_id)
        .values(result=case(
            (CrashBet.cash_out_multiplier < last_game_result, cast('win', ENUM('win', 'lose', name='result_types'))),
            (or_(CrashBet.cash_out_multiplier > last_game_result, CrashBet.cash_out_multiplier.is_(None)), cast('lose', ENUM('win', 'lose', name='result_types'))),
            else_=cast('lose', ENUM('win', 'lose', name='result_types'))
        ))
    )

    # Подтверждение изменений
    await session.commit()

    # Выборка обновленных ставок и создание записей транзакций
    bets = await session.execute(
        select(CrashBet)
        .where(CrashBet.game_id == last_game_hash_id)
    )
    bets = bets.scalars().all()

    # Подготовка и добавление транзакций
    transactions = [
        UserTransaction(
            user_id=bet.user_id,
            profit=(bet.cash_out_multiplier * bet.amount if bet.result == 'win' else -bet.amount),
            timestamp=datetime.now()
        )
        for bet in bets
    ]
    session.add_all(transactions)

    # Фиксация транзакций в базе данных
    await session.commit()


async def listen_for_game() #TODO RabbitMQ singletone listener