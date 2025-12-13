from fastapi import FastAPI

from .routes import albums, playlists, songs, users, graph, search
from . import change_logs
from .dependencies import init_cache, close_cache
from .dependencies_cassandra import get_cassandra_session
from .dependencies_neo4j import init_neo4j, close_neo4j
from .dependencies_elasticsearch import init_elasticsearch, close_elasticsearch

def main():
    print("Hello from 1-mongodb-app!")

app = FastAPI()

app.include_router(albums.router)
app.include_router(playlists.router)
app.include_router(songs.router)
app.include_router(users.router)
app.include_router(graph.router)
app.include_router(search.router)
app.include_router(change_logs.router)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize cache and database connections on app startup"""
    await init_cache()
    await init_neo4j()
    await init_elasticsearch()
    get_cassandra_session()
    print("Cache, Neo4j, and Elasticsearch initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Close cache and database connections on app shutdown"""
    await close_cache()
    await close_neo4j()
    await close_elasticsearch()
    print("Cache, Neo4j, and Elasticsearch closed")

@app.get("/")
async def root():
    return {"message": "Welcome to Spotify Clone!"}

if __name__ == "__main__":
    main()