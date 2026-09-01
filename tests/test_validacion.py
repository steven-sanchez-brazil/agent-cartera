"""
Tests para `_validate_input` — ciclo TDD: RED 🔴
Todos estos tests deben fallar porque la función solo tiene `...` como cuerpo.
"""
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.agent import _validate_input, ValidationError


# ---------------------------------------------------------------------------
# Tests unitarios
# ---------------------------------------------------------------------------

class TestValidarClientIdVacio:
    def test_client_id_vacio_lanza_validation_error(self):
        """client_id vacío "" debe lanzar ValidationError."""
        with pytest.raises(ValidationError):
            _validate_input(
                client_id="",
                deuda=100.0,
                dias_mora=0,
                incumplimientos_previos=0,
            )

    def test_client_id_solo_espacios_lanza_validation_error(self):
        """client_id con solo espacios "   " debe lanzar ValidationError."""
        with pytest.raises(ValidationError):
            _validate_input(
                client_id="   ",
                deuda=100.0,
                dias_mora=0,
                incumplimientos_previos=0,
            )


class TestValidarValoresNegativos:
    def test_dias_mora_negativo_lanza_validation_error(self):
        """dias_mora = -1 debe lanzar ValidationError."""
        with pytest.raises(ValidationError):
            _validate_input(
                client_id="CLI-001",
                deuda=100.0,
                dias_mora=-1,
                incumplimientos_previos=0,
            )

    def test_deuda_negativa_lanza_validation_error(self):
        """deuda = -1.0 debe lanzar ValidationError."""
        with pytest.raises(ValidationError):
            _validate_input(
                client_id="CLI-001",
                deuda=-1.0,
                dias_mora=0,
                incumplimientos_previos=0,
            )


class TestValidarCamposNulos:
    def test_client_id_none_lanza_validation_error_con_nombre(self):
        """client_id=None debe lanzar ValidationError y mencionar 'client_id'."""
        with pytest.raises(ValidationError, match="client_id"):
            _validate_input(
                client_id=None,
                deuda=100.0,
                dias_mora=0,
                incumplimientos_previos=0,
            )

    def test_deuda_none_lanza_validation_error_con_nombre(self):
        """deuda=None debe lanzar ValidationError y mencionar 'deuda'."""
        with pytest.raises(ValidationError, match="deuda"):
            _validate_input(
                client_id="CLI-001",
                deuda=None,
                dias_mora=0,
                incumplimientos_previos=0,
            )

    def test_dias_mora_none_lanza_validation_error_con_nombre(self):
        """dias_mora=None debe lanzar ValidationError y mencionar 'dias_mora'."""
        with pytest.raises(ValidationError, match="dias_mora"):
            _validate_input(
                client_id="CLI-001",
                deuda=100.0,
                dias_mora=None,
                incumplimientos_previos=0,
            )

    def test_incumplimientos_previos_none_lanza_validation_error_con_nombre(self):
        """incumplimientos_previos=None debe lanzar ValidationError y mencionar 'incumplimientos_previos'."""
        with pytest.raises(ValidationError, match="incumplimientos_previos"):
            _validate_input(
                client_id="CLI-001",
                deuda=100.0,
                dias_mora=0,
                incumplimientos_previos=None,
            )


# ---------------------------------------------------------------------------
# Property-based tests con Hypothesis
# ---------------------------------------------------------------------------

CAMPOS_REQUERIDOS = ["client_id", "deuda", "dias_mora", "incumplimientos_previos"]

DEFAULTS_VALIDOS = {
    "client_id": "CLI-001",
    "deuda": 100.0,
    "dias_mora": 0,
    "incumplimientos_previos": 0,
}


@given(
    campos_faltantes=st.frozensets(
        st.sampled_from(CAMPOS_REQUERIDOS),
        min_size=1,
    )
)
@settings(max_examples=100)
def test_propiedad_3_campos_faltantes_mencionados_en_error(campos_faltantes):
    """
    Propiedad 3: Validación de campos faltantes
    Para cualquier subconjunto de campos con None, ValidationError
    debe mencionar cada campo faltante en el mensaje.

    Feature: cartera-strands-agent
    Valida: Requerimiento 1.2
    """
    kwargs = dict(DEFAULTS_VALIDOS)
    for campo in campos_faltantes:
        kwargs[campo] = None

    with pytest.raises(ValidationError) as exc_info:
        _validate_input(**kwargs)

    mensaje = str(exc_info.value)
    for campo in campos_faltantes:
        assert campo in mensaje, (
            f"ValidationError debe mencionar '{campo}', pero el mensaje fue: '{mensaje}'"
        )


@given(
    dias_mora=st.integers(max_value=-1),
    deuda=st.floats(
        max_value=-0.01,
        allow_nan=False,
        allow_infinity=False,
    ),
)
@settings(max_examples=100)
def test_propiedad_4_valores_negativos_rechazados(dias_mora, deuda):
    """
    Propiedad 4: Rechazo de valores numéricos negativos
    Para cualquier dias_mora < 0 o deuda < 0, ValidationError debe lanzarse.

    Feature: cartera-strands-agent
    Valida: Requerimiento 1.3
    """
    # Probar dias_mora negativo con deuda válida
    with pytest.raises(ValidationError):
        _validate_input(
            client_id="CLI-001",
            deuda=100.0,
            dias_mora=dias_mora,
            incumplimientos_previos=0,
        )

    # Probar deuda negativa con dias_mora válido
    with pytest.raises(ValidationError):
        _validate_input(
            client_id="CLI-001",
            deuda=deuda,
            dias_mora=0,
            incumplimientos_previos=0,
        )


@given(
    client_id=st.one_of(
        st.just(""),
        st.text(alphabet=" \t\n\r", min_size=1),
    )
)
@settings(max_examples=100)
def test_propiedad_5_client_id_vacio_rechazado(client_id):
    """
    Propiedad 5: Rechazo de identificador de cliente vacío o solo espacios
    Para cualquier client_id vacío o compuesto solo de whitespace,
    ValidationError debe lanzarse.

    Feature: cartera-strands-agent
    Valida: Requerimiento 1.4
    """
    with pytest.raises(ValidationError):
        _validate_input(
            client_id=client_id,
            deuda=100.0,
            dias_mora=0,
            incumplimientos_previos=0,
        )
