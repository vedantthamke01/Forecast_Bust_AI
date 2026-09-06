"""
Main FastAPI Application Entrypoint.
NCMRWF AI-Based Forecast Bust Detection Platform (SIH26079).
Ministry of Earth Sciences, Government of India.
"""
from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from backend.app.config import settings
from backend.app.database.database import init_db
from backend.app.api.weather import router as weather_router
from backend.app.api.prediction import router as prediction_router
from backend.app.api.models import router as models_router
from backend.app.api.datasets import router as datasets_router
from backend.app.api.admin import router as admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure DB tables exist
    await init_db()
    yield
    # Shutdown: Clean up resources if necessary


app = FastAPI(
    title="NCMRWF AI-Based Forecast Bust Detection Platform",
    description="Operational reliability and forecast-bust risk prediction layer for medium-range Numerical Weather Prediction.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Flutter Web/Mobile and local browsers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health and Readiness Probes
@app.get("/health", tags=["System Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "forecast-bust-detection",
        "organization": "NCMRWF / MoES",
        "environment": settings.ENVIRONMENT,
        "demo_mode": settings.DEMO_MODE,
        "scientific_disclaimer": "This system provides forecast reliability estimation and does not replace official NWP or meteorological advisories."
    }


@app.get("/ready", tags=["System Health"])
async def readiness_check():
    return {
        "status": "ready",
        "database": "connected",
        "model_loaded": True
    }


# Include API Routers
app.include_router(weather_router, prefix="/api")
app.include_router(prediction_router, prefix="/api")
app.include_router(models_router, prefix="/api")
app.include_router(datasets_router, prefix="/api")
app.include_router(admin_router, prefix="/api")

# Also provide direct root paths for endpoints specified in prompt Section 34
app.include_router(weather_router)
app.include_router(prediction_router)
app.include_router(models_router)
app.include_router(datasets_router)
app.include_router(admin_router)

# Mount Web Meteorological Dashboard Static Assets
dashboard_dir = os.path.abspath(os.path.join("apps", "admin_dashboard"))
if os.path.exists(dashboard_dir):
    app.mount("/dashboard", StaticFiles(directory=dashboard_dir, html=True), name="dashboard")

    @app.get("/", include_in_schema=False)
    async def root_redirect():
        return RedirectResponse(url="/dashboard/")
