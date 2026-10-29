"""Expiring, per-session provider keys. Never serialized or written to the database."""
from dataclasses import dataclass, field
from secrets import token_urlsafe
from threading import Lock
from time import monotonic
from fastapi import HTTPException, Request

SESSION_SECONDS = 8 * 3600
MAX_SESSIONS = 100


@dataclass
class KeySession:
    expires_at: float
    keys: dict[str, str] = field(default_factory=dict, repr=False)


sessions: dict[str, KeySession] = {}
lock = Lock()


def require_local_lab(request: Request, settings):
    if settings.app_env != 'lab' or not settings.experimental_config_enabled:
        raise HTTPException(404, 'Função Lab indisponível.')
    if request.client and request.client.host not in {'127.0.0.1', '::1', 'localhost', 'testclient'}:
        raise HTTPException(403, 'O Lab aceita somente conexões locais.')


def _purge():
    now = monotonic()
    for token in list(sessions):
        if sessions[token].expires_at <= now:
            del sessions[token]


def session_keys(token: str | None) -> dict[str, str]:
    if not token:
        return {}
    with lock:
        _purge()
        session = sessions.get(token)
        if session is None:
            raise HTTPException(401, 'Sessão de chaves expirada. Cadastre novamente na aba API keys.')
        return dict(session.keys)


def set_key(token: str | None, provider: str, key: str) -> str:
    with lock:
        _purge()
        if token and token not in sessions:
            raise HTTPException(401, 'Sessão de chaves expirada. Cadastre novamente na aba API keys.')
        if not token:
            if len(sessions) >= MAX_SESSIONS:
                raise HTTPException(429, 'Limite temporário de sessões de chaves atingido.')
            token = token_urlsafe(32)
            sessions[token] = KeySession(monotonic() + SESSION_SECONDS)
        sessions[token].keys[provider] = key
        return token


def effective_keys(settings, request: Request) -> dict[str, str]:
    if settings.app_env == 'lab':
        return {'typesafe': '', 'maritaca': '', 'gemini': '',
                **session_keys(request.headers.get('x-lab-session'))}
    return {'typesafe': settings.typesafe_key, 'maritaca': settings.maritaca_key, 'gemini': settings.gemini_key}


def model_catalog(settings) -> dict[str, str]:
    models = {model: 'maritaca' for model in settings.allowed_llm_models}
    if settings.app_env == 'lab':
        models.update({model: 'maritaca' for model in ('sabia-4', 'sabiazinho-4')})
    models.update({model: 'gemini' for model in settings.allowed_gemini_models})
    return models
