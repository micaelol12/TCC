"""Regressões da inspeção: snapshots, HTML seguro e integração sem APIs."""

import ast
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from analise_jev_llm.fluxograma_playground import (
    EIXOS, criar_dados_fluxograma, exibir_fluxograma, renderizar_fluxograma,
)

ROOT = Path(__file__).resolve().parents[1]


def exemplo():
    d = {"relevante": True, "nivel": 0, "valor_0_100": 50.0,
         "metodo": "jev_ordinal", "status": "sem_posicao"}
    r = {"texto": "Um texto com evidência literal.",
         "eixos_jev": {e: deepcopy(d) for e in EIXOS},
         "eixos": {e: deepcopy(d) for e in EIXOS},
         "chamadas_llm": 1, "config": {"usar_fallback": True},
         "motivos_fallback": {e: [] for e in EIXOS}}
    r["eixos"]["diplomatic"].update(relevante=False, nivel=None, valor_0_100=None)
    r["eixos"]["state"].update(relevante=True, nivel=None, valor_0_100=None,
                               metodo="llm_ordinal", status="posicao_indeterminada")
    r["eixos"]["society"].update(relevante=None, nivel=None, valor_0_100=None,
                                 metodo="llm_ordinal", status="falha_llm")
    coverage = pd.DataFrame([{"eixo": e, "índice A": 50.0 if e == "economic" else np.nan,
                             "chunks com nível": np.int64(e == "economic")}
                            for e in EIXOS])
    return [r], coverage


class FluxogramaTest(unittest.TestCase):
    def test_snapshot_independente_preserva_zero_ausencia_e_falhas(self):
        records, coverage = exemplo()
        context = {"preparacao": {"chunks": {"max_tokens": 600}}}
        data = criar_dados_fluxograma(records, coverage, contexto=context)
        records[0]["eixos"]["economic"]["nivel"] = 2
        context["preparacao"]["chunks"]["max_tokens"] = 10
        coverage.loc[0, "índice A"] = 100
        self.assertEqual(data["contexto"]["preparacao"]["chunks"]["max_tokens"], 600)
        self.assertEqual(data["registros"][0]["eixos"]["economic"]["nivel"], 0)
        self.assertEqual(data["cobertura"][0]["índice A"], 50)
        self.assertIsNone(data["cobertura"][1]["índice A"])
        self.assertEqual(data["registros"][0]["eixos"]["society"]["status"], "falha_llm")
        json.dumps(data, allow_nan=False)

    def test_texto_e_evidencia_nao_encerram_script(self):
        records, coverage = exemplo()
        payload = '</script><script>alert("texto")</script><img onerror="alert(1)"> & ação'
        records[0]["texto"] = payload
        records[0]["eixos"]["state"]["evidencia"] = payload
        page = renderizar_fluxograma(criar_dados_fluxograma(records, coverage))
        self.assertNotIn(payload, page)
        raw = page.split('<script id="data" type="application/json">', 1)[1].split('</script>', 1)[0]
        self.assertEqual(json.loads(raw)["registros"][0]["texto"], payload)
        self.assertEqual(page.count('<script'), 2)

    def test_dados_incompletos_falham_com_mensagem(self):
        records, coverage = exemplo()
        with self.assertRaisesRegex(ValueError, "Execute a análise"):
            criar_dados_fluxograma([], coverage)
        del records[0]["eixos"]["state"]
        with self.assertRaisesRegex(ValueError, "quatro eixos"):
            criar_dados_fluxograma(records, coverage)

    def test_cobertura_de_outra_execucao_nao_e_exibida(self):
        records, coverage = exemplo()
        coverage["chunks"] = 2
        with self.assertRaisesRegex(ValueError, "mesma execução"):
            criar_dados_fluxograma(records, coverage)

    def test_html_exportado_e_iframe_usam_mesma_execucao(self):
        data = criar_dados_fluxograma(*exemplo())
        with tempfile.TemporaryDirectory() as tmp, patch('IPython.display.display') as display:
            path = Path(tmp) / 'fluxograma.html'
            self.assertEqual(exibir_fluxograma(data, path), path)
            self.assertEqual(path.read_text(encoding='utf-8'), renderizar_fluxograma(data))
            iframe = display.call_args.args[0].data
            self.assertIn('sandbox="allow-scripts"', iframe)
            self.assertIn('srcdoc="', iframe)

    def test_celula_analise_congela_config_e_modelo_do_cliente_ativo(self):
        nb = json.loads((ROOT / 'Pipeline - Passo a Passo.ipynb').read_text(encoding='utf-8'))
        source = ''.join(next(c for c in nb['cells'] if c['id'] == 'playground-analise')['source'])
        records, coverage = exemplo()
        client = SimpleNamespace(model='modelo-ativo', temperature=0.25)

        def pipeline(**kwargs):
            return SimpleNamespace(llm=kwargs['llm'], tentativas_llm=kwargs['tentativas_llm'],
                                   config={"usar_fallback": True}, rubricas={})

        async def classify(*args):
            return records

        config = {"modelo_jev": "jev-teste", "timeout_llm_s": 123,
                  "tentativas_llm": 2, "cascata": {"usar_fallback": True}}
        ns = dict(Path=Path, os=os, deepcopy=deepcopy, datetime=datetime, timezone=timezone,
                  load_dotenv=lambda *a, **k: None, CONFIG_PIPELINE_PLAYGROUND=config,
                  CONFIG_PLAYGROUND={"nome": "Teste local"}, playground_llm=client,
                  AsyncTypeSafeClient=lambda **kw: None, CascataJevLLM2Polos=pipeline,
                  AXIS_SPECS={}, TENTATIVAS=3, PAUSA_SEGUNDOS=0,
                  preparacao_playground={"chunks": {"max_tokens": 600}},
                  CONFIG_INDICE={"n_bootstrap": 100, "semente": 42},
                  chunks_playground=[records[0]['texto']], classificar_lote=classify,
                  resumir_documento=lambda r: coverage,
                  display=lambda *args: None,
                  tabela_auditoria_evidencias=lambda r: pd.DataFrame(),
                  converter_documento_8values=lambda c: {"eixos": []})
        with patch.dict(os.environ, TYPESAFE_API_KEY='teste', MARITACA_API_KEY='teste'):
            asyncio.run(eval(compile(source, '<playground-analise>', 'exec',
                                     flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT), ns))
        data = ns['dados_fluxograma_playground']
        client.model = 'outro-modelo'
        ns['CONFIG_INDICE']['semente'] = 99
        self.assertEqual(data['contexto']['pipeline']['modelo_llm'], 'modelo-ativo')
        self.assertEqual(data['contexto']['indice']['semente'], 42)
        self.assertNotIn('api_key', json.dumps(data))


if __name__ == '__main__':
    unittest.main()
