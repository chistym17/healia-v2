from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging
import uvicorn

from api.livekit import router as livekit_router
from api.pipeline_logs import router as pipeline_logs_router
from api.auth import router as auth_router
from api.sessions import router as sessions_router
from security.rate_limit import cors_origins, docs_enabled

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

_docs = "/docs" if docs_enabled() else None
_redoc = "/redoc" if docs_enabled() else None

app = FastAPI(
    title="Healia - Voice-Powered AI Health Consultant",
    description="A voice-powered AI health consultant",
    version="1.0.0",
    docs_url=_docs,
    redoc_url=_redoc,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(livekit_router)
app.include_router(pipeline_logs_router)
app.include_router(auth_router)
app.include_router(sessions_router)


@app.get("/")
async def root():
    endpoints = {
        "livekit_token": "/api/livekit/token",
        "auth": "/api/auth",
        "sessions": "/api/sessions",
        "health": "/health",
    }
    if docs_enabled():
        endpoints["docs"] = "/docs"
    return {
        "message": "Healia - Voice-Powered AI Health Consultant",
        "version": "1.0.0",
        "endpoints": endpoints,
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "healia-backend"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
