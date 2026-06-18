"""
app/models/produto.py
---------------------
Modelos SQLAlchemy que mapeiam as tabelas do banco de dados.

Entidades:
  • Categoria — normalização do tipo de produto (evita string duplicada)
  • Produto    — entidade principal do domínio
  • AuditLog   — rastreabilidade de operações (CREATE/UPDATE/DELETE)

Decisões técnicas:
  • preco: Numeric(10, 2) em vez de Float — precisão financeira exata.
    Float tem imprecisão binária: 19.99 pode virar 19.989999... no banco.
  • estoque: CHECK (estoque >= 0) — constraint no banco, não só no código
  • preco: CHECK (preco > 0) — regra de negócio garantida no nível do banco
  • updated_at com onupdate — SQLAlchemy atualiza o timestamp automaticamente
  • Índices em nome, ativo e categoria_id — campos frequentemente filtrados
  • categoria_id nullable — produto pode existir sem categoria (backward compat)
"""

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Categoria(Base):
    """
    Tabela auxiliar para normalização de categorias de produtos.
    Evita strings duplicadas na tabela de produtos e permite
    filtrar/agrupar por categoria de forma eficiente.
    """

    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False, unique=True)
    descricao = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relacionamento reverso — acesso via categoria.produtos
    produtos = relationship("Produto", back_populates="categoria", lazy="select")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Categoria id={self.id} nome={self.nome!r}>"


class Produto(Base):
    """
    Entidade principal do domínio de e-commerce.
    Representa um item do catálogo de produtos.
    """

    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, autoincrement=True)

    nome = Column(String(255), nullable=False)

    # Numeric(10, 2): suporta valores como 99999999.99 com precisão exata
    preco = Column(Numeric(10, 2), nullable=False)

    estoque = Column(Integer, nullable=False, default=0)

    ativo = Column(Boolean, nullable=False, default=True)

    # FK nullable: produto pode ser criado sem categoria
    categoria_id = Column(
        Integer,
        ForeignKey("categorias.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),  # atualizado automaticamente em cada UPDATE
        nullable=False,
    )

    categoria = relationship("Categoria", back_populates="produtos", lazy="select")

    __table_args__ = (
        # Constraints de integridade — garantidos no banco, não só no Python
        CheckConstraint("preco > 0", name="ck_produtos_preco_positivo"),
        CheckConstraint("estoque >= 0", name="ck_produtos_estoque_nao_negativo"),
        # Índices para queries frequentes
        Index("ix_produtos_nome", "nome"),
        Index("ix_produtos_ativo", "ativo"),
        Index("ix_produtos_categoria_id", "categoria_id"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Produto id={self.id} nome={self.nome!r} preco={self.preco}>"


class AuditLog(Base):
    """
    Tabela de auditoria para rastreabilidade de operações.
    Registra automaticamente CREATE, UPDATE e DELETE de entidades.

    Benefícios em produção:
      • Permite investigar quando/o que foi alterado
      • Requisito legal em muitos setores (LGPD, PCI-DSS)
      • Facilita debug de problemas em produção
    """

    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entidade = Column(String(100), nullable=False)   # ex: "Produto", "Categoria"
    entidade_id = Column(Integer, nullable=False)
    operacao = Column(String(20), nullable=False)     # "CREATE" | "UPDATE" | "DELETE"
    payload = Column(JSON, nullable=True)             # dados da operação (JSON)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_audit_log_entidade_id", "entidade", "entidade_id"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<AuditLog id={self.id} entidade={self.entidade!r} "
            f"operacao={self.operacao!r}>"
        )
