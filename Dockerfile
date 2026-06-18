# =============================================================================
# Dockerfile — E-commerce API
# Imagem leve baseada em Python 3.12 slim
# =============================================================================

FROM python:3.12-slim

# Metadados
LABEL maintainer="ecommerce-api"
LABEL description="API REST para gerenciamento de produtos de e-commerce"

# Variáveis de ambiente para Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Instala dependências do sistema necessárias para psycopg2
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python
# (separado do COPY . . para aproveitar o cache do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copia o código-fonte
COPY . .

EXPOSE 8000

# Roda com uvicorn em modo produção
# Para desenvolvimento, o docker-compose sobrescreve com volume e hot-reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
