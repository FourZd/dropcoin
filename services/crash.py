import hashlib
from datetime import datetime, timedelta, timezone
import asyncio
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.CrashHash import CrashHash
from models.CrashState import CrashState
from configs.db import get_session
import hashlib


async def game_scheduler():
    while True:
        gen = get_session()
        session = await gen.__anext__()
        state_result = await session.execute(select(CrashState).limit(1))
        state = state_result.scalars().first()

        await asyncio.sleep((state.betting_close_time - datetime.now(timezone.utc)).total_seconds())

        # Закрытие ставок
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
        game_duration = timedelta(seconds=30 + 10 * crash_point)  # Базовое время + 10 секунд на каждый пункт коэффициента

        state.last_game_hash_id = state.current_game_hash_id
        state.last_game_result = crash_point
        state.current_game_hash_id = next_hash.id
        state.next_game_time = datetime.now(timezone.utc) + game_duration
        state.betting_close_time = datetime.now(timezone.utc) + timedelta(seconds=30)

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