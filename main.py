from fastapi import FastAPI
from routers.auth import router as auth_router
from routers.crash import router as casino_router
from routers.rewards import router as rewards_router
from routers.user_settings import router as settings_router
from routers.balance import router as balance_router
import hashlib
import hmac

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

@app.on_event("startup")
async def generate_telegram_auth_hash():
    data = {
        "id": '123456789',
        "first_name": "John",
        "last_name": "Doe",
        "username": "johndoe",
        "photo_url": "http://example.com/photo.jpg",
        "auth_date": 1609459200
    }
    secret_key = '6423D56FEB97AE1B27D55AB43D124'
    check_string = '\n'.join([f"{key}={value}" for key, value in sorted(data.items()) if key != 'hash'])
    hash = hmac.new(secret_key.encode(), check_string.encode(), hashlib.sha256).hexdigest()
    print("Test hash for testing is:", hash)