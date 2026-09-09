from contextvars import ContextVar


session_id_context: ContextVar[str | None] = ContextVar(
    "session_id",
    default=None,
)


def set_session_id(session_id: str):
    session_id_context.set(session_id)


def get_session_id() -> str | None:
    return session_id_context.get()