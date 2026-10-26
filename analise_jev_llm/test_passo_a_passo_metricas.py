"""Regressões das métricas do notebook; executa somente definições locais, sem APIs."""

import unittest
from pathlib import Path
from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from tcc_lib.notebook_pipeline import carregar_pipeline_notebook


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "Pipeline - Passo a Passo.ipynb"


def carregar_definicoes():
    nomes = {
        "CONFIG_INDICE", "NIVEIS_POLARIDADE", "SITUACAO_SEM_POSICAO", "AXIS_SPECS",
        "EFFECT_TO_AXIS", "MAPA_SCORE_CASCATA", "esperado_pelo_efeito",
        "estado_da_decisao", "avaliar_registros", "avaliar_escada_ordinal",
        "_indices_blocos", "resumir_eixo_ordinal", "resumir_documento",
        "ECON_ARRAY", "DIPL_ARRAY", "GOVT_ARRAY", "SCTY_ARRAY",
        "DIPL_SCTY_EXPONENT", "MAPA_8VALUES", "rotulo_8values",
        "converter_documento_8values", "grafico_scores", "plotar_documento",
    }
    ns = carregar_pipeline_notebook(NOTEBOOK)
    if faltantes := nomes - ns.keys():
        raise AssertionError(f"Definições não encontradas: {faltantes}")
    return ns


NS = carregar_definicoes()


def decisao(relevante=True, nivel=1):
    return {
        "relevante": relevante, "nivel": nivel,
        "valor_0_100": None if nivel is None else 50 + 25 * nivel,
        "classe": "C" if nivel in (None, 0) else "A" if nivel > 0 else "B",
        "metodo": "jev_ordinal", "status": "simulado",
    }


def registro(texto, d):
    eixos = {e: decisao(False, None) for e in NS["AXIS_SPECS"]}
    eixos["economic"] = d
    return {"texto": texto, "eixos": eixos, "eixos_jev": eixos}


def pergunta(texto, efeito=10):
    return SimpleNamespace(
        id=texto, question=texto,
        effect=SimpleNamespace(econ=efeito, dipl=0, govt=0, scty=0),
    )


class MetricasTest(unittest.TestCase):
    def test_estados_distinguem_zero_irrelevancia_e_duas_abstencoes(self):
        casos = [(decisao(True, 0), "sem_posicao"),
                 (decisao(False, None), "irrelevante"),
                 (decisao(None, None), "abstencao"),
                 (decisao(True, None), "abstencao"),
                 (decisao(True, -2), "direcional")]
        for d, esperado in casos:
            with self.subTest(decisao=d):
                self.assertEqual(NS["estado_da_decisao"](d), esperado)

    def test_benchmark_penaliza_zero_irrelevancia_e_abstencao_em_alvo_direcional(self):
        decisoes = [decisao(True, 0), decisao(False, None),
                    decisao(True, None), decisao(True, 1)]
        perguntas = [pergunta(str(i)) for i in range(4)]
        registros = [registro(str(i), d) for i, d in enumerate(decisoes)]
        _, resumo = NS["avaliar_registros"](perguntas, registros)
        linha = resumo.query("etapa == 'eixos' and eixo == 'economic'").iloc[0]
        self.assertEqual(linha["acuracia_conjunta"], 0.25)
        self.assertEqual(linha["acuracia_direcao_relevantes"], 0.25)
        self.assertEqual(linha["relevantes_esperados"], 4)
        self.assertEqual(linha["acuracia_relevancia"], 0.75)
        for nome in ["direcionais", "sem_posicao", "irrelevantes", "abstencoes"]:
            self.assertEqual(linha[nome], 1)

    def test_efeito_zero_nao_equivale_a_nivel_zero(self):
        for d, acerto in [(decisao(True, 0), 0.0), (decisao(False, None), 1.0)]:
            _, resumo = NS["avaliar_registros"]([pergunta("a", 0)], [registro("a", d)])
            linha = resumo.query("etapa == 'eixos' and eixo == 'economic'").iloc[0]
            self.assertEqual(linha["acuracia_conjunta"], acerto)
            self.assertTrue(pd.isna(linha["acuracia_direcao_relevantes"]))

    def test_escada_zero_exige_relevancia_e_nivel_zero(self):
        decisoes = [decisao(True, 0), decisao(False, None),
                    decisao(True, None), decisao(None, None)]
        escada = [("economic", 0, str(i)) for i in range(4)]
        registros = [registro(str(i), d) for i, d in enumerate(decisoes)]
        _, resumo = NS["avaliar_escada_ordinal"](escada, registros)
        linha = resumo.query("etapa == 'eixos'").iloc[0]
        self.assertEqual(linha["acerto_exato"], 0.25)
        self.assertEqual(linha["cobertura_nivel"], 0.25)
        self.assertEqual(linha["sem_posicao"], 1)
        self.assertEqual(linha["irrelevantes"], 1)
        self.assertEqual(linha["abstencoes"], 2)
        self.assertEqual(linha["sem_nivel"], 3)
        self.assertEqual(linha["erro_absoluto_medio"], 0)

    def test_escada_sem_nivel_tem_mae_ausente(self):
        _, resumo = NS["avaliar_escada_ordinal"](
            [("economic", 2, "a")], [registro("a", decisao(False, None))])
        self.assertTrue(resumo["erro_absoluto_medio"].isna().all())
        self.assertTrue((resumo["acerto_exato"] == 0).all())

    def test_escada_erro_ordinal_preserva_distancia_entre_extremos(self):
        _, resumo = NS["avaliar_escada_ordinal"](
            [("economic", 2, "a")], [registro("a", decisao(True, -2))])
        self.assertTrue((resumo["erro_absoluto_medio"] == 4).all())

    def test_recusa_registros_fora_de_ordem(self):
        with self.assertRaises(ValueError):
            NS["avaliar_escada_ordinal"]([("economic", 0, "a")], [registro("b", decisao())])
        with self.assertRaises(ValueError):
            NS["avaliar_registros"]([pergunta("a")], [registro("b", decisao())])

    def test_recusa_escada_vazia_ou_incompleta(self):
        for escada, registros in [([], []), ([("economic", 0, "a")], [])]:
            with self.assertRaises(ValueError):
                NS["avaliar_escada_ordinal"](escada, registros)


class EvidenciaTest(unittest.TestCase):
    def test_texto_curto_produz_indice_sem_ic(self):
        resumo = NS["resumir_eixo_ordinal"]([decisao()], **NS["CONFIG_INDICE"])
        self.assertEqual(resumo["índice A"], 75)
        self.assertTrue(resumo["evidência disponível"])
        self.assertEqual(resumo["base da estimativa"], "trecho único")
        self.assertIsNone(resumo["IC95 inferior"])
        self.assertIsNone(resumo["IC95 superior"])
        self.assertNotIn("evidência suficiente", resumo)

    def test_um_nivel_em_varios_chunks_continua_sem_ic(self):
        resumo = NS["resumir_eixo_ordinal"](
            [decisao(False, None), decisao(), decisao(True, None)])
        self.assertEqual(resumo["base da estimativa"], "trecho único")
        self.assertEqual(resumo["cobertura"], 1 / 3)
        self.assertIsNone(resumo["IC95 inferior"])

    def test_ausencias_nao_viram_centro(self):
        resumo = NS["resumir_eixo_ordinal"]([decisao(False, None), decisao(None, None)])
        self.assertIsNone(resumo["índice A"])
        self.assertFalse(resumo["evidência disponível"])
        self.assertEqual(resumo["base da estimativa"], "sem evidência")
        self.assertEqual(resumo["cobertura"], 0)

    def test_zero_entra_na_media_e_ausencias_nao(self):
        resumo = NS["resumir_eixo_ordinal"](
            [decisao(), decisao(True, 0), decisao(False, None), decisao(True, None)])
        self.assertEqual(resumo["índice A"], 62.5)
        self.assertEqual(resumo["cobertura"], 0.5)
        self.assertEqual(resumo["base da estimativa"], "múltiplos trechos")
        self.assertIsNotNone(resumo["IC95 inferior"])

    def test_conversao_e_grafico_identificam_resultado_exploratorio(self):
        tabela = NS["resumir_documento"]([registro("a", decisao())])
        resultado = NS["converter_documento_8values"](tabela)
        self.assertEqual(resultado["scores"]["equality"], 75)
        self.assertEqual(resultado["scores"]["wealth"], 25)
        self.assertIsNone(resultado["scores"]["peace"])
        self.assertEqual(resultado["eixos"][0]["base da estimativa"], "trecho único")
        self.assertIn("rótulo exploratório por faixa", resultado["eixos"][0])
        self.assertIn("exploratórios", resultado["interpretacao"])
        ax = NS["grafico_scores"](resultado["scores"], resultado["labels"], "Teste",
                                  contagens=[1, 0, 0, 0])
        self.assertIn("exploratórios", ax.get_title())
        self.assertTrue(any("trecho único" in t.get_text() for t in ax.texts))
        self.assertEqual(ax.patches[0].get_height(), 75)
        self.assertTrue(np.isnan(ax.patches[1].get_height()))
        self.assertEqual(ax.get_xlim(), (-0.6, 3.6))
        plt.close(ax.figure)


if __name__ == "__main__":
    unittest.main()
