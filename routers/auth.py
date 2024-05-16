from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from configs.auth import tweepy_client
from configs.db import get_session
from services.auth import authenticate_user, generate_jwt, verify_telegram_authentication
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.auth import AuthUrlResponse, AuthData, TokenRefreshRequest, AuthenticateResponse, RefreshTokenResponse, UserResponse
from jose import jwt
import os
from models.UserModel import User
import json
from services.auth import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


@router.post("/telegram/authenticate", response_model=AuthenticateResponse)
async def telegram_authenticate(auth_data: AuthData, db: AsyncSession = Depends(get_session)):
    """
    Authenticates a user using the Telegram data sent after user authentication in Telegram.
    Verifies the hash to ensure the data is from Telegram.
    """
    verified = await verify_telegram_authentication(auth_data.id, auth_data.hash)
    if not verified:
        raise HTTPException(status_code=401, detail="Authentication data is tampered or invalid")

    # Предполагаем, что auth_data уже содержит все необходимые данные.
    user_id = auth_data.id
    response, tokens = await authenticate_user(user_id, db)
    if response:
        return JSONResponse(content={"status": "success", "access_token": tokens[0], "refresh_token": tokens[1]})
    else:
        raise HTTPException(status_code=400, detail="Authentication failed or user could not be created.")
    

@router.post("/token/refresh", response_model=RefreshTokenResponse)
async def refresh_token(request: TokenRefreshRequest, db: AsyncSession = Depends(get_session)):
    """
    Accepts a valid refresh token and returns a new access token. Validates the refresh token and checks 
    its type, ensuring it is a 'refresh' type. Generates a new access token valid for 15 minutes if the 
    refresh token is valid.

    It won't return a new refresh token due to security & storaging reasons. The user must authenticate again to get a new refresh token.
    """
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
    

@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """
    Returns the user object of the authenticated user.
    """
    response_model = UserResponse(id=user.id, username=user.username, wallet_address=user.wallet_address, referrals=user.referrals)
    return response_model