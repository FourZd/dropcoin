import os
from configs.environment import get_environment_variables
import tweepy


def tweepy_client():
    client_key = get_environment_variables().TWITTER_API_KEY
    client_secret = get_environment_variables().TWITTER_API_SECRET


    auth = tweepy.OAuth1UserHandler(client_key, client_secret, callback="https://www.booster.trading/farming/auth/twitter/callback")
    
    return auth