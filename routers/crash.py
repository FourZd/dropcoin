
from fastapi import APIRouter, HTTPException, Depends
import asyncio
from datetime import datetime, timedelta, timezone
from schemas.casino import BetRequest, CashOutRequest
from configs.crash import check_and_generate_hashes
from services.crash import game_scheduler
from configs.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.CrashState import CrashState
from models.UserModel import User
from models.CrashBet import CrashBet
from services.auth import get_current_user


router = APIRouter()

next_game_time = datetime.now(timezone.utc) + timedelta(seconds=10)

# Список ставок, где каждая ставка - это словарь
bets = []


@router.on_event("startup")
async def start_scheduler():
    await check_and_generate_hashes()
    asyncio.create_task(game_scheduler())


@router.post("/place_bet")
async def place_bet(bet_request: BetRequest, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    state_result = await session.execute(select(CrashState).limit(1))
    state = state_result.scalars().first()

    if state is None or datetime.now(timezone.utc) >= state.betting_close_time:
        raise HTTPException(status_code=400, detail="Betting is closed for the current game. Wait for the next game.")

    new_bet = CrashBet(
        user_id=user.id,
        amount=bet_request.amount,
        time=datetime.now(timezone.utc),
        game_hash=state.current_game_hash
    )
    session.add(new_bet)
    await session.commit()

    return {"detail": "Bet placed successfully", "bet": new_bet}

@router.post("/cash_out")
async def cash_out(cash_out_request: CashOutRequest, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    state_result = await session.execute(select(CrashState).limit(1))
    state = state_result.scalars().first()

    bet_result = await session.execute(select(CrashBet).where(CrashBet.user_id == user.id, CrashBet.game_hash == state.current_game_hash))
    bet = bet_result.scalars().first()

    if bet is None:
        raise HTTPException(status_code=404, detail="Bet not found or game has already ended.")
    if bet.cash_out_multiplier is not None:
        raise HTTPException(status_code=400, detail="You have already cashed out this bet.")

    bet.cash_out_multiplier = cash_out_request.multiplier
    await session.commit()

    return {"detail": "Cash out registered", "bet": bet}


@router.get("/check_bet_result")
async def check_bet_result(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    state_result = await session.execute(select(CrashState).limit(1))
    state = state_result.scalars().first()

    bets_result = await session.execute(select(CrashBet).where(CrashBet.user_id == user.id, CrashBet.game_hash == state.last_game_hash))
    user_bets = bets_result.scalars().all()

    if not user_bets:
        return {"error": "No bets found for the last game or wrong user ID."}

    results = []
    for bet in user_bets:
        if bet.cash_out_multiplier is None or bet.cash_out_multiplier > state.last_game_result:
            outcome = "Lost"
            win_amount = 0
        else:
            outcome = "Win"
            win_amount = bet.amount * bet.cash_out_multiplier
        results.append({"bet_id": bet.id, "outcome": outcome, "win_amount": win_amount})

    return {"results": results}

@router.get("/last_game_result")
async def get_last_game_result(session: AsyncSession = Depends(get_session)):
    state_result = await session.execute(select(CrashState).limit(1))
    state = state_result.scalars().first()
    
    if state is None or state.last_game_hash is None:
        return {"error": "No previous game available yet."}
    
    return {
        "result": state.last_game_result,
        "hash": state.last_game_hash,
        "betting_close_time": state.betting_close_time,
        "next_game_time": state.next_game_time
    }

@router.get("/game_timing")
async def get_game_timing(session: AsyncSession = Depends(get_session)):
    state_result = await session.execute(select(CrashState).limit(1))
    state = state_result.scalars().first()
    
    if state is None:
        return {"error": "Game state is not initialized."}

    return {
        "current_time": datetime.now(timezone.utc),
        "betting_close_time": state.betting_close_time,
        "next_game_time": state.next_game_time
    }