from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.campuses.router import router as campuses_router
from app.modules.events.router import router as events_router
from app.modules.home.router import router as home_router
from app.modules.notes.router import router as notes_router
from app.modules.todos.router import router as todos_router
from app.modules.users.router import router as users_router
from app.modules.weather.router import router as weather_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=f"{settings.app_name} API",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    if settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    api = APIRouter(prefix="/api")

    @api.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    api.include_router(auth_router)
    api.include_router(users_router)
    api.include_router(todos_router)
    api.include_router(notes_router)
    api.include_router(weather_router)
    api.include_router(home_router)
    api.include_router(campuses_router)
    api.include_router(events_router)
    app.include_router(api)
    return app


app = create_app()
