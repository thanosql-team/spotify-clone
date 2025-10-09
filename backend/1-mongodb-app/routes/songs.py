import os

from fastapi import APIRouter, Body, HTTPException, status
from fastapi.responses import Response
from pydantic import ConfigDict, BaseModel, Field, EmailStr
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated

from bson import ObjectId
import asyncio
from pymongo import AsyncMongoClient
from pymongo import ReturnDocument

from config import settings

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
    # The primary key for the UserModel, stored as a str on the instance.
    # This will be aliased to _id when sent to MongoDB,
    # but provided as id in the API requests and responses.
    id: PyObjectId | None = Field(alias="_id", default=None)
    name: str = Field(...)
    artist: str = Field(...)
    genre: str = Field(...)
    release_year: EmailStr = Field(...)
    duration: str = Field(...)
    album_name: str = Field(...)
    album_ID: str = Field(...)
    # playlist_name: str = Field(...)
    # playlist_ID: str = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "name": "Meiles Daina",
                "artist": "Jane Doe",
                "release_year": "2025",
                "duration (seconds)": "70",
                "album_name": "Metalica",
                "album_ID": "album_ID",
                "playlist_name": "Favourite songs",
                "playlist_ID": "playlist_ID"
            }
        },
    )
    
class UpdateSongModel(BaseModel):
    """
    A set of optional updates to be made to a document in the database.
    """
    name: str | None = None
    artist: str | None = None
    release_year: str | None = None
    duration: str | None = None
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
                "release_year": "2025",
                "duration (seconds)": "70",
                "album_name": "Metalica",
                "album_ID": "album_ID",
                "playlist_name": "Favourite songs",
                "playlist_ID": "playlist_ID"
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
    Insert a new user record.
    A unique ``id`` will be created and provided in the response.
    """
    new_song = song.model_dump(by_alias=True, exclude=["id"])
    result = await song_collection.insert_one(new_song)
    new_song["_id"] = result.inserted_id
    return new_song

@router.get(
    "/",
    response_description="List all songs",
    response_model=SongCollection,
    response_model_by_alias=False,
)
async def list_songs():
    """
    List all the user data in the database.
    The response is unpaginated and limited to 1000 results.
    """
    return SongCollection(songs=await song_collection.find().to_list(1000))

@router.get(
    "/{id}",
    response_description="Get a single song",
    response_model=SongModel,
    response_model_by_alias=False,
)
async def show_song(id: str):
    """
    Get the record for a specific user, looked up by id.
    """
    if (
        song := await song_collection.find_one({"_id": ObjectId(id)})
    ) is not None:
        return song
    raise HTTPException(status_code=404, detail="Song {id} not found")

@router.put(
    "/{id}",
    response_description="Update a song",
    response_model=SongModel,
    response_model_by_alias=False,
)
async def update_song(id: str, s: UpdateSongModel = Body(...)):
    """
    Update individual fields of an existing song record.
    Only the provided fields will be updated.
    Any missing or `null` fields will be ignored.
    """
    song = {
        k: v for k, v in song.model_dump(by_alias=True).items() if v is not None
    }
    if len(song) >= 1:
        update_result = await song_collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": song},
            return_document=ReturnDocument.AFTER,
        )
        if update_result is not None:
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
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=404, detail=f"Song {id} not found")