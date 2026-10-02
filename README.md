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
- Degradación controlada cuando el modelo no está disponible.
- Archivos base para despliegue con Docker y Kubernetes.

## Arquitectura

```text
                         Agente de cartera
                                │
            ┌─────────────────────────────┐
            │                             │
            ▼                             ▼
  Modo estructurado                 Modo conversacional
       main.py                            chat.py
            │                             │
            │                    Lenguaje natural
            │                             │
            │                    Tools y fuentes locales
            └──────────────┬──────────────┘
                           ▼
                    Bedrock Runtime
                           │
                           ▼
                    Amazon Nova Lite
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
│   │   └── __init__.py
│   ├── test_agent.py
│   ├── test_clasificador.py
│   ├── test_conversational_agent.py
│   ├── test_repository.py
│   └── test_validacion.py
├── kubernetes/                 # Manifiestos base de Kubernetes
├── main.py                     # Interfaz de línea de comandos
├── chat.py                     # Interfaz conversacional
├── prompt.md                   # Instrucciones del agente
├── prompt_conversacional.md    # Reglas del modo conversacional
├── .env.example                # Ejemplo de configuración local
├── Dockerfile
└── requirements.txt
```

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
  -v
```

Actualmente no existe una prueba de integración automatizada contra Bedrock. Los comandos de `main.py` y `chat.py` funcionan como pruebas manuales reales y pueden generar cargos por tokens.

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

### La respuesta aparece duplicada o muestra `Tool #1`

El agente debe construirse con `callback_handler=None`. Esto desactiva la impresión incremental de Strands; `main.py` imprime solamente el resultado final.

## Costos

Las invocaciones reales a Bedrock se cobran según el modelo y la cantidad de tokens de entrada y salida. Las pruebas unitarias con mocks no llaman a Bedrock. Configura alertas en AWS Budgets antes de realizar pruebas extensas.

## Despliegue

### Docker

```bash
docker build -t cartera-strands-agent .
docker run --env-file .env cartera-strands-agent \
  --client-id 12345 \
  --deuda 8000000 \
  --dias-mora 75 \
  --incumplimientos 1
```

Para iniciar el modo conversacional dentro del contenedor:

```bash
docker run -it --env-file .env cartera-strands-agent python chat.py
```

### Kubernetes

Los manifiestos de `kubernetes/` son una base y deben revisarse antes de usarlos en producción, especialmente la gestión de secretos y la identidad IAM del workload:

```bash
kubectl apply -f kubernetes/
```

## AgentCore

Este repositorio no está desplegado en Amazon Bedrock AgentCore. AgentCore sería una etapa posterior para alojar el agente como servicio administrado, manejar sesiones y versiones, agregar observabilidad o memoria, y conectar herramientas empresariales mediante Gateway.
