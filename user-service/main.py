from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from pymongo import MongoClient
from jose import jwt, JWTError
import logging
from bson import ObjectId
import os
import json

# Configuration via variables d'environnement
MONGO_HOST = os.getenv("MONGO_HOST", "mongo")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
SECRET_KEY = os.getenv("JWT_SECRET", "changeme")
ALGORITHM = "HS256"

# Logging structuré
logging.basicConfig(format='%(message)s', level=logging.INFO)
def log_structured(message, **kwargs):
    logging.info(json.dumps({"message": message, **kwargs}))

app = FastAPI()
client = MongoClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}")
db = client["user_db"]

class User(BaseModel):
    username: str
    email: str
    full_name: str | None = None
    @classmethod
    def validate(cls, value):
        if not value.username or not value.email:
            raise ValueError("username et email sont obligatoires")
        return value

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
        log_structured("JWT decode error", error=str(e))
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/users", response_model=UserResponse)
async def create_user(user: User, current_user: str = Depends(get_current_user)):
    log_structured("Création utilisateur", username=user.username, by=current_user)
    try:
        user_dict = user.dict()
        user_dict["created_by"] = current_user
        result = db.users.insert_one(user_dict)
        user_dict["id"] = str(result.inserted_id)  # Convertir ObjectId en str
        log_structured("Succès création utilisateur", username=user.username)
        return user_dict
    except Exception as e:
        log_structured("Erreur création utilisateur", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

@app.get("/users", response_model=list[UserResponse])
async def get_users(current_user: str = Depends(get_current_user)):
    log_structured("Récupération utilisateurs", by=current_user)
    try:
        users = list(db.users.find())
        for user in users:
            user["id"] = str(user["_id"])  # Convertir ObjectId en str
            del user["_id"]
        log_structured("Succès récupération utilisateurs", count=len(users))
        return users
    except Exception as e:
        log_structured("Erreur récupération utilisateurs", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")

@app.get("/health")
def health():
    return {"status": "ok"}