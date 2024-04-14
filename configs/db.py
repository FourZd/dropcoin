from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from configs.environment import get_environment_variables

# Runtime Environment Configuration
env = get_environment_variables()

# Generate Database URL
DATABASE_URL = f"{env.DATABASE_DIALECT}+asyncpg://{env.DATABASE_USERNAME}:{env.DATABASE_PASSWORD}@{env.DATABASE_HOSTNAME}:{env.DATABASE_PORT}/{env.DATABASE_NAME}"

# Create Database Engine
Engine = create_async_engine(
    DATABASE_URL, echo=env.DEBUG_MODE, future=True
)

AsyncSessionLocal = sessionmaker(
    bind=Engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session