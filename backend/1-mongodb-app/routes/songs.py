from fastapi import APIRouter, Body, HTTPException, status
from fastapi.responses import Response
from pydantic import ConfigDict, BaseModel, Field
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated

from bson import ObjectId
from pymongo import ReturnDocument

from ..dependencies import db, cache_manager, get_settings

router = APIRouter(
    prefix="/songs",
    tags=["songs"],
    responses={404: {"description": "Not found"}}
)

song_collection = db.get_collection("songs")

PyObjectId = Annotated[str, BeforeValidator(str)]
class SongModel(BaseModel):
    """
    Container for a single song record.
    """
    # The primary key for the SongModel, stored as a str on the instance.
    # This will be aliased to _id when sent to MongoDB,
    # but provided as id in the API requests and responses.
    id: PyObjectId | None = Field(alias="_id", default=None)
    name: str = Field(...)
    artist: str = Field(...)
    genre: str = Field(...)
    release_year: int = Field(...)
    duration: int = Field(..., description="Song duration in seconds")
    album_name: str | None = Field(default=None)
    album_ID: PyObjectId | None = Field(default=None)
    playlist_name: str | None = Field(default=None)
    playlist_ID: PyObjectId | None = Field(default=None)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "name": "Meiles Daina",
                "artist": "Jane Doe",
                "genre": "Rock",
                "release_year": 2025,
                "duration": 210,
                "album_name": "Metalica",
                "album_ID": "652e9f3b9b1d8e77a9b5d333",
                "playlist_name": "Favourite songs",
                "playlist_ID": "652e9f3b9b1d8e77a9b5d444"
            }
        },
    )
    
class UpdateSongModel(BaseModel):
    """
    A set of optional updates to be made to a document in the database.
    """
    name: str | None = None
    artist: str | None = None
    genre: str | None = None
    release_year: int | None = None
    duration: int | None = None
    album_name: str | None = None
    album_ID: PyObjectId | None = None
    playlist_name: str | None = None
    playlist_ID: PyObjectId | None = None
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "name": "Meiles Daina",
                "artist": "Jane Doe",
                "genre": "Rock",
                "release_year": 2025,
                "duration": 210,
                "album_name": "Metalica",
                "album_ID": "652e9f3b9b1d8e77a9b5d333",
                "playlist_name": "Favourite songs",
                "playlist_ID": "652e9f3b9b1d8e77a9b5d444"
            }
        },
    )

class SongCollection(BaseModel):

    songs: list[SongModel]

@router.post(
    "/",
    response_description="Add new song",
    response_model=SongModel,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def create_song(song: SongModel = Body(...)):
    """
    Insert a new song record.
    A unique ``id`` will be created and provided in the response.
    - Invalidates artist aggregation cache when new song is created
    """
    new_song = song.model_dump(by_alias=True, exclude=["id"]) # type: ignore

    # Convert linked IDs to ObjectId
    if new_song.get("album_ID"):
        new_song["album_ID"] = ObjectId(new_song["album_ID"])
    if new_song.get("playlist_ID"):
        new_song["playlist_ID"] = ObjectId(new_song["playlist_ID"])

    result = await song_collection.insert_one(new_song)
    new_song["_id"] = result.inserted_id
    
    # Invalidate aggregation caches
    await cache_manager.invalidate_song_cache(str(result.inserted_id))
    
    return new_song

@router.get(
    "/",
    response_description="List all songs",
    response_model=SongCollection,
    response_model_by_alias=False,
)
async def list_songs():
    """
    List all the song data in the database.
    The response is unpaginated and limited to 1000 results.
    - Reduces database load for frequent list requests
    - Invalidated on: create, update, delete song
    """
    cache_key = "list:songs"
    settings = get_settings()
    
    # Try to get from cache first
    cached = await cache_manager.get_cache(cache_key)
    if cached is not None:
        return SongCollection(songs=cached)
    
    # Cache miss - fetch from DB
    songs = await song_collection.find().to_list(1000)
    result = SongCollection(songs=songs)
    
    # Store in cache with TTL
    await cache_manager.set_cache(
        cache_key,
        result.model_dump()["songs"],
        ttl=settings.cache_ttl_list
    )
    
    return result

@router.get(
    "/artists",
    response_description="Get all artists with their songs listed underneath"
)
async def get_all_artists():
    """
    Return all artists and their songs (artist name on top, songs listed below).
    Uses MongoDB aggregation (server-side) and safely serializes ObjectIds.
    - Invalidated on: any song create/update/delete
    """
    cache_key = "aggregation:artists"
    settings = get_settings()
    
    # Try cache first
    cached = await cache_manager.get_cache(cache_key)
    if cached is not None:
        return cached
    
    pipeline = [
        # Sort by artist name alphabetically
        {"$sort": {"artist": 1}},
        # Group songs under each artist
        {
            "$group": {
                "_id": "$artist",
                "songs": {
                    "$push": {
                        "song_id": "$_id",
                        "name": "$name",
                        "duration": "$duration",
                        "genre": "$genre",
                        "album_name": "$album_name",
                        "release_year": "$release_year"
                    }
                }
            }
        },
        # Project artist name to top-level key for clean output
        {
            "$project": {
                "_id": 0,
                "artist": "$_id",
                "songs": 1
            }
        },
        # Sort artists alphabetically again (optional)
        {"$sort": {"artist": 1}}
    ]

    try:
        cursor = song_collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)

        # Convert ObjectIds to strings for FastAPI serialization
        for artist_doc in results:
            for song in artist_doc.get("songs", []):
                if isinstance(song.get("song_id"), ObjectId):
                    song["song_id"] = str(song["song_id"])

        # Cache the result
        await cache_manager.set_cache(
            cache_key,
            results,
            ttl=settings.cache_ttl_aggregation
        )
        
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Aggregation error: {str(e)}")


@router.get(
    "/{id}",
    response_description="Get a single song",
    response_model=SongModel,
    response_model_by_alias=False,
)
async def show_song(id: str):
    """
    Get the record for a specific song, looked up by id.
    - Single item queries cached for half an hour
    """
    cache_key = f"song:{id}"
    settings = get_settings()
    
    # Try cache first
    cached = await cache_manager.get_cache(cache_key)
    if cached is not None:
        song = cached
    else:
        song = await song_collection.find_one({"_id": ObjectId(id)})
        if song is None:
            raise HTTPException(status_code=404, detail=f"Song {id} not found")
        
        # Cache the result
        await cache_manager.set_cache(
            cache_key,
            song,
            ttl=settings.cache_ttl_single
        )

    # Convert ObjectIds to strings for response
    song["_id"] = str(song["_id"])
    if "album_ID" in song and song["album_ID"]:
        song["album_ID"] = str(song["album_ID"])
    if "playlist_ID" in song and song["playlist_ID"]:
        song["playlist_ID"] = str(song["playlist_ID"])

    return song

@router.put(
    "/{id}",
    response_description="Update a song",
    response_model=SongModel,
    response_model_by_alias=False,
)
async def update_song(id: str, song: UpdateSongModel = Body(...)):
    """
    Update individual fields of an existing song record.
    Only the provided fields will be updated.
    Any missing or `null` fields will be ignored.
    - Invalidates aggregations and single song cache
    """
    song = {
        k: v for k, v in song.model_dump(by_alias=True).items() if v is not None # type: ignore
    }

    # Convert IDs to ObjectId before updating
    if "album_ID" in song:
        song["album_ID"] = ObjectId(song["album_ID"])
    if "playlist_ID" in song:
        song["playlist_ID"] = ObjectId(song["playlist_ID"])

    if len(song) >= 1: # type: ignore
        update_result = await song_collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": song},
            return_document=ReturnDocument.AFTER,
        )
        if update_result is not None:
            # Invalidate caches
            await cache_manager.invalidate_song_cache(id)
            
            return update_result
        else:
            raise HTTPException(status_code=404, detail=f"Song {id} not found")
    # The update is empty, so return the matching document:
    if (existing_song := await song_collection.find_one({"_id": ObjectId(id)})) is not None:
        return existing_song
    raise HTTPException(status_code=404, detail=f"Song {id} not found")

@router.delete("/{id}", response_description="Delete a Song")
async def delete_song(id: str):
    """
    Remove a single song record from the database.
    """
    delete_result = await song_collection.delete_one({"_id": ObjectId(id)})
    if delete_result.deleted_count == 1:
        # Invalidate caches
        await cache_manager.invalidate_song_cache(id)
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=404, detail=f"Song {id} not found")
