from fastapi.middleware.cors import CORSMiddleware
from config import CORS_ORIGINS

def setup_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
