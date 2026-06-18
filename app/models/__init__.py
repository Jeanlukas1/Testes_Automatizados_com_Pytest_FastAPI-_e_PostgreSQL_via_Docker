"""
app/models/__init__.py
----------------------
Exporta todos os modelos para garantir que estejam registrados
no Base.metadata antes de qualquer chamada a create_all() / drop_all().

IMPORTANTE: este import é necessário para o conftest.py funcionar corretamente.
Quando 'from app.models import Produto, Categoria' é executado, o SQLAlchemy
registra as tabelas no metadata — sem isso, create_all() não cria nada.
"""

from app.models.produto import AuditLog, Categoria, Produto  # noqa: F401

__all__ = ["Produto", "Categoria", "AuditLog"]
