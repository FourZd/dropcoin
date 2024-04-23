from pydantic import BaseModel, Field

class PutWalletRequest(BaseModel):
    wallet_address: str

class PutReferrerRequest(BaseModel):
    referrer_username: str = Field(..., pattern=r'^@\w{1,14}$')
