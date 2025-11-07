from fastapi import APIRouter
from .dependencies_cassandra import session

router = APIRouter(prefix="/logs", tags=["logs"])

@router.get("/albums/{album_id}")
async def get_album_logs(album_id: str):
    rows = session.execute("SELECT * FROM album_change_log WHERE album_id=%s", [album_id])
    return [dict(row._asdict()) for row in rows]

@router.get("/playlists/{playlist_id}")
async def get_playlist_logs(playlist_id: str):
    rows = session.execute("SELECT * FROM playlist_change_log WHERE playlist_id=%s", [playlist_id])
    return [dict(row._asdict()) for row in rows]

@router.get("/users/{user_id}")
async def get_user_logs(user_id: str):
    rows = session.execute("SELECT * FROM entity_changes_by_user WHERE user_id=%s", [user_id])
    return [dict(row._asdict()) for row in rows]
