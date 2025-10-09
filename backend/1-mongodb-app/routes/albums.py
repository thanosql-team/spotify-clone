# TODO: Refactor based on how users.py is done based on entities.txt

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
user_collection = db.get_collection("users")

PyObjectId = Annotated[str, BeforeValidator(str)]
class UserModel(BaseModel):
    """
    Container for a single user record.
    """
    # The primary key for the UserModel, stored as a str on the instance.
    # This will be aliased to _id when sent to MongoDB,
    # but provided as id in the API requests and responses.
    id: PyObjectId | None = Field(alias="_id", default=None)
    username: str = Field(...)
    name: str = Field(...)
    surname: str = Field(...)
    email: EmailStr = Field(...)
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "username": "Baitukas",
                "name": "Jane",
                "surname": "Doe",
                "email": "jdoe@example.com",
            }
        },
    )
    
class UpdateUserModel(BaseModel):
    """
    A set of optional updates to be made to a document in the database.
    """
    username: str | None = None
    name: str | None = None
    surname: str | None = None
    email: EmailStr | None = None
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "username": "Baitukas",
                "name": "Jane",
                "surname": "Doe",
                "email": "jdoe@example.com",
            }
        },
    )

class UserCollection(BaseModel):

    users: list[UserModel]

@app.post(
    "/users/",
    response_description="Add new user",
    response_model=UserModel,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def create_user(user: UserModel = Body(...)):
    """
    Insert a new user record.
    A unique ``id`` will be created and provided in the response.
    """
    new_user = user.model_dump(by_alias=True, exclude=["id"])
    result = await user_collection.insert_one(new_user)
    new_user["_id"] = result.inserted_id
    return new_user

@app.get(
    "/users/",
    response_description="List all users",
    response_model=UserCollection,
    response_model_by_alias=False,
)
async def list_users():
    """
    List all the user data in the database.
    The response is unpaginated and limited to 1000 results.
    """
    return UserCollection(users=await user_collection.find().to_list(1000))

@app.get(
    "/users/{id}",
    response_description="Get a single user",
    response_model=UserModel,
    response_model_by_alias=False,
)
async def show_user(id: str):
    """
    Get the record for a specific user, looked up by id.
    """
    if (
        user := await user_collection.find_one({"_id": ObjectId(id)})
    ) is not None:
        return user
    raise HTTPException(status_code=404, detail="User {id} not found")

@app.put(
    "/users/{id}",
    response_description="Update a user",
    response_model=UserModel,
    response_model_by_alias=False,
)
async def update_user(id: str, user: UpdateUserModel = Body(...)):
    """
    Update individual fields of an existing user record.
    Only the provided fields will be updated.
    Any missing or `null` fields will be ignored.
    """
    user = {
        k: v for k, v in user.model_dump(by_alias=True).items() if v is not None
    }
    if len(user) >= 1:
        update_result = await user_collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": user},
            return_document=ReturnDocument.AFTER,
        )
        if update_result is not None:
            return update_result
        else:
            raise HTTPException(status_code=404, detail=f"User {id} not found")
    # The update is empty, so return the matching document:
    if (existing_user := await user_collection.find_one({"_id": ObjectId(id)})) is not None:
        return existing_user
    raise HTTPException(status_code=404, detail=f"User {id} not found")

@app.delete("/users/{id}", response_description="Delete a User")
async def delete_user(id: str):
    """
    Remove a single user record from the database.
    """
    delete_result = await user_collection.delete_one({"_id": ObjectId(id)})
    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=404, detail=f"User {id} not found")
