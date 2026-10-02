# cartera-strands-agent

Agente de gestión de cartera vencida construido con **Strands Agents SDK** y **Amazon Bedrock**. Recibe los datos de un cliente, clasifica su riesgo mediante reglas deterministas y utiliza un modelo fundacional para generar una justificación en lenguaje natural.

> Este proyecto ejecuta el agente localmente y consume modelos mediante Bedrock Runtime. No utiliza Amazon Bedrock AgentCore por el momento.

El proyecto representa **un solo producto: el agente de cartera**, con dos modos de operación. El modo estructurado recibe campos por CLI y el modo conversacional interpreta lenguaje natural y consulta fuentes locales. Técnicamente, cada modo crea su propia instancia de `strands.Agent`, pero no son dos agentes colaborando ni se ejecutan al mismo tiempo.

## Características

- Clasificación determinista de riesgo: `BAJO`, `MEDIO` o `ALTO`.
- Herramientas Strands (`@tool`) para clasificar el riesgo y determinar la estrategia.
- Integración con Amazon Bedrock mediante `BedrockModel`.
- Prompt del sistema externalizado en `prompt.md` para facilitar su auditoría.
- Salida de consola o JSON.
- Consultas en lenguaje natural con contexto durante la sesión.
- Fuentes locales ficticias para clientes, historial y políticas.
- Trazabilidad de las fuentes y versión de la política consultada.
- API HTTP con sesiones temporales separadas por `session_id`.
- Portal web responsive para presentar la demostración.
- Degradación controlada cuando el modelo no está disponible.
- Archivos base para despliegue con Docker y Kubernetes.

## Arquitectura

```text
Navegador ──→ Portal web ──→ FastAPI /v1/chat ──┐
                                                │
Terminal ──→ chat.py ──→ lenguaje natural ──────┤
                                                ├─→ Strands Agent
Sistema ──→ main.py ──→ campos estructurados ───┘         │
                                                          ├─→ tools
                                                          ├─→ fuentes locales
                                                          └─→ Bedrock Runtime
                                                                    │
                                                                    └─→ Nova Lite
```

La clasificación y la estrategia se calculan en el código. El modelo interpreta la consulta y genera la explicación, pero no decide por sí solo el nivel de riesgo.

### Diferencia entre los dos modos

| Modo | Entrada | Consulta fuentes locales | Mantiene contexto | Uso recomendado |
|---|---|---:|---:|---|
| Estructurado (`main.py`) | Argumentos como `--deuda` y `--dias-mora` | No | No | Automatizaciones que ya poseen todos los datos. |
| Conversacional (`chat.py`) | Preguntas en lenguaje natural | Sí | Sí, durante el proceso actual | Interacción con personas y exploración de los datos locales. |

Los modos no se llaman entre sí. Solo se instancia y ejecuta el seleccionado por el comando del usuario.

## Estructura

```text
cartera-strands-agent/
├── app/
│   ├── __init__.py
│   ├── api.py                # API FastAPI y sesiones de demostración
│   ├── agent.py              # Reglas y modo CLI estructurado
│   ├── conversational_agent.py # Construcción del agente conversacional
│   ├── local_tools.py        # Tools de consulta y validación
│   └── repository.py         # Lectura de fuentes locales
├── data/
│   ├── clientes.json
│   ├── historial.json
│   └── politicas.json
├── tests/
│   ├── integration/
│   │   ├── __init__.py
│   │   └── test_agent_real.py
│   ├── test_api.py
│   ├── test_agent.py
│   ├── test_clasificador.py
│   ├── test_conversational_agent.py
│   ├── test_repository.py
│   └── test_validacion.py
├── kubernetes/                 # Manifiestos base de Kubernetes
├── static/                     # Portal web de demostración
├── main.py                     # Interfaz de línea de comandos
├── chat.py                     # Interfaz conversacional
├── prompt.md                   # Instrucciones del agente
├── prompt_conversacional.md    # Reglas del modo conversacional
├── .env.example                # Ejemplo de configuración local
├── .dockerignore               # Exclusiones sensibles del contexto Docker
├── Dockerfile
├── pytest.ini                  # Marcador de pruebas de integración
└── requirements.txt
```

## Inicio rápido de la demo

```bash
python3.12 -m venv .venv312
source .venv312/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
aws sts get-caller-identity
uvicorn app.api:app --host 0.0.0.0 --port 8080 --reload
```

Después abre `http://127.0.0.1:8080` y utiliza uno de los casos sugeridos en pantalla.

## Requisitos

- Python 3.12 recomendado.
- Una cuenta de AWS con acceso a Amazon Bedrock.
- AWS CLI configurado o credenciales temporales/rol IAM equivalente.
- Permisos `bedrock:InvokeModel` y `bedrock:InvokeModelWithResponseStream` sobre el modelo utilizado.

## Instalación

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Configuración de AWS

Para desarrollo local se recomienda configurar AWS CLI en lugar de guardar claves permanentes en `.env`:

```bash
aws configure
aws sts get-caller-identity
```

Si la organización utiliza IAM Identity Center:

```bash
aws configure sso
aws sso login
```

Nunca confirmes un archivo `.env` con credenciales reales en Git.

### Variables de entorno

```bash
cp .env.example .env
```

Para comenzar con Amazon Nova Lite, el archivo puede contener solamente:

```dotenv
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=amazon.nova-lite-v1:0
```

| Variable | Obligatoria | Valor predeterminado en el código | Descripción |
|---|---:|---|---|
| `AWS_REGION` | No | `us-east-1` | Región desde la que se invoca Bedrock. |
| `BEDROCK_MODEL_ID` | No | `amazon.nova-lite-v1:0` | ID de modelo o de inference profile. Se recomienda definirlo explícitamente. |
| `AWS_PROFILE` | No | Perfil predeterminado de AWS | Perfil configurado con AWS CLI. |
| `AWS_SESSION_TOKEN` | Según el caso | — | Necesario cuando se utilizan credenciales temporales. |
| `MAX_DEMO_SESSIONS` | No | `100` | Número máximo de sesiones en memoria antes de retirar la más antigua. |

`boto3` también admite `AWS_ACCESS_KEY_ID` y `AWS_SECRET_ACCESS_KEY`, pero para desarrollo se prefieren perfiles, SSO o credenciales temporales.

### Uso de modelos Anthropic

Los modelos Claude pueden requerir dos pasos adicionales:

1. Completar una vez por cuenta el formulario de caso de uso de Anthropic desde **Amazon Bedrock → Model catalog → Anthropic**.
2. Utilizar un inference profile cuando el modelo no admite capacidad on-demand directa.

Ejemplo para Claude Sonnet 4.5 en Estados Unidos:

```dotenv
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
```

Consulta los perfiles disponibles antes de seleccionar uno:

```bash
aws bedrock list-inference-profiles \
  --region us-east-1 \
  --type-equals SYSTEM_DEFINED \
  --output table
```

## Uso desde la terminal

Elige solamente uno de los siguientes modos para cada ejecución.

### Modo conversacional

Utilízalo cuando una persona quiera consultar al agente en lenguaje natural y los datos deban recuperarse desde `data/`.

```bash
python chat.py
```

Ejemplos de consultas:

```text
Analiza el riesgo del cliente 12345
¿Cuánto debe el cliente 67890?
¿Qué gestión recomiendas para el cliente 12345?
Analiza un cliente
```

En el último caso, el agente solicitará el identificador faltante. El mismo proceso conserva el contexto de la conversación hasta que el usuario escriba `salir`.

Durante el análisis, el agente consulta las fuentes en `data/`, valida la información, aplica las reglas deterministas y reporta las fuentes utilizadas. Los datos incluidos son ficticios y deben reemplazarse por integraciones autorizadas antes de usar el proyecto en un entorno real.

### Modo estructurado

Utilízalo cuando otro proceso ya conozca todos los datos del cliente y necesite una ejecución puntual, predecible y fácil de automatizar.

Salida legible:

```bash
python main.py \
  --client-id 12345 \
  --deuda 8000000 \
  --dias-mora 75 \
  --incumplimientos 1
```

Salida JSON:

```bash
python main.py \
  --client-id 12345 \
  --deuda 8000000 \
  --dias-mora 75 \
  --incumplimientos 1 \
  --json
```

Resultado esperado:

```text
Cliente:             12345
Nivel de riesgo:     ALTO
Acción recomendada:  Gestión prioritaria de cobranza y evaluación de acuerdo de pago
Justificación:
<texto generado por el modelo>
```

La justificación puede variar. Si Bedrock falla, se conservan la clasificación y la estrategia deterministas, y la salida incluye una advertencia o el campo JSON `error`.

## Demo web y API

Inicia el servidor local:

```bash
uvicorn app.api:app --host 0.0.0.0 --port 8080 --reload
```

Abre en el navegador:

```text
http://127.0.0.1:8080
```

La interfaz permite iniciar sesiones, enviar consultas en lenguaje natural y ver el modelo, trace ID y fuentes reportadas en cada respuesta. Las sesiones se conservan solo en memoria y se pierden cuando el servidor se reinicia.

Cada `session_id` mantiene su propia instancia conversacional. Para limitar el consumo de memoria, la demo conserva hasta 100 sesiones por defecto y elimina la menos reciente al superar ese valor. Esto es apropiado para una demostración, no para producción ni para ejecutar múltiples réplicas.

Endpoints disponibles:

| Método | Ruta | Función |
|---|---|---|
| `GET` | `/health` | Comprueba que el proceso responde. |
| `GET` | `/ready` | Comprueba que las fuentes locales existen. |
| `POST` | `/v1/chat` | Envía un mensaje a una sesión conversacional. |
| `GET` | `/docs` | Documentación interactiva de FastAPI. |

Ejemplo de API:

```bash
curl -X POST http://127.0.0.1:8080/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "session_id": "demo-001",
    "user_id": "usuario-demo",
    "message": "Analiza el riesgo del cliente 12345"
  }'
```

Casos preparados para la demostración:

| Cliente | Escenario esperado |
|---|---|
| `10001` | Riesgo bajo. |
| `10002` | Riesgo medio por mora. |
| `10003` | Riesgo medio por antecedente. |
| `10004` | Riesgo alto por mora. |
| `10005` | Riesgo alto por incumplimientos. |
| `10006` | Historial faltante; el agente no debe asumir datos. |
| `10007` | Estado contradictorio; requiere revisión humana. |

## Uso desde Python

```python
from app.agent import run_agent

response = run_agent(
    client_id="CLI-001",
    deuda=5_000_000.0,
    dias_mora=45,
    incumplimientos_previos=1,
)

print(response.nivel_riesgo)        # MEDIO
print(response.accion_recomendada)  # Contacto directo y negociación de plan de pagos
print(response.justificacion)       # Texto generado por el modelo
print(response.error)               # None si Bedrock respondió correctamente
```

## Pruebas

Las pruebas existentes utilizan mocks y no consumen Bedrock:

```bash
python -m pytest \
  tests/test_validacion.py \
  tests/test_clasificador.py \
  tests/test_agent.py \
  tests/test_repository.py \
  tests/test_conversational_agent.py \
  tests/test_api.py \
  -v
```

Existe una prueba de integración opcional contra Bedrock. Los comandos de `main.py` y `chat.py` también funcionan como pruebas manuales reales y pueden generar cargos por tokens.

La prueba real opcional está separada para evitar consumo accidental. Ejecútala solamente cuando quieras autorizar una llamada a Bedrock:

```bash
RUN_BEDROCK_INTEGRATION=1 python -m pytest \
  tests/integration/test_agent_real.py \
  -m integration \
  -v
```

Para excluir siempre las llamadas reales:

```bash
python -m pytest -m "not integration" -v
```

## Solución de problemas

### `Invocation ... with on-demand throughput isn't supported`

El modelo necesita un inference profile. Consulta `list-inference-profiles` y utiliza un ID como `us.<proveedor>.<modelo>` en `BEDROCK_MODEL_ID`.

### `Model use case details have not been submitted`

La cuenta todavía no ha enviado el formulario de primer uso de Anthropic. Complétalo desde la ficha de un modelo Anthropic en **Model catalog**, o utiliza temporalmente Amazon Nova.

### `AccessDeniedException`

Comprueba la identidad:

```bash
aws sts get-caller-identity
```

La identidad necesita acceso al modelo o inference profile y los permisos de invocación indicados en la sección de requisitos.

### `NoCredentialsError: Unable to locate credentials` dentro de Docker

Las credenciales configuradas con AWS CLI permanecen en el equipo y no ingresan automáticamente al contenedor. Para una demo local, expórtalas temporalmente desde el perfil:

```bash
eval "$(aws configure export-credentials \
  --profile default \
  --format env)"
```

Si usas SSO o un perfil con otro nombre:

```bash
aws sso login --profile nombre-del-perfil
eval "$(aws configure export-credentials \
  --profile nombre-del-perfil \
  --format env)"
```

Pasa únicamente los nombres de las variables al contenedor, sin escribir sus valores en el comando:

```bash
docker run --rm \
  --env-file .env \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  -e AWS_SESSION_TOKEN \
  -p 8080:8080 \
  cartera-agent-demo
```

Al terminar:

```bash
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset AWS_SESSION_TOKEN
```

No guardes estas credenciales en `.env`, el Dockerfile, la imagen ni Git.

### La respuesta aparece duplicada o muestra `Tool #1`

El agente debe construirse con `callback_handler=None`. Esto desactiva la impresión incremental de Strands; `main.py` imprime solamente el resultado final.

## Costos

Las invocaciones reales a Bedrock se cobran según el modelo y la cantidad de tokens de entrada y salida. Las pruebas unitarias con mocks no llaman a Bedrock. Configura alertas en AWS Budgets antes de realizar pruebas extensas.

## Despliegue

### Docker

```bash
docker build -t cartera-agent-demo .
```

El contenedor no hereda automáticamente las credenciales de `aws configure`. Expórtalas como se explica en **Solución de problemas** y ejecútalo:

```bash
docker run --rm \
  --env-file .env \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  -e AWS_SESSION_TOKEN \
  -p 8080:8080 \
  cartera-agent-demo
```

Abre `http://127.0.0.1:8080`. La imagen inicia FastAPI mediante Uvicorn, expone el puerto 8080 y contiene un health check sobre `/health`.

Para ejecutar el modo estructurado dentro del contenedor:

```bash
docker run --rm \
  --env-file .env \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  -e AWS_SESSION_TOKEN \
  cartera-agent-demo \
  python main.py \
  --client-id 12345 \
  --deuda 8000000 \
  --dias-mora 75 \
  --incumplimientos 1
```

### Kubernetes

Los manifiestos de `kubernetes/` son una base y deben revisarse antes de usarlos en producción, especialmente la gestión de secretos y la identidad IAM del workload:

```bash
kubectl apply -f kubernetes/
```

## AgentCore

Este repositorio no está desplegado en Amazon Bedrock AgentCore. AgentCore sería una etapa posterior para alojar el agente como servicio administrado, manejar sesiones y versiones, agregar observabilidad o memoria, y conectar herramientas empresariales mediante Gateway.

## Alcance y limitaciones de la demo

- Todos los clientes y movimientos son ficticios.
- Las fuentes JSON son de solo lectura y simulan sistemas empresariales.
- Las sesiones se almacenan en RAM y se pierden al reiniciar.
- No existe autenticación ni autorización corporativa.
- Un `user_id` identifica la solicitud, pero todavía no concede ni restringe permisos.
- El agente recomienda; no modifica deudas, crea acuerdos ni ejecuta pagos.
- El portal y la API no deben exponerse públicamente sin autenticación, HTTPS, límites de tráfico y persistencia apropiada.
- Para Kubernetes se debe usar una identidad de workload, como EKS Pod Identity; para AgentCore se debe asignar un rol IAM al runtime. No se deben distribuir claves estáticas.
