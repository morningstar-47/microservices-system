# from fastapi.testclient import TestClient
# from main import app

# client = TestClient(app)

# def test_login_success():
#     response = client.post("/login", json={"username": "testuser", "password": "password123"})
#     assert response.status_code == 200
#     assert "access_token" in response.json()


import pytest
from httpx import AsyncClient
from .main import app  # Assure-toi que le fichier contenant ton app s'appelle main.py
from unittest.mock import AsyncMock, patch
from passlib.context import CryptContext

# Simule le mot de passe hashé de l'utilisateur
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed_password = pwd_context.hash("secret123")

@pytest.mark.asyncio
@patch("main.get_db_connection")  # Mock de la connexion à la DB
async def test_login_success(mock_get_db_conn):
    # Mock du résultat de la requête SQL
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = {
        "username": "testuser",
        "hashed_password": hashed_password
    }
    mock_get_db_conn.return_value = mock_conn

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/login", json={"username": "testuser", "password": "secret123"})

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
@patch("main.get_db_connection")
async def test_login_invalid_password(mock_get_db_conn):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = {
        "username": "testuser",
        "hashed_password": hashed_password
    }
    mock_get_db_conn.return_value = mock_conn

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/login", json={"username": "testuser", "password": "wrongpass"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

@pytest.mark.asyncio
@patch("main.get_db_connection")
async def test_login_user_not_found(mock_get_db_conn):
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = None
    mock_get_db_conn.return_value = mock_conn

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/login", json={"username": "unknown", "password": "secret123"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
