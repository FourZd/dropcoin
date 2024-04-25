import os
from configs.environment import get_environment_variables
import tweepy


def tweepy_client(access=False, **kwargs):
    client_key = get_environment_variables().TWITTER_API_KEY
    client_secret = get_environment_variables().TWITTER_API_SECRET

    if access:
        access_token = kwargs.get('access_token')
        access_token_secret = kwargs.get('access_token_secret')
        auth = tweepy.OAuth1UserHandler(client_key, client_secret, access_token, access_token_secret)
    else:
        auth = tweepy.OAuth1UserHandler(client_key, client_secret, callback="https://www.booster.trading/farming/auth/twitter/callback")
    
    return auth