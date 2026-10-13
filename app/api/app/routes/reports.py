from collections import deque
import sqlite3
from threading import Lock
from time import monotonic
from fastapi import APIRouter, HTTPException, Response
from ..report_schemas import ReportRequest, ReportResponse
from ..report_store import save_report, SubmissionConflict
from ..settings import settings

router = APIRouter(prefix="/api")
recent_requests: deque[float] = deque()
rate_lock = Lock()


@router.post("/reports", response_model=ReportResponse, status_code=201)
def report(payload: ReportRequest, response: Response):
    if len(payload.text) > settings.max_chars or len(payload.analysis.chunks) > settings.max_chunks:
        raise HTTPException(413, "Report acima do limite.")
    with rate_lock:
        now = monotonic()
        while recent_requests and recent_requests[0] < now - 3600:
            recent_requests.popleft()
        if len(recent_requests) >= settings.reports_hourly_requests:
            raise HTTPException(429, "Limite temporário de reports atingido.")
        recent_requests.append(now)
    try:
        result, created = save_report(settings.reports_db_path, payload)
    except SubmissionConflict:
        raise HTTPException(409, "Identificador já utilizado para outro report.") from None
    except (sqlite3.Error, OSError):
        raise HTTPException(503, "Não foi possível armazenar o report. Tente novamente.") from None
    response.status_code = 201 if created else 200
    return result
