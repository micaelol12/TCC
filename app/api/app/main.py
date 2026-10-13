from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from .routes.analyze import router
from .routes.reports import router as reports_router
from .report_schemas import MAX_REPORT_BYTES

app = FastAPI(title="8values — análise de textos", docs_url=None, redoc_url=None)
app.include_router(router)
app.include_router(reports_router)


@app.middleware("http")
async def privacy_headers(request: Request, call_next):
    length = request.headers.get("content-length", "0")
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


@app.exception_handler(RequestValidationError)
async def safe_validation_error(request: Request, exc: RequestValidationError):
    fields = [".".join(str(part) for part in error["loc"] if part != "body") for error in exc.errors()]
    return JSONResponse({"detail": "Contrato inválido.", "fields": fields}, status_code=422)


dist = Path(__file__).resolve().parents[2] / "web" / "dist"
if dist.is_dir():
    app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        return FileResponse(dist / "index.html")
