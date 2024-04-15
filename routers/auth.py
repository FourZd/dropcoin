from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from configs.auth import tweepy_client
from configs.db import get_session
from services.auth import authenticate_user
from sqlalchemy.ext.asyncio import AsyncSession
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get authorization URL: {str(e)}")

@router.post("/twitter/authenticate")
async def twitter_authenticate(auth_data: AuthData, db: AsyncSession = Depends(get_session)):
    response = await authenticate_user(auth_data.oauth_token, auth_data.oauth_verifier, db)
    if response:
        return JSONResponse(content={"status": "success"})
    else:
        raise HTTPException(status_code=400, detail="Something went wrong...")