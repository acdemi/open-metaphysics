"""Session / reasoning-trace persistence.

Two interchangeable stores:

* ``InMemorySessionStore`` -- always available, used when no ``postgres_dsn``
  is configured or when the SQLAlchemy extra is missing.
* ``SqlAlchemySessionStore`` -- PostgreSQL (``postgresql+psycopg://``) or any
  SQLAlchemy URL (tests use SQLite). Requires the optional ``[persist]`` extra.

Storing is best-effort: a persistence failure must never break a deterministic
calculation, so callers wrap ``save_*`` and ignore errors.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable

try:  # optional [persist] extra
    from sqlalchemy import (
        JSON,
        Column,
        Integer,
        MetaData,
        String,
        Table,
        create_engine,
        delete,
        insert,
        select,
    )

    SQLALCHEMY_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only without the extra
    SQLALCHEMY_AVAILABLE = False


@runtime_checkable
class SessionStore(Protocol):
    def save_session(
        self,
        request_id: str,
        request: dict[str, Any],
        response: dict[str, Any],
        traces: list[dict[str, Any]] | None = None,
    ) -> None: ...

    def get_session(self, request_id: str) -> dict[str, Any] | None: ...

    def get_traces(self, request_id: str) -> list[dict[str, Any]]: ...


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class InMemorySessionStore:
    """Process-local store; deterministic insertion order, no external service."""

    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}
        self._traces: dict[str, list[dict[str, Any]]] = {}

    def save_session(
        self,
        request_id: str,
        request: dict[str, Any],
        response: dict[str, Any],
        traces: list[dict[str, Any]] | None = None,
    ) -> None:
        self._sessions[request_id] = {
            "request_id": request_id,
            "created_at": _now(),
            "request": request,
            "response": response,
        }
        if traces is not None:
            self._traces[request_id] = list(traces)

    def get_session(self, request_id: str) -> dict[str, Any] | None:
        return self._sessions.get(request_id)

    def get_traces(self, request_id: str) -> list[dict[str, Any]]:
        return list(self._traces.get(request_id, []))


class SqlAlchemySessionStore:
    """Durable store backed by SQLAlchemy (PostgreSQL or SQLite in tests)."""

    def __init__(self, dsn: str) -> None:
        if not SQLALCHEMY_AVAILABLE:  # pragma: no cover - defensive
            raise RuntimeError("SQLAlchemy is not installed; use the [persist] extra")
        self.dsn = _normalize_dsn(dsn)
        self._engine = create_engine(self.dsn, future=True, pool_pre_ping=True)
        self._metadata = MetaData()
        self._sessions = Table(
            "om_sessions",
            self._metadata,
            Column("request_id", String(128), primary_key=True),
            Column("created_at", String(32), nullable=False),
            Column("request", JSON, nullable=False),
            Column("response", JSON, nullable=False),
        )
        self._traces = Table(
            "om_traces",
            self._metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("request_id", String(128), nullable=False, index=True),
            Column("agent", String(64), nullable=False),
            Column("steps", JSON, nullable=False),
            Column("created_at", String(32), nullable=False),
        )
        self._metadata.create_all(self._engine)

    def save_session(
        self,
        request_id: str,
        request: dict[str, Any],
        response: dict[str, Any],
        traces: list[dict[str, Any]] | None = None,
    ) -> None:
        with self._engine.begin() as conn:
            conn.execute(delete(self._sessions).where(self._sessions.c.request_id == request_id))
            conn.execute(delete(self._traces).where(self._traces.c.request_id == request_id))
            conn.execute(
                insert(self._sessions).values(
                    request_id=request_id,
                    created_at=_now(),
                    request=request,
                    response=response,
                )
            )
            for trace in traces or []:
                conn.execute(
                    insert(self._traces).values(
                        request_id=request_id,
                        agent=str(trace.get("agent", "")),
                        steps=trace.get("steps", []),
                        created_at=_now(),
                    )
                )

    def get_session(self, request_id: str) -> dict[str, Any] | None:
        with self._engine.connect() as conn:
            row = conn.execute(
                select(self._sessions).where(self._sessions.c.request_id == request_id)
            ).first()
        if row is None:
            return None
        return {
            "request_id": row.request_id,
            "created_at": row.created_at,
            "request": row.request,
            "response": row.response,
        }

    def get_traces(self, request_id: str) -> list[dict[str, Any]]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                select(self._traces)
                .where(self._traces.c.request_id == request_id)
                .order_by(self._traces.c.id)
            ).all()
        return [{"agent": row.agent, "steps": row.steps} for row in rows]


def _normalize_dsn(dsn: str) -> str:
    if dsn.startswith("postgres://"):
        return "postgresql+psycopg://" + dsn[len("postgres://") :]
    if dsn.startswith("postgresql://"):
        return "postgresql+psycopg://" + dsn[len("postgresql://") :]
    return dsn


def create_store(settings: Any | None = None) -> SessionStore:
    """Build the configured store; degrade to memory when unavailable."""
    if settings is None:
        from ..core.config import get_settings

        settings = get_settings()
    dsn = getattr(settings, "postgres_dsn", None)
    if dsn and SQLALCHEMY_AVAILABLE:
        try:
            return SqlAlchemySessionStore(dsn)
        except Exception:
            return InMemorySessionStore()
    return InMemorySessionStore()
