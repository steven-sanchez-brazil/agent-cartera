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
COPY data/ ./data/
COPY prompt.md .
COPY prompt_conversacional.md .
COPY main.py .
COPY chat.py .
COPY static/ ./static/

# Usuario no-root para seguridad
RUN useradd --no-create-home --shell /bin/false appuser
USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3)"]

# Punto de entrada predeterminado: API y portal de demostración
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8080"]
