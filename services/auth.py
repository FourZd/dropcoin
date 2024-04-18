import tweepy
from configs.auth import tweepy_client
from repositories.UserRepository import insert_or_get_user
from models.UserModel import User
import jwt
from datetime import datetime, timezone, timedelta
from configs.environment import get_environment_variables
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2Bearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from configs.db import get_session

oauth2_scheme = OAuth2Bearer()
JWT_SECRET = get_environment_variables().JWT_SECRET


async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)) -> User:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    user_result = await session.execute(select(User).where(User.id == user_id))
    user = user_result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def generate_jwt(user_id: str, token_type: str, expiry_minutes: int):
    payload = {
        "user_id": user_id,
        "type": token_type,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


async def authenticate_user(oauth_token, oauth_verifier, db):
    auth = tweepy_client()
    auth.request_token = {'oauth_token': oauth_token, 'oauth_token_secret': oauth_token}

    try:
        auth.get_access_token(oauth_verifier)
        api = tweepy.API(auth)
        user_info = api.verify_credentials()
        user, created = await insert_or_get_user(user_info.id_str, user_info.screen_name, db)
        if user or created:
            access_token = generate_jwt(user_info.id_str, "access", 15)  # Valid for 15 minutes
            refresh_token = generate_jwt(user_info.id_str, "refresh", 43200)  # Valid for 30 days
            return True, (access_token, refresh_token)
        else:
            return False, None
    except tweepy.TweepyException as e:
        return False, None