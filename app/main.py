"""
app/main.py
-----------
App factory — ponto de entrada da aplicação FastAPI.

Usa o padrão factory function create_app() que:
  1. Cria a instância FastAPI com metadados e lifespan
  2. Registra middlewares (CORS)
  3. Registra todos os routers com seus prefixos e tags
  4. Retorna a aplicação configurada

Por que lifespan em vez de @on_event?
  • @on_event("startup") foi depreciado no FastAPI 0.93+
  • lifespan usa context manager — startup antes do yield, shutdown depois

Uso:
  uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine

# Importa modelos para garantir que estejam registrados no Base.metadata
# IMPORTANTE: usar from-import para NÃO rebinder o nome 'app' (FastAPI instance)
from app.models import AuditLog, Categoria, Produto  # noqa: F401

from app.api.v1.routers import categorias as categorias_router
from app.api.v1.routers import health as health_router
from app.api.v1.routers import produtos as produtos_router


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """
    Ciclo de vida da aplicação (FastAPI 0.93+ pattern).

    STARTUP: cria todas as tabelas no banco se ainda não existirem.
      - Base.metadata.create_all é idempotente: não recria tabelas existentes.
      - Adequado para desenvolvimento. Em produção com times, use Alembic.

    SHUTDOWN: pool de conexões é fechado automaticamente pelo SQLAlchemy.
    """
    Base.metadata.create_all(bind=engine)
    print(f"[{settings.APP_NAME}] Banco inicializado — tabelas criadas/verificadas ✓")
    yield
    print(f"[{settings.APP_NAME}] Encerrando...")


def create_app() -> FastAPI:
    """Factory function que cria e configura a aplicação FastAPI."""

    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        contact={
            "name": "API Support",
            "email": "suporte@ecommerce.com",
        },
        license_info={
            "name": "MIT",
        },
    )

    # ── Middlewares ───────────────────────────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    application.include_router(
        health_router.router,
        prefix="/health",
        tags=["health"],
    )
    application.include_router(
        produtos_router.router,
        prefix="/api/v1/produtos",
        tags=["produtos"],
    )
    application.include_router(
        categorias_router.router,
        prefix="/api/v1/categorias",
        tags=["categorias"],
    )

    return application


# Instância global — usada pelo uvicorn e pelos testes via dependency_overrides
app: FastAPI = create_app()
