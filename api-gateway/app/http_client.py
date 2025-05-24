import httpx
from typing import Optional

class HttpClient:
    def __init__(self, timeout: int = 30):  # valeur par défaut, pas d'import
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None

    async def start(self):
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def stop(self):
        if self.client:
            await self.client.aclose()

    async def request(self, method: str, url: str, **kwargs):
        if not self.client:
            raise RuntimeError("HTTP client not initialized.")
        return await self.client.request(method, url, **kwargs)

# Initialise sans config pour éviter l'import croisé
http_client = HttpClient()
