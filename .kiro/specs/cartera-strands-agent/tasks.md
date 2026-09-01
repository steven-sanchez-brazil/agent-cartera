# Plan de Implementación: cartera-strands-agent

## Visión General

Implementación por ciclos TDD estrictos (Red → Green → Refactor), siguiendo el orden de componentes definido en el diseño:
`_validate_input` → `clasificar_riesgo` → `determinar_estrategia` → `_load_system_prompt` → `run_agent`

Cada componente sigue este patrón: primero se escriben los tests (que fallan), luego se implementa el mínimo código para que pasen, luego se refactoriza.

## Tasks

- [x] 1. Configurar estructura del proyecto y dependencias
  - Crear `app/__init__.py` y `app/agent.py` con stubs vacíos (clases de datos, excepciones, firmas de funciones sin cuerpo)
  - Crear `tests/__init__.py`, `tests/integration/__init__.py` para habilitar descubrimiento de tests
  - Verificar que `requirements.txt` incluya `strands-agents`, `hypothesis`, `pytest`, `boto3`, `python-dotenv`
  - Crear `prompt.md` en el directorio raíz con el contenido exacto especificado en el Requerimiento 6.2
  - _Requerimientos: 6.1, 6.2, 7.1_

- [x] 2. Componente `_validate_input` — ciclo TDD completo
  - [x] 2.1 RED: Escribir tests para `_validate_input` en `tests/test_validacion.py`
    - Test unitario: campos faltantes lanzan `ValidationError` con nombres de campos
    - Test unitario: `dias_mora` negativo lanza `ValidationError`
    - Test unitario: `deuda` negativa lanza `ValidationError`
    - Test unitario: `client_id` vacío o solo espacios lanza `ValidationError`
    - Ejecutar `pytest tests/test_validacion.py` y confirmar que todos fallan (RED 🔴)
    - _Requerimientos: 1.2, 1.3, 1.4_

  - [ ]* 2.2 RED: Escribir property tests para `_validate_input` en `tests/test_validacion.py`
    - **Propiedad 3: Validación de campos faltantes**
    - **Valida: Requerimiento 1.2**
    - **Propiedad 4: Rechazo de valores numéricos negativos**
    - **Valida: Requerimiento 1.3**
    - **Propiedad 5: Rechazo de identificador de cliente vacío o solo espacios**
    - **Valida: Requerimiento 1.4**
    - Usar `@given` con `st.frozensets` para campos faltantes, `st.integers(max_value=-1)` para negativos, `st.text(alphabet=" \t\n")` para client_id vacío
    - Confirmar que los property tests también fallan (RED 🔴)

  - [x] 2.3 GREEN: Implementar `_validate_input` en `app/agent.py`
    - Implementar validación de campos faltantes/nulos con mensaje descriptivo
    - Implementar validación de valores numéricos `>= 0` para `deuda` y `dias_mora`
    - Implementar validación de `client_id` no vacío y no solo espacios
    - Ejecutar `pytest tests/test_validacion.py` y confirmar que todos pasan (GREEN 🟢)
    - _Requerimientos: 1.2, 1.3, 1.4_

  - [x] 2.4 REFACTOR: Refactorizar `_validate_input`
    - Consolidar lógica de validación si hay duplicación
    - Ejecutar `pytest tests/test_validacion.py` y confirmar que sigue en verde (REFACTOR 🔵)
    - _Requerimientos: 1.2, 1.3, 1.4_

- [x] 3. Checkpoint — Validar componente `_validate_input`
  - Ejecutar `pytest tests/test_validacion.py -v` y confirmar que todos los tests pasan
  - Asegurarse que no hay tests pendientes en rojo, preguntar al usuario si hay dudas.

- [x] 4. Componente `clasificar_riesgo` — ciclo TDD completo
  - [x] 4.1 RED: Escribir tests unitarios para `clasificar_riesgo` en `tests/test_clasificador.py`
    - Test: `dias_mora=0, incumplimientos=0` → `"BAJO"`
    - Test: `dias_mora=29, incumplimientos=0` → `"BAJO"`
    - Test: `dias_mora=30, incumplimientos=0` → `"MEDIO"`
    - Test: `dias_mora=60, incumplimientos=0` → `"MEDIO"`
    - Test: `dias_mora=0, incumplimientos=1` → `"MEDIO"`
    - Test: `dias_mora=61, incumplimientos=0` → `"ALTO"`
    - Test: `dias_mora=0, incumplimientos=2` → `"ALTO"`
    - Test de precedencia: `dias_mora=61, incumplimientos=1` → `"ALTO"` (ALTO gana sobre MEDIO)
    - Ejecutar `pytest tests/test_clasificador.py` y confirmar que fallan (RED 🔴)
    - _Requerimientos: 2.1, 2.2, 2.3, 2.4_

  - [ ]* 4.2 RED: Escribir property test para `clasificar_riesgo` en `tests/test_clasificador.py`
    - **Propiedad 1: Corrección total de la clasificación de riesgo**
    - **Valida: Requerimientos 2.1, 2.2, 2.3, 2.4**
    - Usar `@given(dias_mora=st.integers(min_value=0), incumplimientos=st.integers(min_value=0))`
    - Verificar que el resultado está en `{"BAJO", "MEDIO", "ALTO"}`
    - Verificar las tres ramas de clasificación con sus condiciones exactas y precedencia ALTO > MEDIO
    - `@settings(max_examples=100)`
    - Confirmar que el property test falla (RED 🔴)

  - [x] 4.3 GREEN: Implementar `clasificar_riesgo` en `app/agent.py`
    - Decorar con `@tool` de strands-agents
    - Implementar lógica condicional con precedencia: ALTO primero, luego MEDIO, luego BAJO
    - Ejecutar `pytest tests/test_clasificador.py -k "clasificar"` y confirmar que pasan (GREEN 🟢)
    - _Requerimientos: 2.1, 2.2, 2.3, 2.4_

  - [x] 4.4 REFACTOR: Refactorizar `clasificar_riesgo`
    - Simplificar condiciones si es posible, mantener la precedencia correcta
    - Ejecutar `pytest tests/test_clasificador.py -k "clasificar"` y confirmar verde (REFACTOR 🔵)

- [x] 5. Componente `determinar_estrategia` — ciclo TDD completo
  - [x] 5.1 RED: Escribir tests unitarios para `determinar_estrategia` en `tests/test_clasificador.py`
    - Test: `"BAJO"` → `"Seguimiento preventivo y recordatorio de pago"`
    - Test: `"MEDIO"` → `"Contacto directo y negociación de plan de pagos"`
    - Test: `"ALTO"` → `"Gestión prioritaria de cobranza y evaluación de acuerdo de pago"`
    - Ejecutar y confirmar que fallan (RED 🔴)
    - _Requerimientos: 3.1, 3.2, 3.3, 3.4_

  - [ ]* 5.2 RED: Escribir property test para `determinar_estrategia` en `tests/test_clasificador.py`
    - **Propiedad 2: Completitud del mapeo de estrategias de cobranza**
    - **Valida: Requerimientos 3.1, 3.2, 3.3, 3.4**
    - Usar `@given(nivel_riesgo=st.sampled_from(["BAJO", "MEDIO", "ALTO"]))`
    - Verificar que cada nivel retorna exactamente la cadena especificada
    - `@settings(max_examples=100)`
    - Confirmar que el property test falla (RED 🔴)

  - [x] 5.3 GREEN: Implementar `determinar_estrategia` en `app/agent.py`
    - Decorar con `@tool` de strands-agents
    - Implementar mapeo directo nivel_riesgo → estrategia con las cadenas exactas del diseño
    - Ejecutar `pytest tests/test_clasificador.py -k "estrategia"` y confirmar verde (GREEN 🟢)
    - _Requerimientos: 3.1, 3.2, 3.3, 3.4_

  - [x] 5.4 REFACTOR: Refactorizar `determinar_estrategia`
    - Considerar uso de diccionario para el mapeo si mejora legibilidad
    - Ejecutar `pytest tests/test_clasificador.py -k "estrategia"` y confirmar verde (REFACTOR 🔵)

- [x] 6. Checkpoint — Validar componentes clasificador
  - Ejecutar `pytest tests/test_clasificador.py -v` y confirmar que todos los tests pasan
  - Preguntar al usuario si hay dudas antes de continuar.

- [x] 7. Componente `_load_system_prompt` — ciclo TDD completo
  - [x] 7.1 RED: Escribir tests para `_load_system_prompt` en `tests/test_agent.py`
    - Test: lectura de `prompt.md` existente retorna su contenido como string
    - Test: verificar que el contenido de `prompt.md` es exactamente el especificado en Req 6.2
    - Test: `prompt.md` inexistente lanza `SystemPromptError`
    - Test: `prompt.md` sin permiso de lectura lanza `SystemPromptError`
    - Ejecutar `pytest tests/test_agent.py -k "prompt"` y confirmar que fallan (RED 🔴)
    - _Requerimientos: 6.1, 6.2, 6.3_

  - [x] 7.2 GREEN: Implementar `_load_system_prompt` en `app/agent.py`
    - Leer el archivo en la ruta dada, capturar `FileNotFoundError` y `PermissionError` → lanzar `SystemPromptError`
    - Ejecutar `pytest tests/test_agent.py -k "prompt"` y confirmar verde (GREEN 🟢)
    - _Requerimientos: 6.1, 6.2, 6.3_

  - [x] 7.3 REFACTOR: Refactorizar `_load_system_prompt`
    - Usar context manager (`with open(...)`) si no se usa ya
    - Ejecutar `pytest tests/test_agent.py -k "prompt"` y confirmar verde (REFACTOR 🔵)

- [x] 8. Componente `run_agent` — ciclo TDD completo
  - [x] 8.1 RED: Escribir tests unitarios para `run_agent` en `tests/test_agent.py`
    - Test: respuesta exitosa contiene `nivel_riesgo`, `accion_recomendada`, `justificacion` no nulos (mock LLM)
    - Test: LLM no disponible → `AgentResponse` con `nivel_riesgo` y `accion_recomendada` válidos, `justificacion` indica error, campo `error` poblado
    - Test: `prompt.md` ausente → `SystemPromptError` propagado
    - Test: `client_id` vacío → `ValidationError` propagado
    - Test: mensaje de error identifica la etapa del fallo (Req 5.3)
    - Test: `AWS_REGION` no definida → usa `us-east-1` por defecto (Req 7.2)
    - Ejecutar `pytest tests/test_agent.py -k "run_agent"` y confirmar que fallan (RED 🔴)
    - _Requerimientos: 1.1, 4.1, 4.3, 5.1, 5.2, 5.3, 6.3, 7.2_

  - [ ]* 8.2 RED: Escribir property tests para `run_agent` en `tests/test_agent.py`
    - **Propiedad 6: Completitud del contexto enviado al LLM**
    - **Valida: Requerimiento 4.2**
    - Usar `unittest.mock.patch` + `@given` para capturar el prompt enviado al LLM
    - Verificar que el prompt contiene `client_id`, `deuda`, `dias_mora`, `incumplimientos_previos`, `nivel_riesgo` y `estrategia`
    - `@settings(max_examples=50)`
    - **Propiedad 7: Completitud estructural de la respuesta**
    - **Valida: Requerimientos 5.1, 5.2**
    - Usar `@given` con entradas válidas y mock del LLM
    - Verificar que `nivel_riesgo`, `accion_recomendada` y `justificacion` están poblados y no son vacíos
    - `@settings(max_examples=50)`
    - Confirmar que los property tests fallan (RED 🔴)

  - [x] 8.3 GREEN: Implementar `run_agent` en `app/agent.py`
    - Invocar `_validate_input` y propagar `ValidationError` si falla
    - Invocar `_load_system_prompt("prompt.md")` y propagar `SystemPromptError` si falla
    - Construir el `Agent` de Strands con las herramientas `clasificar_riesgo` y `determinar_estrategia`
    - Leer `AWS_REGION` del entorno con fallback a `us-east-1`
    - Leer `BEDROCK_MODEL_ID` del entorno con fallback al modelo por defecto
    - Enviar al LLM el prompt del sistema + datos del cliente (los 6 campos requeridos)
    - En caso de fallo del LLM, capturar excepción y retornar `AgentResponse` con degradación controlada
    - Ejecutar `pytest tests/test_agent.py` y confirmar verde (GREEN 🟢)
    - _Requerimientos: 1.1, 4.1, 4.2, 4.3, 5.1, 5.2, 5.3, 6.1, 6.3, 7.1, 7.2_

  - [x] 8.4 REFACTOR: Refactorizar `run_agent`
    - Extraer construcción del mensaje al LLM a función auxiliar si mejora legibilidad
    - Ejecutar `pytest tests/test_agent.py` y confirmar que sigue en verde (REFACTOR 🔵)

- [x] 9. Checkpoint — Suite completa de tests unitarios y de propiedad
  - Ejecutar `pytest tests/test_validacion.py tests/test_clasificador.py tests/test_agent.py -v`
  - Confirmar que todos los tests pasan, preguntar al usuario si hay dudas.

- [ ] 10. Tests de integración
  - [ ]* 10.1 Escribir tests de integración en `tests/integration/test_agent_real.py`
    - Test: flujo completo con Bedrock real completa en menos de 30 segundos
    - Test: capturar llamada real al LLM y verificar que el contexto contiene los 6 campos requeridos
    - Test: justificación retornada menciona factores de clasificación explícitamente
    - Marcar con `pytest.mark.integration` para poder excluirlos de la ejecución por defecto
    - _Requerimientos: 4.1, 4.2, 4.4, 5.4_

- [x] 11. Archivos de infraestructura y configuración
  - [x] 11.1 Crear/verificar `Dockerfile`
    - Imagen base Python, copiar `wheels/` si existen, instalar dependencias desde `requirements.txt`
    - Copiar `app/`, `prompt.md`; definir `CMD` para ejecutar el agente
    - _Requerimientos: 7.3_

  - [x] 11.2 Crear/verificar manifiestos Kubernetes en `kubernetes/`
    - `deployment.yaml` con variables de entorno desde Secret/ConfigMap
    - `service.yaml` si el agente expone un endpoint HTTP
    - _Requerimientos: 7.4_

  - [x] 11.3 Crear/verificar `.env.example`
    - Incluir `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `BEDROCK_MODEL_ID` con valores de ejemplo
    - _Requerimientos: 7.1, 7.2_

- [x] 12. Checkpoint final — Todo integrado
  - Ejecutar `pytest tests/test_validacion.py tests/test_clasificador.py tests/test_agent.py -v`
  - Verificar que `Dockerfile`, manifiestos Kubernetes y `.env.example` existen y son consistentes
  - Preguntar al usuario si hay dudas antes de dar por finalizada la implementación.

## Notas

- Las subtareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- Cada tarea referencia requerimientos específicos para trazabilidad
- Los property tests usan Hypothesis con `max_examples=100` (50 para tests con mock del LLM)
- Los tests de integración (`tests/integration/`) requieren credenciales AWS reales y deben excluirse con `-m "not integration"` en CI
- El ciclo TDD es estricto: nunca implementar antes de que el test falle en rojo
