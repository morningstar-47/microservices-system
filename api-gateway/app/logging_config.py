import logging
import json
from datetime import datetime
from config import ENVIRONMENT, LOG_LEVEL

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL.upper())
)
logger = logging.getLogger(__name__)

def log_structured(message: str, level: str = "INFO", **kwargs):
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "environment": ENVIRONMENT,
        "service": "api-gateway",
        "message": message,
        **kwargs
    }
    getattr(logger, level.lower())(json.dumps(log_data))
