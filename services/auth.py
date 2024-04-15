import tweepy
from configs.auth import tweepy_client
from repositories.UserRepository import insert_user
from models.UserModel import User
async def authenticate_user(oauth_token, oauth_verifier, db):
    auth = tweepy_client()
    auth.request_token = {'oauth_token': oauth_token, 'oauth_token_secret': oauth_token}

    try:
        auth.get_access_token(oauth_verifier)
        api = tweepy.API(auth)
        user_info = api.verify_credentials()
        result: User = await insert_user(user_info.id_str, user_info.screen_name, db)
        if result:
            return True
        else:
            return False

    except tweepy.TweepyException as e:
        return False