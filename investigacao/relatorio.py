"""Relatório e notebook de leitura das execuções; infraestrutura R4/R5.

Não recalcula nem fabrica métricas. Cada bloco do notebook liga às referências
de METODOLOGIA.md; os resultados são lidos dos manifestos persistidos.
"""
import contextlib
import io
import json
from pathlib import Path

from .protocolo import write_json


def create_notebook(root, gpu=False):
    """R4: notebook independente, executado na geração, preservando TCC.ipynb."""
    cells = []

    def markdown(text):
        """R4: associa narrativa metodológica à célula de implementação seguinte."""
        cells.append({"cell_type": "markdown", "metadata": {}, "source": text.splitlines(True)})

    def code(text):
        """R4: célula executável sem estado do notebook original."""
        cells.append({"cell_type": "code", "metadata": {}, "source": text.splitlines(True), "outputs": [], "execution_count": None})

    markdown("""# Investigação de similaridade semântica — execução do plano

Resultados dos experimentos de 16/09/2026. Este notebook é independente de
`TCC.ipynb` e não muda suas células. Veja [protocolo](investigacao/README.md),
[rastreabilidade](investigacao/METODOLOGIA.md) e
[relatório](analises/implementacao_similaridade_semantica.md).

**Limite:** questionário e B3 são diagnósticos já conhecidos; documentos não têm
gabarito de posição. O experimento supervisionado externo requer textos da base.
Não há nova anotação manual nem resultados de treinamento externo inventados.

## Configuração e reprodução — R4

Kapoor e Narayanan (2023), *Leakage and the reproducibility crisis in machine-learning-based science*,
DOI 10.1016/j.patter.2023.100804: dados/configurações explícitos. Aqui usamos
manifestos e hashes, adaptação de engenharia descrita em `METODOLOGIA.md`.
""")
    code("""import json
from pathlib import Path
from collections import Counter
ROOT = Path.cwd()
if not (ROOT / 'TCC.ipynb').exists():
    raise RuntimeError('Execute o notebook na raiz do repositório TCC.')
RUNS = ROOT / 'analises' / 'execucoes'
def load(run, filename):
    # R4: leitura de resultado persistido, sem recalcular métricas.
    return json.loads((RUNS / run / filename).read_text(encoding='utf-8'))
diag = 'diagnostico_e5_20260916'
doc = 'documento_6x1_20260916'
controlled = 'controlados_20260916'
print(json.dumps(load(diag, 'manifest.json')['config'], ensure_ascii=False, indent=2))
""")
    markdown("""## 1. Direção no instrumento — R1/R2

Chen et al. (2023), *Ideology Prediction from Scarce and Biased Supervision*,
`artigos/2023.acl-long.530.pdf`, §§3–4, e Duan et al. (2025), *Constructing
Vec-tionaries*, arquivo local identificado em `METODOLOGIA.md`, §3.1.
Aplicação: projeções B0/B2 existentes, sem reproduzir treinamento dos artigos.
A margem é proporcional a B0. `effect` é convenção do instrumento, não intensidade.
O prefixo `query:` é aplicado uma vez. A comparação com saídas históricas não é
ablação isolada: também se normalizam espaços e se usa o ambiente/revisão registrados.
""")
    code("""metrics = load(diag, 'diagnostico_metricas.json')
print('eixo | método | calibração | n | balanced accuracy | MCC')
for r in metrics:
    if r['method'] != 'margem_equivalente_B0':
        print(f"{r['axis']} | {r['method']} | {r['calibration']} | {r['n']} | {r['balanced_accuracy']:.4f} | {r['mcc']:.4f}")
""")
    markdown("""## 2. Ordenação e calibração agrupada — R1/R4

Chen et al. (2023), §§3–4, e prevenção de vazamento de R4: lados do mesmo par
ficam juntos no leave-one-pair-out. B5 transfere limiar B3b; não valida limiar
documental. Os pares já foram usados no desenvolvimento.
""")
    code("""pairs = load(diag, 'pares_b3_b4.json')
print('eixo | método | ordenação | BA sem calibração | BA leave-one-pair-out')
for r in pairs:
    if r['dataset'] == 'INDEPENDENT_MINIMAL_PAIRS' and r['method'] != 'margem_equivalente_B0':
        print(f"{r['axis']} | {r['method']} | {r['ordering_accuracy']:.3f} | {r['raw']['balanced_accuracy']:.3f} | {r['leave_one_pair_out']['balanced_accuracy']:.3f}")
""")
    markdown("""## 3. Contextos controlados e NLI — R5/R7

Ribeiro et al. (2020), *Beyond Accuracy: Behavioral Testing of NLP Models with
CheckList*, §2 ([fonte](https://aclanthology.org/2020.acl-main.442/)); Yin et al.
(2019), *Benchmarking Zero-shot Text Classification*, §3
([fonte](https://aclanthology.org/D19-1404/)). Templates declaram apoio/oposição;
não se inverte uma frase natural apenas inserindo negação. Expectativa por
construção não é anotação humana. Recall abaixo é só da passagem inserida.
""")
    code("""cases = load(controlled, 'templates_nli.json')
contexts = load(controlled, 'contextos.json')
print('Expectativas NLI satisfeitas:', sum(r['satisfied'] for r in cases), '/', len(cases))
print('Erros:', [(r['id'], r['expected'], r['predicted']) for r in cases if not r['satisfied']])
for k in ['1', '3', '5']:
    print('Recall da inserção @' + k, sum(r['retrieval']['recall_inserted'][k] for r in contexts) / len(contexts))
""")
    markdown("""## 4. Texto 6x1 sem gabarito — R5/R7 e plano §7

As fontes R5/R7 motivam os testes, mas não validam estes limiares. Deduplicação,
cobertura e intervalo algébrico são adaptações específicas do plano. Direção
aceita pelo sistema não determina intensidade. Por isso `response=null` e o
intervalo integral do quiz continua [0,100]; isso não significa centrismo.
""")
    code("""result = load(doc, 'documento.json')
print('Estados:', dict(Counter(r['state'] for r in result['base']['items'])))
print('Cobertura direcional declarada:', result['base']['direction_coverage'])
print('Invariâncias e estabilidade:', {k: sum(r[k] for r in result['checks']) for k in result['checks'][0] if k != 'question_id'})
print('Custo:', json.dumps(load(doc, 'manifest.json'), ensure_ascii=False, indent=2))
""")
    markdown("""## 5. Próxima execução externa — R3/R6

Silva e Paraboni (2023), *Politically-oriented information inference from text*,
arquivo local, §§3.2/4.1.2: distingue posição textual e ideologia autoral.
Tunstall et al. (2022), *Efficient Few-Shot Learning Without Prompts*, §3.1
([fonte](https://arxiv.org/abs/2209.11055)): duas etapas, adaptação com pares do
mesmo alvo e cabeça logística L2. Treinamento ainda não executado em corpus externo.

O UstanceBR r3 foi acessado: CC BY 4.0, CSVs com `Tweet_ID;Polarity`, sem textos
ou autoria nesses arquivos. Veja `analises/acesso_corpora.json`. Após obter
textos e autores, o adaptador constrói dev sem usar teste. Não é necessária
anotação manual nova. Execute na raiz:

```powershell
python -m investigacao prepare-ustancebr --archive analises/ustancebr_r3.zip --hydrated dados/tweets_hidratados.jsonl --output dados/ustancebr
python -m investigacao external --corpus dados/ustancebr/corpus.jsonl --metadata dados/ustancebr/corpus.meta.json --output analises/execucoes/externo_novo
python -m investigacao documents --text 'content/Escala 6x1.txt' --selected-run analises/execucoes/externo_novo --output analises/execucoes/transferencia_nova
```

Comparação com Sabiá: acrescente `--sabia` com previsões por pergunta e
configuração fixa, conforme README. Nenhum resultado disponível foi tratado
como Sabiá por inferência. A ausência desse comparador está registrada.
""")
    filename = "Investigacao_Similaridade_GPU.ipynb" if gpu else "Investigacao_Similaridade.ipynb"
    if gpu:
        # R4: notebook próprio preserva os resultados e a leitura da execução CPU.
        for cell in cells:
            source = "".join(cell["source"])
            if cell["cell_type"] == "code":
                for old in ("diagnostico_e5_20260916", "documento_6x1_20260916", "controlados_20260916"):
                    source = source.replace(old, old.replace("_20260916", "_gpu_20260916"))
            else:
                source = source.replace("analises/implementacao_similaridade_semantica.md", "analises/execucao_gpu_similaridade_semantica.md")
            cell["source"] = source.splitlines(True)
        markdown("""## Comparação CPU/GPU — R4

Mesmos dados, revisões, pesos e limiares. Python/PyTorch, tamanho de lote e
residência de memória mudaram: os tempos não isolam apenas efeito do hardware.
A GPU usada é a GTX 1060 3 GB; inferências em float32, com um modelo por vez.
""")
        code("""comparison = json.loads((RUNS / 'comparacao_cpu_gpu_20260916.json').read_text(encoding='utf-8'))
print(json.dumps(comparison, ensure_ascii=False, indent=2))
""")
    scope = {}
    count = 0
    for cell in cells:
        if cell["cell_type"] == "code":
            count += 1
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                exec(compile("".join(cell["source"]), filename, "exec"), scope)
            cell["execution_count"] = count
            cell["outputs"] = [{"output_type": "stream", "name": "stdout", "text": stream.getvalue().splitlines(True)}]
    write_json(Path(root) / filename, {"cells": cells, "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 4})


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpu", action="store_true", help="Lê execuções GPU e gera notebook separado")
    args = parser.parse_args()
    create_notebook(Path.cwd(), gpu=args.gpu)
