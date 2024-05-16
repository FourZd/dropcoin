from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone
from models.UserModel import User


async def insert_or_get_user(user_id: str, username: str, db: AsyncSession):
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        user = User(id=user_id, username=username, created_at=datetime.now(timezone.utc))
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user