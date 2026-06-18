"""
conftest.py (raiz do projeto)
------------------------------
Fixtures compartilhadas para toda a suite de testes.

Estratégia de isolamento:
  Para cada teste (scope="function"):
    1. Cria um engine apontando para o banco de TESTES (porta 5433)
    2. Executa Base.metadata.create_all → cria todas as tabelas do zero
    3. Substitui get_db via dependency_overrides → API usa banco de teste
    4. Faz yield do TestClient → teste executa
    5. Limpa dependency_overrides
    6. Executa Base.metadata.drop_all → destrói todas as tabelas
    7. Fecha conexões do engine

Por que drop_all + create_all (e não rollback)?
  • Garante que o estado do banco é IDÊNTICO em cada teste
  • Não depende de transações ou savepoints
  • Mais simples e 100% confiável para isolamento
  • O banco de teste não tem volume — dados são descartáveis por design
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Importa app e as dependências que serão substituídas nos testes
from app.main import app
from app.api.deps import get_db
from app.core.database import Base

# Garante que todos os modelos estão registrados no Base.metadata
# IMPORTANTE: usar 'from app.models import ...' em vez de 'import app.models'
# para NÃO rebinder o nome 'app' (que já aponta para a instância FastAPI acima)
from app.models import AuditLog, Categoria, Produto  # noqa: F401 — efeito colateral necessário

# URL do banco de teste — lida de variável de ambiente ou usa valor padrão
TEST_DATABASE_URL: str = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:univassouras@localhost:5433/ecommerce_test",
)


@pytest.fixture(scope="function")
def client() -> TestClient:
    """
    Fixture principal. Fornece um TestClient conectado ao banco de testes.

    Ciclo de vida por teste:
      SETUP   → create_all (cria tabelas) + dependency_overrides (aponta para teste DB)
      YIELD   → teste executa com TestClient
      TEARDOWN→ dependency_overrides.clear() + drop_all (destrói tabelas) + dispose()

    scope="function" garante que cada teste começa com banco VAZIO.
    """
    # Cria engine específico para o banco de teste
    test_engine = create_engine(
        TEST_DATABASE_URL,
        pool_pre_ping=True,
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    # (a) Cria todas as tabelas no banco de teste
    Base.metadata.create_all(bind=test_engine)

    # (b) Override de get_db: substitui sessão de produção pela de teste
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # (c) Fornece o TestClient para o teste
    with TestClient(app) as test_client:
        yield test_client

    # (d) Teardown: limpa overrides e destrói tabelas
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture
def produto_existente(client: TestClient) -> dict:
    """
    Fixture auxiliar que depende de 'client' e pré-cria um produto no banco.

    Útil para testes que precisam de um produto já existente (GET, PATCH, DELETE).
    Evita duplicação do payload de criação em cada teste.
    """
    payload = {
        "nome": "Produto Teste",
        "preco": 99.90,
        "estoque": 10,
        "ativo": True,
    }
    response = client.post("/api/v1/produtos", json=payload)
    assert response.status_code == 201, (
        f"produto_existente falhou ao criar produto: {response.json()}"
    )
    return response.json()
