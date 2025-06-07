from http_client import http_client
from config import MAP_SERVICE_URL
from circuit_breakers import circuit_breaker

@circuit_breaker("map_service")
async def proxy_map(path: str, request):
    url = f"{MAP_SERVICE_URL}{path}"
    headers = dict(request.headers)
    body = await request.body()
    response = await http_client.client.request(request.method, url, headers=headers, content=body)
    return response
