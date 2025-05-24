from http_client import http_client
from config import AUTH_SERVICE_URL
from circuit_breakers import circuit_breaker

@circuit_breaker("auth_service")
async def proxy_auth(path: str, request):
    url = f"{AUTH_SERVICE_URL}{path}"
    headers = dict(request.headers)
    body = await request.body()
    response = await http_client.client.request(request.method, url, headers=headers, content=body)
    return response
