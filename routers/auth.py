from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import RedirectResponse
from configs.auth import oauth


router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)



@router.get("/login")
def login_via_twitter():
    redirect_uri = 'http://localhost:8000/auth'
    return oauth.twitter.authorize_redirect(redirect_uri)

@router.get("/auth")
async def auth(request: Request):
    try:
        token = await oauth.twitter.authorize_access_token(request)
    except OAuthError as e:
        return HTTPException(status_code=400, detail=str(e))
    resp = await oauth.twitter.get('account/verify_credentials.json', token=token)
    user_info = resp.json()
    return {"user": user_info}
