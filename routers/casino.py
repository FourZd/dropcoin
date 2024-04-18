import hashlib
from fastapi import APIRouter
import asyncio
from datetime import datetime, timedelta

router = APIRouter()

# Инициализация переменных
next_game_time = datetime.now() + timedelta(seconds=10)
current_game_hash = None

def generate_hash(seed):
    return hashlib.sha256(seed.encode()).hexdigest()

def generate_game_hash():
    # Используем текущее время для генерации серверного хэша
    seed = str(datetime.now().timestamp())
    return hashlib.sha256(seed.encode()).hexdigest()

async def game_scheduler():
    global current_game_hash, next_game_time
    while True:
        await asyncio.sleep((next_game_time - datetime.now()).total_seconds())
        current_game_hash = generate_game_hash()
        next_game_time += timedelta(minutes=1)

@router.on_event("startup")
async def start_scheduler():
    asyncio.create_task(game_scheduler())

def crash_point_from_hash(server_seed):
    salt = "0xd2867566759e9158bda9bf93b343bbd9aa02ce1e0c5bc2b37a2d70d391b04f14"
    hash_object = hashlib.sha256((server_seed + salt).encode())
    hash_hex = hash_object.hexdigest()

    # Расчет коэффициента краша по хэшу
    divisor = 100 // 4
    val = 0
    for i in range(0, len(hash_hex), 4):
        val = (val * 65536 + int(hash_hex[i:i + 4], 16)) % divisor

    if val == 0:
        return 1.0

    exponent = 52
    h = int(hash_hex[:13], 16)
    e = 2**exponent
    crash_point = (100 * e - h) / (e - h)
    return crash_point / 100.0

@router.get("/game_result")
def game_result():
    if current_game_hash is None:
        return {"error": "The game has not started yet"}
    result = crash_point_from_hash(current_game_hash)
    return {"result": result}
