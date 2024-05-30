from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
class AuthUrlResponse(BaseModel):
    url: str


class User(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str]
    username: Optional[str]
    language_code: Optional[str]
    is_premium: Optional[bool]
    allows_write_to_pm: Optional[bool]

class TelegramAuthData(BaseModel):
    data_check_string: str


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

class IsRegistered(BaseModel):
    user_id: int