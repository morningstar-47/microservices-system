from fastapi import APIRouter, Request, Response
from services.map_service import proxy_map
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/v1/maps")

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def map_proxy(path: str, request: Request):
    try:
        response = await proxy_map(f"/{path}", request)
        return Response(content=response.content, status_code=response.status_code, headers=dict(response.headers))
    except Exception as e:
        return JSONResponse(status_code=502, content={"detail": f"Map service error: {str(e)}"})
