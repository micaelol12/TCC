"""R4: isolamento do ajuste e fallback sem relaxar meta após avaliação."""
import unittest
from investigacao.calibracao_seletiva import choose, METHODS


class SelectiveTests(unittest.TestCase):
    """Kapoor/Narayanan (2023), R4: testes de engenharia, não validação NLP."""

    def test_selection_and_guards(self):
        """Dev perfeito permite decisão; invertido exige abstenção; teste é rejeitado."""
        rows = []
        for method in METHODS:
            for i in range(40):
                favor = i % 2 == 0
                rows.append(dict(id=str(i), method=method, split='dev', target='A',
                                 truth='favor' if favor else 'against', prediction='favor' if favor else 'against',
                                 probabilities={'entailment': .9 if favor else .05,
                                                'contradiction': .05 if favor else .9, 'neutral': .05}))
        selected, _ = choose(rows, 'B')
        self.assertFalse(selected['abstain_all'])
        self.assertEqual(selected['dev']['coverage'], 1)
        for row in rows:
            row['truth'] = 'against' if row['truth'] == 'favor' else 'favor'
        self.assertTrue(choose(rows, 'B')[0]['abstain_all'])
        with self.assertRaises(ValueError):
            choose(rows, 'A')
        rows[0]['split'] = 'test'
        with self.assertRaises(ValueError):
            choose(rows, 'B')
