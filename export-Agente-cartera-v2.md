# Export: cartera-strands-agent — Sesión de desarrollo

> Resumen estructurado de la sesión de diseño e implementación del agente de gestión de cartera vencida basado en AWS Strands.

---

## Idea original

Construir un agente de cartera básico basado en **AWS Strands** que:

1. Reciba información de un cliente (ID, deuda, días de mora, incumplimientos previos)
2. Analice los días de mora
3. Clasifique el riesgo (BAJO / MEDIO / ALTO)
4. Determine la estrategia de cobranza
5. Use el LLM para explicar la recomendación
6. Responda al usuario

**Ejemplo de uso:**
```
Cliente: 12345 | Deuda: $8.000.000 | Días de mora: 75 | Incumplimientos: 1

Riesgo: ALTO
Acción: Gestión prioritaria de cobranza y evaluación de acuerdo de pago.
Justificación: La mora supera los 60 días y existe un antecedente de incumplimiento.
```

---

## Decisiones tomadas en la sesión

| Decisión | Elección | Razón |
|---|---|---|
| Framework de agente | AWS Strands (`strands-agents`) | Requerimiento explícito |
| LLM backend | Amazon Bedrock (Claude 3 Sonnet) | Integración nativa con Strands |
| Herramientas | `@tool` de Strands | Clasificación determinista |
| Configuración | Variables de entorno + `.env` | Portabilidad en contenedores |
| Instrucciones del agente | `prompt.md` externo | Separación código/configuración |
| Metodología de desarrollo | TDD estricto (Red → Green → Refactor) | Calidad y cobertura desde el inicio |
| Testing de propiedades | Hypothesis (property-based testing) | Validación de invariantes universales |
| Despliegue | Docker + Kubernetes | Requerimiento DevOps explícito |

---

## Estructura del proyecto

```
cartera-strands-agent/
├── app/
│   ├── __init__.py
│   └── agent.py          # Lógica principal del agente
├── tests/
│   ├── __init__.py
│   ├── test_validacion.py    # Tests para _validate_input
│   ├── test_clasificador.py  # Tests para clasificar_riesgo y determinar_estrategia
│   ├── test_agent.py         # Tests para _load_system_prompt y run_agent
│   └── integration/
│       ├── __init__.py
│       └── test_agent_real.py
├── kubernetes/
│   ├── deployment.yaml
│   ├── secret.yaml
│   └── configmap.yaml
├── wheels/
├── prompt.md             # Instrucciones del sistema para el LLM
├── main.py               # CLI entrypoint
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

---

## Flujo del agente

```
Cliente/Consumidor
      ↓
run_agent(client_id, deuda, dias_mora, incumplimientos_previos)
      ↓
_validate_input()         → ValidationError si datos inválidos
      ↓
_load_system_prompt()     → SystemPromptError si prompt.md no existe
      ↓
Agent(Strands) con tools: [clasificar_riesgo, determinar_estrategia]
      ↓
clasificar_riesgo()       → BAJO | MEDIO | ALTO  (determinista)
      ↓
determinar_estrategia()   → texto de estrategia  (determinista)
      ↓
LLM (Bedrock)             → justificación en español
      ↓
AgentResponse(nivel_riesgo, accion_recomendada, justificacion)
```

---

## Reglas de clasificación de riesgo

| Condición | Nivel |
|---|---|
| `dias_mora < 30` AND `incumplimientos == 0` | BAJO |
| `30 <= dias_mora <= 60` OR `incumplimientos == 1` | MEDIO |
| `dias_mora > 60` OR `incumplimientos >= 2` | ALTO |

> ALTO tiene precedencia sobre MEDIO cuando ambas condiciones aplican.

## Estrategias de cobranza

| Nivel | Estrategia |
|---|---|
| BAJO | Seguimiento preventivo y recordatorio de pago |
| MEDIO | Contacto directo y negociación de plan de pagos |
| ALTO | Gestión prioritaria de cobranza y evaluación de acuerdo de pago |

---

## Ciclo TDD aplicado

```
① Escribir test → falla  (RED 🔴)
       ↓
② Implementar mínimo → pasa  (GREEN 🟢)
       ↓
③ Refactorizar → sigue pasando  (REFACTOR 🔵)
       ↓
   Repetir para el siguiente componente
```

**Orden de implementación:**
1. `_validate_input`
2. `clasificar_riesgo`
3. `determinar_estrategia`
4. `_load_system_prompt`
5. `run_agent`

**Resultado final: 32/32 tests en verde**

---

## Propiedades de corrección (Hypothesis)

| Propiedad | Descripción | Requerimiento |
|---|---|---|
| 1 | `clasificar_riesgo` siempre retorna BAJO/MEDIO/ALTO con reglas correctas | 2.1–2.4 |
| 2 | `determinar_estrategia` mapea exactamente las cadenas especificadas | 3.1–3.4 |
| 3 | `_validate_input` menciona cada campo None en el error | 1.2 |
| 4 | `_validate_input` rechaza valores negativos de deuda y dias_mora | 1.3 |
| 5 | `_validate_input` rechaza client_id vacío o solo whitespace | 1.4 |
| 6 | El contexto enviado al LLM contiene los 6 campos requeridos | 4.2 |
| 7 | `AgentResponse` siempre tiene los 3 campos principales poblados | 5.1–5.2 |

---

## Archivos clave

### `app/agent.py`

```python
"""
cartera-strands-agent — módulo principal del agente.
"""
import os
from dataclasses import dataclass
from typing import Optional

from strands import tool, Agent


@dataclass
class AgentResponse:
    nivel_riesgo: str
    accion_recomendada: str
    justificacion: str
    error: Optional[str] = None


class ValidationError(ValueError): ...
class SystemPromptError(RuntimeError): ...
class LLMUnavailableError(RuntimeError): ...


def _validate_input(client_id, deuda, dias_mora, incumplimientos_previos) -> None:
    # Verifica campos None, client_id vacío y valores numéricos >= 0

@tool
def clasificar_riesgo(dias_mora: int, incumplimientos_previos: int) -> str:
    if dias_mora > 60 or incumplimientos_previos >= 2:
        return "ALTO"
    if (30 <= dias_mora <= 60) or incumplimientos_previos == 1:
        return "MEDIO"
    return "BAJO"

@tool
def determinar_estrategia(nivel_riesgo: str) -> str:
    estrategias = {
        "BAJO": "Seguimiento preventivo y recordatorio de pago",
        "MEDIO": "Contacto directo y negociación de plan de pagos",
        "ALTO": "Gestión prioritaria de cobranza y evaluación de acuerdo de pago",
    }
    return estrategias[nivel_riesgo]

def run_agent(client_id, deuda, dias_mora, incumplimientos_previos) -> AgentResponse:
    # 1. Validar → 2. Cargar prompt → 3. Construir Agent →
    # 4. Clasificar determinista → 5. Invocar LLM con degradación controlada
```

### `prompt.md`

```markdown
# Agente de Gestión de Cartera

Eres un agente especializado en gestión de cartera vencida.
Tu responsabilidad es analizar la situación de cartera de un
cliente y recomendar una estrategia de cobranza.

## Objetivo
1. Identificar la información proporcionada del cliente.
2. Utilizar las herramientas disponibles para analizar la cartera.
3. Clasificar el riesgo del cliente.
4. Recomendar una acción de cobranza.
5. Explicar claramente la razón de la recomendación.

## Reglas de clasificación
La clasificación oficial debe provenir de las herramientas disponibles.
- BAJO: menos de 30 días de mora.
- MEDIO: entre 30 y 60 días de mora.
- ALTO: más de 60 días de mora.

## Restricciones
- No inventes información del cliente.
- No modifiques saldos. No condones deudas.
- No realices transacciones financieras.
- No prometas acuerdos de pago.
- Tu función es generar recomendaciones.

## Formato de respuesta
Cliente: | Deuda: | Días de mora: | Nivel de riesgo: | Acción recomendada: | Justificación:
```

### `requirements.txt`

```
strands-agents
hypothesis
pytest
boto3
python-dotenv
```

### `.env.example`

```
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

---

## Cómo probarlo

### Sin AWS (solo lógica determinista)

```bash
pip install -r requirements.txt

# Verificar clasificación del ejemplo del spec
python -c "
from app.agent import clasificar_riesgo, determinar_estrategia
riesgo = clasificar_riesgo(75, 1)
estrategia = determinar_estrategia(riesgo)
print(f'Riesgo: {riesgo}')
print(f'Acción: {estrategia}')
"

# Suite completa de tests (no requiere AWS)
python -m pytest tests/test_validacion.py tests/test_clasificador.py tests/test_agent.py -v
```

### Con AWS Bedrock

```bash
cp .env.example .env
# Editar .env con credenciales reales

# Caso del spec: cliente 12345, $8M, 75 días, 1 incumplimiento
python main.py --client-id 12345 --deuda 8000000 --dias-mora 75 --incumplimientos 1

# Salida JSON
python main.py --client-id 12345 --deuda 8000000 --dias-mora 75 --incumplimientos 1 --json
```

### Con Docker

```bash
docker build -t cartera-strands-agent .
docker run --env-file .env cartera-strands-agent \
  --client-id 12345 --deuda 8000000 --dias-mora 75 --incumplimientos 1
```

### Con Kubernetes

```bash
kubectl apply -f kubernetes/
```

---

## Variables de entorno

| Variable | Obligatoria | Default | Descripción |
|---|---|---|---|
| `AWS_REGION` | No | `us-east-1` | Región de AWS Bedrock |
| `AWS_ACCESS_KEY_ID` | Sí* | — | Credencial AWS |
| `AWS_SECRET_ACCESS_KEY` | Sí* | — | Credencial AWS |
| `BEDROCK_MODEL_ID` | No | `anthropic.claude-3-sonnet-20240229-v1:0` | Modelo LLM |

> *No requeridas si se usa IAM Role en Kubernetes.

---

## Manejo de errores

| Condición | Comportamiento |
|---|---|
| Campo faltante o None | `ValidationError` con nombre del campo |
| Valor numérico negativo | `ValidationError` indicando campo inválido |
| `client_id` vacío | `ValidationError` indicando campo obligatorio |
| `prompt.md` no encontrado | `SystemPromptError` |
| LLM no disponible | `AgentResponse` con clasificación válida + `justificacion` de error + campo `error` poblado |

---

## Commit sugerido

```
feat: initial implementation of cartera-strands-agent

Add AWS Strands-based portfolio management agent with TDD.

- Agent classifies client risk (BAJO/MEDIO/ALTO) based on days
  overdue and prior defaults using deterministic @tool functions
- LLM via Amazon Bedrock generates natural language justification
  with controlled degradation on failure
- System prompt externalized in prompt.md for auditability
- 32 unit and property-based tests (Hypothesis) covering all
  correctness properties
- Docker + Kubernetes manifests for container deployment
- CLI entrypoint via main.py
```

---

## Notas sobre Hypothesis

La carpeta `.hypothesis/` que aparece en el proyecto es generada automáticamente por la librería. Guarda los casos que fallaron en ejecuciones anteriores para repetirlos siempre en futuras corridas. Se recomienda agregar al `.gitignore` en proyectos personales, o incluirlo en proyectos de equipo para compartir casos encontrados.

```bash
echo ".hypothesis/" >> .gitignore
```
