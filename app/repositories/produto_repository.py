"""
app/repositories/produto_repository.py
---------------------------------------
Camada de acesso a dados — Repository Pattern.

Responsabilidade ÚNICA: executar queries no banco de dados.
NÃO contém regras de negócio — isso é responsabilidade do Service.

Por que Repository Pattern?
  • Isola a lógica de banco em um único lugar
  • Service não precisa conhecer SQL
  • Facilita troca de ORM ou banco no futuro
  • Torna o código do Service testável com mocks simples
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session, joinedload

from app.models.produto import AuditLog, Categoria, Produto
from app.schemas.produto import ProdutoCreate, ProdutoUpdate


class ProdutoRepository:
    """Repositório para operações CRUD de Produto."""

    def __init__(self, db: Session) -> None:
        self._db = db

    # ── Leitura ──────────────────────────────────────────────────────────────

    def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        ativo: Optional[bool] = None,
        nome: Optional[str] = None,
        categoria_id: Optional[int] = None,
    ) -> tuple[list[Produto], int]:
        """
        Retorna página de produtos e total de registros.
        joinedload evita o problema N+1 ao carregar a categoria junto.
        """
        query = self._db.query(Produto).options(joinedload(Produto.categoria))

        filters = []
        if ativo is not None:
            filters.append(Produto.ativo == ativo)
        if nome:
            # ilike: busca case-insensitive com wildcard nos dois lados
            filters.append(Produto.nome.ilike(f"%{nome}%"))
        if categoria_id is not None:
            filters.append(Produto.categoria_id == categoria_id)

        if filters:
            query = query.filter(and_(*filters))

        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def get_by_id(self, produto_id: int) -> Optional[Produto]:
        """Busca produto por PK. Retorna None se não encontrado."""
        return (
            self._db.query(Produto)
            .options(joinedload(Produto.categoria))
            .filter(Produto.id == produto_id)
            .first()
        )

    def get_stats(self) -> dict:
        """Retorna métricas agregadas calculadas no banco (eficiente)."""
        total = self._db.query(func.count(Produto.id)).scalar() or 0
        total_ativos = (
            self._db.query(func.count(Produto.id))
            .filter(Produto.ativo.is_(True))
            .scalar()
            or 0
        )
        # Valor total em estoque: soma de (preco * estoque) por produto
        valor_total = (
            self._db.query(func.sum(Produto.preco * Produto.estoque)).scalar()
            or Decimal("0")
        )
        preco_medio = self._db.query(func.avg(Produto.preco)).scalar()
        sem_estoque = (
            self._db.query(func.count(Produto.id))
            .filter(Produto.estoque == 0)
            .scalar()
            or 0
        )

        return {
            "total_produtos": total,
            "total_ativos": total_ativos,
            "total_inativos": total - total_ativos,
            "valor_total_estoque": valor_total,
            "preco_medio": preco_medio,
            "produtos_sem_estoque": sem_estoque,
        }

    # ── Escrita ──────────────────────────────────────────────────────────────

    def create(self, data: ProdutoCreate) -> Produto:
        """Cria produto e faz commit. Retorna o objeto com id preenchido."""
        produto = Produto(**data.model_dump())
        self._db.add(produto)
        self._db.commit()
        self._db.refresh(produto)
        self._registrar_auditoria("CREATE", produto.id, data.model_dump())
        return produto

    def update(self, produto: Produto, data: ProdutoUpdate) -> Produto:
        """
        Atualização parcial — somente campos enviados (exclude_unset=True).
        Impede que campos ausentes no PATCH sobrescrevam valores existentes.
        """
        campos_antes = {
            "nome": produto.nome,
            "preco": str(produto.preco),
            "estoque": produto.estoque,
            "ativo": produto.ativo,
        }
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(produto, field, value)

        self._db.commit()
        self._db.refresh(produto)
        self._registrar_auditoria(
            "UPDATE", produto.id, {"antes": campos_antes, "depois": update_data}
        )
        return produto

    def delete(self, produto: Produto) -> None:
        """Remove produto permanentemente do banco."""
        produto_id = produto.id
        self._db.delete(produto)
        self._db.commit()
        self._registrar_auditoria("DELETE", produto_id, {"nome": produto.nome})

    # ── Auditoria ─────────────────────────────────────────────────────────────

    def _registrar_auditoria(
        self, operacao: str, produto_id: int, payload: dict
    ) -> None:
        """Registra operação na tabela de auditoria (best-effort)."""
        try:
            log = AuditLog(
                entidade="Produto",
                entidade_id=produto_id,
                operacao=operacao,
                payload=payload,
            )
            self._db.add(log)
            self._db.commit()
        except Exception:
            # Falha na auditoria não deve interromper a operação principal
            self._db.rollback()


class CategoriaRepository:
    """Repositório para operações CRUD de Categoria."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_all(self) -> list[Categoria]:
        return self._db.query(Categoria).order_by(Categoria.nome).all()

    def get_by_id(self, categoria_id: int) -> Optional[Categoria]:
        return (
            self._db.query(Categoria)
            .filter(Categoria.id == categoria_id)
            .first()
        )

    def get_by_nome(self, nome: str) -> Optional[Categoria]:
        return (
            self._db.query(Categoria)
            .filter(Categoria.nome == nome)
            .first()
        )

    def create(self, nome: str, descricao: Optional[str] = None) -> Categoria:
        categoria = Categoria(nome=nome, descricao=descricao)
        self._db.add(categoria)
        self._db.commit()
        self._db.refresh(categoria)
        return categoria
