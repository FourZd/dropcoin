from fastapi import FastAPI
from routers.auth import router as auth_router
from routers.crash import router as casino_router
from routers.rewards import router as rewards_router
from routers.user_settings import router as settings_router
from routers.balance import router as balance_router
from routers.farming import router as farming_router
import hashlib
import hmac
from services.crash import listen_for_game
import asyncio
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Booster API",
    description="""
    ## Описание API
    Здесь описаны все эндпоинты бэкэнда нашего сервиса.
    
    ### Контакты
    Если у вас возникнут вопросы по эндпоинтам И/ИЛИ контракту фронтэнда и бэкэнда, пишите руководителю. При необходимости он сможет связать вас с разработчиком бэкэнда.

    ### ВАЖНО
    В API присутствуют моменты, которые необходимо будет изменить в зависимости от реализации фронтэнда. Например, редирект с твиттера после авторизации. 
    Сейчас он установлен на 'https://www.booster.trading/farming/auth/twitter/callback'. В будущекм, вероятнее всего, мы будем использовать домен app.booster.trading/ для фронтэнда. 
    Однако если вам будет удобнее использовать другой домен для разработки, обратитесь к руководителю.

    ### ВАЖНО. Насчет CORS.
    Если у вас возникнут проблемы с CORS, сообщите об этом. Бэкэндер добавит ваш домен в список разрешенных для CORS.
    """,
    version="1.0.0"
)


app.include_router(auth_router)
app.include_router(casino_router)
app.include_router(rewards_router)
app.include_router(settings_router)
app.include_router(balance_router)
app.include_router(farming_router)

origins = [
    "https://booster-app-54f649d23ab2.herokuapp.com/",
    "https://web.telegram.org",
    "https://t.me",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Список источников, которым разрешен доступ
    allow_credentials=True,
    allow_methods=["*"],  # Разрешенные методы
    allow_headers=["*"],  # Разрешенные заголовки
)


@app.on_event("startup")
async def generate_telegram_auth_hash():
    id = '13371488'
    secret_key = '6423D56FEB97AE1B27D55AB43D124'
    hash = hmac.new(secret_key.encode(), id.encode(), hashlib.sha256).hexdigest()
    print("Test hash for testing is:", hash)


@app.on_event("startup")
async def start_scheduler():
    asyncio.create_task(listen_for_game())