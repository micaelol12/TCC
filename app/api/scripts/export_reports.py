"""Run from app/api: python scripts/export_reports.py --output reports.jsonl."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.settings import settings


def main():
    parser = argparse.ArgumentParser(description="Exportar reports para avaliação local.")
    parser.add_argument("--database", default=settings.reports_db_path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--status", choices=("pending", "reviewed", "all"), default="pending")
    args = parser.parse_args()
    path = Path(args.database).expanduser().resolve()
    if args.output.expanduser().resolve() == path:
        parser.error("A saída deve ser diferente do banco de dados.")
    if not path.is_file():
        parser.error("Banco de reports ainda não existe.")
    # Read-only SQLite URI; an incorrect path cannot create a database.
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        query = "SELECT report_id, submission_id, text, analysis_json, comment, client, storage_consent, notice_version, received_at, status FROM classification_reports"
        params = () if args.status == "all" else (args.status,)
        if params:
            query += " WHERE status = ?"
        rows = connection.execute(query + " ORDER BY received_at, report_id", params)
        # Exclusive creation avoids overwriting an earlier export.
        with args.output.open("x", encoding="utf-8") as output:
            for row in rows:
                item = dict(row)
                item["analysis"] = json.loads(item.pop("analysis_json"))
                item["storage_consent"] = bool(item["storage_consent"])
                output.write(json.dumps(item, ensure_ascii=False, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
