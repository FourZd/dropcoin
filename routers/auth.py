from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from configs.auth import tweepy_client
from configs.db import get_session
from services.auth import authenticate_user, generate_jwt
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.auth import AuthUrlResponse, AuthData, TokenRefreshRequest
from jose import jwt
import os
from models.UserModel import User

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
    response, tokens = await authenticate_user(auth_data.oauth_token, auth_data.oauth_verifier, db)
    if response:
        return JSONResponse(content={"status": "success", "access_token": tokens[0], "refresh_token": tokens[1]})
    else:
        raise HTTPException(status_code=400, detail="Authentication failed or user could not be created.")
    

@router.post("/token/refresh")
async def refresh_token(request: TokenRefreshRequest, db: AsyncSession = Depends(get_session)):
    refresh_token = request.refresh_token
    try:
        payload = jwt.decode(refresh_token, os.getenv('JWT_SECRET'), algorithms=["HS256"])
        if payload["type"] != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        user = await db.get(User, payload["sub"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        access_token = generate_jwt(payload["sub"], "access", 15)  # Valid for 15 minutes
        return {"access_token": access_token}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token")