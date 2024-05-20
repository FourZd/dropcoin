from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
class AuthUrlResponse(BaseModel):
    url: str


class TelegramAuthData(BaseModel):
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    username: Optional[str]
    photo_url: Optional[HttpUrl]
    auth_date: int
    hash: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class AuthenticateResponse(BaseModel):
    status: str
    access_token: str
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str

class UserResponse(BaseModel):
    id: str
    username: str | None
    wallet_address: str | None
    referrals: list[str] | None