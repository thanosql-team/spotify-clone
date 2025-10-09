from fastapi import APIRouter, Body, HTTPException, status
from fastapi.responses import Response
from pydantic import ConfigDict, BaseModel, Field, EmailStr
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated

from bson import ObjectId
import asyncio
from pymongo import ReturnDocument

from .. import dependencies

db = dependencies.db

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
    release_year: str = Field(...)
    duration: int = Field(..., description="Song duration in seconds")
    album_name: str = Field(default=None)
    album_ID: PyObjectId = Field(default=None)
    playlist_name: str = Field(default=None)
    playlist_ID: PyObjectId = Field(default=None)
    
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
    """
    new_song = song.model_dump(by_alias=True, exclude=["id"])

    # Convert linked IDs to ObjectId
    if new_song.get("album_ID"):
        new_song["album_ID"] = ObjectId(new_song["album_ID"])
    if new_song.get("playlist_ID"):
        new_song["playlist_ID"] = ObjectId(new_song["playlist_ID"])

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
    List all the song data in the database.
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
    Get the record for a specific song, looked up by id.
    """
    song = await song_collection.find_one({"_id": ObjectId(id)})
    if song is None:
        raise HTTPException(status_code=404, detail=f"Song {id} not found")

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
async def update_song(id: str, s: UpdateSongModel = Body(...)):
    """
    Update individual fields of an existing song record.
    Only the provided fields will be updated.
    Any missing or `null` fields will be ignored.
    """
    song = {
        k: v for k, v in song.model_dump(by_alias=True).items() if v is not None
    }

    # Convert IDs to ObjectId before updating
    if "album_ID" in song:
        song["album_ID"] = ObjectId(song["album_ID"])
    if "playlist_ID" in song:
        song["playlist_ID"] = ObjectId(song["playlist_ID"])

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