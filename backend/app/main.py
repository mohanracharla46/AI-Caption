import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import FRONTEND_DIR, BASE_DIR
from app.api.routes import router as api_router

app = FastAPI(
    title="Tenglish Auto Caption Generator",
    description="Automatic speech recognition and Tenglish subtitle generator for videos",
    version="1.0.0"
)

# Enable CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(api_router)

# Mount samples directory if exists
SAMPLES_DIR = BASE_DIR / "samples"
if SAMPLES_DIR.exists():
    app.mount("/samples", StaticFiles(directory=str(SAMPLES_DIR)), name="samples")

@app.get("/health")
@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "Tenglish Auto Caption Generator"}

# Mount frontend static directory if exists
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
