import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
from .main import app, get_password_hash, verify_password, create_access_token
from jose import jwt
import os

# Test configuration
os.environ["JWT_SECRET"] = "test-secret"
os.environ["ENVIRONMENT"] = "test"

@pytest.fixture
def mock_db_pool():
    """Mock database pool"""
    pool = AsyncMock()
    return pool

@pytest.fixture
async def client():
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
class TestHealthEndpoint:
    async def test_health_check_success(self, client, mock_db_pool):
        with patch("main.db_connection.pool", mock_db_pool):
            mock_connection = AsyncMock()
            mock_connection.fetchval.return_value = 1
            mock_db_pool.acquire.return_value.__aenter__.return_value = mock_connection
            
            response = await client.post("/login", json={
                "username": "nonexistent",
                "password": "Test1234!"
            })
            
            assert response.status_code == 401
            assert response.json()["detail"] == "Invalid credentials"

    async def test_login_invalid_password(self, client, mock_db_pool):
        with patch("main.db_connection.pool", mock_db_pool):
            mock_connection = AsyncMock()
            hashed_password = get_password_hash("Test1234!")
            mock_connection.fetchrow.return_value = {
                "id": 1,
                "username": "testuser",
                "hashed_password": hashed_password,
                "is_active": True
            }
            mock_db_pool.acquire.return_value.__aenter__.return_value = mock_connection
            
            response = await client.post("/login", json={
                "username": "testuser",
                "password": "WrongPassword!"
            })
            
            assert response.status_code == 401
            assert response.json()["detail"] == "Invalid credentials"

    async def test_login_inactive_user(self, client, mock_db_pool):
        with patch("main.db_connection.pool", mock_db_pool):
            mock_connection = AsyncMock()
            hashed_password = get_password_hash("Test1234!")
            mock_connection.fetchrow.return_value = {
                "id": 1,
                "username": "testuser",
                "hashed_password": hashed_password,
                "is_active": False
            }
            mock_db_pool.acquire.return_value.__aenter__.return_value = mock_connection
            
            response = await client.post("/login", json={
                "username": "testuser",
                "password": "Test1234!"
            })
            
            assert response.status_code == 403
            assert response.json()["detail"] == "User account is inactive"

@pytest.mark.asyncio
class TestTokenVerification:
    async def test_verify_valid_token(self, client):
        # Create a valid token
        token = create_access_token({"sub": "testuser", "user_id": 1})
        
        response = await client.get(
            "/verify",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["valid"] is True

    async def test_verify_invalid_token(self, client):
        response = await client.get(
            "/verify",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"

    async def test_verify_missing_token(self, client):
        response = await client.get("/verify")
        
        assert response.status_code == 403
        assert response.json()["detail"] == "Not authenticated"

    async def test_verify_expired_token(self, client):
        # Create an expired token
        from datetime import datetime, timedelta
        expired_data = {
            "sub": "testuser",
            "user_id": 1,
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        expired_token = jwt.encode(expired_data, "test-secret", algorithm="HS256")
        
        response = await client.get(
            "/verify",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"

@pytest.mark.asyncio
class TestPasswordHashing:
    def test_password_hash_and_verify(self):
        password = "Test1234!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False

    def test_different_passwords_different_hashes(self):
        password = "Test1234!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2  # Bcrypt includes salt, so hashes differ
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

@pytest.mark.asyncio
class TestDatabaseConnection:
    async def test_db_pool_initialization(self):
        from main import DatabaseConnection
        
        db = DatabaseConnection()
        
        with patch("asyncpg.create_pool") as mock_create_pool:
            mock_pool = AsyncMock()
            mock_create_pool.return_value = mock_pool
            
            await db.init_pool()
            
            mock_create_pool.assert_called_once()
            assert db.pool is not None

    async def test_db_pool_close(self):
        from main import DatabaseConnection
        
        db = DatabaseConnection()
        db.pool = AsyncMock()
        
        await db.close_pool()
        
        db.pool.close.assert_called_once()

@pytest.mark.asyncio
class TestIntegration:
    async def test_full_registration_and_login_flow(self, client, mock_db_pool):
        with patch("main.db_connection.pool", mock_db_pool):
            mock_connection = AsyncMock()
            
            # Registration
            mock_connection.fetchrow.return_value = None  # User doesn't exist
            mock_connection.fetchval.return_value = 1  # New user ID
            mock_db_pool.acquire.return_value.__aenter__.return_value = mock_connection
            
            register_response = await client.post("/register", json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "Test1234!",
                "full_name": "New User"
            })
            
            assert register_response.status_code == 201
            
            # Login
            hashed_password = get_password_hash("Test1234!")
            mock_connection.fetchrow.return_value = {
                "id": 1,
                "username": "newuser",
                "hashed_password": hashed_password,
                "is_active": True
            }
            mock_connection.execute = AsyncMock()
            
            login_response = await client.post("/login", json={
                "username": "newuser",
                "password": "Test1234!"
            })
            
            assert login_response.status_code == 200
            token_data = login_response.json()
            
            # Verify token
            verify_response = await client.get(
                "/verify",
                headers={"Authorization": f"Bearer {token_data['access_token']}"}
            )
            
            assert verify_response.status_code == 200
            # assert verify_response.json()["username"] == "newuser" = mock_connection
            assert verify_response.json()["username"] == "newuser" 
            
            response = await client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "auth-service"
            assert "timestamp" in data

    async def test_health_check_db_failure(self, client, mock_db_pool):
        with patch("main.db_connection.pool", mock_db_pool):
            mock_db_pool.acquire.side_effect = Exception("DB connection failed")
            
            response = await client.get("/health")
            
            assert response.status_code == 503
            assert response.json()["detail"] == "Service unavailable"

@pytest.mark.asyncio
class TestRegistration:
    async def test_register_success(self, client, mock_db_pool):
        with patch("main.db_connection.pool", mock_db_pool):
            mock_connection = AsyncMock()
            mock_connection.fetchrow.return_value = None  # User doesn't exist
            mock_connection.fetchval.return_value = 1  # New user ID
            mock_db_pool.acquire.return_value.__aenter__.return_value = mock_connection
            
            response = await client.post("/register", json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "Test1234!",
                "full_name": "Test User"
            })
            
            assert response.status_code == 201
            data = response.json()
            assert data["message"] == "User registered successfully"
            assert data["user_id"] == 1

    async def test_register_invalid_username(self, client):
        response = await client.post("/register", json={
            "username": "ab",  # Too short
            "email": "test@example.com",
            "password": "Test1234!"
        })
        
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("username" in str(error).lower() for error in errors)

    async def test_register_invalid_email(self, client):
        response = await client.post("/register", json={
            "username": "testuser",
            "email": "invalid-email",
            "password": "Test1234!"
        })
        
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("email" in str(error).lower() for error in errors)

    async def test_register_weak_password(self, client):
        response = await client.post("/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak"  # Too short, no uppercase, no digit
        })
        
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("password" in str(error).lower() for error in errors)

    async def test_register_duplicate_user(self, client, mock_db_pool):
        with patch("main.db_connection.pool", mock_db_pool):
            mock_connection = AsyncMock()
            mock_connection.fetchrow.return_value = {"id": 1}  # User exists
            mock_db_pool.acquire.return_value.__aenter__.return_value = mock_connection
            
            response = await client.post("/register", json={
                "username": "existinguser",
                "email": "existing@example.com",
                "password": "Test1234!"
            })
            
            assert response.status_code == 400
            assert response.json()["detail"] == "Username or email already registered"

@pytest.mark.asyncio
class TestLogin:
    async def test_login_success(self, client, mock_db_pool):
        with patch("main.db_connection.pool", mock_db_pool):
            mock_connection = AsyncMock()
            hashed_password = get_password_hash("Test1234!")
            mock_connection.fetchrow.return_value = {
                "id": 1,
                "username": "testuser",
                "hashed_password": hashed_password,
                "is_active": True
            }
            mock_connection.execute = AsyncMock()  # For update query
            mock_db_pool.acquire.return_value.__aenter__.return_value = mock_connection
            
            response = await client.post("/login", json={
                "username": "testuser",
                "password": "Test1234!"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
            assert "expires_in" in data
            
            # Verify token
            decoded = jwt.decode(data["access_token"], "test-secret", algorithms=["HS256"])
            assert decoded["sub"] == "testuser"
            assert decoded["user_id"] == 1

    async def test_login_invalid_username(self, client, mock_db_pool):
        with patch("main.db_connection.pool", mock_db_pool):
            mock_connection = AsyncMock()
            mock_connection.fetchrow.return_value = None  # User not found
            mock_db_pool.acquire.return_value.__aenter__.return_value