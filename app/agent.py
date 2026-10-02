"""
cartera-strands-agent — módulo principal del agente.
"""
import os
from dataclasses import dataclass
from typing import Optional

from strands import Agent, tool
from strands.models import BedrockModel


# ---------------------------------------------------------------------------
# Clases de datos
# ---------------------------------------------------------------------------

@dataclass
class AgentResponse:
    nivel_riesgo: str            # BAJO | MEDIO | ALTO
    accion_recomendada: str      # Estrategia de cobranza
    justificacion: str           # Texto en español generado por LLM
    error: Optional[str] = None  # Mensaje de error si aplica


# ---------------------------------------------------------------------------
# Excepciones
# ---------------------------------------------------------------------------

class ValidationError(ValueError):
    """Entrada inválida o campos faltantes."""


class SystemPromptError(RuntimeError):
    """prompt.md no encontrado o no legible."""


class LLMUnavailableError(RuntimeError):
    """LLM no disponible o retornó error."""


# ---------------------------------------------------------------------------
# Funciones internas de soporte
# ---------------------------------------------------------------------------

def _validate_input(
    client_id: str,
    deuda: float,
    dias_mora: int,
    incumplimientos_previos: int,
) -> None:
    """Valida los campos de entrada.

    Lanza ValidationError con descripción de campos inválidos.
    """
    # 1. Verificar campos None — reporta todos los faltantes de una vez
    campos = {
        "client_id": client_id,
        "deuda": deuda,
        "dias_mora": dias_mora,
        "incumplimientos_previos": incumplimientos_previos,
    }
    campos_none = [nombre for nombre, valor in campos.items() if valor is None]
    if campos_none:
        raise ValidationError(
            f"Campos requeridos faltantes: {', '.join(campos_none)}"
        )

    # 2. Verificar que client_id no sea vacío ni solo whitespace
    if not client_id.strip():
        raise ValidationError("client_id es obligatorio y no puede estar vacío")

    # 3. Verificar que los campos numéricos sean >= 0 — reporta todos los inválidos
    campos_negativos = [
        nombre
        for nombre, valor in [
            ("deuda", deuda),
            ("dias_mora", dias_mora),
            ("incumplimientos_previos", incumplimientos_previos),
        ]
        if valor < 0
    ]
    if campos_negativos:
        raise ValidationError(
            f"Los valores de {', '.join(campos_negativos)} deben ser >= 0"
        )


def _load_system_prompt(path: str = "prompt.md") -> str:
    """Lee prompt.md y retorna su contenido.

    Lanza SystemPromptError si el archivo no existe o no puede ser leído.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise SystemPromptError(
            f"El archivo de instrucciones del sistema no fue encontrado: '{path}'"
        )
    except PermissionError:
        raise SystemPromptError(
            f"Sin permiso para leer el archivo de instrucciones del sistema: '{path}'"
        )


# ---------------------------------------------------------------------------
# Herramientas Strands (@tool)
# ---------------------------------------------------------------------------

@tool
def clasificar_riesgo(dias_mora: int, incumplimientos_previos: int) -> str:
    """Clasifica el nivel de riesgo del cliente: BAJO, MEDIO o ALTO."""
    # Precedencia: ALTO primero, luego MEDIO, luego BAJO
    if dias_mora > 60 or incumplimientos_previos >= 2:
        return "ALTO"
    if (30 <= dias_mora <= 60) or incumplimientos_previos == 1:
        return "MEDIO"
    return "BAJO"


@tool
def determinar_estrategia(nivel_riesgo: str) -> str:
    """Retorna la estrategia de cobranza según el nivel de riesgo."""
    estrategias = {
        "BAJO": "Seguimiento preventivo y recordatorio de pago",
        "MEDIO": "Contacto directo y negociación de plan de pagos",
        "ALTO": "Gestión prioritaria de cobranza y evaluación de acuerdo de pago",
    }
    return estrategias[nivel_riesgo]


# ---------------------------------------------------------------------------
# Función pública principal
# ---------------------------------------------------------------------------

def run_agent(
    client_id: str,
    deuda: float,
    dias_mora: int,
    incumplimientos_previos: int,
) -> AgentResponse:
    """Ejecuta el agente de cartera vencida.

    Valida la entrada, carga el prompt del sistema, construye el Agent de
    Strands y delega al LLM la generación de la justificación en lenguaje
    natural.

    Retorna AgentResponse con nivel_riesgo, accion_recomendada y
    justificacion. En caso de fallo del LLM aplica degradación controlada.
    """
    # 1. Validar entrada (propagar ValidationError)
    _validate_input(client_id, deuda, dias_mora, incumplimientos_previos)

    # 2. Cargar prompt del sistema (propagar SystemPromptError)
    system_prompt = _load_system_prompt("prompt.md")

    # 3. Leer configuración del entorno
    region = os.environ.get("AWS_REGION", "us-east-1")
    model_id = os.environ.get(
        "BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0"
    )

    # 4. Construir el Agent de Strands con las herramientas
    bedrock_model = BedrockModel(
        model_id=model_id,
        region_name=region,
    )

    agent = Agent(
        system_prompt=system_prompt,
        tools=[clasificar_riesgo, determinar_estrategia],
        model=bedrock_model,
        callback_handler=None,
    )

    # 5. Determinar clasificación determinista y construir el mensaje
    nivel_riesgo = clasificar_riesgo(dias_mora, incumplimientos_previos)
    estrategia = determinar_estrategia(nivel_riesgo)
    mensaje = _build_llm_message(
        client_id, deuda, dias_mora, incumplimientos_previos, nivel_riesgo, estrategia
    )

    # 6. Invocar LLM con degradación controlada
    try:
        respuesta_llm = agent(mensaje)
        justificacion = str(respuesta_llm)
        return AgentResponse(
            nivel_riesgo=nivel_riesgo,
            accion_recomendada=estrategia,
            justificacion=justificacion,
        )
    except Exception as e:
        return AgentResponse(
            nivel_riesgo=nivel_riesgo,
            accion_recomendada=estrategia,
            justificacion="Justificación no disponible por error del LLM.",
            error=f"Error en etapa LLM: {e}",
        )


def _build_llm_message(
    client_id: str,
    deuda: float,
    dias_mora: int,
    incumplimientos_previos: int,
    nivel_riesgo: str,
    estrategia: str,
) -> str:
    """Construye el mensaje con los 6 campos requeridos para enviar al LLM."""
    return (
        f"Analiza la siguiente información de cartera:\n"
        f"Cliente: {client_id}\n"
        f"Deuda: ${deuda:,.0f}\n"
        f"Días de mora: {dias_mora}\n"
        f"Incumplimientos previos: {incumplimientos_previos}\n"
        f"Nivel de riesgo: {nivel_riesgo}\n"
        f"Estrategia recomendada: {estrategia}\n"
    )
