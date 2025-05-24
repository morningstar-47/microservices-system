# from fastapi import FastAPI, HTTPException, Header, Depends
# from pydantic import BaseModel
# from pymongo import MongoClient
# from jose import jwt, JWTError
# import logging
# from bson import ObjectId
# import os
# import json

# # Configuration via variables d'environnement
# MONGO_HOST = os.getenv("MONGO_HOST", "mongo")
# MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
# SECRET_KEY = os.getenv("JWT_SECRET", "changeme")
# ALGORITHM = "HS256"

# # Logging structuré
# logging.basicConfig(format='%(message)s', level=logging.INFO)
# def log_structured(message, **kwargs):
#     logging.info(json.dumps({"message": message, **kwargs}))

# app = FastAPI()
# client = MongoClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}")
# db = client["user_db"]

# class User(BaseModel):
#     username: str
#     email: str
#     full_name: str | None = None
#     @classmethod
#     def validate(cls, value):
#         if not value.username or not value.email:
#             raise ValueError("username et email sont obligatoires")
#         return value

# class UserResponse(BaseModel):
#     username: str
#     email: str
#     full_name: str | None = None
#     created_by: str
#     id: str  # _id sera converti en chaîne

# async def get_current_user(authorization: str = Header(default=None)):
#     if not authorization:
#         raise HTTPException(status_code=401, detail="Authorization header missing")
#     try:
#         token = authorization.replace("Bearer ", "")
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             raise HTTPException(status_code=401, detail="Invalid token")
#         return username
#     except JWTError as e:
#         log_structured("JWT decode error", error=str(e))
#         raise HTTPException(status_code=401, detail="Invalid token")

# @app.post("/users", response_model=UserResponse)
# async def create_user(user: User, current_user: str = Depends(get_current_user)):
#     log_structured("Création utilisateur", username=user.username, by=current_user)
#     try:
#         user_dict = user.dict()
#         user_dict["created_by"] = current_user
#         result = db.users.insert_one(user_dict)
#         user_dict["id"] = str(result.inserted_id)  # Convertir ObjectId en str
#         log_structured("Succès création utilisateur", username=user.username)
#         return user_dict
#     except Exception as e:
#         log_structured("Erreur création utilisateur", error=str(e))
#         raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

# @app.get("/users", response_model=list[UserResponse])
# async def get_users(current_user: str = Depends(get_current_user)):
#     log_structured("Récupération utilisateurs", by=current_user)
#     try:
#         users = list(db.users.find())
#         for user in users:
#             user["id"] = str(user["_id"])  # Convertir ObjectId en str
#             del user["_id"]
#         log_structured("Succès récupération utilisateurs", count=len(users))
#         return users
#     except Exception as e:
#         log_structured("Erreur récupération utilisateurs", error=str(e))
#         raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")

# @app.get("/health")
# def health():
#     return {"status": "ok"}

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, validator
from motor.motor_asyncio import AsyncIOMotorClient
from jose import jwt, JWTError
from datetime import datetime
import logging
import os
import json
from typing import Optional, List
from bson import ObjectId
from contextlib import asynccontextmanager

# Configuration
MONGO_HOST = os.getenv("MONGO_HOST", "mongo")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "user_db")
SECRET_KEY = os.getenv("JWT_SECRET", "changeme")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL.upper())
)
logger = logging.getLogger(__name__)

def log_structured(message: str, **kwargs):
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "environment": ENVIRONMENT,
        "service": "user-service",
        "message": message,
        **kwargs
    }
    logger.info(json.dumps(log_data))

# MongoDB helpers
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    # def __modify_schema__(cls, field_schema):
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")

# Models
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)
    
    @validator('username')
    def username_valid(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, underscores and hyphens')
        return v.lower().strip()

class UserCreate(UserBase):
    role: Optional[str] = Field("user", pattern="^(user|admin)$")

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    role: str = "user"
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class UserResponse(UserBase):
    id: str
    created_by: str
    created_at: datetime
    is_active: bool
    role: str

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None

# Database
class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

db = MongoDB()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        db.client = AsyncIOMotorClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}")
        db.database = db.client[MONGO_DB_NAME]
        
        # Create indexes
        await db.database.users.create_index("username", unique=True)
        await db.database.users.create_index("email", unique=True)
        await db.database.users.create_index("created_at")
        
        log_structured("MongoDB connected successfully")
    except Exception as e:
        log_structured("Failed to connect to MongoDB", error=str(e), level="ERROR")
        raise
    
    yield
    
    # Shutdown
    if db.client:
        db.client.close()
        log_structured("MongoDB connection closed")

app = FastAPI(
    title="User Service",
    version="1.0.0",
    lifespan=lifespan
)

# Security
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        
        if username is None:
            raise credentials_exception
            
        return TokenData(username=username, user_id=user_id)
    except JWTError as e:
        log_structured("JWT validation error", error=str(e), level="WARNING")
        raise credentials_exception

# Routes
@app.get("/health")
async def health_check():
    try:
        # Check MongoDB connection
        await db.client.admin.command('ping')
        return {
            "status": "healthy",
            "service": "user-service",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        log_structured("Health check failed", error=str(e), level="ERROR")
        return {
            "status": "unhealthy",
            "service": "user-service",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "disconnected"
        }

@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    current_user: TokenData = Depends(get_current_user)
):
    log_structured("Creating user", username=user.username, created_by=current_user.username)
    
    # Check if user exists
    existing_user = await db.database.users.find_one({
        "$or": [
            {"username": user.username},
            {"email": user.email}
        ]
    })
    
    if existing_user:
        log_structured("User creation failed - duplicate", username=user.username)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists"
        )
    
    # Create user document
    user_doc = UserInDB(
        **user.dict(),
        created_by=current_user.username
    )
    
    try:
        result = await db.database.users.insert_one(user_doc.dict(by_alias=True))
        created_user = await db.database.users.find_one({"_id": result.inserted_id})
        
        log_structured("User created successfully", user_id=str(result.inserted_id))
        
        return UserResponse(
            id=str(created_user["_id"]),
            username=created_user["username"],
            email=created_user["email"],
            full_name=created_user.get("full_name"),
            created_by=created_user["created_by"],
            created_at=created_user["created_at"],
            is_active=created_user["is_active"],
            role=created_user["role"]
        )
    except Exception as e:
        log_structured("User creation error", error=str(e), level="ERROR")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@app.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    current_user: TokenData = Depends(get_current_user)
):
    log_structured("Listing users", requested_by=current_user.username)
    
    # Build query
    query = {}
    if is_active is not None:
        query["is_active"] = is_active
    
    try:
        cursor = db.database.users.find(query).skip(skip).limit(limit).sort("created_at", -1)
        users = await cursor.to_list(length=limit)
        
        log_structured("Users retrieved", count=len(users))
        
        return [
            UserResponse(
                id=str(user["_id"]),
                username=user["username"],
                email=user["email"],
                full_name=user.get("full_name"),
                created_by=user["created_by"],
                created_at=user["created_at"],
                is_active=user["is_active"],
                role=user["role"]
            )
            for user in users
        ]
    except Exception as e:
        log_structured("Error listing users", error=str(e), level="ERROR")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    log_structured("Getting user", user_id=user_id, requested_by=current_user.username)
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user = await db.database.users.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        log_structured("User not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        full_name=user.get("full_name"),
        created_by=user["created_by"],
        created_at=user["created_at"],
        is_active=user["is_active"],
        role=user["role"]
    )

@app.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: TokenData = Depends(get_current_user)
):
    log_structured("Updating user", user_id=user_id, updated_by=current_user.username)
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    # Build update document
    update_data = {k: v for k, v in user_update.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    update_data["updated_at"] = datetime.utcnow()
    
    try:
        result = await db.database.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        updated_user = await db.database.users.find_one({"_id": ObjectId(user_id)})
        
        log_structured("User updated successfully", user_id=user_id)
        
        return UserResponse(
            id=str(updated_user["_id"]),
            username=updated_user["username"],
            email=updated_user["email"],
            full_name=updated_user.get("full_name"),
            created_by=updated_user["created_by"],
            created_at=updated_user["created_at"],
            is_active=updated_user["is_active"],
            role=updated_user["role"]
        )
    except Exception as e:
        log_structured("User update error", error=str(e), level="ERROR")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    log_structured("Deleting user", user_id=user_id, deleted_by=current_user.username)
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    # Soft delete - just mark as inactive
    result = await db.database.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    log_structured("User deleted successfully", user_id=user_id)

# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return HTTPException(status_code=400, detail=str(exc))

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    log_structured("Unhandled exception", error=str(exc), level="ERROR")
    return HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)