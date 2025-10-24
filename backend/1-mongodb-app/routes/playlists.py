from fastapi import APIRouter, Body, HTTPException, status
from fastapi.responses import Response
from pydantic import ConfigDict, BaseModel, Field
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated

from bson import ObjectId
from pymongo import ReturnDocument

from ..dependencies import db, cache_manager, get_settings

router = APIRouter(
    prefix="/playlists",
    tags=["playlists"],
    responses={404: {"description": "Not found"}}
)

playlist_collection = db.get_collection("playlists")

PyObjectId = Annotated[str, BeforeValidator(str)]
class PlaylistModel(BaseModel):
    """
    Container for a single playlist record.
    """
    id: PyObjectId | None = Field(alias="_id", default=None)
    user_id: PyObjectId | None = Field(default=None)
    playlistname: str = Field(...)
    song_count: int = Field(default=0)
    song_ID: list[PyObjectId] = Field(default_factory=list)
    song_name: list[str] = Field(default_factory=list)
    song_duration: list[int] = Field(default_factory=list)
    # artist_ID: list[PyObjectId] = Field(default_factory=list)
    artist_name: list[str] = Field(default_factory=list)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "user_id": "652e9f3b9b1d8e77a9b5d222",
                "playlistname": "Baitukas",
                "song_count": 2,
                "song_ID": ["652e9f3b9b1d8e77a9b5d223", "652e9f3b9b1d8e77a9b5d224"],
                # "artist_ID": ["652e9f3b9b1d8e77a9b5d111"],
                "song_name": ["Track 1", "Track 2"],
                "song_duration": [210, 185],
                "artist_name": ["Artist One"]
            }
        },
    )
    
class UpdatePlaylistModel(BaseModel):
    """
    A set of optional updates to be made to a document in the database.
    """
    user_id: PyObjectId | None = None
    playlistname: str | None = None
    song_count: int | None = None
    song_ID: list[PyObjectId] | None = None
    song_name: list[str] | None = None
    song_duration: list[int] | None = None
    # artist_ID: list[PyObjectId] | None = None
    artist_name: list[str] | None = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "user_id": "652e9f3b9b1d8e77a9b5d222",
                "playlistname": "Baitukas",
                "song_count": 2,
                "song_ID": ["652e9f3b9b1d8e77a9b5d223", "652e9f3b9b1d8e77a9b5d224"],
                # "artist_ID": ["652e9f3b9b1d8e77a9b5d111"],
                "song_name": ["Track 1", "Track 2"],
                "song_duration": [210, 185],
                "artist_name": ["Artist One"]
            }
        },
    )


class PlaylistCollection(BaseModel):

    playlists: list[PlaylistModel]

@router.post(
    "/",
    response_description="Add new playlist",
    response_model=PlaylistModel,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def create_playlist(playlist: PlaylistModel = Body(...)):
    """
    Insert a new playlist record.
    A unique ``id`` will be created and provided in the response.
    
    ⚡ Cache Strategy: Active invalidation
    - Invalidates playlist aggregations when new playlist created
    """
    new_playlist = playlist.model_dump(by_alias=True, exclude=["id"]) # type: ignore
    
    # Convert linked ID fields to ObjectIds
    if new_playlist.get("user_id"):
        new_playlist["user_id"] = ObjectId(new_playlist["user_id"])
    if new_playlist.get("song_ID"):
        new_playlist["song_ID"] = [ObjectId(s) for s in new_playlist["song_ID"]]
    if new_playlist.get("artist_ID"):
        new_playlist["artist_ID"] = [ObjectId(a) for a in new_playlist["artist_ID"]]

    result = await playlist_collection.insert_one(new_playlist)
    new_playlist["_id"] = result.inserted_id
    
    # ⚡ Invalidate caches
    await cache_manager.invalidate_aggregations()
    
    return new_playlist

@router.get(
    "/",
    response_description="List all playlists",
    response_model=PlaylistCollection,
    response_model_by_alias=False,
)
async def list_playlists():
    """
    List all the playlist data in the database.
    The response is unpaginated and limited to 1000 results.
    - Invalidated on: create, update, delete playlist (5mins)
    """
    cache_key = "list:playlists"
    settings = get_settings()
    
    # Try to get from cache first
    cached = await cache_manager.get_cache(cache_key)
    if cached is not None:
        return PlaylistCollection(playlists=cached)
    
    # Cache miss - fetch from DB
    playlists = await playlist_collection.find().to_list(1000)
    result = PlaylistCollection(playlists=playlists)
    
    # Store in cache with TTL
    await cache_manager.set_cache(
        cache_key,
        result.model_dump()["playlists"],
        ttl=settings.cache_ttl_list
    )
    
    return result

@router.get(
    "/{id}",
    response_description="Get a single playlist",
    response_model=PlaylistModel,
    response_model_by_alias=False,
)
async def show_playlist(id: str):
    """
    Get the record for a specific playlist, looked up by id.
    - Single item queries cached for half an hour
    """
    cache_key = f"playlist:{id}"
    settings = get_settings()
    
    # Try cache first
    cached = await cache_manager.get_cache(cache_key)
    if cached is not None:
        playlist = cached
    else:
        playlist = await playlist_collection.find_one({"_id": ObjectId(id)})
        if playlist is None:
            raise HTTPException(status_code=404, detail=f"Playlist {id} not found")
        
        # Cache the result
        await cache_manager.set_cache(
            cache_key,
            playlist,
            ttl=settings.cache_ttl_single
        )

    # Convert ObjectIds to strings
    playlist["_id"] = str(playlist["_id"])
    if "user_id" in playlist:
        playlist["user_id"] = str(playlist["user_id"])
    if "song_ID" in playlist:
        playlist["song_ID"] = [str(s) for s in playlist["song_ID"]]
    if "artist_ID" in playlist:
        playlist["artist_ID"] = [str(a) for a in playlist["artist_ID"]]

    return playlist

@router.put(
    "/{id}",
    response_description="Update a playlist",
    response_model=PlaylistModel,
    response_model_by_alias=False,
)
async def update_playlist(id: str, playlist: UpdatePlaylistModel = Body(...)):
    """
    Update individual fields of an existing playlist record.
    Only the provided fields will be updated.
    Any missing or `null` fields will be ignored.
    - Invalidates specific playlist cache and aggregations
    """
    playlist = {
        k: v for k, v in playlist.model_dump(by_alias=True).items() if v is not None # type: ignore
    }
    
    # Convert IDs to ObjectId before updating
    if "user_id" in playlist:
        playlist["user_id"] = ObjectId(playlist["user_id"])
    if "song_ID" in playlist:
        playlist["song_ID"] = [ObjectId(s) for s in playlist["song_ID"]]
    if "artist_ID" in playlist:
        playlist["artist_ID"] = [ObjectId(a) for a in playlist["artist_ID"]]
        
    if len(playlist) >= 1: # type: ignore
        update_result = await playlist_collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": playlist},
            return_document=ReturnDocument.AFTER,
        )
        if update_result is not None:
            # Invalidate caches
            await cache_manager.invalidate_playlist_cache(id)
            
            return update_result
        else:
            raise HTTPException(status_code=404, detail=f"Playlist {id} not found")
    # The update is empty, so return the matching document:
    if (existing_playlist := await playlist_collection.find_one({"_id": ObjectId(id)})) is not None:
        return existing_playlist
    raise HTTPException(status_code=404, detail=f"Playlist {id} not found")

@router.delete("/{id}", response_description="Delete a Playlist")
async def delete_playlist(id: str):
    """
    Remove a single playlist record from the database.
    - Invalidates all related caches
    """
    delete_result = await playlist_collection.delete_one({"_id": ObjectId(id)})
    if delete_result.deleted_count == 1:
        # Invalidate caches
        await cache_manager.invalidate_playlist_cache(id)
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=404, detail=f"Playlist {id} not found")