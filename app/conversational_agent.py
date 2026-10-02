"""Construcción del agente conversacional de cartera."""

import os
from pathlib import Path

from dotenv import load_dotenv
from strands import Agent
from strands.models import BedrockModel

from app.agent import clasificar_riesgo, determinar_estrategia
from app.local_tools import (
    consultar_cliente,
    consultar_historial,
    consultar_politica,
    validar_datos_cartera,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPT_PATH = PROJECT_ROOT / "prompt_conversacional.md"
load_dotenv(PROJECT_ROOT / ".env")


def load_conversational_prompt() -> str:
    """Carga las instrucciones conversacionales desde una ruta estable."""
    return PROMPT_PATH.read_text(encoding="utf-8")


def create_conversational_agent() -> Agent:
    """Crea un agente con memoria de conversación durante el proceso actual."""
    model = BedrockModel(
        model_id=os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )
    return Agent(
        model=model,
        system_prompt=load_conversational_prompt(),
        tools=[
            consultar_cliente,
            consultar_historial,
            validar_datos_cartera,
            clasificar_riesgo,
            consultar_politica,
            determinar_estrategia,
        ],
        callback_handler=None,
    )
