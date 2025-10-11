from functools import lru_cache
from pymongo import AsyncMongoClient
from . import config
# import pymongo

@lru_cache
def get_settings():
    return config.Settings()

@lru_cache
def get_client(mongodb_url: str):
    return AsyncMongoClient(mongodb_url)

@lru_cache
def get_db(client: AsyncMongoClient, db_name: str):
    return client.get_database(db_name) 

settings = get_settings() 

print(settings.mongodb_url)

# IMPORTANT: set a MONGODB_URL environment variable with value as your connection string to MongoDB
client = get_client(settings.mongodb_url) #server_api=pymongo.server_api.ServerApi(version="1", strict=True,deprecation_errors=True)) # type: ignore
db = get_db(client, "spotify-clone")