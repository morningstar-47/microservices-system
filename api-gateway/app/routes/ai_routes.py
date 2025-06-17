from fastapi import APIRouter, Request, Response
from services.ai_service import proxy_ai
from fastapi.responses import JSONResponse

router = APIRouter()

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def ai_proxy(path: str, request: Request):
    try:
        response = await proxy_ai(f"/{path}", request)
        return Response(content=response.content, status_code=response.status_code, headers=dict(response.headers))
    except Exception as e:
        return JSONResponse(status_code=502, content={"detail": f"Ai service error: {str(e)}"})
