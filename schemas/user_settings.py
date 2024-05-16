from pydantic import BaseModel, Field

class PutWalletRequest(BaseModel):
    wallet_address: str

class PutReferrerRequest(BaseModel):
    encoded_username: str

class UpdateUsernameRequest(BaseModel):
    username: str