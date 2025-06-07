from fastapi import APIRouter, Request, Response
from services.report_service import proxy_report
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/v1")

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def report_proxy(path: str, request: Request):
    try:
        response = await proxy_report(f"/{path}", request)
        return Response(content=response.content, status_code=response.status_code, headers=dict(response.headers))
    except Exception as e:
        return JSONResponse(status_code=502, content={"detail": f"Report service error: {str(e)}"})
