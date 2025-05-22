from fastapi import FastAPI, HTTPException, Header
import httpx
import os
import logging
import json

app = FastAPI()

# Configuration via variables d'environnement
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8000")

# Logging structuré
logging.basicConfig(format='%(message)s', level=logging.INFO)
def log_structured(message, **kwargs):
    logging.info(json.dumps({"message": message, **kwargs}))

async def route_to_service(service_url: str, headers: dict, json_data: dict = None):
    async with httpx.AsyncClient() as client:
        response = await client.request("POST" if json_data else "GET", service_url, headers=headers, json=json_data)
        response.raise_for_status()
        return response.json()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/login")
async def login(json: dict):
    headers = {"Content-Type": "application/json"}
    log_structured("Proxy login", service="auth-service")
    return await route_to_service(f"{AUTH_SERVICE_URL}/login", headers=headers, json_data=json)

@app.post("/users")
async def create_user(json: dict, authorization: str = Header(default=None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    headers = {"Authorization": authorization, "Content-Type": "application/json"}
    try:
        log_structured("Proxy create user", service="user-service")
        return await route_to_service(f"{USER_SERVICE_URL}/users", headers=headers, json_data=json)
    except httpx.HTTPStatusError as e:
        log_structured("Erreur proxy create user", status=e.response.status_code)
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json())

@app.get("/users")
async def get_users(authorization: str = Header(default=None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    headers = {"Authorization": authorization}
    try:
        log_structured("Proxy get users", service="user-service")
        return await route_to_service(f"{USER_SERVICE_URL}/users", headers=headers)
    except httpx.HTTPStatusError as e:
        log_structured("Erreur proxy get users", status=e.response.status_code)
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json())
