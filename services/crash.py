import hashlib
from datetime import datetime, timedelta, timezone
import asyncio
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, or_, case, cast
from models.CrashState import CrashState
from models.CrashBet import CrashBet
from models.UserTransaction import UserTransaction
from configs.db import get_session
import hashlib
from decimal import Decimal
from sqlalchemy.dialects.postgresql import ENUM
import aio_pika
import json


async def update_game_data(
    session: AsyncSession,
    next_game_time: datetime,
    betting_close_time: datetime,
    game_hash: str,
    game_result: Decimal,
    state: CrashState,
):
    state.last_game_hash = state.current_game_hash
    state.betting_close_time = betting_close_time
    state.current_game_hash = game_hash
    state.last_game_result = state.current_result
    state.current_result = game_result
    state.next_game_time = next_game_time
    await session.commit()


async def update_previous_crash_bets(session: AsyncSession):

    # Получение последнего раунда
    state = await session.execute(
        select(CrashState).order_by(CrashState.id.desc()).limit(1)
    )
    state = state.scalars().first()
    last_game_hash = state.last_game_hash
    last_game_result = state.last_game_result
    await session.execute(
        update(CrashBet)
        .where(CrashBet.hash == last_game_hash)
        .values(
            result=case(
                (
                    CrashBet.cash_out_multiplier < last_game_result,
                    cast("win", ENUM("win", "lose", name="result_types")),
                ),
                (
                    or_(
                        CrashBet.cash_out_multiplier > last_game_result,
                        CrashBet.cash_out_multiplier.is_(None),
                    ),
                    cast("lose", ENUM("win", "lose", name="result_types")),
                ),
                else_=cast("lose", ENUM("win", "lose", name="result_types")),
            )
        )
    )

    await session.commit()

    bets = await session.execute(
        select(CrashBet).where(CrashBet.hash == last_game_hash)
    )
    bets = bets.scalars().all()

    transactions = [
        UserTransaction(
            user_id=bet.user_id,
            profit=(
                bet.cash_out_multiplier * bet.amount
                if bet.result == "win"
                else -bet.amount
            ),
            timestamp=datetime.now(timezone.utc),
        )
        for bet in bets
    ]

    session.add_all(transactions)

    # Фиксация транзакций в базе данных
    await session.commit()

async def send_to_websocket_clients(publish_channel, message):
    await publish_channel.default_exchange.publish(
        aio_pika.Message(body=json.dumps(message).encode()),
        routing_key='websocket_game_queue'
    )
    
async def listen_for_game():
    # Listen for a game
    connection = await aio_pika.connect_robust(
        "amqp://crashrabbit:crashrabbit@localhost/"
    )
    async with connection:
        channel = await connection.channel()
        publish_channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue("crash_point_queue", durable=True)

        async for message in queue:
            async with message.process():
                data = json.loads(message.body)
                print(" [x] Received %r" % data)

                # Extract crash_point and crash_time from message body
                crash_point = data["crash_point"]
                crash_time = datetime.fromisoformat(data["crash_time"])
                crash_hash = data["crash_hash"]

                betting_close_time = datetime.now(timezone.utc) + timedelta(seconds=10)
                session_gen = get_session()
                session = await session_gen.__anext__()

                # get the current game state from the database
                state = await session.execute(select(CrashState).limit(1))
                state = state.scalars().first()
                await update_game_data(
                    session,
                    crash_time,
                    betting_close_time,
                    crash_hash,
                    crash_point,
                    state,
                )
                await update_previous_crash_bets(session)
                # sleep until betting_close_time
                wait_time = betting_close_time - datetime.now(timezone.utc)
                await asyncio.sleep(wait_time.total_seconds())

                # Assuming you have a function to send messages to websocket clients
                await send_to_websocket_clients(publish_channel, {
                    'event': 'update_game',
                    'crash_point': crash_point,
                    'crash_time': crash_time.isoformat(),
                })
