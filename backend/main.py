from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
import assemblyai as aai
import uvicorn
from demo_router import router as demo_router
import logging

from api.router import router as api_router
from api.livekit import router as livekit_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

app = FastAPI(
    title="Healia - Voice-Powered AI Health Consultant",
    description="A voice-powered AI health consultant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, tags=["API"])
app.include_router(demo_router, tags=["Demo"])
app.include_router(livekit_router)

# Serve static files
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Healia - Voice-Powered AI Health Consultant",
        "version": "1.0.0",
        "endpoints": {
            "demo": "/api/demo",
            "livekit_token": "/api/livekit/token",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "healia-backend"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
