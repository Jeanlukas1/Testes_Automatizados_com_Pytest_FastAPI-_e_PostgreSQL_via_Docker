"""
app/api/v1/routers/health.py
-----------------------------
Endpoint de health check — verifica API e conectividade com banco.
Útil para load balancers, Kubernetes liveness/readiness probes e monitoramento.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings

router = APIRouter()


@router.get(
    "",
    summary="Health check",
    description=(
        "Verifica o status da API e a conectividade com o banco de dados. "
        "Retorna 200 se tudo estiver saudável."
    ),
    response_description="Status da aplicação",
)
def health_check(db: Session = Depends(get_db)) -> dict:
    # Executa query mínima para confirmar conectividade com o banco
    db.execute(text("SELECT 1"))
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": "connected",
    }
