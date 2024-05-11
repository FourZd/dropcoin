from pydantic import BaseModel, Field

class AuthUrlResponse(BaseModel):
    url: str


class AuthData(BaseModel):
    id: int = Field(..., description="The unique identifier for the Telegram user")
    first_name: str = Field(None, description="The first name of the Telegram user")
    last_name: str = Field(None, description="The last name of the Telegram user")
    username: str = Field(None, description="The Telegram username of the user")
    photo_url: str = Field(None, description="URL of the user's profile picture")
    auth_date: int = Field(..., description="Authentication date timestamp")
    hash: str = Field(..., description="Hash of the authentication data for verification")


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class AuthenticateResponse(BaseModel):
    status: str
    access_token: str
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str