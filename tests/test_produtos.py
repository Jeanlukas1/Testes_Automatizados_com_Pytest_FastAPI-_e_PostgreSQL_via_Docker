"""
tests/test_produtos.py
-----------------------
Suite de testes para a API de produtos.

Cobertura:
  ✓ Listagem com banco vazio
  ✓ Criação e persistência
  ✓ Criação aparece na listagem
  ✓ Busca por ID — sucesso
  ✓ Busca por ID — 404
  ✓ Deleção — 204
  ✓ Deleção confirma remoção com GET
  ✓ Deleção — inexistente → 404
  ✓ Campos completos no response
  ✓ PATCH — atualização parcial
  ✓ PATCH — inexistente → 404
  ✓ Filtro por ativo
  ✓ Paginação (skip/limit)
  ✓ Endpoint de estatísticas
  ✓ Isolamento do banco entre testes
  ✓ @parametrize — payloads inválidos → 422
  ✓ Busca por nome parcial (ilike)
  ✓ Múltiplos produtos na listagem
  ✓ Produto com categoria vinculada

Fixtures utilizadas (definidas em conftest.py):
  • client           → TestClient com banco de teste isolado
  • produto_existente → produto pré-criado no banco de teste
"""

import pytest
from fastapi.testclient import TestClient


# =============================================================================
# Factory Helper
# =============================================================================


def make_produto(**kwargs) -> dict:
    """
    Factory para criar payload de produto com valores padrão.
    Permite sobrescrever qualquer campo via kwargs — evita duplicação (DRY).
    """
    defaults = {
        "nome": "Camiseta Básica",
        "preco": 49.90,
        "estoque": 100,
        "ativo": True,
    }
    return {**defaults, **kwargs}


# =============================================================================
# 1. Listagem com banco vazio
# =============================================================================


def test_listar_produtos_banco_vazio(client: TestClient) -> None:
    """
    GET /api/v1/produtos com banco vazio deve retornar lista vazia
    e total igual a zero.
    """
    response = client.get("/api/v1/produtos")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


# =============================================================================
# 2. Criar produto e verificar persistência
# =============================================================================


def test_criar_produto_persistencia(client: TestClient) -> None:
    """
    POST /api/v1/produtos deve criar produto, retornar 201 e um ID gerado
    automaticamente pelo banco.
    """
    payload = make_produto()
    response = client.post("/api/v1/produtos", json=payload)

    assert response.status_code == 201
    data = response.json()

    # ID gerado pelo banco (não pelo cliente)
    assert "id" in data
    assert isinstance(data["id"], int)
    assert data["id"] > 0

    # Dados persistidos corretamente
    assert data["nome"] == payload["nome"]
    assert float(data["preco"]) == payload["preco"]
    assert data["estoque"] == payload["estoque"]
    assert data["ativo"] == payload["ativo"]


# =============================================================================
# 3. Criar produto e verificar na listagem
# =============================================================================


def test_criar_produto_aparece_na_listagem(client: TestClient) -> None:
    """
    Produto criado via POST deve aparecer no GET /api/v1/produtos.
    """
    payload = make_produto(nome="Calça Jeans Premium")
    client.post("/api/v1/produtos", json=payload)

    response = client.get("/api/v1/produtos")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["nome"] == "Calça Jeans Premium"


# =============================================================================
# 4. Buscar produto por ID — sucesso
# =============================================================================


def test_buscar_produto_por_id_sucesso(
    client: TestClient, produto_existente: dict
) -> None:
    """
    GET /api/v1/produtos/{id} deve retornar 200 com os dados do produto.
    """
    produto_id = produto_existente["id"]
    response = client.get(f"/api/v1/produtos/{produto_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == produto_id
    assert data["nome"] == produto_existente["nome"]
    assert float(data["preco"]) == float(produto_existente["preco"])


# =============================================================================
# 5. Buscar produto com ID inexistente — 404
# =============================================================================


def test_buscar_produto_id_inexistente(client: TestClient) -> None:
    """
    GET /api/v1/produtos/{id} com ID que não existe deve retornar 404.
    O detalhe do erro deve mencionar o ID buscado.
    """
    response = client.get("/api/v1/produtos/999999")

    assert response.status_code == 404
    assert "999999" in response.json()["detail"]


# =============================================================================
# 6. Deletar produto — retorna 204
# =============================================================================


def test_deletar_produto_retorna_204(
    client: TestClient, produto_existente: dict
) -> None:
    """
    DELETE /api/v1/produtos/{id} deve retornar 204 No Content.
    Body deve estar vazio (204 não tem body).
    """
    produto_id = produto_existente["id"]
    response = client.delete(f"/api/v1/produtos/{produto_id}")

    assert response.status_code == 204
    assert response.content == b""  # 204 não deve ter body


# =============================================================================
# 7. Deletar produto e confirmar remoção com GET
# =============================================================================


def test_deletar_produto_confirma_remocao(
    client: TestClient, produto_existente: dict
) -> None:
    """
    Após DELETE, um GET no mesmo ID deve retornar 404.
    Confirma que o produto foi de fato removido do banco.
    """
    produto_id = produto_existente["id"]

    delete_response = client.delete(f"/api/v1/produtos/{produto_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/v1/produtos/{produto_id}")
    assert get_response.status_code == 404


# =============================================================================
# 8. Deletar produto inexistente — 404
# =============================================================================


def test_deletar_produto_inexistente_404(client: TestClient) -> None:
    """
    DELETE /api/v1/produtos/{id} com ID inexistente deve retornar 404,
    não 500 ou 204 silencioso.
    """
    response = client.delete("/api/v1/produtos/999999")

    assert response.status_code == 404


# =============================================================================
# 9. Verificar todos os campos no response de criação
# =============================================================================


def test_criar_produto_campos_completos(client: TestClient) -> None:
    """
    O response de criação deve incluir todos os campos esperados,
    incluindo os gerados pelo banco (id, created_at, updated_at).
    """
    payload = make_produto()
    response = client.post("/api/v1/produtos", json=payload)

    assert response.status_code == 201
    data = response.json()

    campos_obrigatorios = {"id", "nome", "preco", "estoque", "ativo", "created_at", "updated_at"}
    assert campos_obrigatorios.issubset(data.keys()), (
        f"Campos ausentes: {campos_obrigatorios - set(data.keys())}"
    )
    # Timestamps devem ser strings ISO 8601
    assert isinstance(data["created_at"], str)
    assert isinstance(data["updated_at"], str)


# =============================================================================
# 10. Atualizar produto parcialmente (PATCH)
# =============================================================================


def test_atualizar_produto_patch(
    client: TestClient, produto_existente: dict
) -> None:
    """
    PATCH /api/v1/produtos/{id} deve atualizar apenas os campos enviados.
    Campos não enviados devem permanecer com o valor original.
    """
    produto_id = produto_existente["id"]
    nome_original = produto_existente["nome"]

    response = client.patch(
        f"/api/v1/produtos/{produto_id}",
        json={"preco": 149.90, "estoque": 50},
    )

    assert response.status_code == 200
    data = response.json()
    assert float(data["preco"]) == 149.90
    assert data["estoque"] == 50
    # Nome não foi enviado no PATCH — deve permanecer igual
    assert data["nome"] == nome_original


# =============================================================================
# 11. PATCH em produto inexistente — 404
# =============================================================================


def test_atualizar_produto_inexistente(client: TestClient) -> None:
    """
    PATCH /api/v1/produtos/{id} com ID inexistente deve retornar 404.
    """
    response = client.patch("/api/v1/produtos/999999", json={"preco": 10.0})

    assert response.status_code == 404


# =============================================================================
# 12. Filtro por ativo
# =============================================================================


def test_filtro_produtos_por_ativo(client: TestClient) -> None:
    """
    GET /api/v1/produtos?ativo=true deve retornar apenas produtos ativos.
    """
    client.post("/api/v1/produtos", json=make_produto(nome="Ativo", ativo=True))
    client.post("/api/v1/produtos", json=make_produto(nome="Inativo", ativo=False))

    response = client.get("/api/v1/produtos?ativo=true")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["nome"] == "Ativo"
    assert all(p["ativo"] for p in data["items"])


# =============================================================================
# 13. Paginação (skip/limit)
# =============================================================================


def test_paginacao_produtos(client: TestClient) -> None:
    """
    GET /api/v1/produtos?skip=0&limit=2 deve retornar 2 itens mas total=5.
    Verifica que paginação funciona sem truncar o total real.
    """
    for i in range(5):
        client.post("/api/v1/produtos", json=make_produto(nome=f"Produto {i + 1}"))

    response = client.get("/api/v1/produtos?skip=0&limit=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2  # página com 2 itens
    assert data["total"] == 5       # total real no banco
    assert data["skip"] == 0
    assert data["limit"] == 2


# =============================================================================
# 14. Endpoint de estatísticas
# =============================================================================


def test_stats_endpoint(client: TestClient) -> None:
    """
    GET /api/v1/produtos/stats deve retornar métricas agregadas corretas.
    """
    client.post("/api/v1/produtos", json=make_produto(nome="P1", preco=10.0, estoque=5, ativo=True))
    client.post("/api/v1/produtos", json=make_produto(nome="P2", preco=20.0, estoque=0, ativo=False))

    response = client.get("/api/v1/produtos/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["total_produtos"] == 2
    assert data["total_ativos"] == 1
    assert data["total_inativos"] == 1
    assert data["produtos_sem_estoque"] == 1
    assert float(data["valor_total_estoque"]) == 50.0  # 10 * 5 + 20 * 0


# =============================================================================
# 15. Isolamento do banco entre testes
# =============================================================================


def test_isolamento_banco_confirmado(client: TestClient) -> None:
    """
    Independente da ordem de execução, este teste verifica que o banco
    começa VAZIO. Prova que a fixture client com create_all/drop_all
    garante isolamento total entre testes.
    """
    response = client.get("/api/v1/produtos")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0, (
        "FALHA DE ISOLAMENTO: banco não estava vazio no início do teste. "
        f"Encontrado: {data['total']} produto(s)"
    )


# =============================================================================
# 16. @parametrize — Payloads inválidos → 422
# =============================================================================


@pytest.mark.parametrize(
    "payload, descricao",
    [
        ({}, "payload vazio — nome e preco obrigatórios ausentes"),
        ({"nome": "Produto X"}, "preco ausente — campo obrigatório"),
        ({"preco": 10.0}, "nome ausente — campo obrigatório"),
        ({"nome": "", "preco": 10.0}, "nome vazio — não permitido"),
        ({"nome": "   ", "preco": 10.0}, "nome só espaços — equivale a vazio"),
        ({"nome": "Produto X", "preco": 0}, "preco = 0 — deve ser maior que zero"),
        ({"nome": "Produto X", "preco": -5.0}, "preco negativo — inválido"),
        ({"nome": "Produto X", "preco": 10.0, "estoque": -1}, "estoque negativo — inválido"),
    ],
)
def test_criar_produto_payloads_invalidos(
    client: TestClient, payload: dict, descricao: str
) -> None:
    """
    Todos esses payloads devem ser rejeitados com 422 Unprocessable Entity.
    Valida que as regras de validação Pydantic estão funcionando.
    """
    response = client.post("/api/v1/produtos", json=payload)

    assert response.status_code == 422, (
        f"Esperado 422 para '{descricao}', mas recebeu {response.status_code}. "
        f"Body: {response.json()}"
    )


# =============================================================================
# 17. Busca por nome parcial (ilike)
# =============================================================================


def test_busca_por_nome_parcial(client: TestClient) -> None:
    """
    GET /api/v1/produtos?nome=Camiseta deve retornar apenas produtos cujo
    nome contém 'Camiseta' (busca case-insensitive).
    """
    client.post("/api/v1/produtos", json=make_produto(nome="Camiseta Azul"))
    client.post("/api/v1/produtos", json=make_produto(nome="Camiseta Vermelha"))
    client.post("/api/v1/produtos", json=make_produto(nome="Calça Jeans"))

    response = client.get("/api/v1/produtos?nome=Camiseta")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all("Camiseta" in p["nome"] for p in data["items"])


# =============================================================================
# 18. Múltiplos produtos na listagem — total correto
# =============================================================================


def test_multiplos_produtos_total_correto(client: TestClient) -> None:
    """
    Cria N produtos e verifica que o total retornado é exatamente N.
    """
    N = 7
    for i in range(N):
        client.post("/api/v1/produtos", json=make_produto(nome=f"Item {i + 1}"))

    response = client.get("/api/v1/produtos?limit=100")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == N
    assert len(data["items"]) == N


# =============================================================================
# 19. Health check
# =============================================================================


def test_health_check(client: TestClient) -> None:
    """
    GET /health deve retornar 200 com status 'healthy'
    e confirmar conectividade com o banco.
    """
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


# =============================================================================
# 20. Criar categoria
# =============================================================================


def test_criar_categoria(client):
    """POST /api/v1/categorias — 201 + campos corretos. Cobre router linha 39,
    CategoriaRepository.create, CategoriaService.criar."""
    payload = {"nome": "Eletrônicos", "descricao": "Produtos eletrônicos"}
    response = client.post("/api/v1/categorias", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["id"] > 0
    assert data["nome"] == "Eletrônicos"
    assert "created_at" in data


# =============================================================================
# 21. Listar categorias
# =============================================================================


def test_listar_categorias(client):
    """GET /api/v1/categorias — lista ordenada. Cobre router linha 25,
    CategoriaRepository.get_all."""
    client.post("/api/v1/categorias", json={"nome": "Roupas"})
    client.post("/api/v1/categorias", json={"nome": "Calçados"})

    response = client.get("/api/v1/categorias")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    nomes = [c["nome"] for c in data]
    assert nomes == sorted(nomes)


# =============================================================================
# 22. Buscar categoria por ID
# =============================================================================


def test_buscar_categoria_por_id(client):
    """GET /api/v1/categorias/{id} — 200. Cobre router linha 52,
    CategoriaRepository.get_by_id."""
    criado = client.post("/api/v1/categorias", json={"nome": "Informática"}).json()

    response = client.get(f"/api/v1/categorias/{criado['id']}")

    assert response.status_code == 200
    assert response.json()["nome"] == "Informática"


# =============================================================================
# 23. Buscar categoria inexistente — 404
# =============================================================================


def test_buscar_categoria_inexistente_404(client):
    """GET /api/v1/categorias/999999 — 404. Cobre CategoriaService linha 96/99."""
    response = client.get("/api/v1/categorias/999999")

    assert response.status_code == 404
    assert "999999" in response.json()["detail"]


# =============================================================================
# 24. Criar categoria duplicada — 409
# =============================================================================


def test_criar_categoria_duplicada_retorna_409(client):
    """POST categoria com nome já existente — 409. Cobre CategoriaService
    linha 102-108, CategoriaRepository.get_by_nome."""
    client.post("/api/v1/categorias", json={"nome": "Esportes"})
    response = client.post("/api/v1/categorias", json={"nome": "Esportes"})

    assert response.status_code == 409
    assert "Esportes" in response.json()["detail"]


# =============================================================================
# 25. Criar categoria com nome vazio — 422
# =============================================================================


def test_criar_categoria_nome_vazio_422(client):
    """POST categoria nome vazio/espacos — 422. Cobre schema CategoriaCreate
    linhas 40-43."""
    assert client.post("/api/v1/categorias", json={"nome": ""}).status_code == 422
    assert client.post("/api/v1/categorias", json={"nome": "   "}).status_code == 422


# =============================================================================
# 26. Produto com categoria + filtro por categoria_id
# =============================================================================


def test_produto_com_categoria_e_filtro(client):
    """Vincula produto a categoria e filtra por categoria_id. Cobre repositório
    linha 55 (filtro categoria_id) e response aninhado com categoria."""
    cat = client.post("/api/v1/categorias", json={"nome": "Games"}).json()
    cat_id = cat["id"]

    client.post("/api/v1/produtos", json={
        "nome": "Controle PS5", "preco": 399.0,
        "estoque": 5, "categoria_id": cat_id
    })
    client.post("/api/v1/produtos", json={
        "nome": "Teclado Mecânico", "preco": 250.0, "estoque": 10
    })

    response = client.get(f"/api/v1/produtos?categoria_id={cat_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["nome"] == "Controle PS5"
    assert data["items"][0]["categoria"]["nome"] == "Games"


# =============================================================================
# 27. PATCH com nome inválido — 422
# =============================================================================


def test_patch_nome_invalido_422(client, produto_existente):
    """PATCH nome vazio/espacos — 422. Cobre ProdutoUpdate.nome_valido
    linhas 123-128 de schemas.py."""
    pid = produto_existente["id"]

    assert client.patch(f"/api/v1/produtos/{pid}", json={"nome": ""}).status_code == 422
    assert client.patch(f"/api/v1/produtos/{pid}", json={"nome": "   "}).status_code == 422


# =============================================================================
# 28. PATCH com preco inválido — 422
# =============================================================================


def test_patch_preco_invalido_422(client, produto_existente):
    """PATCH preco=0 ou negativo — 422. Cobre ProdutoUpdate.preco_positivo
    linha 135 de schemas.py."""
    pid = produto_existente["id"]

    assert client.patch(f"/api/v1/produtos/{pid}", json={"preco": 0}).status_code == 422
    assert client.patch(f"/api/v1/produtos/{pid}", json={"preco": -1.0}).status_code == 422


# =============================================================================
# 29. PATCH com estoque negativo — 422
# =============================================================================


def test_patch_estoque_negativo_422(client, produto_existente):
    """PATCH estoque negativo — 422. Cobre ProdutoUpdate.estoque_nao_negativo
    linha 142 de schemas.py."""
    pid = produto_existente["id"]

    assert client.patch(f"/api/v1/produtos/{pid}", json={"estoque": -5}).status_code == 422


# =============================================================================
# 30. POST com nome muito longo — 422
# =============================================================================


def test_criar_produto_nome_muito_longo_422(client):
    """POST com nome de 256 chars — 422. Cobre ProdutoCreate.nome_valido
    linha 84 de schemas.py."""
    response = client.post("/api/v1/produtos", json={
        "nome": "X" * 256, "preco": 10.0
    })

    assert response.status_code == 422
