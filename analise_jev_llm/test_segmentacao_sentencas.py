"""Fronteiras linguísticas, integridade e compatibilidade, sem rede ou modelos."""
import ast
from copy import deepcopy
import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

import tiktoken.registry
from langchain_text_splitters import RecursiveCharacterTextSplitter

from tcc_lib.segmentacao import intervalos_sentencas, normalizar_quebras_texto, preparar_segmentacao


ROOT = Path(__file__).resolve().parents[1]


class SegmentacaoSentencasTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Mesmo vocabulário cl100k versionado no projeto; não baixa o cache.
        cls.encoder = runpy.run_path(str(ROOT / "app/api/app/pipeline/segmentation.py"))["encoder"]()
        cls.cache = patch.dict(tiktoken.registry.ENCODINGS, {"cl100k_base": cls.encoder})
        cls.cache.start()
        cls.addClassCleanup(cls.cache.stop)
        cls.nb = json.loads((ROOT / "Pipeline - Passo a Passo.ipynb").read_text(encoding="utf-8"))

    def contar(self, texto):
        return len(self.encoder.encode(texto, disallowed_special=()))

    def test_corta_entre_sentencas_com_pontuacao_na_frase_correta(self):
        frases = ["Defendemos a liberdade de expressão.", "Rejeitamos a censura estatal."]
        r = preparar_segmentacao(" ".join(frases), tokens_alvo=15)
        self.assertEqual(r["chunks"], frases)
        self.assertEqual([d["sentencas"] for d in r["diagnostico"]], [1, 1])
        self.assertTrue(all(d["tokens"] <= 15 for d in r["diagnostico"]))

    def test_abreviacoes_numeros_perguntas_e_aspas(self):
        frases = [
            "O art. 5º assegura direitos.", "O Dr. Silva apresentou a proposta.",
            "A resolução nº 23.732/2024 foi aprovada.",
            "O texto diz “Não haverá censura.”", "Devemos ampliar direitos?", "Sim!",
        ]
        # Alvo menor que cada frase: a exceção deve preservá-la inteira.
        r = preparar_segmentacao(" ".join(frases), tokens_alvo=1)
        self.assertEqual(r["chunks"], frases)

    def test_referencias_juridicas_entre_aspas_e_com_quebras(self):
        for referencia in ('“Art. 9º-H', '“Art. 29-A.', '“Art.\n9º-H',
                           '“Art.\n\n9.504', '“Art.\r\n9.504', '"Art. 29-A.', '“Inc. IV'):
            frase = referencia + ' A remoção observará o art. 9º desta resolução.”'
            texto = 'Uma decisão anterior.\n\n' + frase + '\n\nOutra decisão.'
            with self.subTest(referencia=referencia):
                r = preparar_segmentacao(texto, tokens_alvo=1)
                self.assertEqual(r['chunks'], ['Uma decisão anterior.', frase, 'Outra decisão.'])
                self.assertEqual([texto[a:b] for a, b in intervalos_sentencas(texto)], r['chunks'])

    def test_codigos_numeros_abreviacoes_e_urls_nao_perdem_fim_real_da_frase(self):
        frases = [
            'A Res.-TSE nº 23.732/2024 altera a Lei nº 9.504/1997.',
            'O art. 5º remete aos arts. 17 a 20 e ao inc. IV.',
            'Consulte a pág. 12 e o Dr. Silva.',
            'O valor é R$ 2.000,00 e a versão é v1.2.3.',
            'O identificador é ABC.123.XYZ.',
            'Na U.S.A. existem normas.',
            'Consulte https://exemplo.org/a.b?x=1.2 para detalhes.',
            'Consulte https://exemplo.org/a.b.',
            'Escreva para nome.sobrenome@exemplo.org.',
            'Outra frase!',
        ]
        texto = ' '.join(frases)
        self.assertEqual(preparar_segmentacao(texto, tokens_alvo=1)['chunks'], frases)
        for a, b in intervalos_sentencas(texto):
            self.assertIn(texto[a:b], frases)

    def test_regressao_cortes_do_relatorio_tse_sem_chamadas_a_modelos(self):
        from tcc_lib.notebook_pipeline import carregar_pipeline_notebook
        ns = carregar_pipeline_notebook()
        dados = json.loads((ROOT / 'pesquisa_exemplos/textos_teste.json').read_text(encoding='utf-8'))
        original = dados['textos_grandes'][-1]['texto']
        texto, _ = ns['limpar_markdown'](original.strip())
        resultado = preparar_segmentacao(texto, tokens_alvo=600)
        self.assertEqual(' '.join(' '.join(resultado['chunks']).split()), ' '.join(texto.split()))
        for chunk in resultado['chunks']:
            self.assertFalse(chunk.rstrip().endswith('Art.'))
        for referencia in ('“Art. 9º-H', '“Art. 29-A.'):
            self.assertEqual(sum(referencia in chunk for chunk in resultado['chunks']), 1)
        intervalos = intervalos_sentencas(texto)
        tamanho = max(1, (len(intervalos) + 199) // 200)
        esperado = {}
        for i in range(0, len(intervalos), tamanho):
            a, b = intervalos[i][0], intervalos[min(i + tamanho, len(intervalos)) - 1][1]
            esperado[f'S{i // tamanho:03d}'] = {'start': a, 'end': b, 'quote': texto[a:b]}
        self.assertEqual(ns['sentence_spans'](texto), esperado)

    def test_preserva_paragrafo_que_cabe_sem_completar_chunk_com_metade_dele(self):
        primeiro = "Defendemos direitos."
        segundo = "Vamos ampliar a participação social. Também protegeremos as liberdades civis."
        alvo = self.contar(segundo)
        self.assertLess(self.contar(primeiro), alvo)
        r = preparar_segmentacao(primeiro + "\n\n" + segundo, tokens_alvo=alvo)
        self.assertEqual(r["chunks"], [primeiro, segundo])
        self.assertEqual(r["diagnostico"][1]["sentencas"], 2)

    def test_quebras_de_pdf_nao_encerram_frase(self):
        for quebra in ("\n", "\n\n", "\n\n\n"):
            texto = "Precisamos preservar nossa" + quebra + "capacidade de fazer escolhas políticas e econômicas."
            with self.subTest(quebra=repr(quebra)):
                self.assertEqual(preparar_segmentacao(texto, tokens_alvo=10)["chunks"], [texto])

    def test_normalizacao_preserva_titulo_itens_tabela_e_paragrafos(self):
        texto = ("# Direitos\r\nDefendemos a liberdade\r\nde expressão.\r\n\r\n"
                 "1. Ampliar a participação\r\nsocial\r\n2. Garantir direitos\r\n"
                 "| Tema | Proposta |\r\n| Saúde | Ampliar acesso |")
        normalizado, unidas = normalizar_quebras_texto(texto)
        self.assertEqual(unidas, 2)
        self.assertEqual(normalizado, (
            "# Direitos\nDefendemos a liberdade de expressão.\n\n"
            "1. Ampliar a participação social\n2. Garantir direitos\n"
            "| Tema | Proposta |\n| Saúde | Ampliar acesso |"))

    def test_listas_sem_ponto_final_e_numeracao_nao_viram_fragmentos(self):
        for prefixos in (("1.", "2.", "3."), ("I -", "II -", "III -"), ("•", "•", "•")):
            itens = [f"{p} {t}" for p, t in zip(prefixos, (
                "Defender a liberdade de expressão", "Rejeitar a censura estatal",
                "Ampliar a participação social"))]
            with self.subTest(prefixos=prefixos):
                self.assertEqual(preparar_segmentacao("\n".join(itens), tokens_alvo=1)["chunks"], itens)

    def test_titulo_fica_com_o_texto_se_couber(self):
        texto = "# Direitos\n\nDefendemos a liberdade de expressão."
        r = preparar_segmentacao(texto, tokens_alvo=self.contar(texto))
        self.assertEqual(r["chunks"], [texto])
        self.assertEqual(r["diagnostico"][0]["sentencas"], 1)

    def test_titulo_de_paragrafo_longo_nao_fica_no_chunk_anterior(self):
        antes = "Defendemos a liberdade de expressão e a participação de toda a sociedade."
        titulo = "# Acesso à justiça"
        frase = "Garantiremos acesso à justiça."
        alvo = self.contar(antes + "\n\n" + titulo)
        texto = antes + "\n\n" + titulo + "\n\n" + " ".join([frase] * 10)
        r = preparar_segmentacao(texto, tokens_alvo=alvo)
        self.assertEqual(r["chunks"][0], antes)
        self.assertTrue(r["chunks"][1].startswith(titulo + "\n\n" + frase))

    def test_sentenca_longa_fica_sozinha_e_e_sinalizada(self):
        longa = "Defendemos " + "a liberdade de expressão e a participação social, " * 100 + "com direitos."
        antes, depois = "Vamos garantir direitos.", "Rejeitamos a censura."
        r = preparar_segmentacao(f"{antes} {longa} {depois}")
        self.assertEqual(r["chunks"], [antes, longa, depois])
        self.assertGreater(r["diagnostico"][1]["tokens"], 600)
        self.assertEqual(r["diagnostico"][1]["sentencas_longas"], 1)
        self.assertTrue(r["diagnostico"][1]["acima_alvo"])
        with self.assertRaisesRegex(ValueError, "não foi truncado"):
            preparar_segmentacao(longa, limite_tokens_entrada=700)

    def test_integridade_ordem_e_ausencia_de_sobreposicao(self):
        texto = "\n\n".join(f"A proposta {i} amplia direitos e garante participação social." for i in range(30))
        r = preparar_segmentacao(texto, tokens_alvo=45)
        # Normalizar espaços permite comparar o conteúdo sem impor os separadores
        # escolhidos entre chunks. Não pode haver perda, repetição ou reordenação.
        self.assertEqual(" ".join(" ".join(r["chunks"]).split()), " ".join(texto.split()))
        for d in r["diagnostico"]:
            self.assertEqual(d["tokens"], self.contar(d["texto"]))
            self.assertLessEqual(d["tokens"], 45)

    def test_modo_anterior_reproduz_splitter_e_alias(self):
        texto = ("Um plano de governo deve preservar a liberdade de expressão.\n\n" * 20).strip()
        esperado = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            encoding_name="cl100k_base", chunk_size=40, chunk_overlap=5,
            separators=["\n\n", "\n", ". ", " ", ""],
        ).split_text(texto)
        r = preparar_segmentacao(texto, estrategia="tokens", max_tokens=40, overlap_tokens=5)
        self.assertEqual(r["chunks"], esperado)
        self.assertEqual(r["config"]["tokens_alvo"], 40)
        self.assertEqual(r["segmentador_versao"], "recursive_tokens_v1")

    def test_validacao_nao_ignora_configuracoes_incompativeis(self):
        for opcoes in ({"tokens_alvo": 0}, {"tokens_alvo": True}, {"estrategia": "outro"},
                       {"overlap_tokens": 1}, {"tokens_alvo": 10, "max_tokens": 10},
                       {"limite_tokens_entrada": 100}, {"overlap_tokens": False}):
            with self.subTest(opcoes=opcoes), self.assertRaises(ValueError):
                preparar_segmentacao("Texto.", **opcoes)

    def test_texto_inteiro_vazio_e_marcador_literal(self):
        texto = "Direitos.\n\nGarantias <|endoftext|>."
        r = preparar_segmentacao(texto, dividir_em_chunks=False)
        self.assertEqual(r["chunks"], [texto])
        self.assertIsNone(r["metadados"]["chunks"])
        self.assertEqual(r["segmentador_versao"], "texto_inteiro")
        self.assertEqual(preparar_segmentacao(" \n ")["chunks"], [])

    def test_notebook_exporta_estrategia_e_previa_congela_diagnostico(self):
        from tcc_lib.notebook_pipeline import carregar_pipeline_notebook
        ns = carregar_pipeline_notebook()
        self.assertIn(ns["CONFIG_CHUNKS"]["estrategia"], ("sentencas", "tokens"))
        ns["CONFIG_CHUNKS"]["estrategia"] = "sentencas"
        ns.update(TEXTO_PLAYGROUND="Defendemos direitos. Rejeitamos a censura.",
                  CONFIG_PLAYGROUND={"nome": "Teste", "limpar_markdown": True,
                                     "dividir_em_chunks": True,
                                     "chunks": {"estrategia": "sentencas", "tokens_alvo": 8}},
                  display=lambda *args: None)
        cell = next(c for c in self.nb["cells"] if c["id"] == "playground-previa")
        exec(compile("".join(cell["source"]), "<previa>", "exec"), ns)
        protocolo = deepcopy(ns["preparacao_playground"])
        ns["CONFIG_PLAYGROUND"]["chunks"]["tokens_alvo"] = 999
        self.assertEqual(ns["preparacao_playground"], protocolo)
        self.assertEqual(protocolo["chunks"]["tokens_alvo"], 8)
        self.assertEqual(protocolo["segmentador_versao"], "punkt_pt_referencias_v2")
        self.assertEqual(len(protocolo["diagnostico_segmentacao"]), len(ns["chunks_playground"]))
        self.assertNotIn("texto", protocolo["diagnostico_segmentacao"][0])
        # Todas as células continuam compiláveis, inclusive await no nível superior.
        for cell in self.nb["cells"]:
            if cell["cell_type"] == "code":
                compile("".join(cell["source"]), cell.get("id", "<cell>"), "exec",
                        flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)

    def test_preparacao_do_documento_e_dos_28_textos_registra_estrategia(self):
        from tcc_lib.notebook_pipeline import carregar_pipeline_notebook
        ns = carregar_pipeline_notebook()
        ns["CONFIG_CHUNKS"]["estrategia"] = "sentencas"
        ns.update(display=lambda *args: None, DOCUMENTO_NOME="Teste",
                  planos_governo=[{"candidato": "Teste", "md": "# Direitos\n\nDefendemos direitos.\nRejeitamos a censura."}])
        cell = next(c for c in self.nb["cells"] if c["id"] == "7151a035")
        exec("".join(cell["source"]), ns)
        self.assertEqual(ns["preparacao_documento"]["chunks"]["tokens_alvo"], 600)
        self.assertEqual(ns["preparacao_documento"]["segmentador_versao"], "punkt_pt_referencias_v2")
        config = {"arquivo": str(ROOT / "pesquisa_exemplos/textos_teste.json"),
                  "grupos": ["textos_pequenos", "textos_grandes"],
                  "limpar_markdown": True, "dividir_em_chunks": True,
                  "chunks": deepcopy(ns["CONFIG_CHUNKS"])}
        preparados = ns["preparar_textos_teste"](config)
        self.assertEqual(len(preparados), 28)
        self.assertTrue(all(p["erro"] is None for p in preparados))
        for item in preparados:
            self.assertEqual(item["preparacao"]["chunks"]["estrategia"], "sentencas")
            self.assertEqual(len(item["preparacao"]["diagnostico_segmentacao"]), len(item["chunks"]))
            limpo, _ = ns["limpar_markdown"](item["original"]["texto"].strip())
            self.assertEqual(" ".join(" ".join(item["chunks"]).split()), " ".join(limpo.split()))
        self.assertTrue(preparados[-1]["chunks"][-1].endswith("Resolução nº 23.732/2024."))
        self.assertGreater(len(preparados[-1]["chunks"]), 10)
        self.assertIn("Tribunal Superior Eleitoral", preparados[-1]["original"]["fonte"]["nome"])

    def test_pdf_com_sentenca_longa_registra_excecao_e_respeita_orcamento(self):
        import pymupdf
        from tcc_lib.notebook_pipeline import carregar_pipeline_notebook
        ns = carregar_pipeline_notebook()
        ns["pymupdf"] = pymupdf
        with tempfile.TemporaryDirectory(prefix=".test-segmentacao-", dir=ROOT) as tmp:
            self.assertTrue(Path(tmp).resolve().is_relative_to(ROOT.resolve()))
            texto = "Defendemos a liberdade de expressao e a participacao social."
            with pymupdf.open() as pdf:
                pagina = pdf.new_page()
                pagina.insert_text((72, 72), texto)
                pdf.save(str(Path(tmp) / "proposta.pdf"))
            config = {"pasta": tmp, "limite_arquivos": None, "excluir": [], "arquivos": None,
                      "padrao": "*.pdf", "limpar_texto": True,
                      "chunks": {"estrategia": "sentencas", "tokens_alvo": 10}}
            item = ns["preparar_propostas"](config)[0]
            self.assertIsNone(item["erro"])
            self.assertEqual(item["chunks"], [texto])
            self.assertTrue(item["preparacao"]["diagnostico_segmentacao"][0]["acima_alvo"])
            config["chunks"]["limite_tokens_entrada"] = 10
            item = ns["preparar_propostas"](config)[0]
            self.assertIn("não foi truncado", item["erro"])
            self.assertEqual(item["chunks"], [])

    def test_fluxograma_exportado_preserva_diagnostico_e_identifica_alvo(self):
        from tcc_lib.notebook_pipeline import carregar_pipeline_notebook
        ns = carregar_pipeline_notebook()
        d = {"relevante": True, "nivel": 0, "valor_0_100": 50.0,
             "metodo": "jev_ordinal", "status": "sem_posicao"}
        eixos = {e: deepcopy(d) for e in ns["AXIS_SPECS"]}
        registro = {"texto": "Defendemos direitos.", "eixos": eixos, "eixos_jev": eixos}
        cobertura = [{"eixo": e, "chunks": 1, "índice A": 50.0, "chunks com nível": 1}
                     for e in eixos]
        preparacao = preparar_segmentacao(registro["texto"], tokens_alvo=1)["metadados"]
        dados = ns["criar_dados_fluxograma"]([registro], cobertura,
                                            contexto={"preparacao": preparacao})
        pagina = ns["renderizar_fluxograma"](dados)
        raw = pagina.split('<script id="data" type="application/json">', 1)[1].split('</script>', 1)[0]
        self.assertEqual(json.loads(raw)["contexto"]["preparacao"], preparacao)
        self.assertIn("Sentenças completas · alvo", pagina)
        self.assertIn("diagnostico_segmentacao", pagina)


if __name__ == "__main__":
    unittest.main()
