from fastapi import FastAPI
from routers.auth import router as auth_router
from routers.crash import router as casino_router
app = FastAPI()

app.include_router(auth_router)
app.include_router(casino_router)

