# from fastapi import FastAPI, HTTPException, Request, status
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from fastapi.responses import JSONResponse, PlainTextResponse
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.middleware.trustedhost import TrustedHostMiddleware
# import httpx
# import os
# import logging
# import json
# import time
# from datetime import datetime
# from typing import Optional, Dict, Any
# from contextlib import asynccontextmanager
# import asyncio
# from circuitbreaker import circuit
# from prometheus_client import Counter, Histogram, generate_latest

# # Configuration
# AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
# USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8000")
# ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
# LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
# ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")
# CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
# REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
# CIRCUIT_BREAKER_FAILURE_THRESHOLD = int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5"))
# CIRCUIT_BREAKER_RECOVERY_TIMEOUT = int(os.getenv("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "60"))

# # Logging configuration
# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     level=getattr(logging, LOG_LEVEL.upper())
# )
# logger = logging.getLogger(__name__)

# def log_structured(message: str, **kwargs):
#     log_data = {
#         "timestamp": datetime.utcnow().isoformat(),
#         "environment": ENVIRONMENT,
#         "service": "api-gateway",
#         "message": message,
#         **kwargs
#     }
#     logger.info(json.dumps(log_data))

# # Circuit breaker decorators
# @circuit(failure_threshold=CIRCUIT_BREAKER_FAILURE_THRESHOLD, 
#          recovery_timeout=CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
#          expected_exception=httpx.HTTPError)
# async def call_auth_service(client: httpx.AsyncClient, method: str, path: str, **kwargs):
#     return await client.request(method, f"{AUTH_SERVICE_URL}{path}", **kwargs)

# @circuit(failure_threshold=CIRCUIT_BREAKER_FAILURE_THRESHOLD,
#          recovery_timeout=CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
#          expected_exception=httpx.HTTPError)
# async def call_user_service(client: httpx.AsyncClient, method: str, path: str, **kwargs):
#     return await client.request(method, f"{USER_SERVICE_URL}{path}", **kwargs)

# # HTTP client configuration
# class HTTPClient:
#     def __init__(self):
#         self.client = None
    
#     async def start(self):
#         self.client = httpx.AsyncClient(
#             timeout=httpx.Timeout(REQUEST_TIMEOUT),
#             limits=httpx.Limits(max_keepalive_connections=100, max_connections=200)
#         )
#         log_structured("HTTP client initialized")
    
#     async def stop(self):
#         if self.client:
#             await self.client.aclose()
#             log_structured("HTTP client closed")

# http_client = HTTPClient()

# # Lifespan management
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup
#     await http_client.start()
    
#     # Health check services on startup
#     await check_services_health()
    
#     yield
    
#     # Shutdown
#     await http_client.stop()

# app = FastAPI(
#     title="API Gateway",
#     version="1.0.0",
#     lifespan=lifespan
# )

# # Middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=CORS_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# if ENVIRONMENT == "production":
#     app.add_middleware(
#         TrustedHostMiddleware,
#         allowed_hosts=ALLOWED_HOSTS
#     )

# # Metrics
# REQUEST_COUNT = Counter('api_gateway_requests_total', 'Total number of incoming requests', ['method', 'endpoint', 'status_code'])
# REQUEST_LATENCY = Histogram('api_gateway_request_duration_seconds', 'Request latency in seconds', ['method', 'endpoint', 'status_code'])

# # Request ID middleware
# @app.middleware("http")
# async def add_request_id(request: Request, call_next):
#     request_id = request.headers.get("X-Request-ID", str(time.time()))
#     request.state.request_id = request_id
    
#     start_time = time.time()
#     response = await call_next(request)
#     process_time = time.time() - start_time
    
#     response.headers["X-Request-ID"] = request_id
#     response.headers["X-Process-Time"] = str(process_time)
    
#     # Log structured request info
#     log_structured(
#         "Request processed",
#         request_id=request_id,
#         method=request.method,
#         path=request.url.path,
#         status_code=response.status_code,
#         process_time=process_time
#     )
    
#     # Collect metrics
#     endpoint = request.url.path
#     method = request.method
#     status_code = response.status_code
    
#     REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
#     REQUEST_LATENCY.labels(method=method, endpoint=endpoint, status_code=status_code).observe(process_time)
    
#     return response

# # Health check
# async def check_services_health():
#     services_status = {}
    
#     try:
#         response = await http_client.client.get(f"{AUTH_SERVICE_URL}/health")
#         services_status["auth-service"] = response.status_code == 200
#     except Exception as e:
#         services_status["auth-service"] = False
#         log_structured("Auth service health check failed", error=str(e), level="WARNING")
    
#     try:
#         response = await http_client.client.get(f"{USER_SERVICE_URL}/health")
#         services_status["user-service"] = response.status_code == 200
#     except Exception as e:
#         services_status["user-service"] = False
#         log_structured("User service health check failed", error=str(e), level="WARNING")
    
#     return services_status

# # Routes
# @app.get("/health")
# async def health():
#     services_status = await check_services_health()
    
#     return {
#         "status": "healthy" if all(services_status.values()) else "degraded",
#         "service": "api-gateway",
#         "timestamp": datetime.utcnow().isoformat(),
#         "services": services_status
#     }

# @app.get("/metrics")
# async def metrics():
#     return PlainTextResponse(generate_latest())

# @app.post("/auth/register")
# async def register(request: Request):
#     try:
#         body = await request.json()
#         headers = {"Content-Type": "application/json"}
        
#         log_structured("Proxying registration request", username=body.get("username"))
        
#         response = await call_auth_service(
#             http_client.client,
#             "POST",
#             "/register",
#             headers=headers,
#             json=body
#         )
        
#         return response.json()
    
#     except httpx.HTTPStatusError as e:
#         log_structured("Registration proxy error", status=e.response.status_code, level="ERROR")
#         return JSONResponse(
#             status_code=e.response.status_code,
#             content=e.response.json() if e.response.text else {"detail": "Registration failed"}
#         )
#     except Exception as e:
#         log_structured("Registration proxy error", error=str(e), level="ERROR")
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="Auth service unavailable"
#         )

# @app.post("/auth/login")
# async def login(request: Request):
#     try:
#         body = await request.json()
#         headers = {"Content-Type": "application/json"}
        
#         log_structured("Proxying login request", username=body.get("username"))
        
#         response = await call_auth_service(
#             http_client.client,
#             "POST",
#             "/login",
#             headers=headers,
#             json=body
#         )
        
#         return response.json()
    
#     except httpx.HTTPStatusError as e:
#         log_structured("Login proxy error", status=e.response.status_code, level="ERROR")
#         return JSONResponse(
#             status_code=e.response.status_code,
#             content=e.response.json() if e.response.text else {"detail": "Login failed"}
#         )
#     except Exception as e:
#         log_structured("Login proxy error", error=str(e), level="ERROR")
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="Auth service unavailable"
#         )

# @app.get("/auth/verify")
# async def verify_token(request: Request):
#     auth_header = request.headers.get("Authorization")
#     if not auth_header:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Authorization header missing"
#         )
    
#     try:
#         headers = {"Authorization": auth_header}
        
#         response = await call_auth_service(
#             http_client.client,
#             "GET",
#             "/verify",
#             headers=headers
#         )
        
#         return response.json()
    
#     except httpx.HTTPStatusError as e:
#         return JSONResponse(
#             status_code=e.response.status_code,
#             content=e.response.json() if e.response.text else {"detail": "Verification failed"}
#         )
#     except Exception as e:
#         log_structured("Token verification error", error=str(e), level="ERROR")
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="Auth service unavailable"
#         )

# # User service routes
# @app.post("/users")
# async def create_user(request: Request):
#     auth_header = request.headers.get("Authorization")
#     if not auth_header:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Authorization header missing"
#         )
    
#     try:
#         body = await request.json()
#         headers = {
#             "Authorization": auth_header,
#             "Content-Type": "application/json",
#             "X-Request-ID": request.state.request_id
#         }
        
#         log_structured("Proxying create user request")
        
#         response = await call_user_service(
#             http_client.client,
#             "POST",
#             "/users",
#             headers=headers,
#             json=body
#         )
        
#         return response.json()
    
#     except httpx.HTTPStatusError as e:
#         log_structured("Create user proxy error", status=e.response.status_code, level="ERROR")
#         return JSONResponse(
#             status_code=e.response.status_code,
#             content=e.response.json() if e.response.text else {"detail": "Failed to create user"}
#         )
#     except Exception as e:
#         log_structured("Create user proxy error", error=str(e), level="ERROR")
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="User service unavailable"
#         )

# @app.get("/users")
# async def get_users(request: Request, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None):
#     auth_header = request.headers.get("Authorization")
#     if not auth_header:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Authorization header missing"
#         )
    
#     try:
#         headers = {
#             "Authorization": auth_header,
#             "X-Request-ID": request.state.request_id
#         }
        
#         params = {"skip": skip, "limit": limit}
#         if is_active is not None:
#             params["is_active"] = is_active
        
#         log_structured("Proxying get users request", params=params)
        
#         response = await call_user_service(
#             http_client.client,
#             "GET",
#             "/users",
#             headers=headers,
#             params=params
#         )
        
#         return response.json()
    
#     except httpx.HTTPStatusError as e:
#         log_structured("Get users proxy error", status=e.response.status_code, level="ERROR")
#         return JSONResponse(
#             status_code=e.response.status_code,
#             content=e.response.json() if e.response.text else {"detail": "Failed to get users"}
#         )
#     except Exception as e:
#         log_structured("Get users proxy error", error=str(e), level="ERROR")
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="User service unavailable"
#         )

# @app.get("/users/{user_id}")
# async def get_user(user_id: str, request: Request):
#     auth_header = request.headers.get("Authorization")
#     if not auth_header:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Authorization header missing"
#         )
    
#     try:
#         headers = {
#             "Authorization": auth_header,
#             "X-Request-ID": request.state.request_id
#         }
        
#         log_structured("Proxying get user request", user_id=user_id)
        
#         response = await call_user_service(
#             http_client.client,
#             "GET",
#             f"/users/{user_id}",
#             headers=headers
#         )
        
#         return response.json()
    
#     except httpx.HTTPStatusError as e:
#         log_structured("Get user proxy error", status=e.response.status_code, user_id=user_id, level="ERROR")
#         return JSONResponse(
#             status_code=e.response.status_code,
#             content=e.response.json() if e.response.text else {"detail": "User not found"}
#         )
#     except Exception as e:
#         log_structured("Get user proxy error", error=str(e), level="ERROR")
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="User service unavailable"
#         )

# @app.patch("/users/{user_id}")
# async def update_user(user_id: str, request: Request):
#     auth_header = request.headers.get("Authorization")
#     if not auth_header:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Authorization header missing"
#         )
    
#     try:
#         body = await request.json()
#         headers = {
#             "Authorization": auth_header,
#             "Content-Type": "application/json",
#             "X-Request-ID": request.state.request_id
#         }
        
#         log_structured("Proxying update user request", user_id=user_id)
        
#         response = await call_user_service(
#             http_client.client,
#             "PATCH",
#             f"/users/{user_id}",
#             headers=headers,
#             json=body
#         )
        
#         return response.json()
    
#     except httpx.HTTPStatusError as e:
#         log_structured("Update user proxy error", status=e.response.status_code, user_id=user_id, level="ERROR")
#         return JSONResponse(
#             status_code=e.response.status_code,
#             content=e.response.json() if e.response.text else {"detail": "Failed to update user"}
#         )
#     except Exception as e:
#         log_structured("Update user proxy error", error=str(e), level="ERROR")
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="User service unavailable"
#         )

# @app.delete("/users/{user_id}")
# async def delete_user(user_id: str, request: Request):
#     auth_header = request.headers.get("Authorization")
#     if not auth_header:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Authorization header missing"
#         )
    
#     try:
#         headers = {
#             "Authorization": auth_header,
#             "X-Request-ID": request.state.request_id
#         }
        
#         log_structured("Proxying delete user request", user_id=user_id)
        
#         response = await call_user_service(
#             http_client.client,
#             "DELETE",
#             f"/users/{user_id}",
#             headers=headers
#         )
        
#         return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)
    
#     except httpx.HTTPStatusError as e:
#         log_structured("Delete user proxy error", status=e.response.status_code, user_id=user_id, level="ERROR")
#         return JSONResponse(
#             status_code=e.response.status_code,
#             content=e.response.json() if e.response.text else {"detail": "Failed to delete user"}
#         )
#     except Exception as e:
#         log_structured("Delete user proxy error", error=str(e), level="ERROR")
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="User service unavailable"
#         )

# # Error handlers
# @app.exception_handler(Exception)
# async def general_exception_handler(request: Request, exc: Exception):
#     log_structured("Unhandled exception", error=str(exc), path=request.url.path, level="ERROR")
#     return JSONResponse(
#         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         content={"detail": "Internal server error"}
#     )

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)


from fastapi import FastAPI
from middlewares.request_id import request_id_middleware
from middlewares.cors import setup_cors
from routes import auth_routes, user_routes, health, metrics, map_routes, ai_routes, report_routes
from exceptions import setup_exception_handlers
from config import lifespan, ENVIRONMENT, ALLOWED_HOSTS
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI(lifespan=lifespan, title="API Gateway v1", version="1.0.0")

setup_cors(app)
app.middleware("http")(request_id_middleware)

if ENVIRONMENT == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

app.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])
app.include_router(user_routes.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(map_routes.router, prefix="/api/v1/maps", tags=["Maps"])
app.include_router(ai_routes.router, prefix="/api/v1/ais", tags=["AI"])
app.include_router(report_routes.router, prefix="/api/v1/reports", tags=["Reports"])

app.include_router(health.router, tags=["System"])
app.include_router(metrics.router, tags=["System"])

setup_exception_handlers(app)

