import hashlib
from datetime import datetime, timedelta, timezone
import asyncio
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from models.CrashHash import CrashHash
from models.CrashState import CrashState
from models.CrashBet import CrashBet
from configs.db import get_session
import hashlib


async def game_scheduler():
    while True:
        gen = get_session()
        session = await gen.__anext__()
        state_result = await session.execute(select(CrashState).limit(1))
        state = state_result.scalars().first()

        await asyncio.sleep((state.betting_close_time - datetime.now(timezone.utc)).total_seconds())
        await asyncio.sleep((state.next_game_time - datetime.now(timezone.utc)).total_seconds())

        next_hash_result = await session.execute(
                select(CrashHash)
                .where(CrashHash.id < state.current_game_hash_id)
                .order_by(CrashHash.id.desc())
                .limit(1)
            )
        next_hash = next_hash_result.scalars().first()
        if not next_hash:
            print("No available hashes in the database. Please regenerate hashes.")
            break

        crash_point = crash_point_from_hash(next_hash.hash)
        

        finished_game_id = state.current_game_hash_id

        await update_crash_state(session, state, finished_game_id, crash_point, next_hash_id=next_hash.id)
        await update_crash_bets(session=session, last_game_hash_id=finished_game_id, last_game_result=crash_point)
        

        
async def calculate_game_time_final(crash_point):
    initial_time = 2.0  # время от 1x до 1.1x
    time_decrease_factor = 0.91  # каждый следующий интервал уменьшается на 9%
    
    # Начальное время и коэффициент
    time = 0.0
    multiplier = 1.0
    current_time = initial_time

    # Итерируем пока не достигнем краш-поинта
    while multiplier < crash_point:
        time += current_time
        multiplier += 0.1
        # Уменьшаем время следующего интервала по геометрической прогрессии
        current_time *= time_decrease_factor

    return time

async def update_crash_state(session, state, finished_game_id, crash_point, next_hash_id):
    game_duration = await calculate_game_time_final(crash_point)
    betting_close_time = datetime.now(timezone.utc) + timedelta(seconds=10) +timedelta(seconds=2)
    state.last_game_hash_id = finished_game_id
    state.last_game_result = crash_point
    state.current_game_hash_id = next_hash_id
    state.next_game_time = datetime.now(timezone.utc) + game_duration + betting_close_time + timedelta(seconds=2) # 2 seconds for crash animation
    state.betting_close_time = betting_close_time # 2 seconds for crash animation

    await session.commit()

def crash_point_from_hash(server_seed):
    salt = "0xd2867566759e9158bda9bf93b343bbd9aa02ce1e0c5bc2b37a2d70d391b04f14"
    hash_object = hashlib.sha256((server_seed + salt).encode())
    hash_hex = hash_object.hexdigest()

    # Расчет коэффициента краша по хэшу
    divisor = 100 // 4
    val = 0
    for i in range(0, len(hash_hex), 4):
        val = (val * 65536 + int(hash_hex[i:i + 4], 16)) % divisor

    if val == 0:
        return 1.0

    exponent = 52
    h = int(hash_hex[:13], 16)
    e = 2**exponent
    crash_point = (100 * e - h) / (e - h)
    return crash_point / 100.0


async def update_crash_bets(session: AsyncSession, last_game_hash_id, last_game_result):
    await session.execute(
        update(CrashBet)
        .where(CrashBet.game_id == last_game_hash_id, CrashBet.cash_out_multiplier < last_game_result)
        .values(result='win')
    )

    await session.execute(
        update(CrashBet)
        .where(CrashBet.game_id == last_game_hash_id, CrashBet.cash_out_multiplier > last_game_result)
        .values(result='lose')
    )

    await session.commit()