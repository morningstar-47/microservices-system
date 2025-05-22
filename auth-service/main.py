from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import asyncpg

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "56c998560ed656035c4eeaa8bca856e06fe893a81361b7192ba8ec49b9f649c6s"
ALGORITHM = "HS256"

class UserLogin(BaseModel):
    username: str
    password: str

async def get_db_connection():
    return await asyncpg.connect(
        user="user", password="password", database="auth_db", host="postgres"
    )

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/login")
async def login(user: UserLogin):
    conn = await get_db_connection()
    try:
        db_user = await conn.fetchrow(
            "SELECT * FROM users WHERE username = $1", user.username
        )
        if not db_user or not verify_password(user.password, db_user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=timedelta(minutes=30)
        )
        return {"access_token": access_token, "token_type": "bearer"}
    finally:
        await conn.close()

