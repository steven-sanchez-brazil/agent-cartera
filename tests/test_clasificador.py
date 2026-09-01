"""
Tests para `clasificar_riesgo` y `determinar_estrategia` — ciclo TDD: RED 🔴

Tareas 4.1 y 5.1: todos estos tests deben fallar porque ambas funciones
tienen `...` como cuerpo (sin implementación aún).
"""
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.agent import clasificar_riesgo, determinar_estrategia


# ---------------------------------------------------------------------------
# Tests unitarios — clasificar_riesgo (Tarea 4.1)
# ---------------------------------------------------------------------------

class TestClasificarRiesgoBajo:
    def test_cero_dias_sin_incumplimientos_es_bajo(self):
        """dias_mora=0, incumplimientos=0 → 'BAJO'"""
        assert clasificar_riesgo(0, 0) == "BAJO"

    def test_veintinueve_dias_sin_incumplimientos_es_bajo(self):
        """dias_mora=29, incumplimientos=0 → 'BAJO' (límite inferior de MEDIO)"""
        assert clasificar_riesgo(29, 0) == "BAJO"


class TestClasificarRiesgoMedio:
    def test_treinta_dias_sin_incumplimientos_es_medio(self):
        """dias_mora=30, incumplimientos=0 → 'MEDIO' (inicio del rango MEDIO)"""
        assert clasificar_riesgo(30, 0) == "MEDIO"

    def test_sesenta_dias_sin_incumplimientos_es_medio(self):
        """dias_mora=60, incumplimientos=0 → 'MEDIO' (fin del rango MEDIO)"""
        assert clasificar_riesgo(60, 0) == "MEDIO"

    def test_cero_dias_un_incumplimiento_es_medio(self):
        """dias_mora=0, incumplimientos=1 → 'MEDIO'"""
        assert clasificar_riesgo(0, 1) == "MEDIO"


class TestClasificarRiesgoAlto:
    def test_sesenta_un_dias_sin_incumplimientos_es_alto(self):
        """dias_mora=61, incumplimientos=0 → 'ALTO' (supera el rango MEDIO)"""
        assert clasificar_riesgo(61, 0) == "ALTO"

    def test_cero_dias_dos_incumplimientos_es_alto(self):
        """dias_mora=0, incumplimientos=2 → 'ALTO'"""
        assert clasificar_riesgo(0, 2) == "ALTO"

    def test_alto_tiene_precedencia_sobre_medio(self):
        """dias_mora=61, incumplimientos=1 → 'ALTO' (ALTO gana sobre MEDIO)"""
        assert clasificar_riesgo(61, 1) == "ALTO"


# ---------------------------------------------------------------------------
# Property test — Propiedad 1 (Tarea 4.2)
# ---------------------------------------------------------------------------

@given(
    dias_mora=st.integers(min_value=0),
    incumplimientos=st.integers(min_value=0),
)
@settings(max_examples=100)
def test_propiedad_1_clasificacion_correcta(dias_mora, incumplimientos):
    """
    Propiedad 1: Corrección total de la clasificación de riesgo

    Para cualquier par válido (dias_mora >= 0, incumplimientos >= 0),
    clasificar_riesgo debe retornar exactamente el nivel correcto según
    las reglas definidas, con precedencia ALTO > MEDIO > BAJO.

    Feature: cartera-strands-agent
    Valida: Requerimientos 2.1, 2.2, 2.3, 2.4
    """
    resultado = clasificar_riesgo(dias_mora, incumplimientos)

    # El resultado siempre debe ser uno de los tres niveles válidos
    assert resultado in {"BAJO", "MEDIO", "ALTO"}, (
        f"Resultado inesperado '{resultado}' para "
        f"dias_mora={dias_mora}, incumplimientos={incumplimientos}"
    )

    # Determinar el nivel esperado con precedencia ALTO > MEDIO > BAJO
    es_alto = dias_mora > 60 or incumplimientos >= 2
    es_medio = (30 <= dias_mora <= 60 or incumplimientos == 1) and not es_alto
    es_bajo = dias_mora < 30 and incumplimientos == 0

    if es_alto:
        assert resultado == "ALTO", (
            f"Esperaba 'ALTO' para dias_mora={dias_mora}, "
            f"incumplimientos={incumplimientos}, pero obtuvo '{resultado}'"
        )
    elif es_medio:
        assert resultado == "MEDIO", (
            f"Esperaba 'MEDIO' para dias_mora={dias_mora}, "
            f"incumplimientos={incumplimientos}, pero obtuvo '{resultado}'"
        )
    elif es_bajo:
        assert resultado == "BAJO", (
            f"Esperaba 'BAJO' para dias_mora={dias_mora}, "
            f"incumplimientos={incumplimientos}, pero obtuvo '{resultado}'"
        )


# ---------------------------------------------------------------------------
# Tests unitarios — determinar_estrategia (Tarea 5.1)
# ---------------------------------------------------------------------------

class TestDeterminarEstrategia:
    def test_bajo_retorna_seguimiento_preventivo(self):
        """'BAJO' → 'Seguimiento preventivo y recordatorio de pago'"""
        assert determinar_estrategia("BAJO") == "Seguimiento preventivo y recordatorio de pago"

    def test_medio_retorna_contacto_directo(self):
        """'MEDIO' → 'Contacto directo y negociación de plan de pagos'"""
        assert determinar_estrategia("MEDIO") == "Contacto directo y negociación de plan de pagos"

    def test_alto_retorna_gestion_prioritaria(self):
        """'ALTO' → 'Gestión prioritaria de cobranza y evaluación de acuerdo de pago'"""
        assert determinar_estrategia("ALTO") == "Gestión prioritaria de cobranza y evaluación de acuerdo de pago"


# ---------------------------------------------------------------------------
# Property test — Propiedad 2 (Tarea 5.2)
# ---------------------------------------------------------------------------

ESTRATEGIAS_ESPERADAS = {
    "BAJO": "Seguimiento preventivo y recordatorio de pago",
    "MEDIO": "Contacto directo y negociación de plan de pagos",
    "ALTO": "Gestión prioritaria de cobranza y evaluación de acuerdo de pago",
}


@given(nivel_riesgo=st.sampled_from(["BAJO", "MEDIO", "ALTO"]))
@settings(max_examples=100)
def test_propiedad_2_estrategia_mapping_completo(nivel_riesgo):
    """
    Propiedad 2: Completitud del mapeo de estrategias de cobranza

    Para cualquier nivel de riesgo en {"BAJO", "MEDIO", "ALTO"},
    determinar_estrategia debe retornar exactamente la cadena especificada.

    Feature: cartera-strands-agent
    Valida: Requerimientos 3.1, 3.2, 3.3, 3.4
    """
    resultado = determinar_estrategia(nivel_riesgo)
    esperado = ESTRATEGIAS_ESPERADAS[nivel_riesgo]

    assert resultado == esperado, (
        f"Para nivel_riesgo='{nivel_riesgo}' esperaba '{esperado}', "
        f"pero obtuvo '{resultado}'"
    )
