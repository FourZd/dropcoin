from pydantic import BaseModel, Field, EmailStr

class PutWalletRequest(BaseModel):
    wallet_address: str

class PutReferrerRequest(BaseModel):
    encoded_username: str

class UpdateUsernameRequest(BaseModel):
    username: str

class PutEmailRequest(BaseModel):
    email: EmailStr