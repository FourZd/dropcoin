from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from configs.auth import tweepy_client
import tweepy
from schemas.auth import AuthUrlResponse, AuthData

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.get("/twitter/auth_url", response_model=AuthUrlResponse)
def get_twitter_auth_url():
    auth = tweepy_client()
    try:
        redirect_url = auth.get_authorization_url()
        return AuthUrlResponse(url=redirect_url)
    except tweepy.TweepyException as e:
        raise HTTPException(status_code=500, detail=f"Failed to get authorization URL: {str(e)}")

@router.post("/twitter/authenticate")
async def twitter_authenticate(auth_data: AuthData):
    auth = tweepy_client()
    auth.request_token = {'oauth_token': auth_data.oauth_token, 'oauth_token_secret': auth_data.oauth_token}
    
    try:
        auth.get_access_token(auth_data.oauth_verifier)
        api = tweepy.API(auth)
        user_info = api.verify_credentials()
        return JSONResponse(content={"status": "success", "data": {"screen_name": user_info.screen_name}})
    except tweepy.TweepyException as e:
        raise HTTPException(status_code=500, detail=str(e))