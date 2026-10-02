"""API HTTP de demostración para el agente conversacional."""

import os
import logging
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from strands import Agent

from app.conversational_agent import create_conversational_agent


PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / "static"
MAX_DEMO_SESSIONS = int(os.getenv("MAX_DEMO_SESSIONS", "100"))
DEMO_WARNING = (
    "Demostración con datos ficticios. Las recomendaciones requieren "
    "validación humana y no ejecutan transacciones financieras."
)
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """Mensaje enviado por el portal de demostración."""

    session_id: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=4000)
    user_id: str = Field(default="demo-user", min_length=1, max_length=128)


class ChatResponse(BaseModel):
    """Respuesta consolidada que consume la interfaz web."""

    session_id: str
    answer: str
    status: str
    trace_id: str
    timestamp: str
    model_id: str
    sources: list[str]
    warning: str


@dataclass
class DemoSession:
    agent: Agent
    last_used: float


_sessions: dict[str, DemoSession] = {}
_sessions_lock = threading.RLock()


def reset_demo_sessions() -> None:
    """Vacía las sesiones; se utiliza principalmente en pruebas."""
    with _sessions_lock:
        _sessions.clear()


def _get_or_create_agent(session_id: str) -> Agent:
    with _sessions_lock:
        session = _sessions.get(session_id)
        if session is not None:
            session.last_used = monotonic()
            return session.agent

        if len(_sessions) >= MAX_DEMO_SESSIONS:
            oldest_session_id = min(
                _sessions,
                key=lambda key: _sessions[key].last_used,
            )
            del _sessions[oldest_session_id]

        agent = create_conversational_agent()
        _sessions[session_id] = DemoSession(agent=agent, last_used=monotonic())
        return agent


def _detect_sources(answer: str) -> list[str]:
    candidates = [
        "data/clientes.json",
        "data/historial.json",
        "data/politicas.json",
    ]
    answer_lower = answer.lower()
    return [source for source in candidates if source.lower() in answer_lower]


app = FastAPI(
    title="Agente de Cartera Demo",
    description="API de demostración con Strands y Amazon Bedrock.",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, Any]:
    required_files = [
        PROJECT_ROOT / "data/clientes.json",
        PROJECT_ROOT / "data/historial.json",
        PROJECT_ROOT / "data/politicas.json",
        PROJECT_ROOT / "prompt_conversacional.md",
    ]
    missing = [str(path) for path in required_files if not path.exists()]
    if missing:
        raise HTTPException(status_code=503, detail={"missing": missing})
    return {"status": "ready", "sources": len(required_files) - 1}


@app.post("/v1/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    trace_id = str(uuid.uuid4())
    logger.info(
        "chat_request trace_id=%s session_id=%s user_id=%s",
        trace_id,
        request.session_id,
        request.user_id,
    )
    try:
        agent = _get_or_create_agent(request.session_id)
        answer = str(agent(request.message.strip()))
    except Exception as exc:
        logger.exception(
            "chat_error trace_id=%s session_id=%s",
            trace_id,
            request.session_id,
        )
        raise HTTPException(
            status_code=502,
            detail={
                "message": "No fue posible consultar el agente",
                "trace_id": trace_id,
            },
        ) from exc

    return ChatResponse(
        session_id=request.session_id,
        answer=answer,
        status="success",
        trace_id=trace_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        model_id=os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0"),
        sources=_detect_sources(answer),
        warning=DEMO_WARNING,
    )
