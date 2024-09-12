from aiogram import Bot
from aiogram import Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from supabase import Client, create_client
from pydantic_settings import BaseSettings


class Secrets(BaseSettings):
    token: str
    kassa_token: str
    supabase_url: str
    supabase_key: str
    admin_id: int
    admin_thread: int
    redis_url: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


secrets = Secrets()

url: str = secrets.supabase_url
key: str = secrets.supabase_key
supabase: Client = create_client(url, key)

storage = RedisStorage.from_url(secrets.redis_url)
default = DefaultBotProperties(parse_mode='Markdown', protect_content=False)
bot = Bot(token=secrets.token, default=default)
dp = Dispatcher(storage=storage)
