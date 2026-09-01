# cartera-strands-agent

Agente de gestión de cartera vencida construido sobre **AWS Strands**. Recibe datos de un cliente deudor, clasifica su nivel de riesgo crediticio (BAJO / MEDIO / ALTO) y genera una recomendación de estrategia de cobranza explicada en lenguaje natural mediante Amazon Bedrock.

## Características

- Clasificación determinista de riesgo basada en días de mora e incumplimientos previos.
- Herramientas Strands (`@tool`) para `clasificar_riesgo` y `determinar_estrategia`.
- Instrucciones del agente externalizadas en `prompt.md` para facilitar auditoría.
- Degradación controlada ante fallos del LLM.
- Desplegable en contenedores Docker y clusters Kubernetes.

## Estructura del proyecto

```
cartera-strands-agent/
├── app/
│   ├── __init__.py
│   └── agent.py          # Lógica principal del agente
├── tests/
│   ├── __init__.py
│   ├── test_validacion.py
│   ├── test_clasificador.py
│   ├── test_agent.py
│   └── integration/
│       ├── __init__.py
│       └── test_agent_real.py
├── kubernetes/            # Manifiestos Kubernetes
├── wheels/                # Paquetes Python locales (opcional)
├── prompt.md              # Instrucciones del sistema para el LLM
├── .env.example           # Variables de entorno requeridas
├── Dockerfile
└── requirements.txt
```

## Configuración

Copia `.env.example` a `.env` y completa las variables:

```bash
cp .env.example .env
```

| Variable | Obligatoria | Valor por defecto | Descripción |
|---|---|---|---|
| `AWS_REGION` | No | `us-east-1` | Región de AWS Bedrock |
| `AWS_ACCESS_KEY_ID` | Sí* | — | Credenciales AWS |
| `AWS_SECRET_ACCESS_KEY` | Sí* | — | Credenciales AWS |
| `BEDROCK_MODEL_ID` | No | `anthropic.claude-3-sonnet-20240229-v1:0` | Modelo LLM |

> *No requeridas si se usa IAM Role en Kubernetes.

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

```python
from app.agent import run_agent

response = run_agent(
    client_id="CLI-001",
    deuda=5000000.0,
    dias_mora=45,
    incumplimientos_previos=1,
)

print(response.nivel_riesgo)       # MEDIO
print(response.accion_recomendada) # Contacto directo y negociación de plan de pagos
print(response.justificacion)      # Texto generado por el LLM
```

## Tests

```bash
# Tests unitarios y de propiedad (sin integración)
pytest tests/test_validacion.py tests/test_clasificador.py tests/test_agent.py -v

# Todos los tests incluyendo integración (requiere credenciales AWS reales)
pytest -v

# Excluir tests de integración
pytest -m "not integration" -v
```

## Despliegue

### Docker

```bash
docker build -t cartera-strands-agent .
docker run --env-file .env cartera-strands-agent
```

### Kubernetes

```bash
kubectl apply -f kubernetes/
```
