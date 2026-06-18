"""
app/schemas/produto.py
----------------------
Schemas Pydantic para validação de entrada e serialização de saída.

Separação de schemas:
  • *Base    — campos comuns (herança)
  • *Create  — payload de criação (POST) com validações
  • *Update  — payload de atualização parcial (PATCH) — todos opcionais
  • *Response — formato de saída da API (from_attributes=True para ORM)
  • *Stats / Paginated — schemas especializados para endpoints extras

Validações aplicadas:
  • nome: strip de espaços, não-vazio, máximo 255 chars
  • preco: maior que zero (Decimal, não float — precisão exata)
  • estoque: não negativo
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


# =============================================================================
# Categoria
# =============================================================================


class CategoriaBase(BaseModel):
    nome: str
    descricao: Optional[str] = None


class CategoriaCreate(CategoriaBase):
    @field_validator("nome")
    @classmethod
    def nome_nao_vazio(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nome da categoria não pode ser vazio")
        return v


class CategoriaResponse(CategoriaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# =============================================================================
# Produto — Base
# =============================================================================


class ProdutoBase(BaseModel):
    nome: str
    preco: Decimal
    estoque: int = 0
    ativo: bool = True
    categoria_id: Optional[int] = None


# =============================================================================
# Produto — Create (POST /produtos)
# =============================================================================


class ProdutoCreate(ProdutoBase):
    """
    Schema de criação. Todos os campos obrigatórios são validados.
    Pydantic retorna 422 automaticamente se a validação falhar.
    """

    @field_validator("nome")
    @classmethod
    def nome_valido(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nome não pode ser vazio")
        if len(v) > 255:
            raise ValueError("Nome não pode ter mais de 255 caracteres")
        return v

    @field_validator("preco")
    @classmethod
    def preco_positivo(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Preço deve ser maior que zero")
        return v

    @field_validator("estoque")
    @classmethod
    def estoque_nao_negativo(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Estoque não pode ser negativo")
        return v


# =============================================================================
# Produto — Update (PATCH /produtos/{id})
# =============================================================================


class ProdutoUpdate(BaseModel):
    """
    Schema para atualização parcial (PATCH).
    Todos os campos são opcionais — apenas os enviados são atualizados.
    model_dump(exclude_unset=True) no repository garante isso.
    """

    nome: Optional[str] = None
    preco: Optional[Decimal] = None
    estoque: Optional[int] = None
    ativo: Optional[bool] = None
    categoria_id: Optional[int] = None

    @field_validator("nome")
    @classmethod
    def nome_valido(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Nome não pode ser vazio")
            if len(v) > 255:
                raise ValueError("Nome não pode ter mais de 255 caracteres")
        return v

    @field_validator("preco")
    @classmethod
    def preco_positivo(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v <= 0:
            raise ValueError("Preço deve ser maior que zero")
        return v

    @field_validator("estoque")
    @classmethod
    def estoque_nao_negativo(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Estoque não pode ser negativo")
        return v


# =============================================================================
# Produto — Response (saída da API)
# =============================================================================


class ProdutoResponse(ProdutoBase):
    """
    Schema de saída. from_attributes=True permite criar a partir de objetos ORM.
    Inclui campos calculados pelo banco (id, created_at, updated_at).
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    categoria: Optional[CategoriaResponse] = None


# =============================================================================
# Schemas especializados
# =============================================================================


class ProdutoStats(BaseModel):
    """Métricas agregadas do catálogo — endpoint GET /produtos/stats."""

    total_produtos: int
    total_ativos: int
    total_inativos: int
    valor_total_estoque: Decimal
    preco_medio: Optional[Decimal]
    produtos_sem_estoque: int


class PaginatedProdutos(BaseModel):
    """
    Resposta paginada para GET /produtos.
    Inclui metadados de paginação além dos itens.
    """

    items: list[ProdutoResponse]
    total: int
    skip: int
    limit: int
