from pydantic import BaseModel

class AuthUrlResponse(BaseModel):
    url: str


class AuthData(BaseModel):
    oauth_token: str
    oauth_verifier: str

