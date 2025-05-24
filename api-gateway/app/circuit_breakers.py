import time
import asyncio
from functools import wraps
from logging_config import log_structured
from config import CIRCUIT_BREAKER_FAILURE_THRESHOLD, CIRCUIT_BREAKER_RECOVERY_TIMEOUT

class CircuitBreaker:
    def __init__(self):
        self.failures = {}
        self.last_failure_time = {}

    def is_open(self, key):
        if key in self.failures and self.failures[key] >= CIRCUIT_BREAKER_FAILURE_THRESHOLD:
            elapsed = time.time() - self.last_failure_time.get(key, 0)
            return elapsed < CIRCUIT_BREAKER_RECOVERY_TIMEOUT
        return False

    def record_failure(self, key):
        self.failures[key] = self.failures.get(key, 0) + 1
        self.last_failure_time[key] = time.time()

    def reset(self, key):
        self.failures[key] = 0

breaker = CircuitBreaker()

def circuit_breaker(key):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if breaker.is_open(key):
                log_structured("Circuit breaker open", level="warning", service=key)
                raise Exception(f"{key} temporarily unavailable")

            try:
                response = await func(*args, **kwargs)
                breaker.reset(key)
                return response
            except Exception as e:
                breaker.record_failure(key)
                log_structured("Request failed", level="error", error=str(e), service=key)
                raise e
        return wrapper
    return decorator
