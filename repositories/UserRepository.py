from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone
from models.UserModel import User

async def insert_user(user_id: int, username: str, db: AsyncSession):

    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    existing_user = result.scalars().first()
    
    if existing_user:
        return False
    
    new_user = User(id=user_id, username=username, created_at=datetime.now(timezone.utc))
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
