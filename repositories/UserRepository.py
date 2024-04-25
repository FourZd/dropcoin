from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone
from models.UserModel import User
async def insert_or_get_user(user_id: str, username: str, db: AsyncSession, access, secret):
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    existing_user = result.scalars().first()

    if existing_user:
        existing_user.access_token = access
        existing_user.access_token_secret = secret
        await db.commit()
        return existing_user, None

    new_user = User(id=user_id, username=username, created_at=datetime.now(timezone.utc),
                    access_token=access, access_token_secret=secret)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return None, new_user