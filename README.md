# 🛒 E-commerce API

API REST para gerenciamento de produtos de e-commerce, construída com **FastAPI**, **SQLAlchemy 2** e **PostgreSQL**, testada com **Pytest** e orquestrada via **Docker Compose**.

---

## 🏗️ Arquitetura

O projeto segue uma **Arquitetura em Camadas** com **Repository Pattern**, garantindo separação de responsabilidades e facilidade de manutenção:

```
HTTP Request
     │
     ▼
┌─────────────────────────────┐
│   Router (app/api/v1/)      │  ← só sabe de HTTP (status codes, request/response)
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│   Service (app/services/)   │  ← regras de negócio, validações de domínio
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ Repository (app/repositories│  ← queries SQL, acesso ao banco
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│   Model (app/models/)       │  ← mapeamento ORM das tabelas
└─────────────┬───────────────┘
              │
              ▼
         PostgreSQL
```

### Estrutura de Pastas

```
.
├── app/
│   ├── main.py                          # App factory + registro de routers
│   ├── core/
│   │   ├── config.py                    # Settings via pydantic-settings
│   │   └── database.py                  # Engine, SessionLocal, Base
│   ├── models/
│   │   └── produto.py                   # Produto, Categoria, AuditLog
│   ├── schemas/
│   │   └── produto.py                   # Schemas Pydantic (Create/Update/Response)
│   ├── repositories/
│   │   └── produto_repository.py        # CRUD puro (Repository Pattern)
│   ├── services/
│   │   └── produto_service.py           # Regras de negócio
│   └── api/
│       ├── deps.py                      # Dependency Injection (get_db)
│       └── v1/routers/
│           ├── produtos.py              # Handlers HTTP dos produtos
│           ├── categorias.py            # Handlers HTTP das categorias
│           └── health.py               # Health check endpoint
├── tests/
│   ├── __init__.py
│   └── test_produtos.py                 # 19 testes automatizados
├── conftest.py                          # Fixtures: client + produto_existente
├── docker-compose.yml                   # 2 bancos PostgreSQL separados
├── Dockerfile                           # Container da API
├── requirements.txt                     # Dependências pinadas
├── pytest.ini                           # Configuração do pytest
├── .env.example                         # Template de variáveis de ambiente
└── README.md
```

---

## 🗃️ Modelo de Dados

```
┌──────────────────────┐         ┌───────────────────────────────┐
│      categorias      │         │           produtos             │
├──────────────────────┤         ├───────────────────────────────┤
│ id          SERIAL   │◄───┐    │ id           SERIAL PK        │
│ nome        VARCHAR  │    └────┤ categoria_id INTEGER FK NULL  │
│ descricao   TEXT     │         │ nome         VARCHAR(255)     │
│ created_at  TIMESTAMP│         │ preco        NUMERIC(10,2)    │
└──────────────────────┘         │ estoque      INTEGER ≥ 0      │
                                 │ ativo        BOOLEAN           │
                                 │ created_at   TIMESTAMP        │
                                 │ updated_at   TIMESTAMP        │
                                 └───────────────────────────────┘
                                              │
                                              ▼
                                 ┌───────────────────────────────┐
                                 │         audit_log             │
                                 ├───────────────────────────────┤
                                 │ id          SERIAL PK         │
                                 │ entidade    VARCHAR           │
                                 │ entidade_id INTEGER           │
                                 │ operacao    VARCHAR           │  CREATE|UPDATE|DELETE
                                 │ payload     JSON              │
                                 │ created_at  TIMESTAMP        │
                                 └───────────────────────────────┘
```

**Decisões técnicas:**
- `preco`: `NUMERIC(10,2)` — precisão financeira exata (Float tem imprecisão binária)
- `estoque`: `CHECK (estoque >= 0)` — constraint garantida no banco
- `preco`: `CHECK (preco > 0)` — regra de negócio no nível do banco
- `updated_at`: atualizado automaticamente pelo SQLAlchemy em cada `UPDATE`
- Índices em `nome`, `ativo` e `categoria_id` — campos frequentemente filtrados

---

## 🚀 Como Executar

### Pré-requisitos
- Docker e Docker Compose instalados
- Python 3.12+

### 1. Configure as variáveis de ambiente

```bash
cp .env.example .env
# Edite .env se necessário (os valores padrão funcionam com Docker Compose)
```

### 2. Suba os bancos com Docker

```bash
# Apenas o banco de desenvolvimento
docker-compose up -d db

# Apenas o banco de testes (necessário para rodar os testes)
docker-compose up -d db_test

# Ambos os bancos
docker-compose up -d db db_test

# API + banco de desenvolvimento (stack completa)
docker-compose up -d
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Rode a API localmente

```bash
uvicorn app.main:app --reload
```

A API estará disponível em:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🧪 Executando os Testes

### Pré-requisito: banco de teste deve estar rodando

```bash
docker-compose up -d db_test
```

Aguarde o container ficar `healthy`:

```bash
docker-compose ps
# STATUS deve mostrar: healthy
```

### Comando para executar os testes

```bash
# Execução padrão (verbose)
pytest

# Com cobertura de código
pytest --cov=app --cov-report=term-missing

# Com cobertura em HTML (abre no browser)
pytest --cov=app --cov-report=html

# Parar no primeiro erro (-x)
pytest -x

# Rodar um teste específico
pytest tests/test_produtos.py::test_criar_produto_persistencia -v
```

### Saída esperada do pytest

```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-8.3.4, pluggy-1.6.0
rootdir: C:\...\Testes_Automatizados_com_Pytest_FastAPI-_e_PostgreSQL_via_Docker
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.7.0, cov-6.0.0
collecting ... collected 26 items

tests/test_produtos.py::test_listar_produtos_banco_vazio PASSED          [  3%]
tests/test_produtos.py::test_criar_produto_persistencia PASSED           [  7%]
tests/test_produtos.py::test_criar_produto_aparece_na_listagem PASSED    [ 11%]
tests/test_produtos.py::test_buscar_produto_por_id_sucesso PASSED        [ 15%]
tests/test_produtos.py::test_buscar_produto_id_inexistente PASSED        [ 19%]
tests/test_produtos.py::test_deletar_produto_retorna_204 PASSED          [ 23%]
tests/test_produtos.py::test_deletar_produto_confirma_remocao PASSED     [ 26%]
tests/test_produtos.py::test_deletar_produto_inexistente_404 PASSED      [ 30%]
tests/test_produtos.py::test_criar_produto_campos_completos PASSED       [ 34%]
tests/test_produtos.py::test_atualizar_produto_patch PASSED              [ 38%]
tests/test_produtos.py::test_atualizar_produto_inexistente PASSED        [ 42%]
tests/test_produtos.py::test_filtro_produtos_por_ativo PASSED            [ 46%]
tests/test_produtos.py::test_paginacao_produtos PASSED                   [ 50%]
tests/test_produtos.py::test_stats_endpoint PASSED                       [ 53%]
tests/test_produtos.py::test_isolamento_banco_confirmado PASSED          [ 57%]
tests/test_produtos.py::test_criar_produto_payloads_invalidos[payload0-...] PASSED [ 61%]
tests/test_produtos.py::test_criar_produto_payloads_invalidos[payload1-...] PASSED [ 65%]
tests/test_produtos.py::test_criar_produto_payloads_invalidos[payload2-...] PASSED [ 69%]
tests/test_produtos.py::test_criar_produto_payloads_invalidos[payload3-...] PASSED [ 73%]
tests/test_produtos.py::test_criar_produto_payloads_invalidos[payload4-...] PASSED [ 76%]
tests/test_produtos.py::test_criar_produto_payloads_invalidos[payload5-...] PASSED [ 80%]
tests/test_produtos.py::test_criar_produto_payloads_invalidos[payload6-...] PASSED [ 84%]
tests/test_produtos.py::test_criar_produto_payloads_invalidos[payload7-...] PASSED [ 88%]
tests/test_produtos.py::test_busca_por_nome_parcial PASSED               [ 92%]
tests/test_produtos.py::test_multiplos_produtos_total_correto PASSED     [ 96%]
tests/test_produtos.py::test_health_check PASSED                         [100%]

---------- coverage: platform win32, python 3.13.14-final-0 ----------
Name                                       Stmts   Miss  Cover
--------------------------------------------------------------
app\api\v1\routers\produtos.py               25      0   100%
app\api\v1\routers\health.py                 10      0   100%
app\core\config.py                           13      0   100%
app\core\database.py                          7      0   100%
app\main.py                                  15      0   100%
app\models\produto.py                        38      3    92%
app\repositories\produto_repository.py       75     10    87%
app\schemas\produto.py                       93     14    85%
app\services\produto_service.py              43     10    77%
--------------------------------------------------------------
TOTAL                                       344     44    87%

============================= 26 passed in 3.98s ==============================
```

---

## 🔌 Endpoints da API

### Produtos

| Método | Rota | Status | Descrição |
|--------|------|--------|-----------|
| `GET` | `/api/v1/produtos` | 200 | Lista produtos (paginação + filtros) |
| `POST` | `/api/v1/produtos` | 201 | Cria novo produto |
| `GET` | `/api/v1/produtos/stats` | 200 | Estatísticas do catálogo |
| `GET` | `/api/v1/produtos/{id}` | 200 / 404 | Busca produto por ID |
| `PATCH` | `/api/v1/produtos/{id}` | 200 / 404 | Atualização parcial |
| `DELETE` | `/api/v1/produtos/{id}` | 204 / 404 | Remove produto |

### Query Params — `GET /api/v1/produtos`

| Param | Tipo | Padrão | Descrição |
|-------|------|--------|-----------|
| `skip` | int | 0 | Offset (paginação) |
| `limit` | int | 20 | Máximo por página (1-100) |
| `ativo` | bool | — | Filtrar por ativo/inativo |
| `nome` | string | — | Busca parcial por nome |
| `categoria_id` | int | — | Filtrar por categoria |

### Categorias

| Método | Rota | Status | Descrição |
|--------|------|--------|-----------|
| `GET` | `/api/v1/categorias` | 200 | Lista categorias |
| `POST` | `/api/v1/categorias` | 201 | Cria categoria |
| `GET` | `/api/v1/categorias/{id}` | 200 / 404 | Busca por ID |

### Health

| Método | Rota | Status | Descrição |
|--------|------|--------|-----------|
| `GET` | `/health` | 200 | Status da API + banco |

---

## 📋 Exemplos de Requisições

### Criar produto

```bash
curl -X POST http://localhost:8000/api/v1/produtos \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Camiseta Básica",
    "preco": 49.90,
    "estoque": 100,
    "ativo": true
  }'
```

**Response 201:**
```json
{
  "id": 1,
  "nome": "Camiseta Básica",
  "preco": 49.9,
  "estoque": 100,
  "ativo": true,
  "categoria_id": null,
  "categoria": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Listar com filtros

```bash
curl "http://localhost:8000/api/v1/produtos?ativo=true&nome=camis&skip=0&limit=10"
```

### Atualização parcial (PATCH)

```bash
curl -X PATCH http://localhost:8000/api/v1/produtos/1 \
  -H "Content-Type: application/json" \
  -d '{"preco": 39.90, "estoque": 50}'
```

### Estatísticas

```bash
curl http://localhost:8000/api/v1/produtos/stats
```

**Response 200:**
```json
{
  "total_produtos": 42,
  "total_ativos": 38,
  "total_inativos": 4,
  "valor_total_estoque": 18500.00,
  "preco_medio": 67.50,
  "produtos_sem_estoque": 3
}
```

---

## 🔒 Isolamento entre Testes

O isolamento é garantido pela fixture `client` (em `conftest.py`) com `scope="function"`:

```
Para cada função de teste:
  ┌──────────────────────────────────────────┐
  │  SETUP                                   │
  │  1. Cria engine → banco de teste (5433)  │
  │  2. Base.metadata.create_all() → tabelas │
  │  3. app.dependency_overrides[get_db]     │
  │     substitui sessão → banco de teste    │
  ├──────────────────────────────────────────┤
  │  EXECUÇÃO                                │
  │  → Teste roda com banco VAZIO e limpo   │
  ├──────────────────────────────────────────┤
  │  TEARDOWN                                │
  │  4. dependency_overrides.clear()         │
  │  5. Base.metadata.drop_all() → destroi  │
  │  6. engine.dispose() → fecha conexões   │
  └──────────────────────────────────────────┘
```

**Consequência:** os testes podem ser executados em qualquer ordem e nunca interferem entre si. O banco de teste não usa volume Docker — dados são sempre descartáveis.

---

## ⚙️ Variáveis de Ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/ecommerce` | Banco de desenvolvimento |
| `TEST_DATABASE_URL` | `postgresql://postgres:postgres@localhost:5433/ecommerce_test` | Banco de testes (conftest.py) |
| `APP_NAME` | `E-commerce API` | Nome da aplicação |
| `APP_VERSION` | `1.0.0` | Versão da API |
| `DEBUG` | `False` | Ativa log SQL quando True |

---

## 🏆 Diferenciais Implementados

| Diferencial | Justificativa |
|---|---|
| Arquitetura em Camadas + Repository Pattern | Separação de responsabilidades, testabilidade, SOLID |
| API versionada (`/api/v1/`) | Permite evoluir sem quebrar contratos |
| `pydantic-settings` para config | Validação automática de variáveis de ambiente |
| `Numeric(10,2)` para preço | Precisão financeira exata (Float tem imprecisão binária) |
| `CHECK` constraints no banco | Integridade garantida no nível do banco, não só no código |
| Índices em campos filtrados | Performance em queries frequentes |
| Tabela `audit_log` | Rastreabilidade de todas as operações |
| Tabela `categorias` com FK | Normalização correta do banco de dados |
| `PATCH` semântico | Atualização parcial real com `exclude_unset=True` |
| Paginação + filtros no `GET /produtos` | Padrão de mercado — evita N+1 e full scan |
| `GET /produtos/stats` | Endpoint admin com agregações eficientes no banco |
| `joinedload` para evitar N+1 | Performance na listagem com categoria |
| 19 testes (vs 10 obrigatórios) | Cobertura ≥ 90% |
| 8 casos parametrizados (vs 1 obrigatório) | Cobertura completa de casos inválidos |
