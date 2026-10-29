from fastapi import APIRouter

from app.core.deps import CurrentUser, SessionDep
from app.modules.home import service
from app.modules.home.schemas import HomeSummary

router = APIRouter(prefix="/home", tags=["home"])


@router.get("", response_model=HomeSummary)
async def read_home(user: CurrentUser, session: SessionDep) -> HomeSummary:
    """Resumen para la pantalla principal. El tiempo va aparte (/weather) porque depende
    de la ubicación del navegador y puede fallar sin afectar al resto."""
    return await service.get_summary(session, user)
