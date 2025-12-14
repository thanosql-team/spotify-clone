"""
Elasticsearch Sync Module
Automatically syncs CRUD operations from MongoDB to Elasticsearch for full-text search.
"""

import logging
from typing import Optional, Dict, Any

from ..core.dependencies_elasticsearch import get_elasticsearch

logger = logging.getLogger(__name__)


def _prepare_song_for_es(song: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB song document to Elasticsearch-compatible format"""
    return {
        "song_id": str(song.get("_id")),
        "name": song.get("name"),
        "artist": song.get("artist"),
        "genre": song.get("genre"),
        "album_name": song.get("album_name"),
        "release_year": song.get("release_year"),
        "duration": song.get("duration")
    }


def _prepare_album_for_es(album: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB album document to Elasticsearch-compatible format"""
    return {
        "album_id": str(album.get("_id")),
        "album_name": album.get("album_name"),
        "artist_name": album.get("artist_name"),
        "release_year": album.get("release_year")
    }


def _prepare_playlist_for_es(playlist: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB playlist document to Elasticsearch-compatible format"""
    return {
        "playlist_id": str(playlist.get("_id")),
        "playlist_name": playlist.get("playlistname"),
        "user_id": str(playlist.get("user_id")) if playlist.get("user_id") else None,
        "song_count": playlist.get("song_count", 0)
    }


def _prepare_user_for_es(user: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB user document to Elasticsearch-compatible format"""
    return {
        "user_id": str(user.get("_id")),
        "username": user.get("username"),
        "name": user.get("name"),
        "surname": user.get("surname"),
        "email": user.get("email")
    }


async def sync_song_to_elasticsearch(song_id: str, song_data: Optional[Dict[str, Any]] = None, action: str = "index"):
    """
    Sync a song to Elasticsearch
    
    Args:
        song_id: The MongoDB ObjectId of the song as string
        song_data: The song document from MongoDB (required for 'index' action)
        action: 'index' (create/update) or 'delete'
    """
    try:
        es = await get_elasticsearch()
        
        if action == "delete":
            await es.delete_document(index="songs", doc_id=song_id)
            logger.info(f"Deleted song {song_id} from Elasticsearch")
        elif action == "index" and song_data:
            es_doc = _prepare_song_for_es(song_data)
            await es.index_document(index="songs", doc_id=song_id, document=es_doc)
            logger.info(f"Indexed song {song_id} to Elasticsearch")
        else:
            logger.warning(f"Invalid action '{action}' or missing song_data for song {song_id}")
            
    except Exception as e:
        logger.error(f"Failed to sync song {song_id} to Elasticsearch: {e}")
        # Don't raise - we don't want ES failures to break the main operation


async def sync_album_to_elasticsearch(album_id: str, album_data: Optional[Dict[str, Any]] = None, action: str = "index"):
    """
    Sync an album to Elasticsearch
    
    Args:
        album_id: The MongoDB ObjectId of the album as string
        album_data: The album document from MongoDB (required for 'index' action)
        action: 'index' (create/update) or 'delete'
    """
    try:
        es = await get_elasticsearch()
        
        if action == "delete":
            await es.delete_document(index="albums", doc_id=album_id)
            logger.info(f"Deleted album {album_id} from Elasticsearch")
        elif action == "index" and album_data:
            es_doc = _prepare_album_for_es(album_data)
            await es.index_document(index="albums", doc_id=album_id, document=es_doc)
            logger.info(f"Indexed album {album_id} to Elasticsearch")
        else:
            logger.warning(f"Invalid action '{action}' or missing album_data for album {album_id}")
            
    except Exception as e:
        logger.error(f"Failed to sync album {album_id} to Elasticsearch: {e}")
        # Don't raise - we don't want ES failures to break the main operation


async def sync_playlist_to_elasticsearch(playlist_id: str, playlist_data: Optional[Dict[str, Any]] = None, action: str = "index"):
    """
    Sync a playlist to Elasticsearch
    
    Args:
        playlist_id: The MongoDB ObjectId of the playlist as string
        playlist_data: The playlist document from MongoDB (required for 'index' action)
        action: 'index' (create/update) or 'delete'
    """
    try:
        es = await get_elasticsearch()
        
        if action == "delete":
            await es.delete_document(index="playlists", doc_id=playlist_id)
            logger.info(f"Deleted playlist {playlist_id} from Elasticsearch")
        elif action == "index" and playlist_data:
            es_doc = _prepare_playlist_for_es(playlist_data)
            await es.index_document(index="playlists", doc_id=playlist_id, document=es_doc)
            logger.info(f"Indexed playlist {playlist_id} to Elasticsearch")
        else:
            logger.warning(f"Invalid action '{action}' or missing playlist_data for playlist {playlist_id}")
            
    except Exception as e:
        logger.error(f"Failed to sync playlist {playlist_id} to Elasticsearch: {e}")
        # Don't raise - we don't want ES failures to break the main operation


async def sync_user_to_elasticsearch(user_id: str, user_data: Optional[Dict[str, Any]] = None, action: str = "index"):
    """
    Sync a user to Elasticsearch
    
    Args:
        user_id: The MongoDB ObjectId of the user as string
        user_data: The user document from MongoDB (required for 'index' action)
        action: 'index' (create/update) or 'delete'
    """
    try:
        es = await get_elasticsearch()
        
        # Check if users index exists, if not create it
        if es.client and not await es.client.indices.exists(index="users"):
            users_mapping = {
                "mappings": {
                    "properties": {
                        "user_id": {"type": "keyword"},
                        "username": {
                            "type": "text",
                            "fields": {"keyword": {"type": "keyword"}}
                        },
                        "name": {"type": "text"},
                        "surname": {"type": "text"},
                        "email": {"type": "keyword"}
                    }
                }
            }
            if es.client:
                await es.client.indices.create(index="users", body=users_mapping)
                logger.info("Created 'users' index in Elasticsearch")
        
        if action == "delete":
            await es.delete_document(index="users", doc_id=user_id)
            logger.info(f"Deleted user {user_id} from Elasticsearch")
        elif action == "index" and user_data:
            es_doc = _prepare_user_for_es(user_data)
            await es.index_document(index="users", doc_id=user_id, document=es_doc)
            logger.info(f"Indexed user {user_id} to Elasticsearch")
        else:
            logger.warning(f"Invalid action '{action}' or missing user_data for user {user_id}")
            
    except Exception as e:
        logger.error(f"Failed to sync user {user_id} to Elasticsearch: {e}")
        # Don't raise - we don't want ES failures to break the main operation
