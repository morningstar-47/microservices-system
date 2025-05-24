from fastapi import APIRouter, Request, Response
from services.auth_service import proxy_auth
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/auth")

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def auth_proxy(path: str, request: Request):
    try:
        response = await proxy_auth(f"/{path}", request)
        return Response(content=response.content, status_code=response.status_code, headers=dict(response.headers))
    except Exception as e:
        return JSONResponse(status_code=502, content={"detail": f"Auth service error: {str(e)}"})
