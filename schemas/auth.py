from pydantic import BaseModel, Field

class AuthUrlResponse(BaseModel):
    url: str


class AuthData(BaseModel):
    id: str = Field(..., description="The unique identifier for the Telegram user")
    hash: str = Field(..., description="Hash of the authentication data for verification")


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