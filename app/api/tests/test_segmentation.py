import hashlib
import json
from pathlib import Path
import sys
import unittest

from app.experiment_config import CONFIG_VERSION, ExperimentConfig, config_hash
from app.pipeline.segmentation import encoder, split_text
from app.settings import Settings


class SentenceSegmentationTests(unittest.TestCase):
    def test_preserves_sentences_portuguese_abbreviations_and_original_text(self):
        text = '  O Dr. Silva apresentou a proposta de educação pública.\r\n' * 12
        text += '\r\n## Saúde\r\n1. Vamos ampliar a saúde pública.\r\n2. Vamos melhorar os hospitais.  '
        chunks, count = split_text(text, max_tokens=12000, chunk_tokens=45, strategy='sentencas')
        self.assertEqual(''.join(chunks), text)
        self.assertEqual(count, len(encoder().encode(text)))
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertFalse(chunk.rstrip().endswith('Dr.'))
            self.assertFalse(chunk.rstrip().endswith('## Saúde'))
            self.assertTrue(chunk.rstrip().endswith('.'))

    def test_long_sentence_is_not_truncated_and_total_limit_still_applies(self):
        sentence = 'Vamos ampliar ' + 'a educação pública e a saúde ' * 120 + 'em todo o país.'
        text = sentence + ' Outra proposta será discutida.'
        chunks, _ = split_text(text, max_tokens=12000, chunk_tokens=100, strategy='sentencas')
        self.assertEqual(chunks[0].strip(), sentence)
        self.assertGreater(len(encoder().encode(chunks[0])), 100)
        self.assertEqual(''.join(chunks), text)
        with self.assertRaisesRegex(ValueError, 'token_limit'):
            split_text(text, max_tokens=100, strategy='sentencas')
        for strategy in ('sentencas', 'tokens'):
            self.assertEqual(split_text('', max_tokens=100, strategy=strategy), ([], 0))
            self.assertEqual(''.join(split_text(' \n\t ', max_tokens=100, strategy=strategy)[0]), ' \n\t ')

    def test_matches_notebook_grouping_with_local_packaged_resources(self):
        root = Path(__file__).resolve().parents[3]
        sys.path.insert(0, str(root))
        from tcc_lib.segmentacao import _agrupar_sentencas, _unidades
        resource_root = root / 'tcc_lib/resources/punkt_portuguese'
        api_resources = root / 'app/api/app/pipeline/resources/punkt_portuguese'
        for resource in resource_root.iterdir():
            self.assertEqual(resource.read_bytes(), (api_resources / resource.name).read_bytes())
        texts = [
            'O Sr. Silva apresentou a proposta. A saúde deve melhorar.\n\nOutra proposta será analisada. ' * 15,
            '# EDUCAÇÃO\n\nVamos ampliar os serviços públicos.\n- Melhorar a saúde.\n- Investir nas escolas.\n' * 12,
            'Proposta longa ' * 150 + '. Fim.',
        ]
        count = lambda text: len(encoder().encode(text, disallowed_special=()))
        for text in texts:
            expected = _agrupar_sentencas(text, _unidades(text), 60, count)
            actual, _ = split_text(text, max_tokens=12000, chunk_tokens=60, strategy='sentencas')
            self.assertEqual([chunk.strip() for chunk in actual], expected)
            self.assertEqual(''.join(actual), text)

    def test_legacy_hashes_and_lab_defaults(self):
        self.assertEqual(Settings(app_env='lab').algorithm_defaults().chunk_strategy, 'sentencas')
        self.assertEqual(Settings(app_env='development').algorithm_defaults().chunk_strategy, 'tokens')
        config = ExperimentConfig(regra_decisao='polo_primeiro', primitiva_polaridade='choice')
        effective = config.model_dump(exclude={'chunk_strategy'})
        public = {'config_version': CONFIG_VERSION, 'pipeline_version': 'jev-escalas-ordinal-6', 'effective_config': effective}
        expected = hashlib.sha256(json.dumps(public, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()
        self.assertEqual(config_hash(config, 'jev-escalas-ordinal-6'), expected)
        with self.assertRaises(ValueError):
            config_hash(ExperimentConfig(chunk_strategy='sentencas'), 'jev-escalas-ordinal-6')


if __name__ == '__main__':
    unittest.main()
