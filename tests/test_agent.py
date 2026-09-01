"""
Tests para `_load_system_prompt` y `run_agent` — ciclo TDD: RED 🔴

Todos estos tests deben fallar porque las funciones tienen `...` como cuerpo.
"""
import os
import pytest
from unittest.mock import patch, MagicMock

from app.agent import (
    _load_system_prompt,
    run_agent,
    SystemPromptError,
    ValidationError,
    AgentResponse,
)


# ---------------------------------------------------------------------------
# Tarea 7.1 — Tests unitarios para `_load_system_prompt`
# ---------------------------------------------------------------------------

class TestLoadSystemPrompt:
    def test_lectura_prompt_existente_retorna_string(self):
        """prompt.md existe → retorna el contenido como string."""
        contenido = _load_system_prompt("prompt.md")
        assert isinstance(contenido, str)
        assert len(contenido) > 0

    def test_contenido_contiene_encabezado_esperado(self):
        """El contenido de prompt.md debe contener 'Agente de Gestión de Cartera'."""
        contenido = _load_system_prompt("prompt.md")
        assert "Agente de Gestión de Cartera" in contenido

    def test_archivo_inexistente_lanza_system_prompt_error(self):
        """Ruta que no existe → lanza SystemPromptError."""
        with pytest.raises(SystemPromptError):
            _load_system_prompt("ruta/que/no/existe/prompt.md")

    def test_permiso_denegado_lanza_system_prompt_error(self):
        """PermissionError al abrir el archivo → lanza SystemPromptError."""
        with patch("builtins.open", side_effect=PermissionError("Permiso denegado")):
            with pytest.raises(SystemPromptError):
                _load_system_prompt("prompt.md")


# ---------------------------------------------------------------------------
# Tarea 8.1 — Tests unitarios para `run_agent`
# ---------------------------------------------------------------------------

class TestRunAgent:
    def test_respuesta_exitosa_campos_no_nulos(self):
        """Con mock del Agent de Strands, la respuesta contiene los 3 campos principales no nulos."""
        mock_response = MagicMock()
        mock_response.__str__ = lambda self: (
            "Nivel de riesgo: BAJO\n"
            "Acción recomendada: Seguimiento preventivo y recordatorio de pago\n"
            "Justificación: El cliente tiene bajo nivel de mora."
        )

        mock_agent_instance = MagicMock()
        mock_agent_instance.return_value = mock_response

        with patch("app.agent.Agent") as MockAgent:
            MockAgent.return_value = mock_agent_instance
            resultado = run_agent(
                client_id="CLI-001",
                deuda=500_000.0,
                dias_mora=10,
                incumplimientos_previos=0,
            )

        assert resultado.nivel_riesgo is not None
        assert resultado.accion_recomendada is not None
        assert resultado.justificacion is not None

    def test_llm_lanza_excepcion_retorna_agent_response_con_degradacion(self):
        """Cuando el LLM lanza excepción → AgentResponse con nivel_riesgo y
        accion_recomendada válidos, justificacion indica error, campo error poblado."""
        mock_agent_instance = MagicMock()
        mock_agent_instance.side_effect = Exception("LLM no disponible")

        with patch("app.agent.Agent") as MockAgent:
            MockAgent.return_value = mock_agent_instance
            resultado = run_agent(
                client_id="CLI-002",
                deuda=1_000_000.0,
                dias_mora=45,
                incumplimientos_previos=1,
            )

        assert resultado.nivel_riesgo in {"BAJO", "MEDIO", "ALTO"}
        assert resultado.accion_recomendada is not None and resultado.accion_recomendada != ""
        assert resultado.justificacion is not None and resultado.justificacion != ""
        assert resultado.error is not None and resultado.error != ""

    def test_client_id_vacio_lanza_validation_error(self):
        """client_id vacío → ValidationError propagado antes de invocar el LLM."""
        with pytest.raises(ValidationError):
            run_agent(
                client_id="",
                deuda=100.0,
                dias_mora=0,
                incumplimientos_previos=0,
            )

    def test_aws_region_no_definida_usa_us_east_1(self):
        """Con AWS_REGION no definida en el entorno, run_agent construye
        el Agent con la región 'us-east-1' por defecto."""
        mock_response = MagicMock()
        mock_response.__str__ = lambda self: (
            "Nivel de riesgo: BAJO\n"
            "Acción recomendada: Seguimiento preventivo y recordatorio de pago\n"
            "Justificación: Cliente sin mora."
        )

        mock_agent_instance = MagicMock()
        mock_agent_instance.return_value = mock_response

        env_sin_region = {k: v for k, v in os.environ.items() if k != "AWS_REGION"}

        with patch.dict(os.environ, env_sin_region, clear=True):
            with patch("app.agent.Agent") as MockAgent:
                MockAgent.return_value = mock_agent_instance
                run_agent(
                    client_id="CLI-003",
                    deuda=200_000.0,
                    dias_mora=5,
                    incumplimientos_previos=0,
                )

                # Verificar que el Agent fue construido con region us-east-1
                call_kwargs = MockAgent.call_args
                assert call_kwargs is not None, "Agent debe haber sido instanciado"
                # La región puede pasarse como kwarg 'region' o dentro de la config
                args, kwargs = call_kwargs
                region_usada = kwargs.get("region") or kwargs.get("aws_region")
                assert region_usada == "us-east-1", (
                    f"Se esperaba región 'us-east-1' pero se usó: {region_usada!r}"
                )
