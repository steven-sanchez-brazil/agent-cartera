"""Interfaz conversacional local para el agente de cartera."""

from dotenv import load_dotenv

from app.conversational_agent import create_conversational_agent


def main() -> int:
    load_dotenv()
    agent = create_conversational_agent()

    print("Agente conversacional de cartera")
    print("Consulta un cliente en lenguaje natural. Escribe 'salir' para terminar.")

    while True:
        try:
            consulta = input("\nUsuario: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSesión finalizada.")
            return 0

        if consulta.lower() in {"salir", "exit", "quit"}:
            print("Sesión finalizada.")
            return 0
        if not consulta:
            continue

        try:
            respuesta = agent(consulta)
            print(f"\nAgente:\n{respuesta}")
        except Exception as exc:
            print(f"\nNo fue posible procesar la solicitud: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
