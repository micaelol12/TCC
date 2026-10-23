import copy
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
import importlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.report_schemas import MAX_REPORT_BYTES, ReportRequest
from app.report_store import save_report

route_module = importlib.import_module("app.routes.reports")
TEXT = "É preciso ampliar as liberdades civis.\nUma ação política em português."


def report_payload():
    analysis = {
        "schema_version": "1", "pipeline_version": "test-only", "processing_level": "high", "models_used": ["simulado"],
        "axes": [{
            "axis": axis, "pole_a": 75, "pole_b": 25, "status": "estimated", "coverage": 1,
            "valid_chunks": 1, "total_chunks": 1, "sufficient_evidence": False,
            "level_counts": {"minus2": 0, "minus1": 0, "zero": 0, "plus1": 1, "plus2": 0},
            "ci95": None, "methods_used": ["llm"], "reason_codes": ["evidencia_limitada"],
            "evidence": [{"chunk_index": 0, "quote": TEXT, "verified": True}],
        } for axis in ("economic", "diplomatic", "state", "society")],
        "chunks": [{"index": 0, "text": TEXT}], "logical_calls": {"jev": 0, "llm": 1}, "warnings": [],
    }
    return {"submission_id": str(uuid4()), "text": TEXT, "analysis": analysis, "comment": "Discordo do eixo econômico.",
            "client": "web", "storage_consent": True, "notice_version": "1"}


class ReportTests(unittest.TestCase):
    def test_nine_level_reports_and_legacy_snapshots(self):
        legacy = report_payload()
        self.assertEqual(ReportRequest.model_validate(legacy).model_dump(mode='json')['analysis'], legacy['analysis'])
        current = copy.deepcopy(legacy)
        current['analysis'].update(schema_version='2', pipeline_version='jev-9-niveis-evidence-3')
        for axis in current['analysis']['axes']:
            axis['level_counts'].update(minus4=0, minus3=0, plus3=1, plus4=0, plus1=0)
            axis.update(pole_a=87.5, pole_b=12.5)
        self.assertEqual(ReportRequest.model_validate(current).model_dump(mode='json')['analysis'], current['analysis'])
        current['analysis']['schema_version'] = '1'
        with self.assertRaises(ValueError):
            ReportRequest.model_validate(current)

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.database = str(Path(self.temp.name) / "data" / "reports.sqlite3")
        self.settings_patch = patch.object(route_module, "settings", replace(route_module.settings, reports_db_path=self.database, reports_hourly_requests=100))
        self.settings_patch.start()
        route_module.recent_requests.clear()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.settings_patch.stop()
        self.temp.cleanup()

    def test_stores_exact_snapshot_and_survives_new_client(self):
        payload = report_payload()
        with patch("app.routes.reports.save_report", wraps=save_report) as store:
            first = self.client.post("/api/reports", json=payload)
            self.assertEqual(first.status_code, 201)
            store.assert_called_once()
        self.assertEqual(first.headers["cache-control"], "no-store")
        self.assertNotIn(TEXT, first.text)
        self.client.close()
        self.client = TestClient(app)
        repeated = self.client.post("/api/reports", json=payload)
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(first.json(), repeated.json())
        with closing(sqlite3.connect(self.database)) as connection:
            rows = connection.execute("SELECT text, analysis_json, comment, client, storage_consent, notice_version, status FROM classification_reports").fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(json.loads(rows[0][1]), payload["analysis"])
        self.assertEqual((rows[0][0], *rows[0][2:]), (TEXT, payload["comment"], "web", 1, "1", "pending"))
        # A separate Python process proves storage isn't dependent on module memory.
        check = subprocess.run([sys.executable, "-c", "import sqlite3,sys; print(sqlite3.connect(sys.argv[1]).execute('SELECT count(*) FROM classification_reports').fetchone()[0])", self.database], capture_output=True, text=True, check=True)
        self.assertEqual(check.stdout.strip(), "1")

    def test_conflicting_retry_does_not_overwrite(self):
        payload = report_payload()
        first = self.client.post("/api/reports", json=payload)
        changed = {**payload, "comment": "Outro comentário"}
        response = self.client.post("/api/reports", json=changed)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.client.post("/api/reports", json=payload).json(), first.json())

    def test_concurrent_retries_create_one_row(self):
        payload = ReportRequest.model_validate(report_payload())
        with ThreadPoolExecutor(max_workers=4) as workers:
            results = list(workers.map(lambda _: save_report(self.database, payload), range(4)))
        self.assertEqual(sum(created for _, created in results), 1)
        self.assertEqual(len({str(result.report_id) for result, _ in results}), 1)

    def test_consent_and_notice_required_without_echoing_input(self):
        for field, value in (("storage_consent", False), ("storage_consent", 1), ("storage_consent", "true"), ("notice_version", "outdated"), ("client", "unknown")):
            with self.subTest(field=field, value=value):
                payload = report_payload()
                payload[field] = value
                result = self.client.post("/api/reports", json=payload)
                self.assertEqual(result.status_code, 422)
                self.assertNotIn(TEXT, result.text)
        for field in ("storage_consent", "notice_version"):
            payload = report_payload()
            del payload[field]
            self.assertEqual(self.client.post("/api/reports", json=payload).status_code, 422)
        self.assertFalse(Path(self.database).exists())

    def test_rejects_invalid_snapshot_and_unrelated_data(self):
        original = report_payload()
        mutations = [
            lambda p: p.update(profile={"economic": 88}),
            lambda p: p.update(text="Texto diferente da análise."),
            lambda p: p.update(comment="x" * 2001),
            lambda p: p["analysis"].update(axes=[]),
            lambda p: p["analysis"]["axes"][0].update(pole_a=200),
            lambda p: p["analysis"]["axes"][0].update(pole_a=float("nan")),
            lambda p: p["analysis"]["axes"][0].update(axis="society"),
            lambda p: p["analysis"]["axes"][0]["evidence"][0].update(chunk_index=55),
            lambda p: p["analysis"]["axes"][0]["evidence"][0].update(quote="citação inventada e ausente"),
        ]
        for mutation in mutations:
            payload = copy.deepcopy(original)
            mutation(payload)
            response = self.client.post("/api/reports", content=json.dumps(payload), headers={"Content-Type": "application/json"})
            self.assertEqual(response.status_code, 422)
            self.assertNotIn(TEXT, response.text)
        self.assertFalse(Path(self.database).exists())

    def test_existing_pipeline_evidence_normalization_is_accepted(self):
        payload = report_payload()
        payload["analysis"]["axes"][0]["evidence"][0]["quote"] = "É preciso ampliar as liberdades civis. Uma ação política em português."
        self.assertEqual(self.client.post("/api/reports", json=payload).status_code, 201)
        # The tokenizer can emit a whitespace-only final chunk; it remains part of the original snapshot.
        payload = report_payload()
        payload["text"] += "\n "
        payload["analysis"]["chunks"].append({"index": 1, "text": "\n "})
        for axis in payload["analysis"]["axes"]:
            axis.update(total_chunks=2, coverage=0.5)
        self.assertEqual(self.client.post("/api/reports", json=payload).status_code, 201)

    def test_limits_actual_body_bytes_even_without_content_length(self):
        for content in (b"x" * (MAX_REPORT_BYTES + 1), iter([b"x" * 1_000_000, b"y" * 1_000_001])):
            self.assertEqual(self.client.post("/api/reports", content=content).status_code, 413)
        with patch.object(route_module, "settings", replace(route_module.settings, max_chars=10)):
            self.assertEqual(self.client.post("/api/reports", json=report_payload()).status_code, 413)
        self.assertFalse(Path(self.database).exists())

    def test_rate_limit_is_separate_from_analysis_budget(self):
        with patch.object(route_module, "settings", replace(route_module.settings, reports_hourly_requests=1)):
            self.assertEqual(self.client.post("/api/reports", json=report_payload()).status_code, 201)
            self.assertEqual(self.client.post("/api/reports", json=report_payload()).status_code, 429)
        self.assertEqual(self.client.get("/api/health").status_code, 200)

    def test_storage_failure_does_not_confirm_or_leak_paths(self):
        for failure in (sqlite3.OperationalError("private database path"), OSError("private database path")):
            with patch.object(route_module, "save_report", side_effect=failure):
                response = self.client.post("/api/reports", json=report_payload())
                self.assertEqual(response.status_code, 503)
                self.assertNotIn("private database path", response.text)
                self.assertNotIn("report_id", response.json())

    def test_export_preserves_data_and_does_not_overwrite(self):
        payload = report_payload()
        self.client.post("/api/reports", json=payload)
        output = Path(self.temp.name) / "reports.jsonl"
        script = str(Path(__file__).resolve().parents[1] / "scripts" / "export_reports.py")
        command = [sys.executable, script, "--database", self.database, "--output", str(output)]
        subprocess.run(command, check=True, capture_output=True)
        exported = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(exported["analysis"], payload["analysis"])
        self.assertEqual(exported["text"], TEXT)
        self.assertTrue(exported["storage_consent"])
        self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
        self.assertEqual(json.loads(output.read_text(encoding="utf-8")), exported)


if __name__ == "__main__":
    unittest.main()
