from fastapi import APIRouter, Depends, HTTPException, status
from models.UserModel import User
from services.auth import get_current_user
from configs.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from schemas.user_settings import PutWalletRequest, PutReferrerRequest
from models.UserReward import UserReward
from sqlalchemy.orm import selectinload
from configs.environment import get_environment_variables
import base64
from services.transactions import add_reward_and_transaction
TG_BOT_NAME = get_environment_variables().TG_BOT_NAME

router = APIRouter(
    prefix="/user/settings",
    tags=["settings"]
)

@router.put("/wallet")
async def update_wallet(payload: PutWalletRequest, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """
    Update the SOL wallet address of the user. The wallet address is used to send rewards to the user.
    """
    user.wallet_address = payload.wallet_address

    try: 
        session.add(user)
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"An error occured while updating the wallet")
    
    return {"message": "Wallet address updated successfully", "wallet_address": user.wallet_address}

@router.get("/referral_link")
async def get_referral_link(user: User = Depends(get_current_user)):
    encoded_username = base64.urlsafe_b64encode(user.username.encode()).decode()
    return {"referral_link": f"https://t.me/{TG_BOT_NAME}/app?startapp=ref_{encoded_username}"}


@router.put("/referrer")
async def update_referrer(payload: PutReferrerRequest, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    try:
        decoded_username = base64.urlsafe_b64decode(payload.encoded_username.encode()).decode()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid encoded username format")

    referrer_query = (
        select(User)
        .options(selectinload(User.referrer).selectinload(User.referrer))
        .filter(User.username == decoded_username)
    )
    referrer_result = await session.execute(referrer_query)
    referrer = referrer_result.scalars().first()

    if not referrer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referrer not found")

    if referrer.id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot refer yourself")

    user.referrer = referrer
    await session.commit()
    await add_reward_and_transaction(referrer.id, 2, session)

    if referrer.referrer:
        await add_reward_and_transaction(referrer.referrer.id, 10, session)
        
    return {"message": "Referrer updated successfully and rewards issued"}