"""
app/services/produto_service.py
--------------------------------
Camada de negócio — Service Layer.

Responsabilidade: regras de domínio, validações de negócio e orquestração.
NÃO conhece HTTP (sem Request/Response), NÃO escreve SQL diretamente.

Fluxo:
  Router → Service → Repository → Banco

Por que separar Service de Repository?
  • Service pode orquestrar múltiplos repositórios
  • Regras de negócio ficam em um único lugar testável
  • Router não contém "if produto não existe, raise 404" espalhado em todo lugar
"""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.produto import Produto, Categoria
from app.repositories.produto_repository import CategoriaRepository, ProdutoRepository
from app.schemas.produto import (
    PaginatedProdutos,
    ProdutoCreate,
    ProdutoResponse,
    ProdutoStats,
    ProdutoUpdate,
)


class ProdutoService:
    """Serviço de domínio para produtos."""

    def __init__(self, db: Session) -> None:
        self._repo = ProdutoRepository(db)

    def listar(
        self,
        skip: int = 0,
        limit: int = 20,
        ativo: Optional[bool] = None,
        nome: Optional[str] = None,
        categoria_id: Optional[int] = None,
    ) -> PaginatedProdutos:
        """Lista produtos com paginação e filtros opcionais."""
        items, total = self._repo.get_all(
            skip=skip,
            limit=limit,
            ativo=ativo,
            nome=nome,
            categoria_id=categoria_id,
        )
        return PaginatedProdutos(items=items, total=total, skip=skip, limit=limit)

    def buscar_por_id(self, produto_id: int) -> Produto:
        """
        Retorna produto pelo ID.
        Lança HTTPException 404 se não encontrado — evita duplicar essa
        lógica em cada endpoint que precisa buscar produto.
        """
        produto = self._repo.get_by_id(produto_id)
        if not produto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produto com id={produto_id} não encontrado",
            )
        return produto

    def criar(self, data: ProdutoCreate) -> Produto:
        """Cria novo produto. Validação de schema já ocorreu no router."""
        return self._repo.create(data)

    def atualizar(self, produto_id: int, data: ProdutoUpdate) -> Produto:
        """Atualização parcial — busca o produto e aplica apenas os campos enviados."""
        produto = self.buscar_por_id(produto_id)
        return self._repo.update(produto, data)

    def remover(self, produto_id: int) -> None:
        """Remove produto. Lança 404 se não existir."""
        produto = self.buscar_por_id(produto_id)
        self._repo.delete(produto)

    def estatisticas(self) -> ProdutoStats:
        """Retorna métricas agregadas do catálogo."""
        stats = self._repo.get_stats()
        return ProdutoStats(**stats)


class CategoriaService:
    """Serviço de domínio para categorias."""

    def __init__(self, db: Session) -> None:
        self._repo = CategoriaRepository(db)

    def listar(self) -> list[Categoria]:
        return self._repo.get_all()

    def buscar_por_id(self, categoria_id: int) -> Categoria:
        categoria = self._repo.get_by_id(categoria_id)
        if not categoria:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Categoria com id={categoria_id} não encontrada",
            )
        return categoria

    def criar(self, nome: str, descricao: Optional[str] = None) -> Categoria:
        """Cria categoria. Verifica unicidade de nome antes de inserir."""
        existente = self._repo.get_by_nome(nome.strip())
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Categoria com nome '{nome}' já existe",
            )
        return self._repo.create(nome=nome.strip(), descricao=descricao)
