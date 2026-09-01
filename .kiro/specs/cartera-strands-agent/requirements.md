# Documento de Requerimientos

## Introducción

El `cartera-strands-agent` es un agente de gestión de cartera construido sobre AWS Strands. Su responsabilidad es recibir información de un cliente deudor, analizar sus días de mora e incumplimientos previos, clasificar el nivel de riesgo, determinar la estrategia de cobranza más adecuada y generar una recomendación explicada mediante un LLM.

## Glosario

- **Agente**: El sistema `cartera-strands-agent`, construido sobre AWS Strands, que orquesta el análisis de cartera.
- **Cliente**: Persona o entidad identificada por un ID único que posee una deuda registrada.
- **Deuda**: Monto monetario total que el cliente adeuda, expresado en pesos colombianos (COP).
- **Días_de_mora**: Número de días calendario transcurridos desde la fecha de vencimiento de la obligación.
- **Incumplimientos_previos**: Número de veces que el cliente ha incumplido obligaciones financieras anteriores.
- **Nivel_de_riesgo**: Clasificación del riesgo crediticio del cliente: BAJO, MEDIO o ALTO.
- **Estrategia_de_cobranza**: Acción recomendada para la recuperación de la deuda según el nivel de riesgo.
- **LLM**: Modelo de lenguaje grande utilizado por el agente para generar justificaciones en lenguaje natural.
- **Clasificador**: Componente interno del agente responsable de determinar el nivel de riesgo y la estrategia.
- **Respuesta**: Objeto estructurado que contiene el nivel de riesgo, la acción recomendada y la justificación.

---

## Requerimientos

### Requerimiento 1: Recepción de información del cliente

**User Story:** Como analista de cobranza, quiero enviar la información de un cliente al agente, para que pueda ser procesada y analizada automáticamente.

#### Criterios de aceptación

1. THE Agente SHALL aceptar como entrada un identificador de cliente, el monto de la deuda, los días de mora y el número de incumplimientos previos.
2. WHEN la entrada recibida omite alguno de los campos requeridos, THE Agente SHALL retornar un mensaje de error indicando los campos faltantes.
3. WHEN el valor de días de mora o deuda es un número negativo, THE Agente SHALL retornar un mensaje de error indicando que los valores deben ser mayores o iguales a cero.
4. WHEN el identificador de cliente está vacío o es nulo, THE Agente SHALL retornar un mensaje de error indicando que el identificador es obligatorio.

---

### Requerimiento 2: Clasificación del nivel de riesgo

**User Story:** Como analista de cobranza, quiero que el agente clasifique automáticamente el riesgo del cliente, para priorizar los casos que requieren atención urgente.

#### Criterios de aceptación

1. WHEN los días de mora son menores a 30 e incumplimientos previos es igual a 0, THE Clasificador SHALL asignar el nivel de riesgo BAJO.
2. WHEN los días de mora están entre 30 y 60 inclusive, OR el número de incumplimientos previos es igual a 1, THE Clasificador SHALL asignar el nivel de riesgo MEDIO.
3. WHEN los días de mora superan los 60, OR el número de incumplimientos previos es mayor o igual a 2, THE Clasificador SHALL asignar el nivel de riesgo ALTO.
4. THE Clasificador SHALL producir exactamente uno de los valores: BAJO, MEDIO o ALTO como nivel de riesgo.

---

### Requerimiento 3: Determinación de la estrategia de cobranza

**User Story:** Como analista de cobranza, quiero que el agente recomiende una estrategia de acción según el nivel de riesgo, para guiar las gestiones del equipo.

#### Criterios de aceptación

1. WHEN el nivel de riesgo es BAJO, THE Clasificador SHALL asignar la estrategia: "Seguimiento preventivo y recordatorio de pago".
2. WHEN el nivel de riesgo es MEDIO, THE Clasificador SHALL asignar la estrategia: "Contacto directo y negociación de plan de pagos".
3. WHEN el nivel de riesgo es ALTO, THE Clasificador SHALL asignar la estrategia: "Gestión prioritaria de cobranza y evaluación de acuerdo de pago".
4. THE Clasificador SHALL asignar una estrategia de cobranza para cada nivel de riesgo posible.

---

### Requerimiento 4: Generación de justificación mediante LLM

**User Story:** Como analista de cobranza, quiero que el agente explique en lenguaje natural por qué se asignó ese nivel de riesgo y esa estrategia, para comprender la recomendación y comunicarla al cliente.

#### Criterios de aceptación

1. WHEN el nivel de riesgo y la estrategia han sido determinados, THE Agente SHALL invocar el LLM con los datos del cliente para generar una justificación en lenguaje natural en español.
2. THE LLM SHALL recibir como contexto el identificador del cliente, la deuda, los días de mora, los incumplimientos previos, el nivel de riesgo y la estrategia asignada.
3. WHEN el LLM no está disponible o retorna un error, THE Agente SHALL retornar la Respuesta con el nivel de riesgo y la estrategia calculados, e indicar que la justificación no está disponible.
4. THE LLM SHALL generar una justificación que mencione explícitamente los factores que determinaron la clasificación de riesgo.

---

### Requerimiento 5: Estructura de la respuesta al usuario

**User Story:** Como sistema consumidor del agente, quiero recibir una respuesta estructurada y consistente, para procesarla o presentarla de forma uniforme.

#### Criterios de aceptación

1. THE Agente SHALL retornar una Respuesta que incluya los campos: nivel de riesgo, acción recomendada y justificación.
2. WHEN el procesamiento es exitoso, THE Agente SHALL retornar el nivel de riesgo, la estrategia de cobranza y la justificación generada por el LLM.
3. WHEN ocurre un error en cualquier etapa del procesamiento, THE Agente SHALL retornar un mensaje de error descriptivo que identifique la etapa en la que ocurrió el fallo.
4. THE Agente SHALL completar el procesamiento de una solicitud y retornar la Respuesta en un tiempo máximo de 30 segundos en condiciones normales de operación.

---

### Requerimiento 6: Instrucciones del agente (prompt.md)

**User Story:** Como desarrollador del agente, quiero que las instrucciones del sistema estén definidas en un archivo `prompt.md`, para que el comportamiento del agente sea reproducible, auditable y separado del código.

#### Criterios de aceptación

1. THE Agente SHALL leer sus instrucciones de sistema desde el archivo `prompt.md` ubicado en el directorio raíz del proyecto.
2. THE archivo `prompt.md` SHALL contener exactamente el siguiente contenido:

```
# Agente de Gestión de Cartera

Eres un agente especializado en gestión de cartera vencida.
Tu responsabilidad es analizar la situación de cartera de un
cliente y recomendar una estrategia de cobranza.

## Objetivo

Debes:
1. Identificar la información proporcionada del cliente.
2. Utilizar las herramientas disponibles para analizar la cartera.
3. Clasificar el riesgo del cliente.
4. Recomendar una acción de cobranza.
5. Explicar claramente la razón de la recomendación.

## Reglas de clasificación

La clasificación oficial debe provenir de las herramientas
disponibles. No debes inventar una clasificación.

Como orientación:
- BAJO: menos de 30 días de mora.
- MEDIO: entre 30 y 60 días de mora.
- ALTO: más de 60 días de mora.

Los incumplimientos anteriores pueden incrementar el nivel
de riesgo.

## Restricciones

- No inventes información del cliente.
- No modifiques saldos.
- No condones deudas.
- No realices transacciones financieras.
- No prometas acuerdos de pago.
- Tu función es generar recomendaciones.
- Si faltan datos importantes, indícalo.

## Formato de respuesta

Cliente:
Deuda:
Días de mora:
Nivel de riesgo:
Acción recomendada:
Justificación:
```

3. WHEN el archivo `prompt.md` no existe o no puede ser leído al iniciar el agente, THE Agente SHALL retornar un error indicando que las instrucciones del sistema no están disponibles.

---

### Requerimiento 7: Configuración y despliegue

**User Story:** Como ingeniero DevOps, quiero que el agente sea desplegable en contenedores y configurable por variables de entorno, para integrarlo en infraestructuras Kubernetes existentes.

#### Criterios de aceptación

1. THE Agente SHALL leer las credenciales y parámetros de configuración exclusivamente desde variables de entorno definidas en el archivo `.env`.
2. WHERE la variable de entorno `AWS_REGION` no está definida, THE Agente SHALL usar `us-east-1` como valor por defecto.
3. THE Agente SHALL incluir un `Dockerfile` que permita construir una imagen de contenedor funcional sin modificaciones adicionales al código fuente.
4. THE Agente SHALL incluir manifiestos de Kubernetes en el directorio `kubernetes/` que permitan su despliegue en un cluster.
