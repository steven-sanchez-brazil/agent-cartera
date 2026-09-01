"""
Punto de entrada CLI para el agente de cartera vencida.

Uso:
    python main.py --client-id CLI001 --deuda 5000 --dias-mora 45 --incumplimientos 1
    python main.py --help

Variables de entorno necesarias:
    AWS_REGION               Región de AWS (default: us-east-1)
    AWS_ACCESS_KEY_ID        Credencial AWS
    AWS_SECRET_ACCESS_KEY    Credencial AWS
    BEDROCK_MODEL_ID         ID del modelo Bedrock (default: anthropic.claude-3-sonnet-20240229-v1:0)
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv

# Cargar variables desde .env si existe (útil en desarrollo local)
load_dotenv()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Agente de gestión de cartera vencida — powered by AWS Bedrock",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--client-id",
        required=True,
        help="Identificador único del cliente",
    )
    parser.add_argument(
        "--deuda",
        type=float,
        required=True,
        help="Saldo de deuda del cliente (>= 0)",
    )
    parser.add_argument(
        "--dias-mora",
        type=int,
        required=True,
        help="Número de días en mora (>= 0)",
    )
    parser.add_argument(
        "--incumplimientos",
        type=int,
        required=True,
        help="Número de incumplimientos previos (>= 0)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Emitir la respuesta en formato JSON",
    )
    return parser.parse_args()


def main() -> int:
    """Función principal. Retorna 0 en éxito, 1 en error."""
    args = parse_args()

    # Importar aquí para que los errores de importación sean claros
    from app.agent import run_agent, ValidationError, SystemPromptError

    try:
        response = run_agent(
            client_id=args.client_id,
            deuda=args.deuda,
            dias_mora=args.dias_mora,
            incumplimientos_previos=args.incumplimientos,
        )
    except ValidationError as exc:
        print(f"Error de validación: {exc}", file=sys.stderr)
        return 1
    except SystemPromptError as exc:
        print(f"Error de configuración: {exc}", file=sys.stderr)
        return 1

    if args.output_json:
        output = {
            "client_id": args.client_id,
            "nivel_riesgo": response.nivel_riesgo,
            "accion_recomendada": response.accion_recomendada,
            "justificacion": response.justificacion,
        }
        if response.error:
            output["error"] = response.error
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"Cliente:             {args.client_id}")
        print(f"Nivel de riesgo:     {response.nivel_riesgo}")
        print(f"Acción recomendada:  {response.accion_recomendada}")
        print(f"Justificación:\n{response.justificacion}")
        if response.error:
            print(f"\n⚠  Advertencia: {response.error}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
