from fastapi import FastAPI, HTTPException, Header
import httpx

app = FastAPI()

async def route_to_service(service_url: str, headers: dict, json_data: dict = None):
    async with httpx.AsyncClient() as client:
        response = await client.request("POST" if json_data else "GET", service_url, headers=headers, json=json_data)
        response.raise_for_status()
        return response.json()

@app.post("/login")
async def login(json: dict):
    headers = {"Content-Type": "application/json"}
    return await route_to_service("http://auth-service:8000/login", headers=headers, json_data=json)

@app.post("/users")
async def create_user(json: dict, authorization: str = Header(default=None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    headers = {"Authorization": authorization, "Content-Type": "application/json"}
    try:
        return await route_to_service("http://user-service:8000/users", headers=headers, json_data=json)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json())

@app.get("/users")
async def get_users(authorization: str = Header(default=None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    headers = {"Authorization": authorization}
    try:
        return await route_to_service("http://user-service:8000/users", headers=headers)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json())
