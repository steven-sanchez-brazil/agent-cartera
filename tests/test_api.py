"""Pruebas de la API de demostración sin consumir Bedrock."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.api import app, reset_demo_sessions


client = TestClient(app)


def setup_function():
    reset_demo_sessions()


def test_health_y_ready():
    assert client.get("/health").json() == {"status": "ok"}
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_portal_web_disponible():
    response = client.get("/")
    assert response.status_code == 200
    assert "Agente de Cartera" in response.text
    assert "Uso demostrativo" in response.text


def test_chat_devuelve_trazabilidad_y_fuentes():
    fake_agent = MagicMock()
    fake_agent.return_value = (
        "Fuentes consultadas: data/clientes.json, "
        "data/historial.json y data/politicas.json"
    )

    with patch("app.api.create_conversational_agent", return_value=fake_agent):
        response = client.post(
            "/v1/chat",
            json={
                "session_id": "demo-test-001",
                "user_id": "tester",
                "message": "Analiza el cliente 12345",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["trace_id"]
    assert payload["model_id"]
    assert payload["sources"] == [
        "data/clientes.json",
        "data/historial.json",
        "data/politicas.json",
    ]
    assert "datos ficticios" in payload["warning"]


def test_misma_sesion_reutiliza_agente():
    fake_agent = MagicMock(return_value="Respuesta sin fuentes")

    with patch(
        "app.api.create_conversational_agent",
        return_value=fake_agent,
    ) as factory:
        for message in ("Analiza un cliente", "El cliente es 12345"):
            response = client.post(
                "/v1/chat",
                json={"session_id": "misma-sesion", "message": message},
            )
            assert response.status_code == 200

    factory.assert_called_once()
    assert fake_agent.call_count == 2


def test_chat_rechaza_mensaje_vacio():
    response = client.post(
        "/v1/chat",
        json={"session_id": "demo-test-002", "message": ""},
    )
    assert response.status_code == 422
