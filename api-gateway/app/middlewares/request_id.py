import time
from logging_config import log_structured
from metrics import REQUEST_COUNT, REQUEST_LATENCY
from fastapi import Request

async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(time.time()))
    request.state.request_id = request_id

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)

    log_structured("Request processed", method=request.method, path=request.url.path, status_code=response.status_code, process_time=process_time, request_id=request_id)

    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status_code=response.status_code).inc()
    REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path, status_code=response.status_code).observe(process_time)

    return response
