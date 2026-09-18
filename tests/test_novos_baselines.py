"""R4/R7/R10: sinais, simetria e pesos, sem inferir qualidade a partir de fixtures."""
import unittest
from investigacao.nli_bilateral import score_candidates, hypotheses
from investigacao.lexical_dev import topic_weights
from investigacao.temas_reservados import PROPOSITIONS
from investigacao.bge_train_calibration import fit_threshold
from investigacao.ensemble_dev import combine


class BaselineTests(unittest.TestCase):
    """CheckList/R5: propriedades mínimas dos comparadores controlados."""

    def test_bilateral_swap(self):
        """R7: trocar apoio/oposição inverte o sinal bilateral, sem usar truth."""
        pos = dict(entailment=.8, contradiction=.1, neutral=.1)
        neg = dict(entailment=.1, contradiction=.7, neutral=.2)
        normal = score_candidates({k: [pos, neg] for k in ['nominal', 'concordancia', 'defesa']})
        inverted = score_candidates({k: [neg, pos] for k in ['nominal', 'concordancia', 'defesa']})
        for k in normal:
            if not k.startswith('baseline_'):
                self.assertAlmostEqual(normal[k], -inverted[k])
        for target in PROPOSITIONS:
            self.assertEqual(set(hypotheses(target)), {'nominal', 'concordancia', 'defesa'})

    def test_equal_topic_class_weight(self):
        """R4: grupos com tamanhos diferentes recebem a mesma massa total."""
        rows = [dict(target='A', label='favor')] * 3 + [dict(target='A', label='against')]
        weights = topic_weights(rows)
        self.assertAlmostEqual(sum(weights[:3]), weights[3])
        self.assertAlmostEqual(sum(weights), len(rows))

    def test_threshold_train_only(self):
        """R4: ajuste de limiar rejeita dev/teste e separa escores triviais."""
        rows = [dict(split='train', target=t, truth=label, score=score)
                for t in ['A', 'B'] for label, score in [('favor', .4), ('against', -.4)]]
        selection, grid = fit_threshold(rows)
        self.assertEqual(selection['threshold'], 0)
        self.assertEqual(selection['mean_topic_ba'], 1)
        rows[0]['split'] = 'dev'
        with self.assertRaises(ValueError):
            fit_threshold(rows)

    def test_ensemble_alignment(self):
        """R4: IDs são alinhados e rótulos conflitantes rejeitados."""
        left = [dict(id='x', target='A', truth='favor', scores={'baseline_autor': .4})]
        right = [dict(id='x', target='A', truth='favor', scores={'concordancia': .2})]
        self.assertAlmostEqual(combine(left, right)[0]['score'], .3)
        right[0]['truth'] = 'against'
        with self.assertRaises(ValueError):
            combine(left, right)
