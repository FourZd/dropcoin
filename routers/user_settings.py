from fastapi import APIRouter, Depends, HTTPException, status
from models.UserModel import User
from services.auth import get_current_user
from configs.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from schemas.user_settings import PutWalletRequest, PutReferrerRequest
from models.UserReward import UserReward
from sqlalchemy.orm import selectinload

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


@router.put("/referrer")
async def update_referrer(payload: PutReferrerRequest, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """
    Set the referrer for the user. The referrer must be an existing user in the system.
    """
    referrer_username = payload.referrer_username[1:]

    referrer_query = (
        select(User)
        .options(selectinload(User.referrer).selectinload(User.referrer))
        .filter(User.username == referrer_username)
    )
    referrer_result = await session.execute(referrer_query)
    referrer = referrer_result.scalars().first()

    if not referrer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referrer not found")

    if referrer.id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot refer yourself")

    user.referrer = referrer
    await session.commit()

    new_user_reward = UserReward(user_id=user.id, reward_type_id=2)
    session.add(new_user_reward)

    referrer_reward = UserReward(user_id=referrer.id, reward_type_id=3)
    session.add(referrer_reward)

    if referrer.referrer:
        grand_referrer_reward = UserReward(user_id=referrer.referrer.id, reward_type_id=11)
        session.add(grand_referrer_reward)

    await session.commit()

    return {"message": "Referrer updated successfully and rewards issued"}