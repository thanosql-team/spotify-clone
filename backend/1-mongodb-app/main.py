from fastapi import FastAPI

from .routes import albums, playlists, songs, users
from .dependencies import init_cache, close_cache

def main():
    print("Hello from 1-mongodb-app!")

app = FastAPI()

app.include_router(albums.router)
app.include_router(playlists.router)
app.include_router(songs.router)
app.include_router(users.router)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize cache connection on app startup"""
    await init_cache()
    print("Cache initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Close cache connection on app shutdown"""
    await close_cache()
    print("Cache closed")

@app.get("/")
async def root():
    return {"message": "Welcome to Spotify Clone!"}

if __name__ == "__main__":
    main()