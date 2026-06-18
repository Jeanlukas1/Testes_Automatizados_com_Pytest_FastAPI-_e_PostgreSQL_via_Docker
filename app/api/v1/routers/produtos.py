"""
app/api/v1/routers/produtos.py
-------------------------------
Router da entidade Produto — camada de apresentação HTTP.

Responsabilidade ÚNICA: lidar com HTTP.
  • Parseia request (Query params, body)
  • Chama o Service apropriado
  • Retorna Response com o status code correto

NÃO contém regras de negócio nem queries SQL.

IMPORTANTE — Ordem de declaração das rotas:
  /stats deve ser declarado ANTES de /{produto_id}.
  Se estiver depois, FastAPI tentaria fazer cast de "stats" para int
  e retornaria 422 em vez de resolver a rota corretamente.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.produto import (
    PaginatedProdutos,
    ProdutoCreate,
    ProdutoResponse,
    ProdutoStats,
    ProdutoUpdate,
)
from app.services.produto_service import ProdutoService

router = APIRouter()


# =============================================================================
# GET /produtos/stats  ← DEVE vir antes de /{produto_id}
# =============================================================================


@router.get(
    "/stats",
    response_model=ProdutoStats,
    summary="Estatísticas do catálogo",
    description=(
        "Retorna métricas agregadas: total de produtos, ativos, inativos, "
        "valor total em estoque, preço médio e produtos sem estoque."
    ),
)
def get_estatisticas(db: Session = Depends(get_db)) -> ProdutoStats:
    return ProdutoService(db).estatisticas()


# =============================================================================
# GET /produtos
# =============================================================================


@router.get(
    "",
    response_model=PaginatedProdutos,
    summary="Listar produtos",
    description="Lista todos os produtos com suporte a filtros e paginação.",
)
def listar_produtos(
    skip: int = Query(default=0, ge=0, description="Registros a pular (offset)"),
    limit: int = Query(default=20, ge=1, le=100, description="Máximo por página"),
    ativo: Optional[bool] = Query(default=None, description="Filtrar por ativo/inativo"),
    nome: Optional[str] = Query(default=None, description="Busca parcial por nome"),
    categoria_id: Optional[int] = Query(default=None, description="Filtrar por categoria"),
    db: Session = Depends(get_db),
) -> PaginatedProdutos:
    return ProdutoService(db).listar(
        skip=skip,
        limit=limit,
        ativo=ativo,
        nome=nome,
        categoria_id=categoria_id,
    )


# =============================================================================
# POST /produtos
# =============================================================================


@router.post(
    "",
    response_model=ProdutoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar produto",
    description="Cria um novo produto no catálogo. Retorna 422 se payload inválido.",
)
def criar_produto(
    data: ProdutoCreate,
    db: Session = Depends(get_db),
) -> ProdutoResponse:
    return ProdutoService(db).criar(data)


# =============================================================================
# GET /produtos/{produto_id}
# =============================================================================


@router.get(
    "/{produto_id}",
    response_model=ProdutoResponse,
    summary="Buscar produto por ID",
    description="Retorna produto pelo ID. Retorna 404 se não encontrado.",
)
def buscar_produto(
    produto_id: int,
    db: Session = Depends(get_db),
) -> ProdutoResponse:
    return ProdutoService(db).buscar_por_id(produto_id)


# =============================================================================
# PATCH /produtos/{produto_id}
# =============================================================================


@router.patch(
    "/{produto_id}",
    response_model=ProdutoResponse,
    summary="Atualizar produto parcialmente",
    description=(
        "Atualiza apenas os campos enviados no body (PATCH semântico). "
        "Campos ausentes não são alterados. Retorna 404 se não encontrado."
    ),
)
def atualizar_produto(
    produto_id: int,
    data: ProdutoUpdate,
    db: Session = Depends(get_db),
) -> ProdutoResponse:
    return ProdutoService(db).atualizar(produto_id, data)


# =============================================================================
# DELETE /produtos/{produto_id}
# =============================================================================


@router.delete(
    "/{produto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover produto",
    description="Remove produto permanentemente. Retorna 204 no sucesso, 404 se não existir.",
)
def remover_produto(
    produto_id: int,
    db: Session = Depends(get_db),
) -> None:
    ProdutoService(db).remover(produto_id)
