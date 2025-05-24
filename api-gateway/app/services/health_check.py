from http_client import http_client
from config import AUTH_SERVICE_URL, USER_SERVICE_URL

async def check_services_health():
    results = {}
    for name, url in {
        "auth_service": f"{AUTH_SERVICE_URL}/health",
        "user_service": f"{USER_SERVICE_URL}/health"
    }.items():
        try:
            resp = await http_client.client.get(url)
            results[name] = resp.json() if resp.status_code == 200 else {"status": "unhealthy"}
        except Exception:
            results[name] = {"status": "unreachable"}
    return results
