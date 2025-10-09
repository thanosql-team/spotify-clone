from fastapi import Depends, FastAPI

from .routes import albums, playlists, songs, users

def main():
    print("Hello from 1-mongodb-app!")

app = FastAPI()

app.include_router(albums.router)
app.include_router(playlists.router)
app.include_router(songs.router)
app.include_router(users.router)

@app.get("/")
async def root():
    return {"message": "Welcome to Spotify Clone!"}

if __name__ == "__main__":
    main()