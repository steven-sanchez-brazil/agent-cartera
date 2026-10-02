"""Pruebas de configuración del agente conversacional sin invocar Bedrock."""

from unittest.mock import patch

from app.conversational_agent import (
    create_conversational_agent,
    load_conversational_prompt,
)


def test_prompt_exige_fuentes_y_datos_faltantes():
    prompt = load_conversational_prompt()
    assert "No inventes" in prompt
    assert "consultar_cliente" in prompt
    assert "Fuentes consultadas" in prompt


def test_agente_usa_nova_y_region_por_defecto():
    with patch("app.conversational_agent.BedrockModel") as MockModel:
        with patch("app.conversational_agent.Agent") as MockAgent:
            create_conversational_agent()

    MockModel.assert_called_once_with(
        model_id="amazon.nova-lite-v1:0",
        region_name="us-east-1",
    )
    kwargs = MockAgent.call_args.kwargs
    assert kwargs["callback_handler"] is None
    assert len(kwargs["tools"]) == 6
