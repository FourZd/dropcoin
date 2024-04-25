from pydantic import BaseModel

class AuthUrlResponse(BaseModel):
    url: str


class AuthData(BaseModel):
    oauth_token: str
    oauth_verifier: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class AuthenticateResponse(BaseModel):
    status: str
    access_token: str
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str