"""Notebook BRmoral: narrativa e reprodução R3/R4/R6–R9 de METODOLOGIA.md.

Adaptação de engenharia: células executadas sequencialmente com saída stdout,
sem dependências Jupyter para gerar o arquivo e sem reexecutar modelos por padrão.
"""
import contextlib
import hashlib
import io
import json
from pathlib import Path


def create(root):
    """R4 (Kapoor/Narayanan, 2023): executa células e preserva origem/estado."""
    cells = []

    def md(text):
        """R4: associa método, fonte e interpretação ao próximo bloco."""
        cells.append(dict(cell_type='markdown', metadata={}, source=text.splitlines(True)))

    def code(text):
        """R4: registra uma unidade executável e seus resultados reais."""
        cells.append(dict(cell_type='code', metadata={}, source=text.splitlines(True), outputs=[], execution_count=None))

    md('''# BRmoral — avaliação de posição perante temas

Notebook complementar ao **TCC.ipynb**, seguindo sua sequência de instalação,
tipos/variáveis, métodos, testes e comparação. Resultados da rodada de 17/09/2026.

**Pergunta:** os embeddings E5 permitem classificar posição melhor quando recebem
uma cabeça supervisionada? A comparação entre encoder congelado e contrastivo
continua incompleta; somente os baselines foram executados.

## O que é o BRmoral?

É um corpus de opiniões em português brasileiro produzidas por participantes que
também declararam sua posição perante cada tema. A versão obtida tem **510 autores
e oito textos por autor**, totalizando 4.080 opiniões potenciais. Os temas são:
casamento entre pessoas do mesmo sexo, porte de armas, aborto, pena de morte,
legalização das drogas, redução da maioridade penal, cotas raciais e isenção de
impostos para igrejas. Também há dados de perfil e fundamentos morais no original;
eles não são usados como entradas ou rótulos neste experimento.

Cada exemplo é **(texto, tema, posição)**. O mesmo assunto pode aparecer em textos
favoráveis ou contrários: similaridade temática não basta para reconhecer posição.
Aqui não convertemos a ideologia autodeclarada de uma pessoa em rótulo de seus textos.

Fonte acadêmica: Silva e Paraboni (2023), *Politically-oriented information inference
from text*, §§3 e 4.1.2, pp.575–578, arquivo
`artigos/Politically-oriented information inference from text.pdf`.
Descrição dos campos e licença: [README original extraído](analises/brmoral_dataset_readme.txt).
Distribuição v5.10, setembro de 2019, **CC BY 4.0**; não confundir a versão do
arquivo com o ano de publicação dos artigos que o utilizam.

## Instalação e Imports

Para ler e recalcular tabelas: Python e NumPy do ambiente do projeto. Para repetir
modelos, use `.venv-gpu` com `investigacao/requirements-gpu.txt`.
Não há instalação automática nem download ao executar todas as células.

Rastreabilidade **R4**: Kapoor e Narayanan (2023), *Leakage and the reproducibility
crisis in machine-learning-based science*, DOI 10.1016/j.patter.2023.100804.
Adaptação: caminhos explícitos, manifestos e hashes; não reproduzimos um experimento
desse artigo. Execute este notebook a partir da raiz do projeto.
''')
    code('''import json
import hashlib
import subprocess
import sys
from pathlib import Path
from collections import Counter
from typing import TypedDict
from investigacao.protocolo import validate_corpus, classification_metrics, digest

ROOT = Path.cwd()
assert (ROOT / 'TCC.ipynb').is_file(), 'Abra o notebook na raiz do projeto.'
print('Python atual:', sys.version.split()[0])
print('Raiz:', ROOT)
''')
    md('''## Tipos e Variáveis
### Tipos

**R3/R9:** Silva e Paraboni (2023), §§3–4.1.2, e README v5.10. O esquema
abaixo distingue posição por texto/tema, autoria e partição. Tipagem é uma
adaptação de engenharia; a auditoria posterior verifica os valores reais.
''')
    code('''class Exemplo(TypedDict):
    """R3/R9: posição por tema; autoria é usada apenas no agrupamento."""
    id: str
    text: str
    target: str
    label: str
    author_id: str
    family_id: str
    split: str
    label_source: str

print('Campos:', ', '.join(Exemplo.__annotations__))
''')
    md('''### Variáveis
#### Modelos e execuções

**R4/R6/R7:** configurações congeladas da execução, descritas em
[METODOLOGIA.md](investigacao/METODOLOGIA.md). E5 gera embeddings; regressão
logística aprende a fronteira; NLI compara o texto com uma hipótese de apoio.
As tabelas leem artefatos reais, sem executar novamente o treinamento.
''')
    code('''DATA = ROOT / 'analises/dados/brmoral_20260917'
RUN = ROOT / 'analises/execucoes/brmoral_baselines_gpu_20260917'
DOC = ROOT / 'analises/execucoes/documento_6x1_brmoral_gpu_20260917'

def load(path):
    """R4: leitura explícita de artefato UTF-8 persistido."""
    return json.loads(path.read_text(encoding='utf-8'))

rows: list[Exemplo] = [json.loads(s) for s in (DATA / 'corpus.jsonl').read_text(encoding='utf-8').splitlines() if s.strip()]
meta = load(DATA / 'corpus.meta.json')
metrics = load(RUN / 'metricas.json')
predictions = load(RUN / 'previsoes.json')
selection = load(RUN / 'frozen_selection.json')
manifest = load(RUN / 'manifest.json')
print('Corpus:', meta['name'], meta['version'], meta['license'])
print('GPU da rodada:', manifest['gpu']['name'])
print('Seleção completa:', selection['comparison_complete'])
''')
    md('''### Métodos Gerais

**R4:** tabelas calculadas diretamente dos artefatos, com arredondamento somente
na apresentação. A função abaixo formata saídas legíveis sem bibliotecas extras.
''')
    code('''def table(headers, values):
    """R4: formatação; não altera dados ou métricas."""
    values = [[str(v) for v in row] for row in values]
    widths = [max(len(str(h)), *(len(r[i]) for r in values)) for i, h in enumerate(headers)]
    print(' | '.join(str(h).ljust(w) for h, w in zip(headers, widths)))
    print('-+-'.join('-' * w for w in widths))
    for row in values:
        print(' | '.join(v.ljust(w) for v, w in zip(row, widths)))

print('Métodos auxiliares disponíveis.')
''')
    md('''## Testes
### A0 — Dados, exclusões e partições

**R9:** Santos e Paraboni (2019), *Moral Stance Recognition and Polarity
Classification from Twitter and Elicited Text*, §3.1, p.1071,
DOI 10.26615/978-954-452-056-4_123; README v5.10.
Escores 0/1 → contra; 2/3 → neutro; 4/5 → favor. A tarefa atual é binária:
neutros e registros sem texto/escore são excluídos, nunca convertidos em contra.

**Adaptação R4:** 64/16/20% dos componentes autor/duplicata, seed 42.
Não é uma divisão oficial do corpus. Autores e duplicatas não cruzam partições;
os oito temas permanecem conhecidos. Isso testa novos autores, não novos temas.
''')
    code('''audit = validate_corpus(rows, meta)
assert audit['sha256'] == load(DATA / 'audit.json')['sha256']
archive = ROOT / 'analises/brmoral_original.download'
assert hashlib.sha256(archive.read_bytes()).hexdigest() == meta['archive_sha256']
for path_string, expected in manifest['input_hashes'].items():
    path = ROOT / Path(path_string.replace('\\\\', '/'))
    assert digest(path.read_text(encoding='utf-8')) == expected
print('Auditoria e hashes: OK')
print('Exclusões:', meta['exclusions'])
table(['Partição', 'Exemplos', 'Autores', 'Componentes', 'Contra', 'Favor'], [
    [s, sum(r['split'] == s for r in rows),
     len({r['author_id'] for r in rows if r['split'] == s}),
     len({r['family_id'] for r in rows if r['split'] == s}),
     sum(r['split'] == s and r['label'] == 'against' for r in rows),
     sum(r['split'] == s and r['label'] == 'favor' for r in rows)]
    for s in ['train', 'dev', 'test']])
''')
    md('''### A1 — Exemplo de entrada

**R3/R9:** inspecionamos somente um exemplo de treino para explicar o contrato.
`gun-control` é o nome histórico da coluna, mas seu alvo corresponde ao porte de
armas; a tradução literal não deve inverter as classes. Não mostramos perfil
demográfico e não o fornecemos ao modelo.
''')
    code('''example = next(r for r in rows if r['split'] == 'train')
print('Tema:', example['target'])
print('Posição:', example['label'])
print('Texto:', example['text'])
''')
    md('''### B0 — E5 sem ajuste

**R6:** Tunstall et al. (2022), *Efficient Few-Shot Learning Without Prompts*,
§3.1, https://arxiv.org/abs/2209.11055, contextualiza classificadores sobre
embeddings. Nosso baseline de templates é uma adaptação própria, não uma
reprodução do SetFit: codifica `Alvo: ... Texto: ...` e compara com frases fixas
de apoio/oposição, usando margem de cossenos e limiar zero. Prefixo `query:`,
embeddings normalizados, máximo 512 tokens. Ver `modelos.zero_shot`.

Macro-F1 é a média do F1 das duas classes; acurácia balanceada é a média de seus
recalls; MCC mede associação entre previsões e rótulos. **R3/R4** fundamentam a
avaliação separada e suas limitações. Macro-F1 global não é média entre temas.
''')
    code('''global_metrics = [r for r in metrics if 'target' not in r]
baseline = next(r for r in global_metrics if r['method'] == 'sem_ajuste')
print(json.dumps(baseline, ensure_ascii=False, indent=2))
''')
    md('''### B1 — E5 congelado + regressão logística

**R6**, §3.1: separação entre representação e cabeça classificadora. Adaptação:
E5 permanece congelado; cabeça logística L2, pesos balanceados, grade
C={0,01; 0,1; 1; 10}. Treino ajusta coeficientes; dev escolhe C por macro-F1.
Embeddings são calculados em CUDA; a cabeça é treinada na CPU.
As seeds 13/42/77 não alteram as partições e podem produzir resultados idênticos.
''')
    code('''table(['Seed', 'C escolhido', 'Macro-F1 dev', 'Macro-F1 teste'], [
    [seed, load(RUN / f'congelado_{seed}/selection.json')['C'],
     f"{load(RUN / f'congelado_{seed}/selection.json')['dev']['macro_f1']:.4f}",
     f"{next(r for r in global_metrics if r['method'] == 'congelado' and r['seed'] == seed)['macro_f1']:.4f}"]
    for seed in [13, 42, 77]])
print('Escolha por dev:', selection['chosen_method'])
''')
    md('''### C1 — NLI relacional

**R7:** Yin, Hay e Roth (2019), *Benchmarking Zero-shot Text Classification:
Datasets, Evaluation and Entailment Approach*, §3, https://aclanthology.org/D19-1404/.
Adaptação: texto como premissa, “O autor é favorável a {alvo}.” como hipótese.
Comparamos entailment e contradiction para uma previsão binária. A probabilidade
neutral não significa neutralidade política. NLI é comparador, não participa
da escolha entre B0 e B1 no desenvolvimento.
''')
    code('''nli = next(r for r in global_metrics if r['method'] == 'nli_relacional')
print(json.dumps(nli, ensure_ascii=False, indent=2))
''')
    md('''### Comparação — resultados externos

**R3/R4:** mesmo teste e rótulos para todos os métodos. A célula recalcula as
matrizes a partir das previsões para verificar consistência com o relatório.
Não escolhe parâmetros pelo teste. Consulte `METODOLOGIA.md` para referências
completas e diferenças em relação aos trabalhos originais.
''')
    code('''for metric in metrics:
    subset = [r for r in predictions if r['method'] == metric['method']
              and r.get('seed', -1) == metric.get('seed', -1)
              and ('target' not in metric or r['target'] == metric['target'])]
    observed = classification_metrics([r['truth'] for r in subset], [r['prediction'] for r in subset])
    assert observed['confusion'] == metric['confusion']
summary = [r for r in global_metrics if r.get('seed', 13) == 13]
table(['Método', 'N', 'Macro-F1', 'BA', 'MCC'], [
    [r['method'], r['n'], *[f"{r[k]:.4f}" for k in ['macro_f1', 'balanced_accuracy', 'mcc']]] for r in summary])
print('Matrizes conferidas:', len(metrics))
''')
    md('''### B2 — Incerteza do ganho

**R8:** Dror et al. (2018), *The Hitchhiker’s Guide to Testing Statistical
Significance in Natural Language Processing*, https://aclanthology.org/P18-1128/.
Adaptação com **R4**: bootstrap pareado por componentes de autor/duplicata do
teste, 1.000 repetições; intervalo percentil de 95% da diferença de macro-F1.
É condicional ao split e treinamento observados, sem estimar variação entre treinos.
''')
    code('''interval = load(RUN / 'intervalo_baselines.json')
print(json.dumps(interval, ensure_ascii=False, indent=2))
''')
    md('''### B3 — Error Analysis / resultados por tema

**R3/R4:** decompor resultados evita atribuir o desempenho agregado a todos os
temas. A matriz usa linhas verdadeiras e colunas previstas, ordem contra/favor.
Esta análise posterior ao teste serve para diagnóstico, não para retunar a rodada.
''')
    code('''by_topic = [r for r in metrics if 'target' in r and r['method'] == 'congelado' and r.get('seed') == 13]
table(['Tema', 'N', 'Macro-F1', 'Acertos favor / total favor'], [
    [r['target'], r['n'], f"{r['macro_f1']:.4f}",
     f"{r['confusion'][1][1]} / {sum(r['confusion'][1])}"] for r in by_topic])
''')
    md('''**Interpretação:** a cabeça supervisionada melhora muito o resultado global,
mas falha na classe favorável à isenção de impostos para igrejas (0/13 acertos).
Casamento tem somente quatro exemplos contra no teste; estimativas por classe
ficam frágeis. O agregado 0,844 não representa qualidade uniforme por tema.

### D0 — Aplicação ao documento 6×1

**R3/R7:** transferência de domínio, não avaliação com gabarito. A recuperação
usa trechos e perguntas; a cabeça recebe a pergunta como alvo, diferentemente dos
alvos nominais do corpus. Limiar exploratório 0,7, sem calibração documental.
Probabilidade não é intensidade; `response` continua ausente.
''')
    code('''transfer = load(DOC / 'transferencia_externa.json')
assert len(transfer['items']) == 70
assert all(r['response'] is None for r in transfer['items'])
assert transfer['selection']['comparison_complete'] is False
counts = Counter(r['state'] for r in transfer['items'])
table(['Estado', 'Perguntas'], sorted(counts.items()))
print('Transferência exploratória:', transfer['transfer_exploratory'])
''')
    md('''**Interpretação:** 64 favoráveis, 2 contrárias e 4 incertas não comprovam acerto.
A concentração de favoráveis pode refletir comportamento fora do domínio;
não temos gabarito para resolver essa dúvida. Não produzimos escore político validado.

### Custo e limite de hardware

**R4:** manifesto mede esta execução, não um benchmark isolado de GPU. A estimativa
de treinamento float32/AdamW inclui pesos, gradientes e dois estados; exclui
ativações e temporários. É uma verificação de engenharia, não resultado científico.
''')
    code('''memory = load(ROOT / 'analises/brmoral_training_memory.json')
print('Tempo externo (s):', round(manifest['elapsed_seconds'], 2))
print('Pico CUDA alocado (GiB):', round(manifest['gpu']['peak_allocated_bytes'] / 2**30, 3))
print('Estimativa mínima treinamento (GB decimais):', round(memory['float32_weights_grad_adam_two_moments_bytes'] / 1e9, 2))
print('Pendente:', manifest['config']['pending'])
''')
    md('''### Reprodução opcional na GPU

**R4/R6/R7/R9:** orquestração dos métodos já descritos. Por padrão, apenas mostra
o comando; altere `REEXECUTAR_GPU` para repetir os baselines em uma nova pasta.
O comando exige CUDA e não faz fallback silencioso. Não executa ajuste contrastivo.
''')
    code('''REEXECUTAR_GPU = False
PYTHON_GPU = ROOT / '.venv-gpu/Scripts/python.exe'
NEW_RUN = ROOT / 'analises/execucoes/brmoral_notebook_nova_rodada'
command = [str(PYTHON_GPU), '-m', 'investigacao', 'external',
           '--corpus', str(DATA / 'corpus.jsonl'), '--metadata', str(DATA / 'corpus.meta.json'),
           '--output', str(NEW_RUN), '--device', 'cuda', '--batch-size', '1',
           '--low-vram', '--baselines-only']
print(subprocess.list2cmdline(command))
if REEXECUTAR_GPU:
    assert PYTHON_GPU.is_file(), 'Ambiente GPU não encontrado.'
    assert not NEW_RUN.exists(), 'Escolha uma pasta nova para preservar as execuções.'
    subprocess.run(command, cwd=ROOT, check=True)
else:
    print('Modo leitura: nenhum modelo foi reexecutado nesta sessão.')
''')
    md('''### D1 — Diagnóstico de transferência ao 8values

**R5/R7:** CheckList (Ribeiro et al., 2020, §2) e NLI (Yin et al., 2019, §3).
280 textos construídos: apoio/oposição em duas formas para cada uma das 70
perguntas. O texto da proposição é preservado; `effect` não fornece os rótulos.
Modelos e limiares congelados antes da execução em GPU. As expectativas são
por construção, não anotações humanas ou estimativas de acurácia documental.

Macro-F1 abaixo força uma escolha binária. Cobertura e acerto condicional usam
o limiar 0,7 da cabeça; NLI também exige margem 0,2. Ordenação verifica apenas
se o apoio recebe escore maior; ambos corretos exige decisões absolutas certas.
''')
    code('''TRANSFER_RUN = ROOT / 'analises/execucoes/transferencia_8values_gpu_20260917'
if (TRANSFER_RUN / 'metrics.json').exists():
    transfer_metrics = load(TRANSFER_RUN / 'metrics.json')
    table(['Método', 'Macro-F1', 'Cobertura', 'Acerto aceitos', 'Ordenação', 'Ambos corretos'], [
        [r['method'], *[f"{r[k]:.4f}" if r[k] is not None else 'n/a' for k in
         ['macro_f1', 'direction_coverage', 'accuracy_when_accepted', 'pair_ordering', 'both_sides_correct']]]
        for r in transfer_metrics if r['template'] == 'all'])
else:
    print('Diagnóstico ainda não disponível nesta cópia do projeto.')
''')
    md('''**Conclusão do diagnóstico:** cabeça BRmoral: macro-F1 0,779 e ordenação
100%, porém ambos os lados corretos em apenas 55,7% dos pares. Com confiança
0,7, decide em 51,8% dos casos e acerta 88,3% dessas decisões; ainda há 17
erros entre 145 decisões aceitas. Não calibramos limiares nesses resultados.
NLI com hipótese literal da pergunta classificou todos os 280 casos como apoio,
falhando nas 140 rejeições. Isso demonstra uma falha nestes templates citacionais,
não que NLI falhe em todo texto natural. Não há liberação de pontuação 8values.
Ver [relatório da transferência](analises/transferencia_8values_20260917.md).

## Conclusões

1. O BRmoral permitiu avaliação externa real, com posição por texto/tema e
   separação de autores/duplicatas; 3.211 exemplos binários após exclusões.
2. E5 congelado + regressão logística alcançou macro-F1 **0,844**, contra **0,499**
   sem ajuste e **0,658** do NLI. Melhorar a fronteira de decisão ajudou neste corpus.
3. O ganho não é uniforme entre temas e não valida automaticamente documentos
   longos, perguntas 8values ou pontuações de intensidade.
4. A transferência para o documento 6×1 permanece exploratória e sem gabarito.
5. Ainda falta testar ajuste contrastivo do mesmo encoder; float32/AdamW completo
   excede os 3 GB da GPU. Não é possível concluir se adaptar a representação ajuda.

## Referências e rastreabilidade

- Silva e Paraboni (2023), *Politically-oriented information inference from text*,
  §§3–4.1.2, [artigo local](artigos/Politically-oriented%20information%20inference%20from%20text.pdf).
- Santos e Paraboni (2019), *Moral Stance Recognition and Polarity Classification
  from Twitter and Elicited Text*, §3.1, DOI 10.26615/978-954-452-056-4_123.
- Pavan et al., *Morality Classification in Natural Language Text*,
  DOI 10.1109/TAFFC.2020.3034050: referência solicitada pela distribuição original.
  O README cita 2020; Silva e Paraboni citam a publicação em 2023.
- Kapoor e Narayanan (2023), Tunstall et al. (2022), Yin et al. (2019) e
  Dror et al. (2018): identificados junto das etapas correspondentes.
- [Métodos, referências completas e adaptações](investigacao/METODOLOGIA.md).
- [Relatório da rodada](analises/resultados_brmoral_gpu_20260917.md).

**Validação:** a rodada de implementação passou em 16 testes. Este notebook
adiciona auditoria dos dados, hashes, recálculo das matrizes e verificações dos
70 resultados documentais. Suas células foram executadas em sequência na geração;
os modelos são resultados persistidos da execução GPU, não novo treinamento.
''')
    md('''## D2 — Ablação de formato e hipótese NLI

**R5/R7:** CheckList (Ribeiro et al., 2020, §2) e Yin et al. (2019, §3).
Fatorial aspas × posição da concordância/discordância: 560 casos em 70 famílias.
A proposição permanece literal mesmo sem aspas; não são paráfrases ou documentos
naturais. A segunda hipótese NLI trata da concordância do autor, não da verdade
da proposição. Comparação exploratória pré-definida; sem treino ou calibração.

Usamos a rodada v2, que preserva a regência “discordo da/dessa” do diagnóstico
anterior. A primeira rodada está preservada, mas não é a comparação principal.
''')
    code('''FORMAT_RUN = ROOT / 'analises/execucoes/ablacao_formato_8values_gpu_20260917_v2'
if (FORMAT_RUN / 'metrics.json').exists():
    format_metrics = load(FORMAT_RUN / 'metrics.json')
    table(['Método', 'Formato', 'Macro-F1', 'Cobertura'], [
        [r['method'], r['template'], f"{r['macro_f1']:.4f}", f"{r['direction_coverage']:.4f}"]
        for r in format_metrics])
else:
    print('Rodada de formato ainda não disponível nesta cópia.')
''')
    md('''**Limite:** melhoria em templates explícitos não demonstra validade
documental. Não promovemos a nova hipótese a configuração final nem calculamos
pontuações 8values. Consulte o [relatório](analises/ablacao_formato_8values_20260917.md)
para resultados e próximos testes em linguagem natural.
''')
    md('''## D3 — Textos naturais com temas reservados

**R3/R4/R6/R7/R8:** unidade texto-alvo, controle de vazamento, cabeça congelada,
hipóteses NLI e comparação pareada; referências em METODOLOGIA.md.
Em cada uma de oito rodadas, retiramos um tema de treino e dev. O teste contém
esse tema e autores que não participaram do ajuste. C usa apenas dev dos demais
temas. O agregado da cabeça reúne oito modelos, não um único classificador.
NLI compara proposição normativa versus concordância do autor, sem treinamento.

O teste já foi consultado anteriormente: avaliação exploratória, não novo teste
cego. Os rótulos são naturais do corpus (neutros excluídos), não templates.
''')
    code('''TOPIC_RUN = ROOT / 'analises/execucoes/temas_reservados_gpu_20260917'
if (TOPIC_RUN / 'metrics.json').exists():
    topic_metrics = load(TOPIC_RUN / 'metrics.json')
    table(['Método', 'Macro-F1', 'BA', 'Cobertura', 'Acerto aceitos'], [
        [r['method'], *[f"{r[k]:.4f}" if r[k] is not None else 'n/a' for k in
         ['macro_f1', 'balanced_accuracy', 'coverage', 'accepted_accuracy']]]
        for r in topic_metrics if r['target'] is None])
    table(['Tema', 'Método', 'N', 'Macro-F1'], [
        [r['target'], r['method'], r['n'], f"{r['macro_f1']:.4f}"]
        for r in topic_metrics if r['target'] is not None and r['method'] != 'maioria_treino'])
    print('Diferença entre hipóteses NLI:', load(TOPIC_RUN / 'interval_nli.json'))
else:
    print('Rodada de temas reservados ainda não disponível.')
''')
    md('''**Resultado:** E5 com tema reservado obteve macro-F1 0,523; NLI literal
0,690 e NLI sobre concordância do autor 0,704. A diferença entre hipóteses NLI
foi +0,013, com IC95% [-0,022; 0,050]: não há vantagem clara nesta rodada.
A hipótese sobre o autor piorou em cinco dos oito temas. O sucesso nos templates
não se repetiu com a mesma magnitude nos textos naturais.

A avaliação permite confrontar o ganho em templates com textos naturais,
mas não valida escala de intensidade 8values. Hipóteses e limiares não são
escolhidos pelos resultados desta rodada. Consulte o
[relatório](analises/temas_reservados_20260917.md).
''')
    md('''## D4 — Seleção de decisão e abstenção no desenvolvimento

**R4/R7:** isolamento dos dados e hipóteses NLI; referências completas em
METODOLOGIA.md. Ajustamos limiares, não probabilidades. Excluímos do dev o tema
avaliado e escolhemos a maior cobertura com acerto empírico ≥80%, cobertura ≥25%
e dez aceitos por classe. Sem opção elegível, abstenção total. Requisitos locais
pré-especificados, sem garantia para outro tema. Seleções congeladas antes de
carregar previsões de teste; teste já consultado, avaliação exploratória.
''')
    code('''SELECTIVE_RUN = ROOT / 'analises/execucoes/calibracao_seletiva_gpu_20260917'
if (SELECTIVE_RUN / 'metrics.json').exists():
    selective_results = load(SELECTIVE_RUN / 'metrics.json')
    table(['Política', 'Aceitos', 'Acertos', 'Erros', 'Cobertura', 'Acerto aceitos'], [
        [r['policy'], r['accepted'], r['correct'], r['errors'],
         f"{r['coverage']:.4f}", f"{r['accepted_accuracy']:.4f}" if r['accepted_accuracy'] is not None else 'n/a']
        for r in selective_results if r['target'] is None])
else:
    print('Seleção de limiares ainda não disponível nesta cópia.')
''')
    md('''**Conclusão:** a seleção aceitou 274/641 casos e acertou 192 (70,1% dos
aceitos), abaixo do NLI literal fixo, que aceitou 382 e acertou 290 (75,9%).
Menos erros absolutos vieram acompanhados de menor cobertura e menor acerto
condicional. Para pena de morte, nenhum candidato cumpriu a meta no dev e houve
abstenção total. Não promovemos essa política ao pipeline documental.
Ver [relatório](analises/calibracao_seletiva_20260917.md). Suite: 21 testes aprovados.
''')
    md('''## D5 — Busca de alternativas somente no treino/desenvolvimento

**R4/R7/R10:** prevenção de vazamento, hipóteses de classe e classificadores
universais. Laurer et al. (2024), *Building Efficient Universal Classifiers with
Natural Language Inference*, §2, https://arxiv.org/abs/2312.17543.
Baseline lexical: Santos e Paraboni (2019), §§3.3.1–3.3.3,
https://aclanthology.org/R19-1123/. Adaptações descritas em METODOLOGIA.md.

Comparações: hipóteses bilaterais no mDeBERTa; n-gramas TF-IDF em temas reservados;
BGE multilíngue FP16 com duas classes NLI (not-entailment não é contradição);
média fixa entre modelos; fronteira BGE ajustada no treino excluindo tema do dev.
Meta provisória: BA média entre temas ≥0,75 e pior tema ≥0,60. Critério local,
não padrão da literatura. Triagem no desenvolvimento não é validação externa.
''')
    code('''search_runs = {
    'NLI bilateral': 'nli_bilateral_dev_gpu_20260917',
    'Lexical': 'lexical_dev_20260917',
    'BGE': 'bge_dev_gpu_20260917',
    'Média de modelos': 'ensemble_dev_20260917',
    'BGE limiar treino': 'bge_train_calibration_20260917',
    'Cabeça BGE conjunta': 'crossencoder_head_dev_20260917',
}
search_summary = []
for label, run_name in search_runs.items():
    path = ROOT / 'analises/execucoes' / run_name / 'metrics.json'
    if not path.exists():
        continue
    result = load(path)
    best = result[0] if isinstance(result, list) else result
    search_summary.append([label, best.get('candidate', 'fixo'),
                           f"{best['mean_topic_ba']:.4f}", f"{best['min_topic_ba']:.4f}",
                           best['satisfies_provisional_criterion']])
table(['Alternativa', 'Candidato', 'BA média temas', 'Pior tema BA', 'Meta dev'], search_summary)
''')
    md('''Os candidatos foram examinados no desenvolvimento; comparar o melhor
resultado desse processo ao teste exigirá congelar método, hipóteses e regra
antes da execução. O teste histórico já foi consultado e continua exploratório.
Modelos maiores não foram confundidos com ajuste contrastivo do E5.
''')
    md('''## D6 — Resultado em temas reservados e transferência exploratória

**R4/R6/R8/R10:** separação de dados, cabeça sobre representação congelada,
bootstrap por autor e pares texto–hipótese; referências em METODOLOGIA.md.
Adaptação: BGE congelado em FP16/CUDA e regressão logística sobre 1.024 features.
Em cada rodada, o tema avaliado fica fora do treino e da seleção de C no dev.
O teste histórico já foi examinado: resultado exploratório, não novo teste cego.
''')
    code('''HEAD_RUN = ROOT / 'analises/execucoes/crossencoder_head_test_20260917'
head_metrics = load(HEAD_RUN / 'metrics.json')
print('Macro-F1 global:', round(head_metrics['global']['macro_f1'], 4))
print('BA média entre temas:', round(head_metrics['mean_topic_ba'], 4))
print('BA no pior tema:', round(head_metrics['min_topic_ba'], 4))
table(['Tema', 'N', 'Macro-F1', 'BA'], [
    [r['target'], r['n'], f"{r['macro_f1']:.4f}", f"{r['balanced_accuracy']:.4f}"]
    for r in head_metrics['topics']])
for interval in load(HEAD_RUN / 'intervals.json'):
    print(interval['comparison'], 'delta F1:', round(interval['delta_macro_f1'], 4),
          'IC95%:', interval['percentile_interval_95'])
''')
    md('''A meta provisória foi atingida: macro-F1 global 0,786, BA média 0,780 e
pior BA 0,703. O ganho sobre NLI anterior foi 0,082 em macro-F1, com intervalo
bootstrap de 0,043 a 0,118. A seleção adaptativa de métodos e o teste histórico
limitam a interpretação desse intervalo. Aborto permanece difícil (macro-F1
0,590); casamento tem apenas quatro exemplos contrários no teste.

**R5/R10 — transferência:** cabeça final ajustada nos 2.060 exemplos de treino,
C escolhido no dev, sem usar teste para ajuste. Os 280 templates conhecidos
verificam direção, não generalização a documentos naturais. Limiar 0,7 é uma
regra exploratória sem garantia de probabilidade calibrada. Evidências do
documento são reaproveitadas do recuperador anterior, sem gabarito humano.
''')
    code('''APP_RUN = ROOT / 'analises/execucoes/crossencoder_application_20260917'
controlled = load(APP_RUN / 'controlled_metrics.json')[0]
document_result = load(APP_RUN / 'document_transfer.json')
print('Templates:', controlled['n'], '| Macro-F1:', controlled['macro_f1'],
      '| Cobertura:', controlled['direction_coverage'])
print('Estados documentais:', document_result['counts'])
assert all(item['response'] is None for item in document_result['items'])
print('Nenhuma intensidade 8values foi inferida.')
''')
    md('''**Conclusão desta rodada:** melhora satisfatória segundo o critério local
para temas reservados do BRmoral; transferência controlada correta em 280/280
casos. O documento tem 18 posições favoráveis, 11 contrárias e 41 incertas,
sem estimativa de acurácia. Isso não valida um perfil político nem as cinco
intensidades do 8values. Próxima validação científica: documentos independentes
com evidências e posições anotadas por humanos. O ajuste contrastivo original
do E5 segue pendente; o resultado atual usa outro método.

Relatório: [melhoria de generalização](analises/melhoria_generalizacao_20260917.md).
''')
    namespace = {'__name__': '__notebook__'}
    count = 0
    for cell in cells:
        if cell['cell_type'] == 'code':
            count += 1
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                exec(compile(''.join(cell['source']), f'BRmoral-cell-{count}', 'exec'), namespace)
            cell['execution_count'] = count
            cell['outputs'] = [dict(output_type='stream', name='stdout', text=stream.getvalue().splitlines(True))]
        cell['id'] = f'brmoral-{len(cell["source"])}-{hashlib.sha256("".join(cell["source"]).encode()).hexdigest()[:12]}'
    notebook = dict(nbformat=4, nbformat_minor=5, cells=cells, metadata={
        'kernelspec': {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'},
        'language_info': {'name': 'python', 'version': '3.12.14'},
        'execution': {'method': 'sequential Python exec with stdout capture', 'model_runs_reexecuted': False}})
    output = root / 'BRmoral.ipynb'
    output.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'{output}: {len(cells)} células, {count} células de código executadas.')


if __name__ == '__main__':
    create(Path.cwd())
