"""
app/core/config.py
------------------
Configurações centralizadas da aplicação via pydantic-settings.

Por que pydantic-settings em vez de os.getenv?
  • Validação de tipos automática (ex: DATABASE_URL como PostgresDsn)
  • Falha rápida com mensagem clara se variável obrigatória não existir
  • Suporte nativo a arquivo .env
  • Cache com @lru_cache para evitar leituras repetidas de disco
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Banco de dados ────────────────────────────────────────────────────────
    # Valor padrão aponta para o banco de dev local; em produção/CI, sobrescreva
    # via variável de ambiente DATABASE_URL
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/ecommerce"

    # ── Metadados da aplicação ────────────────────────────────────────────────
    APP_NAME: str = "E-commerce API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "API REST para gerenciamento de produtos de e-commerce"

    # ── Comportamento ─────────────────────────────────────────────────────────
    DEBUG: bool = False

    # pydantic-settings: lê de variáveis de ambiente e opcionalmente de .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # ignora variáveis extras no .env (ex: TEST_DATABASE_URL)
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna instância única (singleton) das configurações.
    Usar @lru_cache garante que o arquivo .env seja lido apenas uma vez.
    """
    return Settings()


# Instância global — use `from app.core.config import settings` nos outros módulos
settings: Settings = get_settings()
