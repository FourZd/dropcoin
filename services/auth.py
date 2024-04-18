import tweepy
from configs.auth import tweepy_client
from repositories.UserRepository import insert_or_get_user
from models.UserModel import User
import jwt
from datetime import datetime, timezone, timedelta
from configs.environment import get_environment_variables

def generate_jwt(user_id: str, token_type: str, expiry_minutes: int):
    payload = {
        "user_id": user_id,
        "type": token_type,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)
    }
    return jwt.encode(payload, get_environment_variables().JWT_SECRET, algorithm="HS256")


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