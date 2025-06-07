import os
import logging
import json
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from http_client import http_client  # Ton client httpx centralisé

# =========================
# 🌍 ENVIRONMENT CONFIG
# =========================
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8000")
MAP_SERVICE_URL = os.getenv("MAP_SERVICE_URL", "http://map-service:8000")
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai-service:8000")
REPORT_SERVICE_URL = os.getenv("REPORT_SERVICE_URL", "http://report-service:8000")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
CIRCUIT_BREAKER_FAILURE_THRESHOLD = int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5"))
CIRCUIT_BREAKER_RECOVERY_TIMEOUT = int(os.getenv("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "60"))


http_client.timeout = REQUEST_TIMEOUT

# =========================
# 📝 LOGGING CONFIG
# =========================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL.upper())
)
logger = logging.getLogger(__name__)

def log_structured(message: str, **kwargs):
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "environment": ENVIRONMENT,
        "service": "api-gateway",
        "message": message,
        **kwargs
    }
    logger.info(json.dumps(log_data))

# =========================
# 🔁 LIFESPAN HANDLER
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialise le client HTTP
    await http_client.start()
    
    # Tu peux aussi ajouter un health check ici si tu veux
    # ex: await check_services_health() si tu veux pré-vérifier

    yield  # Place où l’app tourne (entre startup et shutdown)
    
    # Shutdown: ferme le client HTTP
    await http_client.stop()
