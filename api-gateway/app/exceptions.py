from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from logging_config import log_structured

def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        log_structured("Unhandled exception", level="error", error=str(exc))
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
