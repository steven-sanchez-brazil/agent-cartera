FROM python:3.11-slim

# Metadata
LABEL org.opencontainers.image.description="Cartera Strands Agent — Agente de gestión de cartera vencida"

# Variables de entorno con defaults
ENV AWS_REGION=us-east-1 \
    BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Copiar wheels locales si existen (se pueden instalar offline)
COPY --chown=root:root wheels/ /tmp/wheels/

# Instalar dependencias desde requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && if [ "$(ls -A /tmp/wheels/*.whl 2>/dev/null)" ]; then \
         pip install --no-cache-dir /tmp/wheels/*.whl; \
       fi \
    && rm -rf /tmp/wheels

# Copiar código fuente y prompt del sistema
COPY app/ ./app/
COPY prompt.md .
COPY main.py .

# Usuario no-root para seguridad
RUN useradd --no-create-home --shell /bin/false appuser
USER appuser

# Punto de entrada: ejecutar el agente como módulo
CMD ["python", "main.py"]
