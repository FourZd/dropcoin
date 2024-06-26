
from fastapi import APIRouter, HTTPException, Depends, WebSocket
import asyncio
from datetime import datetime, timedelta, timezone
from schemas.casino import BetRequest, CashOutRequest, BetResponse, CancelBetResponse, BetResultResponse, LastGameResultResponse, TimingResponse, CurrentBet
from configs.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.CrashState import CrashState
from models.UserModel import User
from models.CrashBet import CrashBet
from services.auth import get_current_user
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import text
from services.balance import calculate_user_balance
from services.crash import publish_bet_update
from decimal import Decimal
import json
import aio_pika
import logging
from configs.environment import get_environment_variables
from typing import List
from models.GameHistory import GameHistory

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

env = get_environment_variables()
rabbitmq_host = env.RABBITMQ_HOST
rabbitmq_port = env.RABBITMQ_PORT

router = APIRouter(
    prefix="/crash",
    tags=["crash"]
)

next_game_time = datetime.now(timezone.utc) + timedelta(seconds=10)

# Список ставок, где каждая ставка - это словарь
bets = []


@router.post("/place_bet", response_model=BetResponse)
async def place_bet(bet_request: BetRequest, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """
    Place a bet for the current game. The bet is placed only if the user has not already placed a bet for the current game.
    """
    # Retrieve the current state of the game
    result = await session.execute(select(CrashState).limit(1))
    state = result.scalars().first()

    if state is None or datetime.now(timezone.utc) >= state.betting_close_time:
        raise HTTPException(
            status_code=400, detail="Betting is closed for the current game. Wait for the next game.")

    # Check if the user has already placed a bet for the current game
    existing_bet_result = await session.execute(select(CrashBet).where(CrashBet.user_id == user.id, CrashBet.hash == state.current_game_hash))
    existing_bet = existing_bet_result.scalars().first()

    if existing_bet:
        raise HTTPException(
            status_code=400, detail="You have already placed a bet for this game.")

    current_balance = await calculate_user_balance(user.id, session)
    if current_balance < bet_request.amount:
        raise HTTPException(
            status_code=400, detail="Insufficient balance to place the bet.")

    # Place a new bet if no existing bet is found
    new_bet = CrashBet(
        user_id=user.id,
        amount=bet_request.amount,
        time=datetime.now(timezone.utc),
        hash=state.current_game_hash
    )
    session.add(new_bet)
    await session.commit()
    user_data = {
        "user": user.username,
        "bet": bet_request.amount
    }
    await publish_bet_update(user_data)
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
        raise HTTPException(
            status_code=404, detail="No game currently active.")

    # Check if betting is still open
    if datetime.now(timezone.utc) >= state.betting_close_time:
        raise HTTPException(
            status_code=400, detail="Betting has closed; bet cannot be deleted.")

    bet_check_query = text(
        "SELECT 1 FROM crash_bets WHERE user_id = :user_id AND hash = :hash")
    bet_check_result = await session.execute(
        bet_check_query,
        {'user_id': user.id, 'hash': state.current_game_hash}
    )
    bet_exists = bet_check_result.scalar()

    # Если ставка существует, то выполняем её удаление
    if bet_exists:
        delete_query = text(
            "DELETE FROM crash_bets WHERE user_id = :user_id AND hash = :hash")
        await session.execute(
            delete_query,
            {'user_id': user.id, 'hash': state.current_game_hash}
        )
        await session.commit()
        return {"detail": "Bet deletion successful"}
    else:
        # Если ставка не найдена, возвращаем ошибку
        raise HTTPException(status_code=404, detail="Bet not found.")

@router.get("/games")
async def get_previous_games(limit: int, db: AsyncSession = Depends(get_session)):
    # Define the current time for filtering
    current_time = datetime.utcnow()

    # Query to fetch games with manual join on game_hash and eager loading of user info
    stmt = (
        select(GameHistory)
        .where(GameHistory.end_time < current_time)
        .order_by(GameHistory.end_time.desc())
        .limit(limit)
    )

    # Execute the query to get games
    result = await db.execute(stmt)
    games = result.scalars().all()

    # Extract game_hashes for fetching bets
    game_hashes = [game.game_hash for game in games]

    # Fetch all bets for the games in a single query
    bets_stmt = (
        select(CrashBet)
        .options(selectinload(CrashBet.user))
        .where(CrashBet.hash.in_(game_hashes))
    )
    bets_result = await db.execute(bets_stmt)
    bets = bets_result.scalars().all()

    # Group bets by game_hash
    bets_by_game = {}
    for bet in bets:
        if bet.hash not in bets_by_game:
            bets_by_game[bet.hash] = []
        bets_by_game[bet.hash].append(bet)

    # Prepare the response data
    response = []
    for game in games:
        game_data = {
            "id": game.id,
            "game_hash": game.game_hash,
            "result": game.result,
            "start_time": game.start_time,
            "end_time": game.end_time,
            "bets": [],
            "total_bet_amount": 0
        }

        if game.game_hash in bets_by_game:
            for bet in bets_by_game[game.game_hash]:
                game_data["bets"].append({
                    "id": bet.id,
                    "user_id": bet.user_id,
                    "username": bet.user.username,
                    "amount": bet.amount,
                    "time": bet.time,
                    "hash": bet.hash,
                    "cash_out_multiplier": bet.cash_out_multiplier,
                    "cash_out_datetime": bet.cash_out_datetime,
                    "result": bet.result
                })
                game_data["total_bet_amount"] += bet.amount

        response.append(game_data)

    return response

@router.post("/cash_out", response_model=BetResponse)
async def cash_out(cash_out_request: CashOutRequest, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """
    Sets a cashout multiplier for the current game. The cash out is registered only if the user has not already cashed out the bet. 
    To place a new cash out, cancel the existing cash out first.
    """
    state_result = await session.execute(select(CrashState).limit(1))
    state = state_result.scalars().first()

    bet_result = await session.execute(select(CrashBet).where(CrashBet.user_id == user.id, CrashBet.hash == state.current_game_hash))
    bet = bet_result.scalars().first()

    if bet is None:
        raise HTTPException(
            status_code=404, detail="Bet not found or game has already ended.")
    if bet.cash_out_multiplier is not None:
        raise HTTPException(
            status_code=400, detail="You have already cashed out this bet.")

    bet.cash_out_multiplier = cash_out_request.multiplier
    bet.cash_out_datetime = datetime.now(timezone.utc)
    await session.commit()
    user_data = {
        "user": user.username,
        "cashout_multiplier": cash_out_request.multiplier
    }
    await publish_bet_update(user_data)
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
    bet_result = await session.execute(select(CrashBet).where(CrashBet.user_id == user.id, CrashBet.hash == state.current_game_hash))
    bet = bet_result.scalars().first()

    if bet is None:
        raise HTTPException(status_code=404, detail="Bet not found.")

    # Check if the bet has a cash out and if betting is still open
    if bet.cash_out_datetime is None:
        raise HTTPException(
            status_code=404, detail="No cash out registered for this bet.")

    # Check if the cash out time is before the betting close time
    if bet.cash_out_datetime >= state.betting_close_time:
        raise HTTPException(
            status_code=400, detail="Betting has closed; cash out cannot be cancelled.")

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

    bets_result = await session.execute(select(CrashBet).where(CrashBet.user_id == user.id, CrashBet.hash == state.last_game_hash))
    user_bets = bets_result.scalars().all()

    if not user_bets:
        raise HTTPException(
            status_code=400, detail="No bets found for the last game or wrong user ID.")

    result = None
    for bet in user_bets:
        if bet.cash_out_multiplier is None or bet.cash_out_multiplier > state.last_game_result:
            outcome = "Lost"
            win_amount = 0
        else:
            outcome = "Win"
            win_amount = bet.amount * bet.cash_out_multiplier
        result = {"bet_id": bet.id, "outcome": outcome,
                  "win_amount": win_amount}

    return result


@router.get("/last_game_result", response_model=LastGameResultResponse)
async def get_last_game_result(session: AsyncSession = Depends(get_session)):
    """
    Check the result of the last game.
    """
    state_result = await session.execute(select(CrashState).limit(1))
    state = state_result.scalars().first()

    if state is None or state.last_game_hash is None:
        return {"error": "No previous game available yet."}

    return {
        "result": state.last_game_result,
        "hash": state.last_game_hash,
        "betting_close_time": state.betting_close_time
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
    }


@router.get("/bets", response_model=List[CurrentBet])
async def get_actual_bets(session: AsyncSession = Depends(get_session)):
    response_list = []
    current_game = await session.execute(select(CrashState).limit(1))
    current_game: CrashState = current_game.scalars().first()
    current_game_hash = current_game.current_game_hash
    current_game_bets = await session.execute(select(CrashBet).options(joinedload(CrashBet.user)).filter(CrashBet.hash == current_game_hash))
    current_game_bets: list[CrashBet] = current_game_bets.scalars().all()
    for bet in current_game_bets:
        formatted_bet = CurrentBet(
            user_id=bet.user_id,
            username=bet.user.username,
            amount=bet.amount,
            time=bet.time,
            cash_out_multiplier=bet.cash_out_multiplier,
            cash_out_datetime=bet.cash_out_datetime,
            result=bet.result
        )
        response_list.append(formatted_bet)
    return response_list


@router.websocket("/ws")
async def game_websocket(websocket: WebSocket):
    await websocket.accept()
    env = get_environment_variables()  # Не забывайте получать переменные окружения здесь
    connection = await aio_pika.connect_robust(f"amqp://fourzd:1FArjOL1!@{env.RABBITMQ_HOST}:{env.RABBITMQ_PORT}/")
    async with connection:
        channel = await connection.channel()

        # Создаем или подключаемся к существующему exchange типа 'fanout'.
        exchange_name = 'game_updates'
        await channel.declare_exchange(exchange_name, 'fanout', durable=True)

        # Создаем временную эксклюзивную очередь.
        queue = await channel.declare_queue('', exclusive=True)
        await queue.bind(exchange_name)

        async for message in queue:
            async with message.process():
                data = json.loads(message.body.decode())

                if data['event'] == 'start':
                    # Отправляем сообщение о начале игры.
                    await websocket.send_json({"type": "start", "event": data['event'], "time": data['time']})

                elif data['event'] == 'end':
                    # Отправляем сообщение о завершении игры с финальным коэффициентом.
                    await websocket.send_json({"type": "end", "time": data['time'], "final_ratio": str(data['crash_point'])})


@router.websocket("/listen-for-bets")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connection = await aio_pika.connect_robust(f"amqp://fourzd:1FArjOL1!@{rabbitmq_host}:{rabbitmq_port}/")
    async with connection:
        channel = await connection.channel()  # Open a channel
        # Declare exchange
        exchange = await channel.declare_exchange('game_bets', "fanout", durable=True)
        # Ensure the queue is declared and bind to the exchange
        # exclusive queue
        queue = await channel.declare_queue('', exclusive=True)
        await queue.bind(exchange)

        # Consume messages
        async for message in queue:
            async with message.process():
                # Преобразование текста обратно в JSON
                json_data = json.loads(message.body.decode())
                json_type = type(json_data)
                logging.info(f"json type is {json_type}")
                # Отправка JSON-объекта через WebSocket
                await websocket.send_json(json_data)
