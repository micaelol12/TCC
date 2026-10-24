"""Durable Lab execution records. No credentials, session tokens or provider errors."""
from contextlib import closing
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sqlite3
from uuid import uuid4
from .experiment_config import ExperimentConfig


def now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def connect(database):
    path = Path(database).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(path, timeout=5)


def initialize(connection):
    connection.execute('''CREATE TABLE IF NOT EXISTS lab_executions (
        execution_id TEXT PRIMARY KEY, started_at TEXT NOT NULL, finished_at TEXT,
        status TEXT NOT NULL, http_status INTEGER, client TEXT NOT NULL,
        text TEXT NOT NULL, processing_level TEXT, requested_config_json TEXT NOT NULL,
        effective_config_json TEXT, analysis_json TEXT, error_code TEXT, elapsed_ms INTEGER
    )''')
    connection.execute('CREATE INDEX IF NOT EXISTS lab_execution_time ON lab_executions(started_at)')


def public_request(payload, settings):
    if not isinstance(payload, dict):
        return '', None, {}
    text = payload.get('text')
    text = text[:settings.max_chars] if isinstance(text, str) else ''
    mode = payload.get('processing_level')
    mode = mode if mode in ('low', 'medium', 'high') else None
    from .lab_credentials import model_catalog
    incoming = payload.get('experiment_config')
    config = {}
    if isinstance(incoming, dict):
        for name in ExperimentConfig.model_fields:
            value = incoming.get(name)
            if name == 'escala':
                from .polarity import validar_escala
                try:
                    config[name] = validar_escala(value).model_dump(mode='json')
                except (ValueError, TypeError):
                    pass
            elif name == 'jev_model' and value in settings.allowed_jev_models or name == 'llm_model' and isinstance(value, str) and value in model_catalog(settings):
                config[name] = value
            elif name in ('semantic_evidence_check', 'jev_evidence_search') and type(value) is bool:
                config[name] = value
            elif (name == 'primitiva_polaridade' and value in ('score', 'choice')
                  or name == 'regra_decisao' and value in ('nivel', 'polo_primeiro')):
                config[name] = value
            elif name not in ('jev_model', 'llm_model') and type(value) in (int, float) and math.isfinite(value):
                config[name] = value
    return text, mode, config


def begin_execution(database, payload, settings, client='unknown'):
    identifier = str(uuid4())
    text, mode, config = public_request(payload, settings)
    from .experiment_config import ExperimentOverrides, resolve_config
    try:
        incoming = payload.get('experiment_config', {}) if isinstance(payload, dict) else {}
        effective = resolve_config(settings, ExperimentOverrides.model_validate(incoming)).model_dump()
    except ValueError:
        effective = None
    with closing(connect(database)) as connection, connection:
        initialize(connection)
        connection.execute('INSERT INTO lab_executions (execution_id, started_at, status, client, text, processing_level, requested_config_json, effective_config_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (identifier, now(), 'running', client if client in ('web', 'extension') else 'unknown', text, mode, json.dumps(config, allow_nan=False), json.dumps(effective) if effective else None))
    return identifier


def finish_execution(database, identifier, status, http_status, elapsed_ms, analysis=None, error_code=None):
    effective = analysis.get('effective_config') if isinstance(analysis, dict) else None
    with closing(connect(database)) as connection, connection:
        connection.execute('UPDATE lab_executions SET finished_at=?, status=?, http_status=?, elapsed_ms=?, effective_config_json=COALESCE(?, effective_config_json), analysis_json=?, error_code=? WHERE execution_id=?',
            (now(), status, http_status, elapsed_ms, json.dumps(effective) if effective else None,
             json.dumps(analysis, ensure_ascii=False, allow_nan=False) if analysis else None, error_code, identifier))


def recover_interrupted(database):
    with closing(connect(database)) as connection, connection:
        initialize(connection)
        connection.execute("UPDATE lab_executions SET status='interrupted', finished_at=?, error_code='server_restarted' WHERE status='running'", (now(),))
