"""Read-only export of all Lab executions, including failures and cancellations."""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import sys

os.environ['APP_ENV'] = 'lab'
os.environ['EXPERIMENTAL_CONFIG_ENABLED'] = 'true'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.settings import settings


def main():
    parser = argparse.ArgumentParser(description='Exportar execuções Lab para JSONL.')
    parser.add_argument('--database', default=settings.reports_db_path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--status', choices=('all', 'running', 'completed', 'completed_with_warnings', 'failed', 'cancelled', 'interrupted'), default='all')
    args = parser.parse_args()
    database = Path(args.database).expanduser().resolve()
    if not database.is_file() or database == args.output.expanduser().resolve():
        parser.error('Use um banco Lab existente e uma saída diferente do banco.')
    with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        query = 'SELECT * FROM lab_executions'
        params = () if args.status == 'all' else (args.status,)
        if params:
            query += ' WHERE status=?'
        rows = connection.execute(query + ' ORDER BY started_at, execution_id', params)
        with args.output.open('x', encoding='utf-8') as output:
            for row in rows:
                item = dict(row)
                for field in ('requested_config', 'effective_config', 'analysis'):
                    raw = item.pop(field + '_json')
                    item[field] = json.loads(raw) if raw else None
                output.write(json.dumps(item, ensure_ascii=False, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
