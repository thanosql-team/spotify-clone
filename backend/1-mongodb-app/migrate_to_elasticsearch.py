"""
MongoDB to Elasticsearch Migration Script

This script migrates data from MongoDB collections to Elasticsearch indexes.
It handles the following collections:
- songs
- albums
- playlists
- users
"""

import asyncio
import logging
from typing import List, Dict, Any
from bson import ObjectId

from .dependencies import db
from .dependencies_elasticsearch import init_elasticsearch, close_elasticsearch, get_elasticsearch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def convert_objectid_to_str(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB ObjectId to string for Elasticsearch"""
    if doc is None:
        return None
    
    doc_copy = doc.copy()
    
    # Convert _id to string
    if "_id" in doc_copy:
        doc_copy["_id"] = str(doc_copy["_id"])
    
    # Convert any other ObjectId fields
    for key, value in doc_copy.items():
        if isinstance(value, ObjectId):
            doc_copy[key] = str(value)
        elif isinstance(value, list):
            doc_copy[key] = [
                str(item) if isinstance(item, ObjectId) else item
                for item in value
            ]
    
    return doc_copy


async def migrate_songs():
    """Migrate songs collection from MongoDB to Elasticsearch"""
    logger.info("Starting songs migration...")
    
    songs_collection = db.get_collection("songs")
    total_songs = await songs_collection.count_documents({})
    logger.info(f"Found {total_songs} songs to migrate")
    
    if total_songs == 0:
        logger.warning("No songs found in MongoDB")
        return
    
    # Fetch all songs
    songs_cursor = songs_collection.find()
    songs = await songs_cursor.to_list(length=None)
    
    # Convert ObjectIds to strings
    songs_for_es = []
    for song in songs:
        song_es = convert_objectid_to_str(song)
        # Map to Elasticsearch schema
        es_doc = {
            "_id": song_es["_id"],
            "song_id": song_es["_id"],
            "name": song_es.get("name", ""),
            "artist": song_es.get("artist", ""),
            "genre": song_es.get("genre", ""),
            "album_name": song_es.get("album_name", ""),
            "release_year": song_es.get("release_year"),
            "duration": song_es.get("duration")
        }
        songs_for_es.append(es_doc)
    
    # Bulk index to Elasticsearch
    es = await get_elasticsearch()
    await es.bulk_index("songs", songs_for_es)
    logger.info(f"✓ Successfully migrated {len(songs_for_es)} songs to Elasticsearch")


async def migrate_albums():
    """Migrate albums collection from MongoDB to Elasticsearch"""
    logger.info("Starting albums migration...")
    
    albums_collection = db.get_collection("albums")
    total_albums = await albums_collection.count_documents({})
    logger.info(f"Found {total_albums} albums to migrate")
    
    if total_albums == 0:
        logger.warning("No albums found in MongoDB")
        return
    
    # Fetch all albums
    albums_cursor = albums_collection.find()
    albums = await albums_cursor.to_list(length=None)
    
    # Convert ObjectIds to strings
    albums_for_es = []
    for album in albums:
        album_es = convert_objectid_to_str(album)
        # Map to Elasticsearch schema
        es_doc = {
            "_id": album_es["_id"],
            "album_id": album_es["_id"],
            "album_name": album_es.get("album_name", album_es.get("name", "")),
            "artist_name": album_es.get("artist_name", album_es.get("artist", "")),
            "release_year": album_es.get("release_year")
        }
        albums_for_es.append(es_doc)
    
    # Bulk index to Elasticsearch
    es = await get_elasticsearch()
    await es.bulk_index("albums", albums_for_es)
    logger.info(f"✓ Successfully migrated {len(albums_for_es)} albums to Elasticsearch")


async def migrate_playlists():
    """Migrate playlists collection from MongoDB to Elasticsearch"""
    logger.info("Starting playlists migration...")
    
    playlists_collection = db.get_collection("playlists")
    total_playlists = await playlists_collection.count_documents({})
    logger.info(f"Found {total_playlists} playlists to migrate")
    
    if total_playlists == 0:
        logger.warning("No playlists found in MongoDB")
        return
    
    # Fetch all playlists
    playlists_cursor = playlists_collection.find()
    playlists = await playlists_cursor.to_list(length=None)
    
    # Convert ObjectIds to strings
    playlists_for_es = []
    for playlist in playlists:
        playlist_es = convert_objectid_to_str(playlist)
        # Map to Elasticsearch schema
        es_doc = {
            "_id": playlist_es["_id"],
            "playlist_id": playlist_es["_id"],
            "playlist_name": playlist_es.get("playlistname", playlist_es.get("name", "")),
            "user_id": playlist_es.get("user_id", ""),
            "song_count": playlist_es.get("song_count", len(playlist_es.get("songs", [])))
        }
        playlists_for_es.append(es_doc)
    
    # Bulk index to Elasticsearch
    es = await get_elasticsearch()
    await es.bulk_index("playlists", playlists_for_es)
    logger.info(f"✓ Successfully migrated {len(playlists_for_es)} playlists to Elasticsearch")


async def migrate_users():
    """Migrate users collection from MongoDB to Elasticsearch (optional)"""
    logger.info("Starting users migration...")
    
    users_collection = db.get_collection("users")
    total_users = await users_collection.count_documents({})
    logger.info(f"Found {total_users} users to migrate")
    
    if total_users == 0:
        logger.warning("No users found in MongoDB")
        return
    
    # Check if users index exists, if not create it
    es = await get_elasticsearch()
    if not await es.client.indices.exists(index="users"):
        users_mapping = {
            "mappings": {
                "properties": {
                    "user_id": {"type": "keyword"},
                    "email": {"type": "keyword"},
                    "username": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "name": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "surname": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword"}}
                    }
                }
            }
        }
        await es.client.indices.create(index="users", body=users_mapping)
        logger.info("Created 'users' index")
    
    # Fetch all users
    users_cursor = users_collection.find()
    users = await users_cursor.to_list(length=None)
    
    # Convert ObjectIds to strings
    users_for_es = []
    for user in users:
        user_es = convert_objectid_to_str(user)
        # Map to Elasticsearch schema
        es_doc = {
            "_id": user_es["_id"],
            "user_id": user_es["_id"],
            "username": user_es.get("username", ""),
            "email": user_es.get("email", ""),
            "name": user_es.get("name", ""),
            "surname": user_es.get("surname", "")
        }
        users_for_es.append(es_doc)
    
    # Bulk index to Elasticsearch
    await es.bulk_index("users", users_for_es)
    logger.info(f"✓ Successfully migrated {len(users_for_es)} users to Elasticsearch")


async def verify_migration():
    """Verify the migration by checking document counts"""
    logger.info("\n=== Verifying Migration ===")
    
    # Give Elasticsearch a moment to refresh indexes
    await asyncio.sleep(1)
    
    es = await get_elasticsearch()
    
    collections = ["songs", "albums", "playlists", "users"]
    
    for collection_name in collections:
        # MongoDB count
        mongo_collection = db.get_collection(collection_name)
        mongo_count = await mongo_collection.count_documents({})
        
        # Elasticsearch count
        try:
            # Force refresh the index to make sure documents are searchable
            await es.client.indices.refresh(index=collection_name)
            es_result = await es.client.count(index=collection_name)
            es_count = es_result["count"]
            
            status = "✓" if mongo_count == es_count else "✗"
            logger.info(f"{status} {collection_name}: MongoDB={mongo_count}, Elasticsearch={es_count}")
        except Exception as e:
            logger.warning(f"Could not count {collection_name} in Elasticsearch: {e}")


async def main():
    """Main migration function"""
    try:
        logger.info("=" * 60)
        logger.info("MongoDB to Elasticsearch Migration")
        logger.info("=" * 60)
        
        # Initialize Elasticsearch
        logger.info("Initializing Elasticsearch connection...")
        await init_elasticsearch()
        logger.info("✓ Elasticsearch connected\n")
        
        # Run migrations
        await migrate_songs()
        await migrate_albums()
        await migrate_playlists()
        await migrate_users()
        
        # Verify migration
        await verify_migration()
        
        logger.info("\n" + "=" * 60)
        logger.info("Migration completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        raise
    finally:
        # Cleanup
        await close_elasticsearch()
        logger.info("Connections closed")


if __name__ == "__main__":
    asyncio.run(main())
