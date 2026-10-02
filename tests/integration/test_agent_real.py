"""Prueba real opcional contra Bedrock; genera consumo de tokens."""

import os

import pytest

from app.conversational_agent import create_conversational_agent


pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    os.getenv("RUN_BEDROCK_INTEGRATION") != "1",
    reason="Define RUN_BEDROCK_INTEGRATION=1 para autorizar la llamada real",
)
def test_consulta_real_cliente_12345():
    agent = create_conversational_agent()
    respuesta = str(agent("Analiza el riesgo del cliente 12345"))

    assert "12345" in respuesta
    assert "ALTO" in respuesta.upper()
    assert "data/clientes.json" in respuesta
