"""
app/api/v1/routers/categorias.py
---------------------------------
Router para gerenciamento de categorias de produtos.
Rota separada de /produtos para evitar conflitos de path parameters.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.produto import CategoriaCreate, CategoriaResponse
from app.services.produto_service import CategoriaService

router = APIRouter()


@router.get(
    "",
    response_model=list[CategoriaResponse],
    summary="Listar categorias",
    description="Lista todas as categorias disponíveis, ordenadas por nome.",
)
def listar_categorias(db: Session = Depends(get_db)) -> list[CategoriaResponse]:
    return CategoriaService(db).listar()


@router.post(
    "",
    response_model=CategoriaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar categoria",
    description="Cria nova categoria. Retorna 409 se o nome já existir.",
)
def criar_categoria(
    data: CategoriaCreate,
    db: Session = Depends(get_db),
) -> CategoriaResponse:
    return CategoriaService(db).criar(nome=data.nome, descricao=data.descricao)


@router.get(
    "/{categoria_id}",
    response_model=CategoriaResponse,
    summary="Buscar categoria por ID",
    description="Retorna categoria pelo ID. Retorna 404 se não encontrada.",
)
def buscar_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
) -> CategoriaResponse:
    return CategoriaService(db).buscar_por_id(categoria_id)
