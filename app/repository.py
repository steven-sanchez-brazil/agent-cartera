"""Acceso de solo lectura a las fuentes locales del agente."""

import json
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class DataSourceError(RuntimeError):
    """Una fuente local no existe, no es legible o contiene JSON inválido."""


def _read_json(filename: str) -> Any:
    path = DATA_DIR / filename
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        raise DataSourceError(f"No fue posible leer la fuente '{path}': {exc}") from exc


def obtener_cliente(client_id: str) -> dict[str, Any] | None:
    """Busca un cliente por su identificador exacto."""
    return next(
        (
            cliente
            for cliente in _read_json("clientes.json")
            if cliente.get("client_id") == client_id
        ),
        None,
    )


def obtener_historial(client_id: str) -> dict[str, Any] | None:
    """Busca el historial asociado a un cliente."""
    return next(
        (
            registro
            for registro in _read_json("historial.json")
            if registro.get("client_id") == client_id
        ),
        None,
    )


def obtener_politica(nivel_riesgo: str) -> dict[str, Any] | None:
    """Obtiene una política junto con sus metadatos de vigencia."""
    documento = _read_json("politicas.json")
    regla = documento.get("reglas", {}).get(nivel_riesgo)
    if regla is None:
        return None
    return {
        "version": documento.get("version"),
        "fecha_vigencia": documento.get("fecha_vigencia"),
        **regla,
    }
