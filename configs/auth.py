from authlib.integrations.starlette_client import OAuth, OAuthError
import os
from configs.environment import get_environment_variables

client_id = get_environment_variables().TWITTER_API_KEY
client_secret = get_environment_variables().TWITTER_API_SECRET
# Настройка OAuth 2 клиента для Twitter
oauth = OAuth()
oauth.register(
    name='twitter',
    client_id=os.getenv('TWITTER_API_KEY'),
    client_secret=os.getenv('TWITTER_API_SECRET'),
    request_token_url='https://api.twitter.com/oauth/request_token',
    request_token_params=None,
    access_token_url='https://api.twitter.com/oauth/access_token',
    access_token_params=None,
    authorize_url='https://api.twitter.com/oauth/authenticate',
    authorize_params=None,
    api_base_url='https://api.twitter.com/1.1/',
    client_kwargs=None,
)