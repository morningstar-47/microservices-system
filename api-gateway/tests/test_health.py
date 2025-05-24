# import pytest
# from httpx import AsyncClient
# from ..main import app

# @pytest.mark.asyncio
# async def test_health():
#     async with AsyncClient(app=app, base_url="http://test") as ac:
#         response = await ac.get("/health")
#     assert response.status_code == 200
#     assert response.json() == {"status": "ok"} 

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app 

client = TestClient(app)

@pytest.fixture
def mock_auth_service():
    with patch("app.main.http_client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"message": "Auth OK"}
        yield mock_get

@pytest.fixture
def mock_user_service():
    with patch("app.main.http_client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"message": "User OK"}
        yield mock_get

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_metrics_exposed():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "gateway_request_duration_seconds" in response.text

def test_request_id_header():
    response = client.get("/health")
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] != ""

def test_process_time_header():
    response = client.get("/health")
    assert "X-Process-Time" in response.headers
    assert float(response.headers["X-Process-Time"]) > 0

@pytest.mark.asyncio
async def test_auth_proxy(mock_auth_service):
    with patch("app.main.http_client.request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = {"message": "Auth Proxy OK"}

        response = client.get("/auth/verify", headers={"Authorization": "Bearer dummy"})
        assert response.status_code == 200
        assert response.json() == {"message": "Auth Proxy OK"}

@pytest.mark.asyncio
async def test_user_proxy(mock_user_service):
    with patch("app.main.http_client.request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = {"message": "User Proxy OK"}

        response = client.get("/users/profile", headers={"Authorization": "Bearer dummy"})
        assert response.status_code == 200
        assert response.json() == {"message": "User Proxy OK"}

@pytest.mark.asyncio
async def test_circuit_breaker_triggers():
    with patch("app.main.http_client.request", new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = Exception("Service down")

        for _ in range(3):
            client.get("/users/test", headers={"Authorization": "Bearer dummy"})

        # Le circuit breaker est ouvert maintenant
        response = client.get("/users/test", headers={"Authorization": "Bearer dummy"})
        assert response.status_code == 503
        assert response.json()["detail"] == "User Service temporarily unavailable"

