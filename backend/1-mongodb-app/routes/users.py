from fastapi import APIRouter, Body, HTTPException, status
from fastapi.responses import Response
from pydantic import ConfigDict, BaseModel, Field, EmailStr
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated

from bson import ObjectId
from pymongo import ReturnDocument

from ..dependencies import db, cache_manager, get_settings

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}}
)

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

@router.post(
    "/",
    response_description="Add new user",
    response_model=UserModel,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def create_user(user: UserModel = Body(...)):
    """
    Insert a new user record.
    A unique ``id`` will be created and provided in the response.
    - Invalidates list cache when new user created
    """
    new_user = user.model_dump(by_alias=True, exclude=["id"]) # type: ignore
    result = await user_collection.insert_one(new_user)
    new_user["_id"] = result.inserted_id
    # Invalidate list cache
    await cache_manager.delete_cache("list:users")
    
    return new_user

@router.get(
    "/",
    response_description="List all users",
    response_model=UserCollection,
    response_model_by_alias=False,
)
async def list_users():
    """
    List all the user data in the database.
    The response is unpaginated and limited to 1000 results.
    - Invalidated on: create, update, delete user
    """
    cache_key = "list:users"
    settings = get_settings()
    
    # Try to get from cache first
    cached = await cache_manager.get_cache(cache_key)
    if cached is not None:
        return UserCollection(users=cached)
    
    # Cache miss - fetch from DB
    users = await user_collection.find().to_list(1000)
    result = UserCollection(users=users)
    
    # Store in cache with TTL
    await cache_manager.set_cache(
        cache_key,
        result.model_dump()["users"],
        ttl=settings.cache_ttl_list
    )
    
    return result

@router.get(
    "/{id}",
    response_description="Get a single user",
    response_model=UserModel,
    response_model_by_alias=False,
)
async def show_user(id: str):
    """
    Get the record for a specific user, looked up by id.
    """
    cache_key = f"user:{id}"
    settings = get_settings()
    
    # Try cache first
    cached = await cache_manager.get_cache(cache_key)
    if cached is not None:
        return cached
    
    # Cache miss - fetch from DB
    if (user := await user_collection.find_one({"_id": ObjectId(id)})) is not None:
        # Cache the result
        await cache_manager.set_cache(
            cache_key,
            user,
            ttl=settings.cache_ttl_single
        )
        return user
    
    raise HTTPException(status_code=404, detail="User {id} not found")
    
@router.put(
    "/{id}",
    response_description="Update a user",
    response_model=UserModel,
    response_model_by_alias=False,
)
async def update_user(id: str, user: UpdateUserModel = Body(...)):
    """
    Update individual fields of an existing user record.
    Only the provided fields will be updated.
    Any missing or `null` fields will be ignored.
    - Invalidates user cache and list cache
    """
    user = {
        k: v for k, v in user.model_dump(by_alias=True).items() if v is not None # type: ignore
    }
    if len(user) >= 1: # type: ignore
        update_result = await user_collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": user},
            return_document=ReturnDocument.AFTER,
        )
        if update_result is not None:
            # Invalidate caches
            await cache_manager.delete_cache(f"user:{id}")
            await cache_manager.delete_cache("list:users")
            
            return update_result
        else:
            raise HTTPException(status_code=404, detail=f"User {id} not found")
    # The update is empty, so return the matching document:
    if (existing_user := await user_collection.find_one({"_id": ObjectId(id)})) is not None:
        return existing_user
    raise HTTPException(status_code=404, detail=f"User {id} not found")

@router.delete("/{id}", response_description="Delete a User")
async def delete_user(id: str):
    """
    Remove a single user record from the database.
    """
    delete_result = await user_collection.delete_one({"_id": ObjectId(id)})
    if delete_result.deleted_count == 1:
        # Invalidate caches
        await cache_manager.delete_cache(f"user:{id}")
        await cache_manager.delete_cache("list:users")
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=404, detail=f"User {id} not found")