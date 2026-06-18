"""
app/core/database.py
--------------------
Configuração central do SQLAlchemy:
  - Engine com pool de conexões otimizado
  - SessionLocal factory para injeção de dependência
  - Base declarativa que todos os modelos herdam

Decisões técnicas:
  • pool_pre_ping=True: testa conexões antes de usá-las (detecta conexões mortas)
  • pool_size=10 / max_overflow=20: configuração adequada para apps web com
    múltiplos workers
  • DeclarativeBase (SQLAlchemy 2.x) em vez do antigo declarative_base()
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,   # reconecta automaticamente após timeout de idle
    pool_size=10,          # conexões mantidas no pool
    max_overflow=20,       # conexões extras além do pool_size (temporárias)
    echo=settings.DEBUG,   # loga SQLs quando DEBUG=True (útil em desenvolvimento)
)

# ── Session Factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    autocommit=False,  # transações explícitas — garante atomicidade
    autoflush=False,   # flush manual — evita queries inesperadas durante o request
    bind=engine,
)


# ── Base Declarativa ──────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """
    Classe base que todos os modelos SQLAlchemy devem herdar.
    Registra automaticamente as tabelas em Base.metadata,
    permitindo o uso de Base.metadata.create_all() e drop_all().
    """
    pass
