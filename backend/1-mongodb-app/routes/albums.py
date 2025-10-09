# TODO: Refactor based on how users.py is done based on entities.txt

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

router = APIRouter(
    prefix="/albums",
    tags=["albums"],
    responses={404: {"description": "Not found"}}
)

album_collection = db.get_collection("albums")

PyObjectId = Annotated[str, BeforeValidator(str)]
class AlbumModel(BaseModel):
    """
    Container for a single album record.
    """
    id: PyObjectId = Field(alias="_id", default=None)
    user_id: PyObjectId = Field(default=None, description="Owner of the album")
    album_name: str = Field(...)
    artist_name: str = Field(...)
    release_year: int = Field(...)
    song_IDs: list[PyObjectId] = Field(default_factory=list)
    song_names: list[str] = Field(default_factory=list)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "user_id": "652e9f3b9b1d8e77a9b5d222",
                "album_name": "Metallica: Reloaded",
                "artist_name": "Metallica",
                "release_year": 2025,
                "song_IDs": ["652e9f3b9b1d8e77a9b5d333", "652e9f3b9b1d8e77a9b5d334"],
                "song_names": ["Fuel", "The Memory Remains"]
            }
        },
    )

class UpdateAlbumModel(BaseModel):
    """
    A set of optional updates to be made to a document in the database.
    """
    user_id: PyObjectId | None = None
    album_name: str | None = None
    artist_name: str | None = None
    genre: str | None = None
    release_year: int | None = None
    song_IDs: list[PyObjectId] | None = None
    song_names: list[str] | None = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "album_name": "Metallica: Reloaded (Remastered)",
                "artist_name": "Metallica",
                "genre": "Heavy Metal",
                "release_year": 2026,
                "song_IDs": ["652e9f3b9b1d8e77a9b5d333", "652e9f3b9b1d8e77a9b5d334"],
                "song_names": ["Fuel", "The Memory Remains"]
            }
        },
    )

class AlbumCollection(BaseModel):

    albums: list[AlbumModel]

@router.post(
    "/",
    response_description="Add new album",
    response_model=AlbumModel,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def create_album(album: AlbumModel = Body(...)):
    """
    Insert a new album record.
    A unique ``id`` will be created and provided in the response.
    """
    new_album = album.model_dump(by_alias=True, exclude=["id"])
    
    if new_album.get("user_id"):
        new_album["user_id"] = ObjectId(new_album["user_id"])
    if new_album.get("song_IDs"):
        new_album["song_IDs"] = [ObjectId(s) for s in new_album["song_IDs"]]
        
    result = await album_collection.insert_one(new_album)
    new_album["_id"] = result.inserted_id
    return new_album

@router.get(
    "/",
    response_description="List all Albums",
    response_model=AlbumCollection,
    response_model_by_alias=False,
)
async def list_albums():
    """
    List all the album data in the database.
    The response is unpaginated and limited to 1000 results.
    """
    return AlbumCollection(albums=await album_collection.find().to_list(1000))

@router.get(
    "/{id}",
    response_description="Get a single album",
    response_model=AlbumModel,
    response_model_by_alias=False,
)
async def show_album(id: str):
    """
    Get the record for a specific album, looked up by id.
    """
    album = await album_collection.find_one({"_id": ObjectId(id)})
    if album is None:
        raise HTTPException(status_code=404, detail=f"Album {id} not found")

    # Convert ObjectIds to strings
    album["_id"] = str(album["_id"])
    if "user_id" in album and album["user_id"]:
        album["user_id"] = str(album["user_id"])
    if "song_IDs" in album:
        album["song_IDs"] = [str(s) for s in album["song_IDs"]]

    return album

@router.put(
    "/{id}",
    response_description="Update an album",
    response_model=AlbumModel,
    response_model_by_alias=False,
)
async def update_album(id: str, album: UpdateAlbumModel = Body(...)):
    """
    Update individual fields of an existing album record.
    Only the provided fields will be updated.
    Any missing or `null` fields will be ignored.
    """
    album = {
        k: v for k, v in album.model_dump(by_alias=True).items() if v is not None
    }
    
    # Convert linked IDs
    if "user_id" in album:
        album["user_id"] = ObjectId(album["user_id"])
    if "song_IDs" in album:
        album["song_IDs"] = [ObjectId(s) for s in album["song_IDs"]]

    if len(album) >= 1:
        update_result = await album_collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": album},
            return_document=ReturnDocument.AFTER,
        )
        if update_result is not None:
            return update_result
        else:
            raise HTTPException(status_code=404, detail=f"Album {id} not found")
    # The update is empty, so return the matching document:
    if (existing_album := await album_collection.find_one({"_id": ObjectId(id)})) is not None:
        return existing_album
    raise HTTPException(status_code=404, detail=f"Album {id} not found")

@router.delete("/{id}", response_description="Delete an Album")
async def delete_album(id: str):
    """
    Remove a single album record from the database.
    """
    delete_result = await album_collection.delete_one({"_id": ObjectId(id)})
    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=404, detail=f"Album {id} not found")
