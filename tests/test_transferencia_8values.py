"""R5/CheckList §2: testes de engenharia do diagnóstico, não qualidade NLP."""
import unittest
from investigacao.transferencia_8values import cases, format_cases, summarize


class TransferTests(unittest.TestCase):
    """R3/R5: direção do instrumento não vira rótulo de posição."""

    def test_format_factorial(self):
        """R5: 2×2×2 casos; remover aspas não altera texto ou rótulo."""
        q = {'id': 7, 'question': 'Adultos não devem ser censurados.', 'effect': {'govt': 10}}
        rows = format_cases([q])
        self.assertEqual(len(rows), 8)
        self.assertEqual(len({r['id'] for r in rows}), 8)
        self.assertTrue(all(q['question'] in r['text'] for r in rows))
        for row in rows:
            if row['template'].startswith('aspas_'):
                other = next(r for r in rows if r['template'] == 'sem_' + row['template'] and r['label'] == row['label'])
                self.assertEqual(row['text'].replace('«', '').replace('»', ''), other['text'])

    def test_cases_and_metrics(self):
        """Mesma proposição preservada em quatro casos; recusa não vira acerto."""
        q = {'id': 1, 'question': 'O governo não deve censurar opiniões.', 'effect': {'govt': -10}}
        rows = cases([q])
        self.assertEqual(len(rows), 4)
        self.assertEqual({r['label'] for r in rows}, {'favor', 'against'})
        self.assertTrue(all(q['question'] in r['text'] for r in rows))
        self.assertEqual(len({r['family_id'] for r in rows}), 1)
        predictions = [{**r, 'method': 'fixture', 'prediction': r['label'],
                        'state': 'incerta', 'score': int(r['label'] == 'favor')} for r in rows]
        all_metrics = summarize(predictions)[0]
        self.assertEqual(all_metrics['macro_f1'], 1)
        self.assertEqual(all_metrics['pair_ordering'], 1)
        self.assertEqual(all_metrics['direction_coverage'], 0)
        self.assertIsNone(all_metrics['accuracy_when_accepted'])
        with self.assertRaises(ValueError):
            cases([q, q])
