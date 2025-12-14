from fastapi import APIRouter, Query
from datetime import datetime
from typing import Optional
from ..core.dependencies_cassandra import session

router = APIRouter(prefix="/logs", tags=["logs"])

@router.get("/albums/{album_id}")
async def get_album_logs(album_id: str):
    """
    Select all logs about a specific album.
    """
    rows = session.execute("SELECT * FROM album_change_log WHERE album_id=%s", [album_id])
    return [dict(row._asdict()) for row in rows]

@router.get("/playlists/{playlist_id}")
async def get_playlist_logs(playlist_id: str):
    """
    Select all logs about a specific playlist.
    """
    rows = session.execute("SELECT * FROM playlist_change_log WHERE playlist_id=%s", [playlist_id])
    return [dict(row._asdict()) for row in rows]

@router.get("/users/{user_id}")
async def get_user_logs(user_id: str):
    """
    Select all logs about a specific user changes (shows all changes made by a user).
    """
    rows = session.execute("SELECT * FROM entity_changes_by_user WHERE user_id=%s", [user_id])
    return [dict(row._asdict()) for row in rows]

@router.get("/search")
async def search_logs(
    action: str = Query(..., description="Action performed on the entity. Possible actions: create, update, delete"),
    entity: str = Query(..., description="On which entity was action performed. Possible entities: playlist, album"),
    start: Optional[datetime] = Query(None, description="Start date in ISO format. Use: YYYY-MM-DDTHH:MM:SS"),
    end: Optional[datetime] = Query(None, description="End date in ISO format. Use: YYYY-MM-DDTHH:MM:SS")
):
    """
    Filter logs about entity changes.
    """
    query = """
        SELECT * FROM entity_changes_by_entity_action
        WHERE entity_type=%s AND action=%s
    """
    params = [entity, action]

    if start:
        query += " AND change_time >= %s"
        params.append(start)

    if end:
        query += " AND change_time <= %s"
        params.append(end)

    rows = session.execute(query, params)
    return [dict(row._asdict()) for row in rows]
