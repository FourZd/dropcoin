from functools import lru_cache
import os
from pydantic_settings import BaseSettings

@lru_cache
def get_env_filename():
    runtime_env = os.getenv("ENV")
    return f".env.{runtime_env}" if runtime_env else ".env"

class EnvironmentSettings(BaseSettings):
    TWITTER_API_KEY: str
    TWITTER_API_SECRET: str
    TWITTER_BEARER_TOKEN: str
    DATABASE_DIALECT: str
    DATABASE_HOSTNAME: str
    DATABASE_NAME: str
    DATABASE_PASSWORD: str
    DATABASE_PORT: int
    DATABASE_USERNAME: str
    DEBUG_MODE: bool
    JWT_SECRET: str
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    TG_BOT_NAME: str

    class Config:
        env_file = get_env_filename()
        env_file_encoding = "utf-8"

@lru_cache
def get_environment_variables():
    return EnvironmentSettings()