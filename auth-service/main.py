from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import asyncpg
import os
import logging
import json

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuration via variables d'environnement
SECRET_KEY = os.getenv("JWT_SECRET", "changeme")
ALGORITHM = "HS256"
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "auth_db")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")

# Logging structuré
logging.basicConfig(format='%(message)s', level=logging.INFO)
def log_structured(message, **kwargs):
    logging.info(json.dumps({"message": message, **kwargs}))

class UserLogin(BaseModel):
    username: str
    password: str
    # Validation stricte : username non vide, password min 6 caractères
    @classmethod
    def validate(cls, value):
        if not value.username or not value.password or len(value.password) < 6:
            raise ValueError("Nom d'utilisateur ou mot de passe invalide")
        return value

async def get_db_connection():
    return await asyncpg.connect(
        user=DB_USER, password=DB_PASSWORD, database=DB_NAME, host=DB_HOST
    )

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/login")
async def login(user: UserLogin):
    log_structured("Tentative de login", username=user.username)
    conn = await get_db_connection()
    try:
        db_user = await conn.fetchrow(
            "SELECT * FROM users WHERE username = $1", user.username
        )
        if not db_user or not verify_password(user.password, db_user["hashed_password"]):
            log_structured("Echec login", username=user.username)
            raise HTTPException(status_code=401, detail="Invalid credentials")
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=timedelta(minutes=30)
        )
        log_structured("Succès login", username=user.username)
        return {"access_token": access_token, "token_type": "bearer"}
    finally:
        await conn.close()

