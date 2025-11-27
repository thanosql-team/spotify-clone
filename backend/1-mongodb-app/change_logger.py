from datetime import datetime
import json
from .dependencies_cassandra import session
from bson import ObjectId

def json_safe(data):
    """Convert ObjectId and other types into JSON-safe strings."""
    if data is None:
        return None
    def convert(o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        raise TypeError(f"Type {type(o)} not serializable")
    return json.dumps(data, default=convert)

async def log_album_change(album_id: str, user_id: str, action: str, old_data: dict | None, new_data: dict | None):
    now = datetime.utcnow()
    session.execute(
        """
        INSERT INTO album_change_log (album_id, change_time, user_id, action, old_data, new_data)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (album_id, now, user_id, action, json_safe(old_data), json_safe(new_data))
    )
    session.execute(
        """
        INSERT INTO entity_changes_by_user (user_id, change_time, entity_type, entity_id, action)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (user_id, now, "album", album_id, action)
    )
    session.execute(
        """
        INSERT INTO entity_changes_all (entity_type, change_time, user_id, entity_id, action)
        VALUES (%s, %s, %s, %s, %s)
        """,
        ("album", now, user_id, album_id, action)
    )

async def log_playlist_change(playlist_id: str, user_id: str, action: str, old_data: dict | None, new_data: dict | None):
    now = datetime.utcnow()
    session.execute(
        """
        INSERT INTO playlist_change_log (playlist_id, change_time, user_id, action, old_data, new_data)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (playlist_id, now, user_id, action, json_safe(old_data), json_safe(new_data))
    )
    session.execute(
        """
        INSERT INTO entity_changes_by_user (user_id, change_time, entity_type, entity_id, action)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (user_id, now, "playlist", playlist_id, action)
    )
    session.execute(
        """
        INSERT INTO entity_changes_all (entity_type, change_time, user_id, entity_id, action)
        VALUES (%s, %s, %s, %s, %s)
        """,
        ("playlist", now, user_id, playlist_id, action)
    )
