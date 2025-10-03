import os
from typing import Optional, List

from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import Response
from pydantic import ConfigDict, BaseModel, Field, EmailStr
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated

from bson import ObjectId
import asyncio
from pymongo import AsyncMongoClient
from pymongo import ReturnDocument

def main():
    print("Hello from 1-mongodb-app!")

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome!"}

if __name__ == "__main__":
    main()