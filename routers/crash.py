
from fastapi import APIRouter, HTTPException, Depends, WebSocket
import asyncio
from datetime import datetime, timedelta, timezone
from schemas.casino import BetRequest, CashOutRequest, BetResponse, CancelBetResponse, BetResultResponse, LastGameResultResponse, TimingResponse
from configs.crash import check_and_generate_hashes
from services.crash import game_scheduler, crash_point_from_hash
from models.CrashHash import CrashHash
from configs.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.CrashState import CrashState
from models.UserModel import User
from models.CrashBet import CrashBet
from services.auth import get_current_user
from sqlalchemy.orm import selectinload
from sqlalchemy import text
from services.balance import calculate_user_balance


router = APIRouter(
    prefix="/crash",
    tags=["crash"]
)

next_game_time = datetime.now(timezone.utc) + timedelta(seconds=10)

# Список ставок, где каждая ставка - это словарь
bets = []


@router.on_event("startup")
async def start_scheduler():
    await check_and_generate_hashes()
    asyncio.create_task(game_scheduler())


@router.post("/place_bet", response_model=BetResponse)
async def place_bet(bet_request: BetRequest, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """
    Place a bet for the current game. The bet is placed only if the user has not already placed a bet for the current game.
    """
    # Retrieve the current state of the game
    result = await session.execute(select(CrashState).limit(1))
    state = result.scalars().first()

    if state is None or datetime.now(timezone.utc) >= state.betting_close_time:
        raise HTTPException(status_code=400, detail="Betting is closed for the current game. Wait for the next game.")

    # Check if the user has already placed a bet for the current game
    existing_bet_result = await session.execute(select(CrashBet).where(CrashBet.user_id == user.id, CrashBet.game_id == state.current_game_hash_id))
    existing_bet = existing_bet_result.scalars().first()

    if existing_bet:
        raise HTTPException(status_code=400, detail="You have already placed a bet for this game.")

    current_balance = await calculate_user_balance(user.id, session)
    if current_balance < bet_request.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance to place the bet.")
    
    # Place a new bet if no existing bet is found
    new_bet = CrashBet(
        user_id=user.id,
        amount=bet_request.amount,
        time=datetime.now(timezone.utc),
        game_id=state.current_game_hash_id
    )
    session.add(new_bet)
    await session.commit()

    return {"detail": "Bet placed successfully", "bet": new_bet}


@router.delete("/cancel_bet", response_model=CancelBetResponse)
async def cancel_bet(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """
    Cancel a bet for the current game. The bet can only be cancelled if the betting is still open.
    """
    # Get the current game state
    state_result = await session.execute(select(CrashState).limit(1))
    state = state_result.scalars().first()

    if state is None:
        raise HTTPException(status_code=404, detail="No game currently active.")

    # Check if betting is still open
    if datetime.now(timezone.utc) >= state.betting_close_time:
        raise HTTPException(status_code=400, detail="Betting has closed; bet cannot be deleted.")

    bet_check_query = text("SELECT 1 FROM crash_bets WHERE user_id = :user_id AND game_id = :game_id")
    bet_check_result = await session.execute(
        bet_check_query,
        {'user_id': user.id, 'game_id': state.current_game_hash_id}
    )
    bet_exists = bet_check_result.scalar()

    # Если ставка существует, то выполняем её удаление
    if bet_exists:
        delete_query = text("DELETE FROM crash_bets WHERE user_id = :user_id AND game_id = :game_id")
        await session.execute(
            delete_query,
            {'user_id': user.id, 'game_id': state.current_game_hash_id}
        )
        await session.commit()
        return {"detail": "Bet deletion successful"}
    else:
        # Если ставка не найдена, возвращаем ошибку
        raise HTTPException(status_code=404, detail="Bet not found.")


@router.post("/cash_out", response_model=BetResponse)
async def cash_out(cash_out_request: CashOutRequest, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """
    Sets a cashout multiplier for the current game. The cash out is registered only if the user has not already cashed out the bet. 
    To place a new cash out, cancel the existing cash out first.
    """
    state_result = await session.execute(select(CrashState).limit(1))
    state = state_result.scalars().first()

    bet_result = await session.execute(select(CrashBet).where(CrashBet.user_id == user.id, CrashBet.game_id == state.current_game_hash_id))
    bet = bet_result.scalars().first()

    if bet is None:
        raise HTTPException(status_code=404, detail="Bet not found or game has already ended.")
    if bet.cash_out_multiplier is not None:
        raise HTTPException(status_code=400, detail="You have already cashed out this bet.")

    bet.cash_out_multiplier = cash_out_request.multiplier
    bet.cash_out_datetime = datetime.now(timezone.utc)
    await session.commit()

    return {"detail": "Cash out registered", "bet": bet}


@router.delete("/cancel_cash_out", response_model=CancelBetResponse)
async def cancel_cash_out(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """
    Cancel a cash out for the current game. The cash out can only be cancelled if the betting is still open.
    """
    # Get the current game state
    state_result = await session.execute(select(CrashState).limit(1))
    state = state_result.scalars().first()

    # Retrieve the user's current bet for the ongoing game
    bet_result = await session.execute(select(CrashBet).where(CrashBet.user_id == user.id, CrashBet.game_id == state.current_game_hash_id))
    bet = bet_result.scalars().first()

    if bet is None:
        raise HTTPException(status_code=404, detail="Bet not found.")

    # Check if the bet has a cash out and if betting is still open
    if bet.cash_out_datetime is None:
        raise HTTPException(status_code=404, detail="No cash out registered for this bet.")

    # Check if the cash out time is before the betting close time
    if bet.cash_out_datetime >= state.betting_close_time:
        raise HTTPException(status_code=400, detail="Betting has closed; cash out cannot be cancelled.")

    # If checks pass, remove the cash out
    bet.cash_out_multiplier = None
    bet.cash_out_datetime = None
    await session.commit()

    return {"detail": "Cash out deletion successful"}


@router.get("/check_bet_result", response_model=BetResultResponse)
async def check_bet_result(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """
    Check the results of the user's bets for the last game.
    """
    state_result = await session.execute(select(CrashState).limit(1))
    state = state_result.scalars().first()

    bets_result = await session.execute(select(CrashBet).where(CrashBet.user_id == user.id, CrashBet.game_id == state.last_game_hash_id))
    user_bets = bets_result.scalars().all()

    if not user_bets:
        raise HTTPException(status_code=400, detail="No bets found for the last game or wrong user ID.")

    result = None
    for bet in user_bets:
        if bet.cash_out_multiplier is None or bet.cash_out_multiplier > state.last_game_result:
            outcome = "Lost"
            win_amount = 0
        else:
            outcome = "Win"
            win_amount = bet.amount * bet.cash_out_multiplier
        result = {"bet_id": bet.id, "outcome": outcome, "win_amount": win_amount}

    return result

@router.get("/last_game_result", response_model=LastGameResultResponse)
async def get_last_game_result(session: AsyncSession = Depends(get_session)):
    """
    Check the result of the last game.
    """
    state_result = await session.execute(select(CrashState).options(selectinload(CrashState.last_game_hash)).limit(1))
    state = state_result.scalars().first()
    
    if state is None or state.last_game_hash is None:
        return {"error": "No previous game available yet."}
    
    return {
        "result": state.last_game_result,
        "hash": state.last_game_hash.hash,
        "betting_close_time": state.betting_close_time,
        "next_game_time": state.next_game_time
    }

@router.get("/game_timing", response_model=TimingResponse)
async def get_game_timing(session: AsyncSession = Depends(get_session)):
    """
    Returns the current time, the betting close time, and the next game time.
    """
    state_result = await session.execute(select(CrashState).limit(1))
    state = state_result.scalars().first()
    
    if state is None:
        return {"error": "Game state is not initialized."}

    return {
        "current_time": datetime.now(timezone.utc),
        "betting_close_time": state.betting_close_time,
        "next_game_time": state.next_game_time
    }


@router.websocket("/ws")
async def game_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            gen = get_session()
            session = await gen.__anext__()
            state_result = await session.execute(select(CrashState).limit(1))
            state = state_result.scalars().first()
            
            await asyncio.sleep((state.betting_close_time - datetime.now(timezone.utc)).total_seconds())
            await asyncio.sleep((state.next_game_time - datetime.now(timezone.utc)).total_seconds())

            next_hash_result = await session.execute(
                select(CrashHash)
                .where(CrashHash.id < state.current_game_hash_id)
                .order_by(CrashHash.id.desc())
                .limit(1)
            )
            next_hash = next_hash_result.scalars().first()
            if not next_hash:
                await websocket.send_json({"type": "end", "final_ratio": 0})
                break

            crash_point = crash_point_from_hash(next_hash.hash)
            multiplier = 1.0
            current_time = 2.0
            time_decrease_factor = 0.95
            
            # Sending updates at each interval
            while multiplier < crash_point:
                multiplier += 0.1
                current_time *= time_decrease_factor
                await websocket.send_json({"type": "ratio", "current_ratio": multiplier})
                await asyncio.sleep(current_time)

            # Send final crash point 
            await websocket.send_json({"type": "end", "final_ratio": crash_point})
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
    finally:
        await websocket.close()