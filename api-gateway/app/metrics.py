from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "api_gateway_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status_code"]
)

REQUEST_LATENCY = Histogram(
    "api_gateway_request_duration_seconds",
    "Request latency",
    ["method", "endpoint", "status_code"]
)
