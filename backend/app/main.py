"""
SmartKYC FastAPI Application
Main entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    yield

app = FastAPI(
    title="SmartKYC API",
    description="Le Badge de Confiance du B2B Africain",
    version="1.0.0-hackathon",
    lifespan=lifespan
)

# Mount static files (logo, images, etc.)
# Mount static files (logo, images, etc.)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Mount data files (QR codes, badges)
import os
os.makedirs("data", exist_ok=True)
app.mount("/data", StaticFiles(directory="data"), name="data")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "SmartKYC API",
        "version": "1.0.0-hackathon",
        "status": "running"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Import routers
from app.api import auth_router, trustscores_router, documents_router, badges_router, verify_router

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(trustscores_router, prefix="/api/trustscores", tags=["trustscores"])
app.include_router(documents_router, prefix="/api/documents", tags=["documents"])
app.include_router(badges_router, prefix="/api/badges", tags=["badges"])
app.include_router(verify_router, prefix="/verify", tags=["verification"])
