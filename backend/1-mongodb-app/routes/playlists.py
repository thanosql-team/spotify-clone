import os

from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import Response
from pydantic import ConfigDict, BaseModel, Field, EmailStr
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated

from bson import ObjectId
import asyncio
from pymongo import AsyncMongoClient
from pymongo import ReturnDocument

app = FastAPI()

# IMPORTANT: set a MONGODB_URL environment variable with value as your connection string to MongoDB
client = AsyncMongoClient(os.environ["MONGODB_URL"]) #,server_api=pymongo.server_api.ServerApi(version="1", strict=True,deprecation_errors=True))
db = client.get_database("spotify-clone")
playlist_collection = db.get_collection("playlists")

PyObjectId = Annotated[str, BeforeValidator(str)]
class PlaylistModel(BaseModel):
    """
    Container for a single playlist record.
    """
    # The primary key for the PlaylistModel, stored as a str on the instance.
    # This will be aliased to _id when sent to MongoDB,
    # but provided as id in the API requests and responses.
    id: PyObjectId | None = Field(alias="_id", default=None)
    user_id: PyObjectId | None = Field(default=None)
    playlistname: str = Field(...)
    song_count: int = Field(...)
    song_ID: list[int] = Field(default_factory=)
    song_name: str = Field(...)
    song_duration: int = Field(...)
    artist_ID: int = Field(...)
    artist_name: str = Field(...)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "playlistname": "Baitukas",
                "song_count": "67",
            }
        },
    )
    
class UpdatePlaylistModel(BaseModel):
    """
    A set of optional updates to be made to a document in the database.
    """
    
    playlistname: str | None = None
    name: str | None = None
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "playlistname": "Baitukas",
                "name": "Jane",
                "surname": "Doe",
                "email": "jdoe@example.com",
            }
        },
    )

class PlaylistCollection(BaseModel):

    playlists: list[PlaylistModel]

@app.post(
    "/playlists/",
    response_description="Add new playlist",
    response_model=PlaylistModel,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def create_playlist(playlist: PlaylistModel = Body(...)):
    """
    Insert a new playlist record.
    A unique ``id`` will be created and provided in the response.
    """
    new_playlist = playlist.model_dump(by_alias=True, exclude=["id"])
    result = await playlist_collection.insert_one(new_playlist)
    new_playlist["_id"] = result.inserted_id
    return new_playlist

@app.get(
    "/playlists/",
    response_description="List all playlists",
    response_model=PlaylistCollection,
    response_model_by_alias=False,
)
async def list_playlists():
    """
    List all the playlist data in the database.
    The response is unpaginated and limited to 1000 results.
    """
    return PlaylistCollection(playlists=await playlist_collection.find().to_list(1000))

@app.get(
    "/playlists/{id}",
    response_description="Get a single playlist",
    response_model=PlaylistModel,
    response_model_by_alias=False,
)
async def show_playlist(id: str):
    """
    Get the record for a specific playlist, looked up by id.
    """
    if (
        playlist := await playlist_collection.find_one({"_id": ObjectId(id)})
    ) is not None:
        return playlist
    raise HTTPException(status_code=404, detail="Playlist {id} not found")

@app.put(
    "/playlists/{id}",
    response_description="Update a playlist",
    response_model=PlaylistModel,
    response_model_by_alias=False,
)
async def update_playlist(id: str, playlist: UpdatePlaylistModel = Body(...)):
    """
    Update individual fields of an existing playlist record.
    Only the provided fields will be updated.
    Any missing or `null` fields will be ignored.
    """
    playlist = {
        k: v for k, v in playlist.model_dump(by_alias=True).items() if v is not None
    }
    if len(playlist) >= 1:
        update_result = await playlist_collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": playlist},
            return_document=ReturnDocument.AFTER,
        )
        if update_result is not None:
            return update_result
        else:
            raise HTTPException(status_code=404, detail=f"Playlist {id} not found")
    # The update is empty, so return the matching document:
    if (existing_playlist := await playlist_collection.find_one({"_id": ObjectId(id)})) is not None:
        return existing_playlist
    raise HTTPException(status_code=404, detail=f"Playlist {id} not found")

@app.delete("/playlists/{id}", response_description="Delete a Playlist")
async def delete_playlist(id: str):
    """
    Remove a single playlist record from the database.
    """
    delete_result = await playlist_collection.delete_one({"_id": ObjectId(id)})
    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=404, detail=f"Playlist {id} not found")