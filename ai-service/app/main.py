import os
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, validator
from motor.motor_asyncio import AsyncIOMotorClient
from jose import jwt, JWTError
from datetime import datetime, timezone
import logging
import os
import json
from prometheus_client import Counter, Histogram, generate_latest
from contextlib import asynccontextmanager
from bson import ObjectId
from fastapi.responses import PlainTextResponse
import time
from typing import Optional, List

# Configuration
MONGO_HOST = os.getenv("MONGO_HOST", "mongo")
MONGO_PORT = int(os.environ.get("MONGO_PORT", "27017"))
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "ai_db")
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": ENVIRONMENT,
        "service": "ai-service",
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
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")

class AIBase(BaseModel):
    name: str
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    updated_by: str 

class AICreate(AIBase):
    pass

class AIUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None   

class AIInDB(AIBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)   

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None

# Database
class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

db = MongoDB()

# Metrics
REQUEST_COUNT = Counter('ai_service_requests_total', 'Total number of incoming requests', ['method', 'endpoint', 'status_code'])
REQUEST_LATENCY = Histogram('ai_service_request_duration_seconds', 'Request latency in seconds', ['method', 'endpoint', 'status_code'])

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        db.client = AsyncIOMotorClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}")
        db.database = db.client[MONGO_DB_NAME]

        # Create indexes
        await db.database.ais.create_index("ai_id", unique=True)
        await db.database.ais.create_index("created_at")
        
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
    title="AI Service v1",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware for metrics
@app.middleware("http")
async def collect_metrics(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # Metrics
    endpoint = request.url.path
    method = request.method
    status_code = response.status_code

    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint, status_code=status_code).observe(process_time)

    return response

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
            "service": "ai-service",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        log_structured("Health check failed", error=str(e), level="ERROR")
        return {
            "status": "unhealthy",
            "service": "ai-service",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "disconnected"
        }

@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest())

@app.post('/', response_model=AIInDB, status_code=status.HTTP_201_CREATED)
async def create_ai(
    ai: AICreate,
    current_user: TokenData = Depends(get_current_user)
):
    ai_dict = ai.model_dump()
    ai_dict['created_by'] = current_user.username
    ai_dict['updated_by'] = current_user.username
    ai_dict['created_at'] = datetime.now(timezone.utc)
    ai_dict['updated_at'] = datetime.now(timezone.utc)

    result = await db.database.ais.insert_one(ai_dict)
    created_ai = await db.database.ais.find_one({"_id": result.inserted_id})
    return AIInDB(**created_ai)

@app.get('/', response_model=List[AIInDB])
async def list_ais(
    skip: int = 0,
    limit: int = 100,
    current_user: TokenData = Depends(get_current_user)
):
    ais = await db.database.ais.find().skip(skip).limit(limit).to_list(length=limit)
    return ais

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return HTTPException(status_code=400, detail=str(exc))

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    log_structured("Unhandled exception", error=str(exc), level="ERROR")
    return HTTPException(status_code=500, detail="Internal server error")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000) 