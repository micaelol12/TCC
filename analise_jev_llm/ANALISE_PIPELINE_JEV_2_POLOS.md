# Análise do `Pipeline_JEV_2_Polos_LLM.ipynb`

Data: 06/10/2026. Alvo: [`Pipeline_JEV_2_Polos_LLM.ipynb`](../Pipeline_JEV_2_Polos_LLM.ipynb), com código e saídas salvas.
Anexo com os 142 achados detalhados: [`ACHADOS_PIPELINE_JEV_2_POLOS.md`](ACHADOS_PIPELINE_JEV_2_POLOS.md).
As células são citadas pelo índice JSON, começando em zero (`CELL n`).

## Como esta análise foi feita

- Seis revisores independentes cobriram código, benchmark, aplicação a documentos, neutralidade das rubricas, APIs e literatura (incluindo o docx do TCC).
- Cada lote de achados passou por um verificador que tentou refutá-los. O verificador releu o código e as saídas salvas, reproduziu offline o que dava para reproduzir (funções puras com dublês, a segmentação com `langchain-text-splitters==1.1.3`/`tiktoken==0.14.0`, os hashes de `metadata.origem`) e conferiu a documentação oficial da TypeSafe e da Maritaca. Também leu, sem executar, o código do `typesafe-sdk==0.7.2` e do `openai==3.24.0`.
- Um crítico de completude percorreu as 45 células em busca de lacunas e contradições.
- Resultado: 142 achados. 86 foram confirmados, 41 parcialmente confirmados e corrigidos, 14 acrescentados na verificação e 1 refutado.
- **Nenhuma chamada ao JEV ou ao Sabiá foi feita.** Os números vêm das saídas salvas, que são truncadas, de recálculos sobre elas e de `tcc/questions.json`. Onde a evidência é parcial, isso está indicado.

## Resumo executivo

1. **Os números salvos não formam uma execução única.** O gráfico da CELL 44 (91,0 / 32,8 / 81,7 / 98,7) não bate com a tabela da CELL 39 (93,4 / 27,4 / 77,9 / 98,75). O benchmark rodou antes das definições atuais. Antes de citar qualquer número no TCC, é preciso uma execução limpa e salva em disco.
2. **O "score" não é intensidade.** No Score de 2 níveis, o score é P(polo A). A documentação do SDK define o score como a média dos níveis ponderada pelas probabilidades, e as saídas confirmam. A "confiança" é igual a |2·P(A) − 1|. Com o fallback devolvendo 0 ou 100, o índice do documento equivale, na prática, a **100 × a proporção de trechos com posição classificados no polo A**.
3. **Os rótulos do 8Values ("Comunista", "Revolucionário" etc.) não deveriam ser aplicados ao documento.** O índice não está na escala do quiz, e os intervalos de incerteza atravessam várias faixas de rótulo. Isso é o principal risco de neutralidade do notebook, e vale para qualquer plano.
4. **A métrica "acurácia de polaridade" mistura erro de relevância com erro de direção.** A direção condicional aos eixos detectados acerta cerca de 89,5% (JEV) e 89,7% (cascata), mas a coluna reporta 0,38–0,82. O erro dominante é a relevância: 40 falsos negativos em 68 erros do JEV.
5. **O ganho da cascata (212 → 221/280) é frágil.** A regra "tudo irrelevante" já faz 58,6%. O saldo de +9 vem quase todo de pares de efeito zero (+7). O McNemar dá p = 0,022, mas a conclusão depende de um único par discordante. O LLM roda com a temperatura padrão de 0,7, e a mesma configuração do JEV deu 215/280 numa execução anterior.
6. **As rubricas têm assimetrias que podem empurrar qualquer documento na mesma direção:**
   - o polo `authority` descreve um regime autoritário, sem segurança pública nem polícia;
   - o eixo diplomático não tem "paz", "militar" nem "guerra" nos polos, embora o gabarito e os rótulos tratem disso;
   - o eixo social inclui ciência, educação e ambiente no tópico, e só `progress` tem contrapartida para eles: os 72 trechos com posição do exemplo ficaram todos no polo A;
   - `wealth` não nomeia instrumentos fiscais;
   - a ordem dos critérios é fixa ([B, A]), com os quatro polos A no mesmo quadrante.
7. **O objetivo declarado do TCC, o alinhamento texto × usuário, ainda não está implementado,** e as escalas não são comensuráveis. O quiz comprime para 50: "concordo" em todas as afirmações no sentido A dá 75. O documento é uma proporção.
8. **Há dados prontos e baratos que não foram usados.** `tcc/d0_manual_validation_avaliado.csv` traz rótulos de relevância. Os baselines de embeddings, NLI e Laya do `TCC.ipynb` podem ser trazidos. O teste de 5 níveis já existe. E, com o LLM em todos os eixos uma vez (~250 s), dá para simular offline qualquer regra de roteamento.

## 1. O que já está bom e deve ser mantido

- **Comparação pareada sem inferência duplicada.** JEV inicial e cascata usam as mesmas respostas do JEV, e decisão original, decisão final, motivos e latências ficam registrados (CELL 22 e CELL 27).
- **Validação rigorosa das saídas do JEV** (intervalos, chaves, soma com tolerância) e contrato do LLM com `extra="forbid"` (CELL 19 e CELL 20).
- **Ausência de evidência e abstenção não viram 50.** Eixos sem posição ficam `None`, com status explícito.
- **Fidelidade ao bloco original e segmentação reprodutível.** As rubricas são idênticas às do bloco "Teste 2 polos extremos" do `TCC.ipynb` (conferido por AST). Os três hashes de `metadata.origem` conferem (o das perguntas só depois de normalizar CRLF para LF), e a segmentação reproduz exatamente os 84 chunks.
- **Proteção contra injeção no prompt do LLM.** O prompt diz que o texto é para análise, não uma instrução a seguir, e exige citação literal.
- **Parte da análise anterior já foi incorporada.** As recomendações P0 de engenharia de [`ANALISE_PIPELINE_JEV_LLM.md`](ANALISE_PIPELINE_JEV_LLM.md) foram adotadas: relevância e posição separadas, abstenção, ablação sobre as mesmas respostas e rubrica comum. Ficaram abertos validação, baselines, estimando, incerteza e reprodutibilidade (LIT-12).

## 2. Correções prioritárias

### 2.1 Gerar todos os números a partir de uma execução única e persistida

Achados COD-01, DOC-03, API-V01, COD-04, BEN-13, API-05 e CMP-03.

**O problema:**
- Os `execution_count` mostram a ordem real: benchmark em 14–18, definições em 41–56, CELL 41 em 23, CELL 44 em 25, CELL 39 em 60. As CELLs 37 e 43 aparecem como `None`, ou seja, foram editadas depois de executadas.
- O resumo "84 chunks / 46 chamadas LLM" pertence à execução do gráfico, não à da tabela de cobertura.
- `registros` só existe em memória. Recalcular qualquer métrica exige novas chamadas, que não são determinísticas.
- Já há dois JSONs truncados versionados: `tcc/teste_estabilidade.json` (133 bytes) e `tcc/resultados_total_estimado.json` (14 bytes). A escrita precisa ser incremental e atômica.

**O que fazer:**
- Gravar uma linha JSONL por pergunta ou chunk assim que ela for obtida, com `encoding="utf-8"` e `allow_nan=False`.
- Gravar um manifesto com `run_id`, data, commit, versões de SDK e modelo, hash da configuração e das rubricas, e `usage`.
- Gerar tabelas e figuras **a partir dos arquivos gravados**.
- Executar com "Restart & Run All" (ou `nbconvert --execute`) e acrescentar uma célula final de invariantes: tabela = gráfico = registros.

```python
import hashlib, json, os, platform, subprocess
from datetime import datetime, timezone
from importlib.metadata import version

RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
DIR_RUN = Path("runs") / RUN_ID
DIR_RUN.mkdir(parents=True, exist_ok=True)

def _hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()

MANIFESTO = {  # MODELO_JEV: ID versionado fixado conforme a seção 3 (COD-06/API-03)
    "run_id": RUN_ID, "python": platform.python_version(),
    "typesafe_sdk": version("typesafe-sdk"), "openai": version("openai"),
    "commit": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
    "modelo_jev": MODELO_JEV, "modelo_llm": MODELO_LLM,
    "config": CONFIG_JEV_LLM_2_POLOS, "config_chunks": CONFIG_CHUNKS,
    "hash_rubricas": _hash(pipeline_jev_llm_2_polos.rubricas),
}
(DIR_RUN / "manifesto.json").write_text(json.dumps(MANIFESTO, ensure_ascii=False, indent=2), encoding="utf-8")

def anexar_jsonl(caminho, registro):
    """Uma linha por item, gravada assim que obtida; uma falha posterior não apaga o que já foi feito."""
    with open(caminho, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False, allow_nan=False, default=str) + "\n")
        f.flush(); os.fsync(f.fileno())
```

No laço da CELL 27 e da CELL 37, envolver cada item em `try/except`, gravar `{"chave", "registro" | "erro"}` e, na reexecução, pular as chaves já concluídas. Ao repetir uma tentativa, **refaça só a etapa do LLM**, reaproveitando a resposta do JEV já obtida (COD-03). Ao reler, as chaves `0`/`1` de `probabilities_score` voltam como strings.

### 2.2 Retirar os rótulos ideológicos do documento e renomear o índice

Achados VIE-01 (crítico), LIT-02, DOC-01, COD-V01, API-01, DOC-02 e BEN-03.

**Fatos verificados:**
- **O score é P(polo A).** No `typesafe_sdk/_schemas/models.py`, `ScoreAnswer.score` é "the probability-weighted average of the rubric levels". Com `criteria=[polo B, polo A]` (níveis 0 e 1), isso dá score = P(polo A).
  - Nas saídas: score 61 corresponde a margem 0,22; score 99 a 0,98; score 1 a 0,98.
  - Nas cerca de 20 linhas visíveis (CELLs 31 e 41), |confiança − margem| ≤ 0,01.
  - A página de limitações do jev-1.13 desaconselha usar a expectativa do Score como magnitude.
- **A regra efetiva de roteamento (`_motivos`) tem só dois parâmetros.** Um eixo é encaminhado se P(relevante) ∈ (0,40; 0,60), **ou** se é relevante e P(A) ∈ (0,15; 0,85). `margem_score_minima = 0,20` nunca dispara sozinha (P(A) ∈ (0,40; 0,60) já está contido). Os limiares 0,70/0,20 foram herdados de pipelines com Choice de 3 classes, em que tinham outro significado.
- **O índice do documento é, na prática, uma proporção de votos.** Os valores do JEV que não são encaminhados ficam em ≤15 ou ≥85, e os do LLM valem 0 ou 100. Em economic, diplomatic e state, o desvio-padrão observado é 90–95% do máximo possível para uma variável binária com a mesma média. Em society, os 72 trechos com posição ficaram todos no polo A.
- **Os rótulos caem em faixas extremas por construção.** `rotulo_8values` aplica os limiares do quiz (90/75/60/40/25/10) a essa proporção. Com 24–30 trechos, os ICs de Wilson são diplomatic [14,7; 45,2] e state [58,1; 89,9], cada um atravessando três faixas de rótulo.

**O que fazer:**
1. Remover `rotulo_8values` e `DOCUMENTO_NOME` do gráfico do documento. Usar identificadores cegos nas figuras.
2. Declarar o estimando: **"% de trechos com posição cuja direção é o polo A"**. Renomear `score_8values` para algo como `voto_polo_A`, e o score nativo para `p_polo_A`.
3. Corrigir a CELL 35, que diz que os valores finais "não são probabilidades": para o JEV, eles são 100·P(A).
4. Remover `margem_score_minima` ou documentar que ela é redundante. Parametrizar o roteamento como faixas de P(relevante) e de P(A).
5. Agregar numa escala homogênea, com contagens, cobertura e IC:

```python
import math
import numpy as np

def wilson(k, n, z=1.96):
    if n == 0:
        return (math.nan, math.nan)
    p, den = k / n, 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return 100 * (c - h), 100 * (c + h)

def agregar_eixo(registros, eixo, minimo=16):
    """Voto rígido para JEV e LLM; a P média do JEV fica à parte, como sensibilidade."""
    finais = [r["eixos"][eixo] for r in registros]
    n_a = sum(d["classe"] == "A" for d in finais)
    n_b = sum(d["classe"] == "B" for d in finais)
    n = n_a + n_b
    p_jev = [r["eixos_jev"][eixo]["score_nativo"] for r in registros
             if r["eixos_jev"][eixo]["relevante"] and r["eixos"][eixo]["metodo"] == "jev_2_polos"]
    return {
        "eixo": eixo, "trechos": len(finais), "votos_A": n_a, "votos_B": n_b,
        "sem_posicao_ou_irrelevante": len(finais) - n,
        "decididos_pelo_llm": sum(d["metodo"] == "llm_2_polos" for d in finais),
        "proporcao_A_%": 100 * n_a / n if n else None,
        "ic95_wilson": wilson(n_a, n),
        "p_media_A_jev_%": 100 * np.mean(p_jev) if p_jev else None,  # P(A), não intensidade
        "evidencia_suficiente": n >= minimo,  # ±20 p.p. com p≈0,75 exige n≈16 (pré-registrar)
    }
```

Trechos vizinhos não são independentes. Como robustez, use o bootstrap em blocos móveis que já existe no `TCC.ipynb` (CELL 237, `moving_block_indices`/`bootstrap_plan_score_intervals`).

### 2.3 Decompor as métricas do benchmark e mostrar os baselines

Achados BEN-01, BEN-02, LIT-03, LIT-04 e BEN-10.

**O problema:**
- Em `_decisao_jev`, um eixo previsto irrelevante recebe classe `C`, e a CELL 26 conta `C` como erro de polaridade. A coluna `acuracia_polaridade`, portanto, mede "relevância **e** direção". A frase da CELL 25 de que "a agregação permanece a do notebook original" não vale para essa coluna: no bloco original, a polaridade não dependia da relevância (103/116 = 88,8%).
- Os números abaixo foram derivados das contagens salvas.

| | JEV inicial | Cascata |
|---|---|---|
| Acurácia conjunta (280 pares) | 75,7% | 78,9% |
| Baseline "tudo irrelevante" | 58,6% | 58,6% |
| Relevância: precisão / revocação | 0,792 / 0,655 | 0,857 / 0,672 |
| Relevância: acurácia balanceada / κ | 0,767 / 0,547 | 0,797 / 0,612 |
| Direção entre relevantes detectados | 68/76 (89,5%) | 70/78 (89,7%) |
| Erros: FN relevância / FP / direção | 40 / 20 / 8 | 38 / 13 / 8 |

- **State:** a direção acerta 14/17 dos detectados (82%). Os 0,378 reportados vêm sobretudo dos 20 falsos negativos de relevância.
- **De onde vem o +9:** 7 verdadeiros negativos a mais (pares de efeito zero) e +2 entre os relevantes. A revocação de relevância, maior fonte de erro, quase não muda. Pela regra efetiva, um eixo previsto irrelevante só vai ao LLM se P(relevante) ∈ (0,40; 0,50).

**Código pronto para rodar sobre os `registros`:**

```python
def tabela_longa(registros, perguntas, estagio="eixos"):
    """Uma linha por pergunta × eixo. estagio: 'eixos_jev' (JEV inicial) ou 'eixos' (cascata)."""
    linhas = []
    for p, r in zip(perguntas, registros):
        for nome, eixo in EFFECT_TO_AXIS.items():
            efeito, d, dj = getattr(p.effect, nome), r[estagio][eixo], r["eixos_jev"][eixo]
            linhas.append({
                "id": p.id, "eixo": eixo, "efeito": efeito, "rel_esp": efeito != 0,
                "polo_esp": None if efeito == 0 else ("A" if efeito > 0 else "B"),
                "rel_prev": d["relevante"], "classe_prev": d["classe"],
                "p_A_jev": dj["probabilities_score"][1],
                "roteado": bool(r["motivos_fallback"][eixo]),
            })
    return pd.DataFrame(linhas)

def metricas_decompostas(df):
    linhas = []
    for eixo, g in [*df.groupby("eixo"), ("TODOS", df)]:
        y = g["rel_esp"]
        sim, nao = g["rel_prev"].eq(True), g["rel_prev"].eq(False)  # None (abstenção) é erro nos dois casos
        tp, fn, fp, tn = (int(m.sum()) for m in (y & sim, y & ~sim, ~y & ~nao, ~y & nao))
        n = tp + fn + fp + tn
        po = (tp + tn) / n
        pe = ((tp + fp) * (tp + fn) + (tn + fn) * (tn + fp)) / n ** 2
        det = g[y & sim]
        bruta = g[y]
        sinal = np.where(bruta["polo_esp"] == "A", 1, -1)
        linhas.append({
            "eixo": eixo, "TP": tp, "FN": fn, "FP": fp, "TN": tn,
            "precisao": tp / (tp + fp) if tp + fp else np.nan,
            "revocacao": tp / (tp + fn) if tp + fn else np.nan,
            "acc_balanceada": (tp / (tp + fn) + tn / (tn + fp)) / 2,
            "kappa": (po - pe) / (1 - pe),
            "direcao_nos_detectados": (det["classe_prev"] == det["polo_esp"]).mean(),
            "direcao_bruta_jev": ((bruta["p_A_jev"] - 0.5) * sinal > 0).mean(),  # comparável ao bloco original
            "baseline_tudo_irrelevante": (~y).mean(),
        })
    return pd.DataFrame(linhas).round(3)

J = tabela_longa(registros_pipeline_score, perguntas_benchmark, "eixos_jev")
C = tabela_longa(registros_pipeline_score, perguntas_benchmark, "eixos")
display(metricas_decompostas(J), metricas_decompostas(C))
```

Renomeie a coluna atual para algo como `acerto_relevancia_e_direcao` e use como métrica principal uma média macro por eixo de acurácia balanceada e direção condicional. Coloque na mesma tabela os comparadores que já existem no `TCC.ipynb`: embeddings na CELL 209 (relevância com BA 66,4%; polaridade 72,4%), NLI carregado na CELL 177 mas testado numa única frase, e Laya com 162/280, abaixo do trivial.

### 2.4 Tratar o ganho da cascata com inferência adequada

Achados BEN-06, BEN-12, API-04, BEN-V01, CMP-V02 e BEN-08.

**O problema:**
- **Significância no limite.** McNemar exato para 11 corrigidos × 2 piorados dá p = 0,0225; com 10 × 3, p = 0,092. Os 280 pares estão agrupados em 70 perguntas (a Q70 sozinha tem 4 FN). Por isso, use bootstrap por pergunta e o teste do sinal por pergunta. ICs de Wilson com n = 280: JEV [70,4; 80,4], cascata [73,8; 83,3]. Com n efetivo de 70, que é conservador: [64,5; 84,2] e [68,0; 86,8].
- **Estocasticidade não medida.** A Maritaca usa `temperature = 0,7` por padrão (documentação da Responses API), e o JEV não tem temperatura nem seed. A mesma configuração JEV deu 215/280 no `TCC.ipynb` (CELL 311) e 212/280 aqui. A Q2/economic, contada como "corrigida", era acerto do JEV na execução anterior (P(A) = 0,51) e aqui virou empate exato 0,50/0,50. As probabilidades têm granularidade de 0,01, então empates exatos não são raros.
- **Sem conjunto de validação.** A CELL 4 promete "selecionar na validação", mas as 70 perguntas já serviram para iterar o desenho (há 25 resultados de acertos conjuntos no `TCC.ipynb`).

**O que fazer:**
- `temperature=0` no Sabiá.
- k = 3–5 repetições do JEV (≈20 s cada) e do LLM nos eixos encaminhados. Reportar média ± dp, número de pares instáveis e κ de Fleiss.
- Reportar quantas correções vieram de `empate_polaridade`.
- Tratar as 70 perguntas como **desenvolvimento** e congelar a configuração por hash antes do teste final (ver 4.1).

### 2.5 Corrigir as assimetrias da rubrica antes de comparar documentos

Achados VIE-02, VIE-03, VIE-04, VIE-05, VIE-06, API-06, API-V02, DOC-10 e DOC-V01.

**Assimetrias medidas em `TEXTOS_EIXOS_2` (CELL 14), que é o que o JEV e o LLM realmente recebem:**

| Eixo | Assimetria verificada | Efeito provável |
|---|---|---|
| state | `authority` traz "Restrição do pluralismo e da oposição política", "Subordinação dos indivíduos…", isto é, 4 de 9 itens de grau extremo. "segurança", "polícia" e "puni*" aparecem 0 vezes nos dois polos. | Propostas democráticas de ordem e segurança, de qualquer campo, não se reconhecem no polo B, e a direção deriva para `liberty`. |
| diplomatic | "paz", "pacíf*", "milit*" e "guerra" aparecem 0 vezes nos polos, embora o tópico de relevância inclua forças armadas e guerra. O gabarito tem itens militares (Q17, Q21, Q22, Q23), e `DIPL_ARRAY` usa "Pacífico" e "Chauvinista". "Soberania" aparece em 10 dos 12 planos, em sentidos setoriais (alimentar, digital, sanitária). | O eixo mede "autonomia nacional × integração supranacional", não o construto rotulado. Pode virar contagem lexical de "soberania". |
| society | O tópico inclui ciência, tecnologia, educação e meio ambiente, e só `progress` tem contrapartida (it. 3, "uso da razão, da ciência"). No exemplo, 67 de 84 trechos têm termos de C&T, educação ou ambiente, e todos os 72 trechos com posição ficaram ≥ ~84. No CSV humano, 21 de 26 trechos técnico-científicos foram marcados como irrelevantes para society. | Efeito-teto: o eixo mede o volume de conteúdo setorial, não valores e costumes. |
| economic | `wealth` não tem "tribut*", "impost*", "fiscal" nem "gasto" (o gabarito Q4, "orçamento equilibrado", é Mercado). `equality` nomeia tributação progressiva. A relevância econômica cobre 89% dos trechos no exemplo, contra 24% no critério humano do CSV, que é de outro plano. | Programas sociais sem trade-off tendem a `equality`. |
| todos | `criteria=[B, A]` é fixo no JEV e no prompt do LLM, e os quatro polos A (equality, peace, liberty, progress) ficam no mesmo quadrante. Não há teste de ordem. | Um viés de posição seria indistinguível de um deslocamento ideológico, sempre no mesmo sentido. |
| todos | O Score de 2 níveis não tem opção "sem posição". No documento, 201 de 201 trechos-eixo relevantes receberam um polo. A documentação do Score recomenda Choice quando não há nível intermediário. A Q1/society, com P(relevante) = 0,11, ainda recebeu P(progress) = 0,98. | Menção ao tema vira voto. A abstenção prevista no desenho não ocorre nos dados. |

**O que fazer:**
1. **Separar "trata do tema" de "defende uma posição".** Testar, no benchmark e sem fallback, uma Choice `{polo_B, polo_A, sem_posicao}` com rótulos semânticos e ordem contrabalançada, contra o Score atual (API-V02 e DOC-V01).
2. **Reescrever os polos (v3) com a mesma estrutura nos dois lados:** princípio, papel do Estado, instrumentos típicos, custo aceito, forma moderada e forma forte. Escrever cada polo como seus defensores o descreveriam, sem adjetivos valorativos ("excessiva", "ultrapassadas"), e com exemplos que atravessem campos (VIE-08 traz uma proposta completa). Específico por eixo:
   - **diplomatic:** dividir em D1 (autonomia × integração) e D2 (força × diplomacia), e acrescentar uma nota simétrica sobre "soberania X".
   - **society:** decidir o construto. Restringir a valores, costumes, religião, família e sexualidade, ou dar contrapartes a `tradition` com base em Q45 e Q65.
   - **economic:** formular os instrumentos como trade-offs nos dois polos.
   - **tradition:** retirar "autoridade", que vaza para o eixo state.
3. **Auditar a simetria antes de rodar**: contagem de palavras, marcadores temáticos por polo e codificação de extremidade por dois juízes, com κ.
4. **Validar a v3 só no conjunto de desenvolvimento** (banco sintético, ver seção 5) e congelar por hash.
5. **Remover o código morto** `AXIS_SPECS[*]['a'/'b']` e o `polaridade` de `criar_questoes_eixo`, que são descartados (`relevancia, _ = ...`), e alinhar a tabela da CELL 12 ao que o modelo de fato vê (COD-15, VIE-09, LIT-V01).

## 3. Correções de código e de ambiente

| ID | Severidade | Problema | Correção |
|---|---|---|---|
| COD-02 / CMP-V03 | Média | A CELL 8 usa `type[T]` antes de `T` existir (CELL 17). Funciona só no Python 3.14 (PEP 649); em 3.11 e 3.12 dá `NameError`. A CELL 1 promete "3.10+", mas pandas 3.0.6 exige ≥3.11. | Definir `T = TypeVar("T")` na CELL 3 e declarar "Python ≥ 3.11 (resultados gerados em 3.14.8)". Corrigir também o typo `ler_json_tiptado`. |
| COD-05 | Média | `requirements.txt` é um `pip freeze` em UTF-16 de 132 pacotes, com `torch==2.14.1+cu132` (não existe no PyPI, então `pip install -r` falha). O git o trata como binário. A CELL 2 instala sem versões. | Criar `requirements-pipeline.txt` em UTF-8 só com as dependências diretas fixadas e usá-lo na CELL 2. No PowerShell 5.1, gravar com `Out-File -Encoding utf8`. |
| COD-06 / API-03 | Média | O SDK usa `jev-latest` por padrão (ou `TYPESAFE_DEFAULT_MODEL` do `.env`), e `sabia-4` é alias. O modelo registrado para o LLM é o pedido, não o que respondeu. | `AsyncTypeSafeClient(..., model="jev-1.13.0")`, `MODELO_LLM = "sabia-4-2026-01-06"`, conferir `response.model` e registrar as versões dos SDKs. |
| API-04 / API-10 / COD-11 / API-07 | Alta/Média | Sem `temperature`, `timeout` ou `max_retries` explícitos. O tier `flex` pode ficar até 5 min na fila antes de um 429 e não está documentado para a Responses API. `output_parsed=None` vira `ValidationError` e aborta tudo. `eixo` aceita qualquer string. | Cliente abaixo. Trocar `eixo: str` por `Literal[...]` dos 4 eixos. Para comparar latências, medir uma amostra no tier padrão. |
| COD-03 | Média | Qualquer exceção (resposta vazia, eixo com outro nome, timeout) descarta todo o benchmark ou documento. | Laço com `try/except` por item e JSONL incremental (2.1). |
| COD-07 | Média | `_score_evidencia_confere` aceita "a", "de" e "Brasil" ("brasil" está em 68 de 84 chunks). Recusa citações corretas que atravessam `## **título**` (17 de 17 casos), reticências nas bordas ou `\n` copiado do JSON do prompt. O documento não conta `evidencia_nao_verificada`. | Versão abaixo e prompt pedindo "oração completa com ≥ 4 palavras". Contar os status também na CELL 41. |
| COD-12 / API-08 | Baixa/Média | Num eixo encaminhado só por polaridade, o LLM pode reverter uma relevância que o JEV decidiu com margem 0,90 (ex.: chunk 84/state). | Primeiro medir quantas inversões ocorrem. Depois, como ablação, usar a tarefa "apenas_nivel". Implementar junto com a ampliação da faixa de relevância (BEN-10), senão o alcance da cascata cai. |
| API-09 / CMP-04 | Média/Baixa | Regras e dados no mesmo `input`; "A/B" com dois sentidos (relevância e polo); `nivel=0 → polo B`; ordem fixa; a resposta de um eixo pode depender dos outros eixos que vieram junto. | Regras em `instructions` e JSON em `input`, nomes dos polos no lugar de A/B, ordem embaralhada com semente. Medir agrupado × um eixo por chamada nos 31 pares. |
| API-12 | Média | A Choice de relevância sempre apresenta "Sim" primeiro, e o jev-1.13 documenta viés pela primeira opção. A relevância responde por 60 das 68 falhas. | Rótulos `relevante`/`irrelevante` e contrabalanço da ordem na mesma chamada (média das duas). |
| COD-08 / BEN-15 | Baixa | As margens médias da cascata são calculadas só nos pares não encaminhados. | Reportar as margens do JEV sobre todos os pares e as do LLM como "não aplicável". |
| COD-16, COD-17, COD-18 / DOC-17 | Baixa | `acerto polaridade avaliada` tem dtype `object`, então `round` não é aplicado. `rotulo_8values(NaN)` devolve "Laissez-Faire". O gráfico altera o resultado e lê uma variável global. | `astype("boolean")`, `if not math.isfinite(val): return ""` e uma função de figura pura, com IC e n. |
| COD-10 / DOC-18 | Baixa | As CELLs 0 e 33 dizem que tudo está "incorporado", mas as CELLs 9 e 10 leem `tcc/*.json`. O hash de origem nunca é verificado. | Corrigir o texto e fazer `assert sha256(md) == metadata.origem.documento_texto_sha256`. |
| COD-13 / DOC-06 | Média/Alta | Os chunks incluem capa, sumário (o chunk 2 deu voto econômico com score 99), `<!-- picture text -->` com siglas de coligação e 43 quebras no meio de frase. A contaminação varia entre planos: 13,4% de chunks de sumário num plano contra 0–1,7% nos demais. | Limpeza padronizada e versionada, com log por plano, aplicada igualmente a todos (código em DOC-06). |
| BEN-19 | Baixa | `LIMITE_PERGUNTAS = N` pega as N primeiras perguntas, todas de economia. | Amostra estratificada pelo eixo primário, com semente fixa. |
| CMP-02 | Média | Tradução de `questions.json` (os efeitos conferem 70/70 com o original): a Q67 está em espanhol ("Deberíamos…"), a Q11 traz "Utilitários básicos" (falso cognato), na Q25 "grande" é ambíguo, nas Q36/Q39 "estado" está em minúscula (itens só de state, o eixo pior). O mesmo arquivo alimenta o quiz do usuário. | Revisão por duas pessoas com retrotradução. Versionar o original em inglês (MIT) e rodar o benchmark também em EN como controle. |
| CMP-V01 | Média | O corpus usa só os anexos `_01` do TSE, e o `leiame.pdf` diz que uma candidatura pode anexar vários. | Conferir no ZIP do TSE, agrupar por candidatura e concatenar os anexos em ordem. |
| `.env.example` | Baixa | `OPENROUTER_API_KEY=s`. | Deixar o valor vazio. |

**Cliente LLM com reprodutibilidade e metadados** (API-04, API-10, API-03, COD-11):

```python
class MaritacaClient(LLMClient):
    def __init__(self, api_key, model, *, temperature=0.0, timeout=360.0, max_retries=4,
                 service_tier="flex"):
        # flex: fila de até 5 min antes do 429, por isso timeout > 300 s
        self.client = AsyncOpenAI(api_key=api_key, base_url="https://chat.maritaca.ai/api",
                                  timeout=timeout, max_retries=max_retries)
        self.model, self.temperature, self.service_tier = model, temperature, service_tier
        self.ultima_chamada = None  # uso sequencial; com concorrência, devolver junto da resposta

    async def generate(self, prompt, response_schema):
        r = await self.client.responses.parse(
            model=self.model, input=prompt, text_format=response_schema,
            temperature=self.temperature, extra_body={"service_tier": self.service_tier},
        )
        self.ultima_chamada = {"id": r.id, "model": r.model,
                               "usage": r.usage.model_dump() if r.usage else None}
        if r.output_parsed is None:
            raise ValueError(f"Resposta sem saída estruturada (id={r.id}).")
        return r.output_parsed
```

**Verificação de evidência** (COD-07, testada com os 84 chunks reais; os falsos negativos título + parágrafo caem de 17/17 para 0/17):

```python
import re
_MARCACAO_MD = re.compile(r"(\*\*|__|<br\s*/?>|^#{1,6}\s+|^>\s?|\|)", re.M)
_RETICENCIAS = re.compile(r"^(\.\.\.|…)\s*|\s*(\.\.\.|…)$")

def _sem_markdown(texto):
    return _MARCACAO_MD.sub(" ", texto)

def _score_evidencia_confere(texto, evidencia, min_palavras=4):
    """Trecho contínuo do texto, ignorando marcação Markdown e escapes do JSON do prompt."""
    citacao = evidencia.replace("\\n", " ").replace('\\"', '"')
    citacao = _score_normalizar_citacao(_sem_markdown(citacao)).strip(" \"'.,;:")
    citacao = _RETICENCIAS.sub("", citacao).strip(" \"'")
    if len(citacao.split()) < min_palavras:
        return False
    return citacao in _score_normalizar_citacao(_sem_markdown(texto))
```

A verificação continua só de **existência** da citação, não de que ela sustenta o eixo e o polo. Ver VIE-V01 na seção 5.

## 4. Melhorias metodológicas

### 4.1 Separar desenvolvimento e teste, e medir o que a cascata promete

Achados BEN-09, LIT-05, BEN-08, VIE-19, LIT-07 e BEN-14.

- **Rodar o LLM uma vez em todos os eixos das 70 perguntas** (≈250 s) e persistir o resultado. Com isso, sem novas chamadas, dá para:
  - ter o baseline "LLM sozinho" e o oráculo ("acerta se JEV ou LLM acerta");
  - traçar a fronteira de Pareto "chamadas ao LLM × acurácia balanceada";
  - escolher as faixas de roteamento por validação cruzada agrupada por pergunta.
  - Limitação: o prompt com 4 eixos difere do prompt parcial (CMP-04).
- **Ampliar o alcance sobre os falsos negativos.** Testar offline uma faixa assimétrica de relevância, encaminhando os "irrelevantes" com P(relevante) ∈ [q_min; 0,5). Antes, olhar a distribuição de P(relevante) nos 40 falsos negativos: se a maioria estiver perto de 0, o problema é de rubrica ou gabarito, não de roteamento.
- **Calibração e risco × cobertura** da relevância do JEV (Brier, ECE, diagrama de confiabilidade). Os dados já existem nos registros.
- **Pré-registrar:** congelar configuração e rubrica por hash, declarar as métricas principais e os critérios de aceite, e avaliar **uma única vez** no conjunto de teste. Declarar no TCC as variantes já testadas nas 70 perguntas.

### 4.2 Refinar o gabarito do 8Values

Achados BEN-04, BEN-05, BEN-11, VIE-15 e LIT-15.

- 23 dos 116 pares relevantes são **secundários** (|efeito| menor que o máximo da pergunta), e state concentra 9 secundários e 15 primários empatados. Estratificar todas as métricas em primário único, primário empatado e secundário, e reportar também a acurácia ponderada por |efeito| e versões sem Q69/Q70 (quatro eixos com ±10).
- O efeito descreve como **concordar** move a pontuação do respondente, o que nem sempre é a posição defendida pelo texto. Exemplo: a Q1, sobre opressão por corporações, tem state −5. Escrever no TCC que o benchmark mede "concordância com a codificação do 8Values".
- Reportar a **revocação por polo**. O gabarito é desbalanceado: state tem 24 itens B e 13 A.

### 4.3 Aplicação a documentos

Achados DOC-04, DOC-06, DOC-07, DOC-12, DOC-13, LIT-16 e DOC-11.

- **Regra de evidência mínima pré-registrada**, por exemplo n ≥ 16 trechos posicionados para ±20 p.p. Abaixo dela, mostrar "evidência insuficiente" sem imputar 50.
  - Com a segmentação atual, os 12 planos variam de 8 a 156 trechos (828 no total). Nos dois menores, os eixos de baixa cobertura teriam 2–3 trechos.
  - Calcular offline, antes de chamar a API, o n esperado por plano e eixo.
- **Sensibilidade da agregação sem novas chamadas:**
  - voto rígido × P média do JEV × só JEV (`usar_fallback=False`);
  - com e sem trechos de diagnóstico ou balanço de gestão;
  - unidade de 300/600/1000 tokens × parágrafo, mantendo os tokens fixos como protocolo principal, porque a densidade de títulos varia 18× entre os planos.
- Marcar como "não robusta" qualquer conclusão que mude de lado em relação a 50.

### 4.4 Validação com dados humanos

Achados DOC-09, BEN-16, CMP-01, LIT-06 e VIE-18.

**`tcc/d0_manual_validation_avaliado.csv`:**
- São 66 unidades de ~94 tokens, com o caminho de seções como prefixo, do plano `2026BR280002552484_01.pdf` (não o do exemplo).
- Só há rótulos de relevância (positivos: economic 16, diplomatic 4, state 15, society 7) e não há registro de anotador.
- Rode a cascata nelas (66 chamadas JEV) e reporte o resultado como "relevância em unidades de ~95 tokens", não como validação do regime de 600 tokens: projetado nos chunks do notebook, o plano vira 8 chunks. Use bootstrap por seção, porque as unidades vizinhas se sobrepõem.

**Validação no regime real:**
- Anotar uma amostra estratificada dos chunks da própria CELL 36, por exemplo 5–10 por plano, cegos quanto à origem, com relevância **e** polaridade.
- Dupla anotação em ~30% da amostra para calcular κ ou α, com diretriz escrita e, se possível, anotadores de orientações diversas.
- Hoje não há nenhum gabarito de **direção** em documentos (DOC-V02). Enquanto não houver, state e diplomatic, os eixos com a pior direção no benchmark, deveriam aparecer com o aviso "direção não validada".

### 4.5 Alinhamento com o usuário, o objetivo declarado do TCC

Achados LIT-01, DOC-05, VIE-21 e CMP-05.

- **O componente falta.** O notebook termina no índice do documento, e o `TCC.ipynb` só calcula a "ideologia mais próxima" do usuário.
- **As escalas não conversam.** No quiz (`calc_score`), respostas neutras entram no máximo: "concordo" em todas as afirmações no sentido A dá 75,0. Nos três conjuntos de `tcc/lista_total.json`, a diferença entre o score do quiz e a "% pró-A entre respostas posicionadas" chega a 23 pontos, sempre no sentido de afastar de 50.

**Opções:**
- **(a), recomendada para começar:** medir o usuário com o mesmo estimando do documento, ou seja, a % pró-A entre respostas não neutras, ponderada por |efeito|, com a fração de neutras como cobertura. Comparar direção e cobertura por eixo, com IC, e listar os eixos "não comparáveis" em vez de imputar 50.
- **(b):** "questionário por procuração", em que o documento responde às 70 afirmações com "não aborda" explícito e citação verificada. O escore usa a fórmula do quiz, mas exclui do máximo os itens não abordados. As tentativas anteriores em `results.json` regrediram a 50 justamente por não excluir.
- Mostrar o alinhamento **por afirmação**, com a evidência, e nunca exibir "ideologia mais próxima" para planos.

**Dados do usuário (LGPD):**
- Opinião política é dado sensível (art. 5º, II; art. 11).
- O perfil é aritmética local e não precisa de API.
- O termo do docx chama de "anônima" uma opinião que fica num histórico que o usuário pode excluir, o que configura pseudonimização. Trocar o termo.
- Se houver coleta com pessoas, verificar com o orientador a necessidade de passar pelo CEP.

## 5. Bateria de testes de neutralidade

Os testes podem ser executados no próprio pipeline e respondem diretamente à exigência de pesquisa "sem viés". Critérios sugeridos pelos revisores, a serem pré-registrados:

| Teste | O que isola | Critério de aceite sugerido | Achado |
|---|---|---|---|
| Permutação da ordem dos critérios [B,A] ↔ [A,B] (P(A) = 1 − score na ordem invertida), no JEV e no LLM | Viés de posição | Por eixo, \|Δ médio\| ≤ 0,02 e inversão de direção ≤ 3%. Se falhar, usar a média das duas ordens | VIE-06 |
| Contrabalanço "Sim/Não" na relevância | Viés de primeira opção (documentado no jev-1.13) | Registrar \|p₁ − p₂\| por item | API-12 |
| Negação e pares mínimos dos 70 itens; paráfrases | Equivariância (a direção deve inverter) e invariância | Inversão ≥ 90% nas negações; paráfrases preservam a direção | VIE-16, BEN-17 |
| Banco sintético espelhado (4 eixos × 2 intensidades × 2 registros × 5 pares = 160 frases) | Revocação e inclinação por polo, como conjunto de desenvolvimento | Diferença de revocação entre polos ≤ 10 p.p. | VIE-17 |
| Prior por eixo: os 164 pares de efeito 0 (sem custo, com os registros salvos) e textos neutros | Direção "padrão" que entra via falsos positivos de relevância | \|média P(A) − 0,5\| ≤ 0,10 e ≤ 20% de decisões confiantes | VIE-11 |
| Mascaramento de identidade (nomes, siglas, coligações, slogans) e inserção contrafactual de cada uma das 12 identidades em ~40 frases neutras | Invariância a quem fala | \|ΔP(A)\| médio ≤ 0,03, nenhuma inversão, Friedman com p > 0,05 | VIE-10, DOC-15 |
| Autodescrição: mascarar adjetivos e slogans com vocabulário dos critérios, com controle de palavras neutras | Sensibilidade do jev-1.13 a textos que se autoclassificam | ΔP(A) líquido do controle | API-16 |
| Decisões do LLM por polo (LLM→A, LLM→B, abstenção) e índice só JEV × cascata | Prior do LLM nos casos de fronteira, que pesam com 0/100 | Reportar sempre; simetrizar (duas ordens, aceitar só se coincidirem) numa amostra | VIE-12 |
| Coerência citação → eixo → polo verificada pelo JEV, com ordem alternada | Se a evidência "verificada" sustenta a decisão | Coerência ≥ 90% e diferença entre polos ≤ 10 p.p. | VIE-V01 |
| Os 12 planos processados de forma cega, idêntica e com 2–3 repetições | Discriminabilidade e estabilidade | ICC(2,1) ≥ 0,75 por eixo; alerta se ≥ 10 de 12 planos caírem na mesma faixa | VIE-07, DOC-08, DOC-10 |
| Idioma: experimento 2×2 (instruções PT/EN × texto PT/EN) usando os itens originais do 8Values, sem retrotradução automática | Efeito do idioma no JEV | Comparar acurácia, confiança e taxa de encaminhamento | API-13, CMP-08 |

## 6. Novas ideias para o TCC, por valor e esforço

| Valor | Esforço | Ideia | Achado |
|---|---|---|---|
| Alto | Baixo | Tabela única de comparadores no mesmo protocolo: trivial, polo majoritário, embeddings (código já existe), NLI zero-shot com hipóteses vindas de `TEXTOS_EIXOS_2`, JEV, LLM sozinho e cascata | LIT-04, LIT-05 |
| Alto | Baixo | Teste-reteste antes de qualquer comparação entre planos ou eixos | COD-20, BEN-12 |
| Alto | Médio | Choice de 3 opções com "sem posição" × Score de 2 níveis | API-V02, DOC-V01 |
| Alto | Médio | Ficha do instrumento (model card e datasheet): uso pretendido, usos fora de escopo, proveniência (TSE, extrator, hashes), limitações | CMP-07 |
| Alto | Médio | Interface que mostra, por eixo, as evidências dos dois polos, a cobertura e o contraste entre planos (requisito de explicabilidade do docx) | DOC-16, LIT-21 |
| Médio | Baixo | Reaproveitar o Score de 5 níveis já testado (`TCC.ipynb` CELLs 298–302, 216/280) como rubrica ordinal, reportando a distribuição por nível e não o valor esperado. A documentação do jev-1.13 diz que os níveis são fracos em calibração numérica | LIT-13, API-15 |
| Médio | Médio | Ensemble de LLMs (a abstração `LLMClient` já permite), com a discordância como incerteza e critério de abstenção. Só depois de ter cache e versões fixadas, e só com documentos públicos | LIT-14 |
| Médio | Médio | Análise de erros tipificada: magnitude do efeito, itens com vários eixos, tipo de falha | LIT-15 |
| Médio | Baixo | Testes offline com dublês do JEV e do LLM, extraindo o pipeline para um módulo (`analise_jev_llm/pipeline_score.py` já serve de modelo) | COD-19 |
| Baixo | Médio | Validade convergente externa, sem tratá-la como verdade: ordenações de partidos por especialistas e corpus BRmoral (referências marcadas "a verificar" no anexo) | LIT-17 |
| Baixo | Médio | Baselines clássicos no nível do documento (Wordfish/Wordscores) e escalonamento por comparações pareadas (Bradley–Terry) entre planos | LIT-18, LIT-19 |
| Baixo | Baixo | Few-shot balanceado por polo no fallback, como ablação | LIT-20 |

## 7. Plano de ação sugerido

**Fase 0, sem chamadas de API (1–2 dias):**
- Corrigir `T` e a versão do Python, `requirements-pipeline.txt` e `.env.example`.
- Retirar os rótulos do 8Values e o nome do candidato das figuras do documento. Renomear o índice e corrigir a CELL 35.
- Implementar a persistência JSONL com manifesto, fixar os modelos e usar `temperature=0`, `timeout` e `max_retries` explícitos.
- Implementar as métricas decompostas, os baselines, McNemar e o bootstrap por pergunta.
- Implementar a nova verificação de evidência e a limpeza de Markdown com log.
- Amostra estratificada em `LIMITE_PERGUNTAS`.
- Revisar a tradução das perguntas e guardar o original em inglês.

**Fase 1, chamadas baratas:**
- Execução limpa e persistida.
- 3–5 repetições do JEV (≈20 s cada) e do LLM nos eixos encaminhados.
- LLM em todos os eixos uma vez (≈250 s), para Pareto, oráculo e LLM sozinho.
- Testes de prior, permutação, contrabalanço "Sim/Não", negação e identidade.
- Cascata no CSV d0.

**Fase 2, rubrica e validação:**
- Rubrica v3 simétrica e Choice com "sem posição".
- Banco sintético como conjunto de desenvolvimento; congelar por hash e pré-registrar.
- Anotação de chunks dos 12 planos (relevância e polaridade, κ).

**Fase 3, documentos e usuário:**
- Processar os 12 planos de forma cega e idêntica, com IC, regra de evidência mínima e teste de discriminabilidade.
- Alinhamento usuário × documento com estimando comum, fluxo de dados local e ficha do instrumento.

## 8. Como descrever os resultados no texto do TCC

- **Benchmark:** "concordância com a codificação do 8Values em 70 afirmações curtas", reportando relevância e direção separadamente, baselines, IC por pergunta e variação entre execuções. Não descrever como validação em planos de governo.
- **Índice do documento:** "proporção de trechos com posição cuja direção é o polo A, entre os trechos relevantes", sempre com n, cobertura e IC. Não chamar de "pontuação 8Values do plano" nem associar a rótulos ideológicos sem uma escala validada.
- **Cascata:** "melhora a precisão de relevância; a direção entre os detectados fica igual". Até haver repetições e um conjunto de teste independente, apresentar o ganho como resultado de desenvolvimento.
- **Neutralidade:** apresentar os resultados da bateria da seção 5, inclusive os que falharem, e as decisões de rubrica com justificativa.

## 9. Limitações desta análise

- Nenhuma inferência remota foi executada. As saídas salvas estão truncadas (cerca de 10 linhas visíveis por tabela). As matrizes de confusão foram reconstruídas a partir das acurácias por eixo, que são exatas porque vêm de contagens inteiras sobre 70.
- A igualdade "confiança = margem" foi conferida em cerca de 20 linhas visíveis. O SDK documenta o `score`, mas não a fórmula da `confidence`. Antes de remover `margem_score_minima`, confira nos 280 pares persistidos.
- As hipóteses sobre efeito-teto (society, economic) e sobre o eixo diplomático vêm de um único plano. Só se confirmam ou refutam processando os 12 planos com a mesma configuração.
- Afirmações sobre as APIs se baseiam na documentação pública e no código do SDK em 06/10/2026. A aplicação do `service_tier="flex"` à Responses API da Maritaca não está confirmada.
