from fastapi import APIRouter, Request, Response
from services.user_service import proxy_user
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/v1/users")

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def user_proxy(path: str, request: Request):
    try:
        response = await proxy_user(f"/{path}", request)
        return Response(content=response.content, status_code=response.status_code, headers=dict(response.headers))
    except Exception as e:
        return JSONResponse(status_code=502, content={"detail": f"User service error: {str(e)}"})
