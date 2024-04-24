from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone
from models.UserModel import User

async def insert_or_get_user(user_id: str, username: str, oauth_token: str, oauth_token_secret: str, db: AsyncSession):
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    existing_user = result.scalars().first()

    if existing_user:
        return existing_user, None

    new_user = User(id=user_id, username=username, created_at=datetime.now(timezone.utc),
                    oauth_token=oauth_token, oauth_token_secret=oauth_token_secret)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return None, new_user