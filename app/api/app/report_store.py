"""SQLite storage with atomic, content-aware idempotency."""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from uuid import uuid4
from .report_schemas import ReportRequest, ReportResponse


class SubmissionConflict(Exception):
    pass


def save_report(database: str, payload: ReportRequest) -> tuple[ReportResponse, bool]:
    path = Path(database).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    content = payload.model_dump(mode="json", exclude={"submission_id"})
    serialized = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    report_id = str(uuid4())
    received_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with closing(sqlite3.connect(path, timeout=5)) as connection, connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS classification_reports (
            report_id TEXT PRIMARY KEY,
            submission_id TEXT NOT NULL UNIQUE,
            content_hash TEXT NOT NULL,
            text TEXT NOT NULL,
            analysis_json TEXT NOT NULL,
            comment TEXT NOT NULL,
            client TEXT NOT NULL,
            storage_consent INTEGER NOT NULL CHECK (storage_consent = 1),
            notice_version TEXT NOT NULL,
            received_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed'))
        )""")
        connection.execute("CREATE INDEX IF NOT EXISTS reports_review_queue ON classification_reports(status, received_at)")
        connection.execute("PRAGMA user_version = 1")
        cursor = connection.execute("""INSERT INTO classification_reports
            (report_id, submission_id, content_hash, text, analysis_json, comment, client, storage_consent, notice_version, received_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?) ON CONFLICT(submission_id) DO NOTHING""",
            (report_id, str(payload.submission_id), digest, payload.text,
             json.dumps(content["analysis"], ensure_ascii=False, allow_nan=False), payload.comment,
             payload.client, payload.notice_version, received_at))
        row = connection.execute("SELECT report_id, received_at, content_hash FROM classification_reports WHERE submission_id = ?",
                                 (str(payload.submission_id),)).fetchone()
        if row[2] != digest:
            raise SubmissionConflict()
        result = ReportResponse(report_id=row[0], received_at=row[1])
        created = cursor.rowcount == 1
    # The transaction has committed before the caller can return success.
    return result, created
