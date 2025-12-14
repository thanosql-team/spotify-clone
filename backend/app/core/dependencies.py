from functools import lru_cache
from motor.motor_asyncio import AsyncIOMotorClient
from .. import config
from .cache_manager import CacheManager
import asyncio

# import pymongo

@lru_cache
def get_settings():
    return config.Settings()

@lru_cache
def get_client(mongodb_url: str):
    return AsyncIOMotorClient(mongodb_url)

@lru_cache
def get_db(client: AsyncIOMotorClient, db_name: str):
    return client.get_database(db_name) 

settings = get_settings() 

if settings.mongodb_url is None:
    print("MONGODB_URL connection string not found in environment (either .env at project root or your environment)")
# else:
#     print(settings.mongodb_url)

client = get_client(settings.mongodb_url) #server_api=pymongo.server_api.ServerApi(version="1", strict=True,deprecation_errors=True)) # type: ignore
db = get_db(client, "spotify-clone")

cache_manager = CacheManager(redis_url=settings.redis_url)

async def init_cache():
    """Initialize cache connection"""
    await cache_manager.connect()

async def close_cache():
    """Close cache connection"""
    await cache_manager.disconnect()