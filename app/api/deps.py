"""
app/api/deps.py
---------------
Dependências compartilhadas para injeção via FastAPI Depends().

get_db é o ponto central de injeção da sessão do banco.
Em testes, app.dependency_overrides[get_db] substitui esta função
por uma que aponta para o banco de teste — sem alterar nenhum outro código.
"""

from typing import Generator

from sqlalchemy.orm import Session

from app.core.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Dependency que fornece uma sessão de banco de dados por request.

    Uso:
        @router.get("/")
        def endpoint(db: Session = Depends(get_db)):
            ...

    Garante que a sessão seja sempre fechada, mesmo em caso de exceção,
    graças ao bloco finally.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
