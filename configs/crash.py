import hashlib
from models.CrashHash import CrashHash
from configs.db import get_session
from sqlalchemy.future import select

async def generate_and_save_hashes():
    initial_seed = "initial_random_seed"
    current_hash = hashlib.sha256(initial_seed.encode()).hexdigest()

    async with get_session() as session:
        for _ in range(2000000):
            game_hash = CrashHash(hash=current_hash)
            session.add(game_hash)
            current_hash = hashlib.sha256(current_hash.encode()).hexdigest()
        await session.commit()

async def check_and_generate_hashes():
    async with get_session() as session:
        exists = await session.execute(select(CrashHash).limit(1))
        if not exists.scalars().first():
            await generate_and_save_hashes()


