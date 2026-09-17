"""R9/R4: contrato de rótulos e isolamento; fixture não mede qualidade NLP."""
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from investigacao.dados import BRMORAL_TARGETS, import_brmoral


class BRmoralTests(unittest.TestCase):
    """Santos e Paraboni (2019), §3.1; adaptações em METODOLOGIA R9."""

    def test_labels_exclusions_and_group_isolation(self):
        """Neutro/ausente excluídos; duplicata entre autores não cruza partições."""
        records = []
        for i in range(30):
            r = {'sid': str(i)}
            for j, topic in enumerate(BRMORAL_TARGETS):
                r['t.' + topic] = f'Opinião {i} sobre {topic}'
                r['s.' + topic] = '0' if j % 2 else '5'
                r['st.' + topic] = 'against' if j % 2 else 'for'
            records.append(r)
        records[1]['t.gay-marriage'] = records[0]['t.gay-marriage']
        records[2]['s.abortion'], records[2]['st.abortion'] = '2', 'neutral'
        records[3]['s.abortion'] = 'na'
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=list(records[0]), delimiter=';')
        writer.writeheader()
        writer.writerows(records)
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / 'source.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr('data.csv', buf.getvalue().encode('cp1252'))
            output = Path(tmp) / 'prepared'
            audit = import_brmoral(archive, output)
            self.assertEqual(audit['n'], 238)
            rows = [json.loads(s) for s in (output / 'corpus.jsonl').read_text(encoding='utf-8').splitlines()]
            self.assertEqual(len({r['split'] for r in rows if r['author_id'] in {'0', '1'}}), 1)
            other = Path(tmp) / 'repeat'
            self.assertEqual(audit, import_brmoral(archive, other))
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr('data.csv', buf.getvalue().replace(';5;for', ';5;against', 1).encode('cp1252'))
            with self.assertRaises(ValueError):
                import_brmoral(archive, Path(tmp) / 'invalid')
