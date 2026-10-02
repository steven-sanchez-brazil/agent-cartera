"""Pruebas para las fuentes locales y sus herramientas."""

from app.local_tools import (
    consultar_cliente,
    consultar_historial,
    consultar_politica,
    validar_datos_cartera,
)
from app.repository import obtener_cliente, obtener_historial, obtener_politica


def test_obtener_cliente_existente():
    cliente = obtener_cliente("12345")
    assert cliente is not None
    assert cliente["deuda"] == 8_000_000
    assert cliente["dias_mora"] == 75


def test_obtener_cliente_inexistente():
    assert obtener_cliente("NO-EXISTE") is None


def test_obtener_historial_existente():
    historial = obtener_historial("12345")
    assert historial is not None
    assert historial["incumplimientos_previos"] == 1


def test_obtener_politica_incluye_trazabilidad():
    politica = obtener_politica("ALTO")
    assert politica is not None
    assert politica["prioridad"] == "ALTA"
    assert politica["version"] == "1.0"
    assert politica["fecha_vigencia"] == "2026-10-01"


def test_tool_cliente_reporta_fuente():
    resultado = consultar_cliente("12345")
    assert resultado["encontrado"] is True
    assert resultado["fuente"] == "data/clientes.json"


def test_tool_historial_faltante_no_inventa_datos():
    resultado = consultar_historial("NO-EXISTE")
    assert resultado["encontrado"] is False
    assert "datos" not in resultado


def test_tool_politica_normaliza_nivel():
    resultado = consultar_politica("alto")
    assert resultado["encontrada"] is True
    assert resultado["nivel_riesgo"] == "ALTO"


def test_validacion_detecta_campos_invalidos():
    resultado = validar_datos_cartera("12345", -1, 75, -1)
    assert resultado["valido"] is False
    assert resultado["campos_invalidos"] == [
        "deuda",
        "incumplimientos_previos",
    ]


def test_validacion_acepta_datos_completos():
    resultado = validar_datos_cartera("12345", 8_000_000, 75, 1)
    assert resultado == {
        "valido": True,
        "campos_faltantes": [],
        "campos_invalidos": [],
        "inconsistencias": [],
        "requiere_revision_humana": False,
    }


def test_validacion_detecta_estado_contradictorio():
    resultado = validar_datos_cartera("10007", 3_200_000, 40, 0, "AL_DIA")
    assert resultado["valido"] is False
    assert resultado["requiere_revision_humana"] is True
    assert resultado["inconsistencias"]


def test_dataset_incluye_casos_de_demostracion():
    assert obtener_cliente("10001")["dias_mora"] == 12
    assert obtener_cliente("10004")["dias_mora"] == 95
    assert obtener_historial("10006") is None
