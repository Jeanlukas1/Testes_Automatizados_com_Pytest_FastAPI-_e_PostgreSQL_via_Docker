"""
app/main.py
-----------
App factory — ponto de entrada da aplicação FastAPI.

Usa o padrão factory function create_app() que:
  1. Cria a instância FastAPI com metadados
  2. Registra middlewares (CORS)
  3. Registra todos os routers com seus prefixos e tags
  4. Retorna a aplicação configurada

Por que factory function?
  • Torna o app testável — tests podem importar create_app() e criar
    instâncias isoladas se necessário
  • Evita efeitos colaterais no nível de módulo
  • Facilita configuração condicional (ex: middlewares diferentes em teste)

Uso:
  uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

# Importa modelos para garantir que estejam registrados no Base.metadata
# IMPORTANTE: usar from-import para NÃO rebinder o nome 'app' (FastAPI instance)
from app.models import AuditLog, Categoria, Produto  # noqa: F401

from app.api.v1.routers import categorias as categorias_router
from app.api.v1.routers import health as health_router
from app.api.v1.routers import produtos as produtos_router


def create_app() -> FastAPI:
    """Factory function que cria e configura a aplicação FastAPI."""

    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
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
        allow_origins=["*"],       # Em produção: restringir para domínios conhecidos
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
