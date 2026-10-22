"""Acrescenta somente a seção de cookbooks; preserva as células anteriores."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "TCC.ipynb"
TAG = "tcc-jev-cookbooks-v1"


def cell(kind, source, name):
    result = dict(cell_type=kind, id="cookbooks-" + name,
                  metadata={"tags": [TAG]}, source=source.strip().splitlines(keepends=True))
    if kind == "code":
        result.update(execution_count=None, outputs=[])
    return result


def build():
    nb = json.loads(PATH.read_text(encoding="utf-8"))
    if any(TAG in c.get("metadata", {}).get("tags", []) for c in nb["cells"]):
        raise RuntimeError("Seção já existe; recuso duplicar ou apagar os experimentos")
    cells = []
    def md(name, text):
        cells.append(cell("markdown", text, name))
    def code(name, text):
        cells.append(cell("code", text, name))
    md("intro", """
## Experimentos dos cookbooks JEV aplicados ao TCC

Esta seção pode ser executada **diretamente após reiniciar o kernel**, sem executar
as células anteriores. Ela preserva os experimentos históricos e usa a **rubrica
ordinal de cinco níveis do aplicativo** (`app/api/app/pipeline`), em namespace
separado. Não comparar seus números diretamente com a antiga escala de dois polos.

Os auxiliares estão em `tcc_lib/jev_cookbooks.py`; nenhuma API é chamada ao importar.
O manifesto registra hashes do código/rubricas/dados, modelos e configuração.
As respostas brutas, textos enviados, consumo de tokens, duração e erros são salvos
em `runs/cookbooks/<rodada>/`. Nenhuma chave é salva. Tempos de cache não são latências
de inferência. Não estimamos preço em dinheiro sem uma tabela de preços verificada.

**Escopo:** oito experimentos: citações, estabilidade, busca de evidências,
recuperação de estrutura, resolução por confiança, perguntas em lote,
cascata invertida e descoberta de atributos. O piloto testa funcionamento e
comportamento; não comprova validade científica nem qualidade em planos reais.
Expectativas sintéticas são didáticas. Efeitos das perguntas 8values são
supervisão fraca, não anotações humanas independentes de documentos políticos.
""")
    code("setup", """
import os as _cb_os
import sys as _cb_sys
from pathlib import Path as _CbPath
from IPython.display import display as _cb_display
import pandas as _cb_pd

CB_ROOT = next((p for p in [_CbPath.cwd(), *_CbPath.cwd().parents]
                if (p / "tcc_lib/jev_cookbooks.py").exists()), None)
if CB_ROOT is None:
    raise FileNotFoundError("Abra o notebook dentro da pasta TCC")
if str(CB_ROOT) not in _cb_sys.path:
    _cb_sys.path.insert(0, str(CB_ROOT))
from tcc_lib import jev_cookbooks as cb

# Mude para True para uma nova rodada. O executor CLI usa esta variável de ambiente.
EXECUTAR_COOKBOOKS = _cb_os.getenv("TCC_COOKBOOKS_LIVE", "0") == "1"
CB_CONFIG = dict(live=EXECUTAR_COOKBOOKS, max_calls=180,
                 jev_model="jev-1.13.0", small_model="sabiazinho-4", large_model="sabia-4")
CB_REPETICOES = 3  # piloto; ampliar a amostra e as repetições na avaliação final
CB_CASOS = cb.PILOT
CB_RETOMAR = _cb_os.getenv("TCC_COOKBOOKS_OUTPUT")
cb_lab = cb.Lab(**CB_CONFIG, output=CB_RETOMAR, resume=bool(CB_RETOMAR)) if EXECUTAR_COOKBOOKS else None
cb_resultados = {}

def cb_executar(nome, funcao, *args, **kwargs):
    if cb_lab is None:
        print(f"{nome}: modo leitura. Ative EXECUTAR_COOKBOOKS para executar.")
        return {}
    tabelas = cb_lab.run(nome, funcao, *args, **kwargs)
    cb_resultados.update(tabelas)
    for titulo, tabela in tabelas.items():
        print(titulo, f"({len(tabela)} linhas)")
        _cb_display(tabela.head(12))
    return tabelas

print("APIs habilitadas:", EXECUTAR_COOKBOOKS)
print("Limite:", CB_CONFIG["max_calls"], "chamadas, sem tentativas automáticas")
print("Casos sintéticos:", len(CB_CASOS), "| repetições:", CB_REPETICOES)
if cb_lab:
    print("Rodada:", cb_lab.output)
""")
    md("citacoes-nota", """
### 1. A citação existe e sustenta a classificação?

[Cookbook: Double-checking citations](https://docs.typesafe.ai/cookbooks/citation_check).
Comparar busca literal com verificação semântica: apoio, negação, fala de terceiro
e citação ausente. A busca literal usa a mesma regra do aplicativo. Uma citação
não localizada não é automaticamente uma falsificação: pode haver extração ruim.
O JEV responde **sustenta / contradiz / insuficiente** nos casos localizados.
O limiar 0,8 é ilustrativo, não calibrado. Julgamento por outro modelo não substitui
revisão humana. A coluna de acerto usa apenas as expectativas sintéticas declaradas.
""")
    code("citacoes", 'cb_citacoes = cb_executar("citacoes", cb.citations)')
    md("estabilidade-nota", """
### 2. O mesmo texto recebe a mesma decisão?

[Cookbook: Self-consistency](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook).
Cada um dos seis textos é analisado três vezes, nos quatro eixos, com **entrada
idêntica e cache local desativado**. Não acrescentamos identificadores ao texto;
não controlamos eventual cache interno do provedor. O modelo efetivo deve permanecer
igual. Acordo com a moda mede repetição, não acerto.

Observar amplitude/desvio do escore, mudanças de rótulo e taxa de encaminhamento
**prevista** pela política JEV → LLM (esta etapa não chama o LLM). A tabela de
limiares inclui cobertura e quantidade de grupos com pelo menos duas decisões
aceitas; excluir casos difíceis pode aumentar artificialmente o acordo.
As pontuações aqui são por trecho, não resultados agregados de um plano.
Bootstrap de trechos e repetição de inferências medem incertezas diferentes.
""")
    code("estabilidade", 'cb_estabilidade = cb_executar("estabilidade", cb.stability, CB_CASOS, CB_REPETICOES)')
    md("busca-nota", """
### 3. Encontrar evidências sem gerar uma citação

[Cookbook: Line-by-line search](https://docs.typesafe.ai/cookbooks/semantic_find).
As frases recebem IDs; `Choice` escolhe uma frase e `Noul` verifica se existe uma
resposta substantiva. O código recupera a frase original. Há uma consulta respondida
e uma sem resposta, para detectar o falso positivo de sempre escolher o primeiro
do ranking. Limiares 0,35/0,7 são provisórios. Esta busca serve para explicar decisões,
não para selecionar apenas frases extremas e recalcular o índice do documento.
""")
    code("busca", 'cb_busca = cb_executar("busca", cb.search)')
    md("estrutura-nota", """
### 4. Recuperar estrutura antes de segmentar

[Cookbook: Structure recovery](https://docs.typesafe.ai/cookbooks/autoformat).
Simulamos quebras de linha de uma extração de PDF. `Noul` decide quais linhas
continuam a mesma frase e `Choice` identifica o tipo dos blocos recuperados.
O código apenas junta linhas: verifica que nenhuma palavra foi acrescentada ou
removida. Comparamos também a classificação do texto antes/depois.

Este é um teste controlado de recuperação de formatação. Não mede ainda a qualidade
do OCR nem o efeito de segmentar um plano inteiro. Não excluir tabelas ou títulos
reais sem inspecionar o conteúdo; podem conter propostas substantivas.
""")
    code("estrutura", 'cb_estrutura = cb_executar("estrutura", cb.structure)')
    md("confianca-nota", """
### 5. Informar direção quando a intensidade é incerta

[Cookbook: Classification using confidence](https://docs.typesafe.ai/cookbooks/classification_using_confidence).
Reaproveitamos as respostas do experimento 2, sem novas chamadas. Comparamos
limiares de confiança para o nível completo. Quando não há confiança suficiente
na intensidade, somamos as probabilidades dos dois níveis de A e dos dois de B:
com massa ≥ 0,8 em um polo, apresentamos apenas a direção. Nos demais casos, incerteza.

**Direção sem intensidade não vira um escore arbitrário 0/100.** Ausência de
relevância, posição não direcional e incerteza permanecem situações distintas.
`confidence` não é taxa empírica de acerto. Estes limiares devem ser calibrados
num conjunto de desenvolvimento anotado e depois avaliados em teste separado.
""")
    code("confianca", """
if "estabilidade_bruta" in cb_resultados:
    cb_confianca = cb_executar("confianca", cb.confidence, cb_resultados["estabilidade_bruta"])
else:
    print("Confiança: depende da conclusão do experimento de estabilidade.")
""")
    md("lote-nota", """
### 6. Oito perguntas juntas versus oito requisições

[Cookbook: Parallel questions](https://docs.typesafe.ai/cookbooks/parallel_questions).
Três comparações pareadas, alternando qual estratégia roda primeiro. Todas as
chamadas são novas, sequenciais e sem cache local. Medimos duração, tokens de entrada,
diferenças de rótulo e maior diferença entre probabilidades. A comparação inclui
as oito perguntas do mesmo texto. Não atribuir toda diferença à estratégia:
também há variação entre inferências e condições de rede.
""")
    code("lote", 'cb_lote = cb_executar("lote", cb.batching, CB_REPETICOES)')
    md("cascata-nota", """
### 7. LLM menor → verificador JEV → LLM maior

[Cookbook: SDE cascade](https://docs.typesafe.ai/cookbooks/sde_cascade).
Adaptamos a verificação de extração para classificação política. O menor fornece
nível e citação; o JEV estima se existe erro. Testamos limiares 0,3/0,5/0,7 e
encaminhamos também respostas sem evidência literal válida. O maior é executado
em todos os casos do piloto para comparar inclusive os casos não encaminhados.
Isso custa mais no experimento que numa futura execução da cascata.

Também registramos JEV primeiro → maior quando necessário, com a política atual
de confiança. Ambos usam as mesmas rubricas. O modelo maior é comparador, não
gabarito; o acerto disponível é apenas de direção em exemplos sintéticos.
Chamadas lógicas da cascata são contrafactuais; o diário registra o gasto real.
""")
    code("cascata", 'cb_cascata = cb_executar("cascata", cb.cascade, CB_CASOS[:3])')
    md("atributos-nota", """
### 8. Descobrir perguntas que ajudam um classificador supervisionado

[Cookbook: Autoresearch feature discovery](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery).
Piloto no eixo econômico: perguntas 8values com efeito econômico diferente de zero,
usando o **sinal** desse efeito como referência fraca. Não usar a magnitude como
gabarito de intensidade nem efeito zero como prova de ausência do tema.

Divisão estratificada aproximada 60/20/20, por pergunta: treino, desenvolvimento,
teste. Duas rodadas: LLM propõe perguntas binárias; JEV gera atributos; regressão
logística aprende a direção. O feedback para a segunda proposta usa erros fora
da dobra **somente do treino**. Desenvolvimento escolhe a rodada; teste é aberto
uma vez, após a seleção. Comparadores: classe majoritária e TF-IDF + regressão.

Adaptação deliberada: usamos regressão logística já instalada, em vez de CatBoost,
para limitar dependências e complexidade nesta amostra pequena. Isso testa o
princípio do cookbook, não reproduz seus números. Rubricas foram desenvolvidas
com conhecimento do 8values: mesmo uma partição correta não torna este teste
uma validação independente em propostas reais. Para o TCC, repetir com anotações
humanas e separação por documento/autor. Não ajustar o método olhando o teste.
""")
    code("atributos", 'cb_atributos = cb_executar("atributos", cb.features)')
    md("balanco-nota", """
### Registro da rodada e critérios para decidir o que incorporar

- Evidências: medir sustentação semântica contra revisão humana, incluindo negações.
- Estabilidade: reportar oscilação junto com acerto, cobertura e encaminhamento.
- Busca: verificar também consultas sem resposta; não confundir ranking com existência.
- Estrutura: conferir preservação textual e limites de trechos em documentos reais.
- Confiança: escolher limiares em desenvolvimento, sem transformar incerteza em neutralidade.
- Lote: comparar tokens e latência de chamadas novas; não extrapolar preços do cookbook.
- Cascata: avaliar erros que passaram pelo verificador, além dos casos encaminhados.
- Atributos: comparar com baselines e guardar teste independente, sem vazamento entre documentos.

Saídas salvas abaixo pertencem à rodada identificada. Reexecutar apenas a exibição
não faz chamadas. Para uma nova rodada completa, habilite APIs na configuração;
estabilidade e lote sempre fazem inferências novas. Os demais testes podem usar cache,
identificado no diário. Falhas não são convertidas em resultados simulados.
""")
    code("balanco", """
if cb_lab:
    cb_status = _cb_pd.DataFrame(cb_lab.status)
    _cb_display(cb_status)
    print("Tentativas de chamadas remotas:", cb_lab.calls)
    print("Arquivos:", cb_lab.output)
    cb_lab.close()
else:
    print("Modo leitura: consulte as saídas salvas ou abra runs/cookbooks/<rodada>/status.json.")
""")
    nb["cells"].extend(cells)
    PATH.write_text(json.dumps(nb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Adicionadas {len(cells)} células. As {len(nb['cells']) - len(cells)} anteriores foram preservadas.")


if __name__ == "__main__":
    build()
