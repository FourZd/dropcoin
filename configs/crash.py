import hashlib
from models.CrashHash import CrashHash
from configs.db import get_session
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.CrashState import CrashState
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone

async def generate_and_save_hashes(session: AsyncSession):
    # Проверяем, существует ли текущее состояние игры
    state = await session.execute(select(CrashState).options(selectinload(CrashState.current_game_hash)))
    state = state.scalars().first()

    if state and state.current_game_hash:
        # Начинаем с последнего сохраненного хеша
        initial_hash = state.current_game_hash.hash
    else:
        # Если состояние игры не найдено, начинаем с заданного начального значения
        initial_hash = "initial_random_seed"
        state = CrashState(next_game_time=datetime.now(timezone.utc), betting_close_time=datetime.now(timezone.utc))
        session.add(state)

    current_hash = hashlib.sha256(initial_hash.encode()).hexdigest()
    hashes_to_create = []
    for _ in range(2000000):
        game_hash = CrashHash(hash=current_hash)
        hashes_to_create.append(game_hash)
        current_hash = hashlib.sha256(current_hash.encode()).hexdigest()

    session.add_all(hashes_to_create)
    await session.commit()

    # Обновляем состояние игры с новыми хешами
    state.current_game_hash = hashes_to_create[-1]
    if hasattr(state, 'last_game_hash'):
        state.last_game_hash = hashes_to_create[-2] if len(hashes_to_create) > 1 else hashes_to_create[-1]

    await session.commit()

async def check_and_generate_hashes():
    gen = get_session()
    session = await gen.__anext__()
    exists = await session.execute(select(CrashHash).limit(1))
    if not exists.scalars().first():
        await generate_and_save_hashes(session)


