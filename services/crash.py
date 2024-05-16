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
from configs.environment import get_environment_variables
import logging

env = get_environment_variables()
rabbitmq_host = env.RABBITMQ_HOST
rabbitmq_port = env.RABBITMQ_PORT

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


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
                (bet.cash_out_multiplier - 1) * bet.amount  # Вычитаем 1, чтобы учесть основную ставку
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


async def send_to_websocket_clients(exchange, message):
    # Здесь предполагаем, что exchange уже создан с нужным типом.
    # 'game_updates' - это название exchange, 'game' - ключ маршрутизации.
    await exchange.publish(
        aio_pika.Message(body=json.dumps(message).encode(), delivery_mode=2),
        routing_key="",
    )
    logging.info("Message sent to websocket clients successfully")


async def listen_for_game():
    env = get_environment_variables()
    rabbitmq_host = env.RABBITMQ_HOST
    rabbitmq_port = env.RABBITMQ_PORT
    connection = await aio_pika.connect_robust(
        f"amqp://fourzd:1FArjOL1!@{rabbitmq_host}:{rabbitmq_port}/"
    )

    async with connection:
        channel = await connection.channel()
        publish_channel = await connection.channel()
        exchange_name = "game_updates"
        try:
            await publish_channel.exchange_delete(exchange_name)
            logging.info(f"Existing exchange '{exchange_name}' deleted.")
        except Exception as e:
            logging.info(f"No existing exchange '{exchange_name}' to delete: {str(e)}")
        exchange = await publish_channel.declare_exchange(
            exchange_name, "fanout", durable=True
        )

        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue(
            "crash_point_queue",
            durable=True,
            auto_delete=True,
            arguments={"x-max-length": 1},
        )

        logging.info("waiting for message....")
        async for message in queue:
            logging.info("Message received")
            try:
                async with message.process():
                    logging.info("Processing message")
                    data = json.loads(message.body)
                    logging.info(f"Received data: {data}")

                    crash_point = data["crash_point"]
                    crash_time = datetime.fromisoformat(data["crash_time"])
                    crash_hash = data["crash_hash"]

                    betting_close_time = datetime.now(timezone.utc) + timedelta(
                        seconds=10
                    )
                    session_gen = get_session()
                    session = await session_gen.__anext__()

                    logging.info("Session started")
                    state = await session.execute(select(CrashState).limit(1))
                    state = state.scalars().first()

                    if not state:
                        logging.info("No existing state found, creating new state")
                        state = CrashState(
                            current_game_hash=crash_hash,
                            current_result=Decimal(0),
                            betting_close_time=betting_close_time,
                            last_game_hash=None,
                            last_game_result=Decimal(0),
                            next_game_time=crash_time,
                        )
                        session.add(state)
                        await session.commit()
                        logging.info("New state committed")

                    await update_game_data(
                        session,
                        crash_time,
                        betting_close_time,
                        crash_hash,
                        crash_point,
                        state,
                    )
                    logging.info("Game data updated")

                    await update_previous_crash_bets(session)
                    logging.info("Previous crash bets updated")

                    wait_time = betting_close_time - datetime.now(timezone.utc)
                    await asyncio.sleep(wait_time.total_seconds())

                    await send_to_websocket_clients(
                        exchange,
                        {
                            "event": "update_game",
                            "crash_point": crash_point,
                            "crash_time": crash_time.isoformat(),
                        },
                    )
                    logging.info("Data sent to websocket clients")
                    await session.close()
                logging.info("message closed")

            except Exception as e:
                logging.error(f"Error: {e}")
                await session.close()
                raise e
            logging.info("try closed")


async def publish_bet_update(bet_info):
    connection = await aio_pika.connect_robust(
        f"amqp://fourzd:1FArjOL1!@{rabbitmq_host}:{rabbitmq_port}/"
    )
    channel = await connection.channel()
    exchange = await channel.declare_exchange('game_bets', "fanout", durable=True)
    await exchange.publish(
        aio_pika.Message(body=bet_info.encode()),
        routing_key=''  
    )
    await connection.close()