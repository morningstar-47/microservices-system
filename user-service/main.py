from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from pymongo import MongoClient
from jose import jwt, JWTError
import logging
from bson import ObjectId

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
client = MongoClient("mongodb://mongo:27017")
db = client["user_db"]
SECRET_KEY = "56c998560ed656035c4eeaa8bca856e06fe893a81361b7192ba8ec49b9f649c6s"
ALGORITHM = "HS256"

class User(BaseModel):
    username: str
    email: str
    full_name: str | None = None

class UserResponse(BaseModel):
    username: str
    email: str
    full_name: str | None = None
    created_by: str
    id: str  # _id sera converti en chaîne

async def get_current_user(authorization: str = Header(default=None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/users", response_model=UserResponse)
async def create_user(user: User, current_user: str = Depends(get_current_user)):
    try:
        user_dict = user.dict()
        user_dict["created_by"] = current_user
        result = db.users.insert_one(user_dict)
        user_dict["id"] = str(result.inserted_id)  # Convertir ObjectId en str
        return user_dict
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

@app.get("/users", response_model=list[UserResponse])
async def get_users(current_user: str = Depends(get_current_user)):
    try:
        users = list(db.users.find())
        for user in users:
            user["id"] = str(user["_id"])  # Convertir ObjectId en str
            del user["_id"]
        return users
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")