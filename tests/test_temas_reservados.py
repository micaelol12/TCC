"""R4: verifica ausência de tema/autoria do teste no ajuste, não acurácia NLP."""
import unittest
from investigacao.temas_reservados import held_out, evaluate


class TopicTests(unittest.TestCase):
    """Kapoor/Narayanan (2023), R4, adaptação de isolamento por tema."""

    def test_topic_author_isolation(self):
        """Tema retido sai de treino e dev; vazamento original causa falha."""
        meta = dict(name='fixture', version='1', source='fixture', license='fixture',
                    label_definition='binary', split_policy='fixture', annotation_unit='text_target')
        rows = [dict(id=f'{s}:{t}:{y}', text=f'{s} {t} {y}', author_id=f'{s}:{y}',
                     target=t, label=y, split=s, label_source='corpus_publico')
                for s in ['train', 'dev', 'test'] for t in ['A', 'B'] for y in ['favor', 'against']]
        train, dev, test = held_out(rows, 'A', meta)
        self.assertEqual({r['target'] for r in train + dev}, {'B'})
        self.assertEqual({r['target'] for r in test}, {'A'})
        self.assertFalse({r['author_id'] for r in test} & {r['author_id'] for r in train + dev})
        rows[-1]['author_id'] = rows[0]['author_id']
        with self.assertRaises(ValueError):
            held_out(rows, 'A', meta)

    def test_selective_metrics(self):
        """R4: abstenção não recebe acerto seletivo inventado."""
        r = [dict(truth='favor', prediction='favor', state='incerta')]
        self.assertEqual(evaluate(r)['coverage'], 0)
        self.assertIsNone(evaluate(r)['accepted_accuracy'])
