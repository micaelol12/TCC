from pathlib import Path
import asyncio
from contextlib import asynccontextmanager
import json
import sqlite3
from time import monotonic
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from .routes.analyze import router
from .routes.reports import router as reports_router
from .report_schemas import MAX_REPORT_BYTES
from .settings import settings
from .routes.lab import router as lab_router
from .execution_store import begin_execution, finish_execution, recover_interrupted


@asynccontextmanager
async def lifespan(application):
    if settings.app_env == 'lab':
        recover_interrupted(settings.reports_db_path)
    yield

app = FastAPI(title="8values — análise de textos", docs_url=None, redoc_url=None, lifespan=lifespan)
app.include_router(router)
app.include_router(reports_router)
app.include_router(lab_router)


@app.middleware("http")
async def privacy_headers(request: Request, call_next):
    if request.url.path == '/api/analyze' and settings.app_env == 'lab':
        return await record_lab_execution(request, call_next)
    length = request.headers.get("content-length", "0")
    if request.url.path.startswith('/api/lab/'):
        body = bytearray()
        async for chunk in request.stream():
            if len(body) + len(chunk) > 2000:
                return JSONResponse({'detail': 'Entrada de chaves acima do limite.'}, status_code=413, headers={'Cache-Control': 'no-store'})
            body.extend(chunk)
        request._body = bytes(body)
    if request.url.path == "/api/analyze" and length.isdigit() and int(length) > 250000:
        return JSONResponse({"detail": "Entrada acima do limite."}, status_code=413, headers={"Cache-Control": "no-store"})
    if request.url.path == "/api/reports":
        if length.isdigit() and int(length) > MAX_REPORT_BYTES:
            return JSONResponse({"detail": "Report acima do limite."}, status_code=413, headers={"Cache-Control": "no-store"})
        # Bound actual bytes too, including requests without Content-Length.
        body = bytearray()
        async for chunk in request.stream():
            if len(body) + len(chunk) > MAX_REPORT_BYTES:
                return JSONResponse({"detail": "Report acima do limite."}, status_code=413, headers={"Cache-Control": "no-store"})
            body.extend(chunk)
        request._body = bytes(body)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; style-src-attr 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'self'"
    return response


async def record_lab_execution(request, call_next):
    started = monotonic()
    body = bytearray()
    oversized = False
    async for chunk in request.stream():
        if len(body) + len(chunk) > 250000:
            oversized = True
            break
        body.extend(chunk)
    request._body = bytes(body)
    try:
        payload = json.loads(body) if not oversized else {}
    except (ValueError, UnicodeDecodeError):
        payload = {}
    try:
        identifier = begin_execution(settings.reports_db_path, payload, settings, request.headers.get('x-lab-client', 'unknown'))
    except (sqlite3.Error, OSError):
        return JSONResponse({'detail': 'Não foi possível registrar a execução Lab. Nenhum provedor foi chamado.'}, status_code=503, headers={'Cache-Control': 'no-store'})
    elapsed = lambda: round((monotonic() - started) * 1000)
    try:
        if oversized:
            finish_execution(settings.reports_db_path, identifier, 'failed', 413, elapsed(), error_code='input_limit')
            return JSONResponse({'detail': 'Entrada acima do limite.', 'lab_execution_id': identifier}, status_code=413, headers={'Cache-Control': 'no-store'})
        response = await call_next(request)
        content = b''.join([part async for part in response.body_iterator])
        try:
            data = json.loads(content)
        except (ValueError, UnicodeDecodeError):
            data = None
        success = response.status_code == 200 and isinstance(data, dict) and 'axes' in data
        if success:
            data['lab_execution_id'] = identifier
            status = 'completed_with_warnings' if data.get('warnings') else 'completed'
            finish_execution(settings.reports_db_path, identifier, status, response.status_code, elapsed(), analysis=data)
            content = json.dumps(data, ensure_ascii=False, allow_nan=False).encode('utf-8')
        else:
            error = {401: 'key_session_expired', 413: 'input_limit', 422: 'invalid_request', 429: 'rate_limit', 499: 'cancelled', 503: 'provider_unavailable', 504: 'timeout'}.get(response.status_code, 'request_failed')
            finish_execution(settings.reports_db_path, identifier, 'cancelled' if response.status_code == 499 else 'failed', response.status_code, elapsed(), error_code=error)
            if isinstance(data, dict):
                data['lab_execution_id'] = identifier
                content = json.dumps(data, ensure_ascii=False).encode('utf-8')
        headers = dict(response.headers)
        headers.pop('content-length', None)
        headers.update({'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer'})
        return Response(content, status_code=response.status_code, headers=headers, media_type=response.media_type, background=response.background)
    except asyncio.CancelledError:
        try:
            finish_execution(settings.reports_db_path, identifier, 'cancelled', 499, elapsed(), error_code='cancelled')
        except (sqlite3.Error, OSError):
            pass  # The durable initial record is recovered on the next startup.
        raise
    except (sqlite3.Error, OSError):
        return JSONResponse({'detail': 'Falha ao confirmar o registro da execução Lab.', 'lab_execution_id': identifier}, status_code=503, headers={'Cache-Control': 'no-store'})
    except Exception:
        try:
            finish_execution(settings.reports_db_path, identifier, 'failed', 500, elapsed(), error_code='internal_error')
        except (sqlite3.Error, OSError):
            return JSONResponse({'detail': 'Falha ao confirmar o registro da execução Lab.', 'lab_execution_id': identifier}, status_code=503, headers={'Cache-Control': 'no-store'})
        return JSONResponse({'detail': 'Falha na execução Lab.', 'lab_execution_id': identifier}, status_code=500, headers={'Cache-Control': 'no-store'})


@app.exception_handler(RequestValidationError)
async def safe_validation_error(request: Request, exc: RequestValidationError):
    fields = [".".join(str(part) for part in error["loc"] if part != "body") for error in exc.errors()]
    return JSONResponse({"detail": "Contrato inválido.", "fields": fields}, status_code=422)


dist = Path(__file__).resolve().parents[2] / "web" / ("dist-lab" if settings.app_env == "lab" else "dist")
if dist.is_dir():
    app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        return FileResponse(dist / "index.html")
