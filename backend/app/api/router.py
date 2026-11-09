from fastapi import APIRouter

from app.api import admin, auth, bands, health

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(bands.router)
api_router.include_router(admin.router)
