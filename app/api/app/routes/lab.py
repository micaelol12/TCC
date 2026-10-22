from typing import Literal
from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from ..settings import settings
from ..lab_credentials import require_local_lab, set_key, SESSION_SECONDS, sessions, lock

router = APIRouter(prefix='/api/lab')


class KeyRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    provider: Literal['typesafe', 'maritaca', 'gemini']
    api_key: SecretStr = Field(min_length=1, max_length=512)

    @field_validator('api_key')
    @classmethod
    def safe_key(cls, value):
        key = value.get_secret_value()
        if key != key.strip() or any(ord(char) < 33 or ord(char) > 126 for char in key):
            raise ValueError('Formato de chave inválido.')
        return value


@router.post('/api-keys')
def save_key(payload: KeyRequest, request: Request):
    require_local_lab(request, settings)
    token = set_key(request.headers.get('x-lab-session'), payload.provider, payload.api_key.get_secret_value())
    return {'session_token': token, 'expires_in_seconds': SESSION_SECONDS}


@router.delete('/api-keys/{provider}')
def remove_key(provider: Literal['typesafe', 'maritaca', 'gemini'], request: Request):
    require_local_lab(request, settings)
    token = set_key(request.headers.get('x-lab-session'), provider, '')
    return {'session_token': token, 'expires_in_seconds': SESSION_SECONDS}


@router.delete('/session')
def reset_session(request: Request):
    require_local_lab(request, settings)
    token = request.headers.get('x-lab-session')
    with lock:
        sessions.pop(token, None)
    return {'status': 'cleared'}
