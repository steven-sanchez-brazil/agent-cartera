"""Herramientas Strands para consultar y validar fuentes locales."""

from typing import Any

from strands import tool

from app.repository import obtener_cliente, obtener_historial, obtener_politica


@tool
def consultar_cliente(client_id: str) -> dict[str, Any]:
    """Consulta deuda, mora y estado de un cliente en la fuente local."""
    cliente = obtener_cliente(client_id.strip())
    if cliente is None:
        return {
            "encontrado": False,
            "client_id": client_id,
            "error": "Cliente no encontrado",
            "fuente": "data/clientes.json",
        }
    return {
        "encontrado": True,
        "fuente": "data/clientes.json",
        "datos": cliente,
    }


@tool
def consultar_historial(client_id: str) -> dict[str, Any]:
    """Consulta pagos e incumplimientos anteriores de un cliente."""
    historial = obtener_historial(client_id.strip())
    if historial is None:
        return {
            "encontrado": False,
            "client_id": client_id,
            "error": "Historial no encontrado",
            "fuente": "data/historial.json",
        }
    return {
        "encontrado": True,
        "fuente": "data/historial.json",
        "datos": historial,
    }


@tool
def consultar_politica(nivel_riesgo: str) -> dict[str, Any]:
    """Consulta la política vigente para un nivel BAJO, MEDIO o ALTO."""
    nivel = nivel_riesgo.strip().upper()
    politica = obtener_politica(nivel)
    if politica is None:
        return {
            "encontrada": False,
            "nivel_riesgo": nivel,
            "error": "Política no encontrada",
            "fuente": "data/politicas.json",
        }
    return {
        "encontrada": True,
        "nivel_riesgo": nivel,
        "fuente": "data/politicas.json",
        "datos": politica,
    }


@tool
def validar_datos_cartera(
    client_id: str,
    deuda: float,
    dias_mora: int,
    incumplimientos_previos: int,
    estado: str | None = None,
) -> dict[str, Any]:
    """Valida completitud y consistencia básica antes de analizar la cartera."""
    faltantes = [
        nombre
        for nombre, valor in {
            "client_id": client_id,
            "deuda": deuda,
            "dias_mora": dias_mora,
            "incumplimientos_previos": incumplimientos_previos,
        }.items()
        if valor is None or (isinstance(valor, str) and not valor.strip())
    ]
    invalidos = []
    for nombre, valor in {
        "deuda": deuda,
        "dias_mora": dias_mora,
        "incumplimientos_previos": incumplimientos_previos,
    }.items():
        if valor is not None and valor < 0:
            invalidos.append(nombre)

    inconsistencias = []
    estado_normalizado = estado.strip().upper() if estado else None
    if estado_normalizado == "AL_DIA" and dias_mora and dias_mora > 0:
        inconsistencias.append(
            "El estado AL_DIA contradice un valor positivo de dias_mora"
        )
    if estado_normalizado == "VENCIDA" and dias_mora == 0:
        inconsistencias.append(
            "El estado VENCIDA contradice un valor de cero dias_mora"
        )

    return {
        "valido": not faltantes and not invalidos and not inconsistencias,
        "campos_faltantes": faltantes,
        "campos_invalidos": invalidos,
        "inconsistencias": inconsistencias,
        "requiere_revision_humana": bool(inconsistencias),
    }
