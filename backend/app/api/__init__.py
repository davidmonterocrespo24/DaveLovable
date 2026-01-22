from fastapi import APIRouter

from app.api import chat, projects, firebase_proxy

api_router = APIRouter()

api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(firebase_proxy.router, prefix="/firebase", tags=["firebase"])
