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
│   └── test_produtos.py                 # 37 testes automatizados
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
- Python 3.13+

### 1. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

### 2. Suba os bancos com Docker

```bash
# Banco de teste (obrigatório para rodar os testes)
docker-compose up -d db_test

# Stack completa: API + banco de dev
docker-compose up -d
```

### 3. Crie o ambiente virtual e instale as dependências

```bash
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
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
# STATUS deve mostrar: (healthy)
```

### Ativar o ambiente virtual

```powershell
.venv\Scripts\Activate.ps1
# Se necessário: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Comandos de execução

```bash
# Execução padrão com cobertura
pytest --cov=app --cov-report=term-missing -v

# Parar no primeiro erro
pytest -x -v

# Gerar relatório HTML de cobertura
pytest --cov=app --cov-report=html
# Abrir: htmlcov/index.html
```

### ✅ Saída real da última execução

```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-8.3.4, pluggy-1.6.0
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.7.0, cov-6.0.0
collecting ... collected 37 items

tests/test_produtos.py::test_listar_produtos_banco_vazio PASSED          [  2%]
tests/test_produtos.py::test_criar_produto_persistencia PASSED           [  5%]
tests/test_produtos.py::test_criar_produto_aparece_na_listagem PASSED    [  8%]
tests/test_produtos.py::test_buscar_produto_por_id_sucesso PASSED        [ 10%]
tests/test_produtos.py::test_buscar_produto_id_inexistente PASSED        [ 13%]
tests/test_produtos.py::test_deletar_produto_retorna_204 PASSED          [ 16%]
tests/test_produtos.py::test_deletar_produto_confirma_remocao PASSED     [ 18%]
tests/test_produtos.py::test_deletar_produto_inexistente_404 PASSED      [ 21%]
tests/test_produtos.py::test_criar_produto_campos_completos PASSED       [ 24%]
tests/test_produtos.py::test_atualizar_produto_patch PASSED              [ 27%]
tests/test_produtos.py::test_atualizar_produto_inexistente PASSED        [ 29%]
tests/test_produtos.py::test_filtro_produtos_por_ativo PASSED            [ 32%]
tests/test_produtos.py::test_paginacao_produtos PASSED                   [ 35%]
tests/test_produtos.py::test_stats_endpoint PASSED                       [ 37%]
tests/test_produtos.py::test_isolamento_banco_confirmado PASSED          [ 40%]
tests/test_produtos.py::test_criar_produto_payloads_invalidos[payload0-...] PASSED [ 43%]
tests/test_produtos.py::test_criar_produto_payloads_invalidos[payload1-...] PASSED [ 45%]
tests/test_produtos.py::test_criar_produto_payloads_invalidos[payload2-...] PASSED [ 48%]
tests/test_produtos.py::test_criar_produto_payloads_invalidos[payload3-...] PASSED [ 51%]
tests/test_produtos.py::test_criar_produto_payloads_invalidos[payload4-...] PASSED [ 54%]
tests/test_produtos.py::test_criar_produto_payloads_invalidos[payload5-...] PASSED [ 56%]
tests/test_produtos.py::test_criar_produto_payloads_invalidos[payload6-...] PASSED [ 59%]
tests/test_produtos.py::test_criar_produto_payloads_invalidos[payload7-...] PASSED [ 62%]
tests/test_produtos.py::test_busca_por_nome_parcial PASSED               [ 64%]
tests/test_produtos.py::test_multiplos_produtos_total_correto PASSED     [ 67%]
tests/test_produtos.py::test_health_check PASSED                         [ 70%]
tests/test_produtos.py::test_criar_categoria PASSED                      [ 72%]
tests/test_produtos.py::test_listar_categorias PASSED                    [ 75%]
tests/test_produtos.py::test_buscar_categoria_por_id PASSED              [ 78%]
tests/test_produtos.py::test_buscar_categoria_inexistente_404 PASSED     [ 81%]
tests/test_produtos.py::test_criar_categoria_duplicada_retorna_409 PASSED [ 83%]
tests/test_produtos.py::test_criar_categoria_nome_vazio_422 PASSED       [ 86%]
tests/test_produtos.py::test_produto_com_categoria_e_filtro PASSED       [ 89%]
tests/test_produtos.py::test_patch_nome_invalido_422 PASSED              [ 91%]
tests/test_produtos.py::test_patch_preco_invalido_422 PASSED             [ 94%]
tests/test_produtos.py::test_patch_estoque_negativo_422 PASSED           [ 97%]
tests/test_produtos.py::test_criar_produto_nome_muito_longo_422 PASSED   [100%]

---------- coverage: platform win32, python 3.13.14-final-0 ----------
Name                                     Stmts   Miss  Cover
------------------------------------------------------------
app\api\deps.py                              3      0   100%
app\api\v1\routers\categorias.py            15      0   100%
app\api\v1\routers\health.py                10      0   100%
app\api\v1\routers\produtos.py              25      0   100%
app\core\config.py                          13      0   100%
app\core\database.py                         7      0   100%
app\main.py                                 15      0   100%
app\models\produto.py                       32      0   100%
app\repositories\produto_repository.py      75      0   100%
app\schemas\produto.py                      93      3    97%
app\services\produto_service.py             43      0   100%
------------------------------------------------------------
TOTAL                                      333      3    99%

============================= 37 passed in 5.73s ==============================
```

---

## 🔌 Endpoints da API

### Produtos

| Método | Rota | Status | Descrição |
|--------|------|--------|-----------|
| `GET` | `/api/v1/produtos` | 200 | Lista produtos (paginação + filtros) |
| `POST` | `/api/v1/produtos` | 201 | Cria novo produto |
| `GET` | `/api/v1/produtos/stats` | 200 | Estatísticas agregadas do catálogo |
| `GET` | `/api/v1/produtos/{id}` | 200 / 404 | Busca produto por ID |
| `PATCH` | `/api/v1/produtos/{id}` | 200 / 404 | Atualização parcial |
| `DELETE` | `/api/v1/produtos/{id}` | 204 / 404 | Remove produto |

### Query Params — `GET /api/v1/produtos`

| Param | Tipo | Padrão | Descrição |
|-------|------|--------|-----------|
| `skip` | int | 0 | Offset para paginação |
| `limit` | int | 20 | Máximo por página (1–100) |
| `ativo` | bool | — | Filtrar por ativo/inativo |
| `nome` | string | — | Busca parcial por nome (case-insensitive) |
| `categoria_id` | int | — | Filtrar por categoria |

### Categorias

| Método | Rota | Status | Descrição |
|--------|------|--------|-----------|
| `GET` | `/api/v1/categorias` | 200 | Lista categorias (ordenadas por nome) |
| `POST` | `/api/v1/categorias` | 201 / 409 | Cria categoria (409 se nome duplicado) |
| `GET` | `/api/v1/categorias/{id}` | 200 / 404 | Busca por ID |

### Health

| Método | Rota | Status | Descrição |
|--------|------|--------|-----------|
| `GET` | `/health` | 200 | Status da API e conectividade com o banco |

---

## 📋 Exemplos de Requisições

### Criar categoria

```bash
curl -X POST http://localhost:8000/api/v1/categorias \
  -H "Content-Type: application/json" \
  -d '{"nome": "Eletrônicos", "descricao": "Produtos eletrônicos em geral"}'
```

**Response 201:**
```json
{
  "id": 1,
  "nome": "Eletrônicos",
  "descricao": "Produtos eletrônicos em geral",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Criar produto

```bash
curl -X POST http://localhost:8000/api/v1/produtos \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Camiseta Básica",
    "preco": 49.90,
    "estoque": 100,
    "ativo": true,
    "categoria_id": 1
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
  "categoria_id": 1,
  "categoria": {
    "id": 1,
    "nome": "Eletrônicos",
    "created_at": "2024-01-15T10:30:00Z"
  },
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

## 🧪 Cobertura de Testes

### 37 testes em 11 grupos

| # | Teste | O que valida |
|---|-------|-------------|
| 1 | `test_listar_produtos_banco_vazio` | GET retorna lista vazia |
| 2 | `test_criar_produto_persistencia` | POST 201 + ID gerado pelo banco |
| 3 | `test_criar_produto_aparece_na_listagem` | Produto criado aparece no GET |
| 4 | `test_buscar_produto_por_id_sucesso` | GET /{id} 200 |
| 5 | `test_buscar_produto_id_inexistente` | GET /{id} 404 |
| 6 | `test_deletar_produto_retorna_204` | DELETE 204 sem body |
| 7 | `test_deletar_produto_confirma_remocao` | DELETE + GET 404 confirma remoção |
| 8 | `test_deletar_produto_inexistente_404` | DELETE /{id} inexistente 404 |
| 9 | `test_criar_produto_campos_completos` | Response com todos os campos + timestamps |
| 10 | `test_atualizar_produto_patch` | PATCH parcial preserva campos não enviados |
| 11 | `test_atualizar_produto_inexistente` | PATCH /{id} inexistente 404 |
| 12 | `test_filtro_produtos_por_ativo` | GET ?ativo=true filtra corretamente |
| 13 | `test_paginacao_produtos` | skip/limit + total real correto |
| 14 | `test_stats_endpoint` | GET /stats com métricas corretas |
| 15 | `test_isolamento_banco_confirmado` | Banco começa vazio em cada teste |
| 16–23 | `test_criar_produto_payloads_invalidos` | 8 casos inválidos → 422 (`@parametrize`) |
| 24 | `test_busca_por_nome_parcial` | GET ?nome= busca ilike |
| 25 | `test_multiplos_produtos_total_correto` | Total = N produtos exatos |
| 26 | `test_health_check` | GET /health 200 + banco connected |
| 27 | `test_criar_categoria` | POST /categorias 201 |
| 28 | `test_listar_categorias` | GET /categorias ordenado |
| 29 | `test_buscar_categoria_por_id` | GET /categorias/{id} 200 |
| 30 | `test_buscar_categoria_inexistente_404` | GET /categorias/{id} 404 |
| 31 | `test_criar_categoria_duplicada_retorna_409` | POST duplicado → 409 Conflict |
| 32 | `test_criar_categoria_nome_vazio_422` | Validator CategoriaCreate nome vazio |
| 33 | `test_produto_com_categoria_e_filtro` | Produto com categoria + filtro categoria_id |
| 34 | `test_patch_nome_invalido_422` | PATCH nome vazio/espaços → 422 |
| 35 | `test_patch_preco_invalido_422` | PATCH preco=0 ou negativo → 422 |
| 36 | `test_patch_estoque_negativo_422` | PATCH estoque negativo → 422 |
| 37 | `test_criar_produto_nome_muito_longo_422` | POST nome > 255 chars → 422 |

---

## 🔒 Isolamento entre Testes

Estratégia de isolamento via fixture `client` com `scope="function"`:

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

> O banco de teste (porta 5433) não usa volume Docker — dados são sempre descartáveis.

---

## ⚙️ Variáveis de Ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:univassouras@localhost:5432/ecommerce` | Banco de desenvolvimento |
| `TEST_DATABASE_URL` | `postgresql://postgres:univassouras@localhost:5433/ecommerce_test` | Banco de testes |
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
| Tabela `audit_log` | Rastreabilidade de todas as operações (CREATE/UPDATE/DELETE) |
| Tabela `categorias` com FK | Normalização correta do banco de dados |
| `PATCH` semântico | Atualização parcial real com `exclude_unset=True` |
| Paginação + filtros no `GET /produtos` | Padrão de mercado — evita full scan |
| `GET /produtos/stats` | Endpoint admin com agregações eficientes no banco |
| `joinedload` para evitar N+1 | Performance na listagem com categoria |
| **37 testes** (vs 10 obrigatórios) | Cobertura de 99% |
| **8 casos parametrizados** (vs 1 obrigatório) | Cobertura completa de casos inválidos |
| **99% de cobertura de código** | Qualidade e confiabilidade verificadas |
