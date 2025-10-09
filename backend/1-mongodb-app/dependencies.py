from pymongo import AsyncMongoClient
from config import Settings

settings = Settings() 

# IMPORTANT: set a MONGODB_URL environment variable with value as your connection string to MongoDB
client = AsyncMongoClient(settings.mongodb_url) #,server_api=pymongo.server_api.ServerApi(version="1", strict=True,deprecation_errors=True))
db = client.get_database("spotify-clone")