# Comparação JEV/LLM — perguntas 8values

Execuções registradas: 1176/1260. Estado: incomplete_provider_or_budget_stop.
Modelos solicitados: jev-1.13.0 / sabia-4.
Concorrência: 1; repetições planejadas: 3.
Comparação principal: 840 análises; 2 repetições iniciais completas. 336 análises de rodadas incompletas preservadas somente no JSONL.

Se nenhuma rodada estiver completa, os números são parciais e não sustentam uma comparação balanceada.

Acurácia conjunta: nos efeitos não nulos, exige relevância e polo corretos; nos efeitos zero, exige declarar irrelevância. É a convenção do benchmark anterior. Acurácia de relevância verifica apenas se o eixo é relevante, sem exigir polo correto.

Acurácia direcional = acertos / todos os eixos com efeito diferente de zero. Ausência, posição intermediária, abstenção e falha contam como erro nesses alvos. Efeito zero não é rótulo de neutralidade nem prova de irrelevância; fica fora da acurácia. O sinal do efeito determina o polo A/B; a magnitude não é usada como rótulo ordinal.

Latência real de classify_chunk, incluindo rede, validação e retries; sem fila, HTTP do app, segmentação ou agregação. Uma pergunta corresponde a um trecho. Nenhuma resposta é reaproveitada pelo script entre braços. O aquecimento fica no JSONL, fora das métricas.

Chamadas HTTP são tentativas de envio observadas no cliente (inclusive retries), não uma confirmação de cobrança. O médio agrupa os eixos incertos numa chamada LLM.

## Todas as perguntas (descritivo)

| Estratégia | Conjunta | Relevância | Direcional | LLM lógicas | LLM HTTP | JEV HTTP | Média s | P50 s | P95 s | Falhas* |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| atual_alto | 74.8% | 82.1% | 40.9% | 140 | 140 | 0 | 1.28 | 1.21 | 1.61 | 0 |
| atual_baixo | 71.2% | 78.9% | 50.4% | 0 | 0 | 140 | 0.20 | 0.20 | 0.25 | 0 |
| atual_medio | 76.1% | 81.8% | 49.1% | 89 | 89 | 140 | 0.78 | 0.87 | 1.48 | 0 |
| cascata_0.3 | 76.8% | 82.0% | 50.4% | 90 | 90 | 140 | 0.72 | 0.87 | 1.33 | 0 |
| cascata_0.7 | 75.2% | 80.7% | 44.8% | 107 | 107 | 140 | 0.99 | 0.93 | 1.58 | 0 |
| cascata_0.9 | 74.5% | 80.7% | 41.8% | 117 | 117 | 140 | 1.10 | 1.15 | 1.83 | 0 |

## Calibração

| Estratégia | Conjunta | Relevância | Direcional | LLM lógicas | LLM HTTP | JEV HTTP | Média s | P50 s | P95 s | Falhas* |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| atual_alto | 76.8% | 82.8% | 44.4% | 100 | 100 | 0 | 1.27 | 1.20 | 1.61 | 0 |
| atual_baixo | 73.2% | 81.5% | 49.4% | 0 | 0 | 100 | 0.20 | 0.20 | 0.25 | 0 |
| atual_medio | 76.8% | 83.0% | 46.9% | 63 | 63 | 100 | 0.80 | 0.87 | 1.48 | 0 |
| cascata_0.3 | 78.0% | 83.2% | 49.4% | 64 | 64 | 100 | 0.72 | 0.87 | 1.33 | 0 |
| cascata_0.7 | 76.2% | 82.2% | 43.8% | 71 | 71 | 100 | 0.93 | 0.92 | 1.44 | 0 |
| cascata_0.9 | 75.5% | 81.5% | 42.5% | 78 | 78 | 100 | 0.98 | 1.12 | 1.55 | 0 |

## Teste reservado

| Estratégia | Conjunta | Relevância | Direcional | LLM lógicas | LLM HTTP | JEV HTTP | Média s | P50 s | P95 s | Falhas* |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| atual_alto | 70.0% | 80.6% | 33.3% | 40 | 40 | 0 | 1.32 | 1.23 | 1.61 | 0 |
| atual_baixo | 66.2% | 72.5% | 52.8% | 0 | 0 | 40 | 0.20 | 0.20 | 0.23 | 0 |
| atual_medio | 74.4% | 78.8% | 54.2% | 26 | 26 | 40 | 0.73 | 0.87 | 1.34 | 0 |
| cascata_0.3 | 73.8% | 78.8% | 52.8% | 26 | 26 | 40 | 0.70 | 0.87 | 1.21 | 0 |
| cascata_0.7 | 72.5% | 76.9% | 47.2% | 36 | 36 | 40 | 1.14 | 0.98 | 2.16 | 0 |
| cascata_0.9 | 71.9% | 78.8% | 40.3% | 39 | 39 | 40 | 1.42 | 1.17 | 3.75 | 0 |

## Interpretação

A acurácia conjunta foi 71.2% no baixo, 76.1% no médio e 74.8% no alto. Os tempos médios foram 0.20 s, 0.78 s e 1.28 s, respectivamente.

No médio, a direção teve 114/232 acertos (49.1%). Incluindo acertos de irrelevância nos efeitos zero, a conjunta teve 426/560 acertos (76.1%). Esses percentuais têm denominadores diferentes; não representam uma queda entre duas execuções da mesma métrica.

A cascata 0,90 teve conjunta 74.5%, direcional 41.8%, 117 chamadas LLM e tempo médio 1.10 s. O médio teve 89 chamadas LLM. Comparar qualidade, chamadas e tempo em conjunto antes de atribuir níveis.

Neste recorte, o modo alto não superou o médio na acurácia conjunta. O baixo serve como opção rápida, o médio como referência híbrida e o alto permanece uma opção experimental de revisão por LLM. Os nomes não garantem uma ordem crescente de precisão.

## Diferenças de acurácia direcional

Bootstrap pareado por pergunta, 2.000 amostras; eixos e repetições da mesma pergunta ficam juntos. Comparações exploratórias, sem correção por múltiplas comparações.

| Estratégia | Referência | Partição | Diferença (p.p.) | IC95% (p.p.) |
|---|---|---|---:|---:|
| atual_alto | atual_medio | calibration | -2.5 | [-12.0; 6.6] |
| atual_alto | atual_medio | test | -20.8 | [-35.1; -6.8] |
| atual_baixo | atual_medio | calibration | 2.5 | [-4.2; 8.9] |
| atual_baixo | atual_alto | calibration | 5.0 | [-6.9; 16.7] |
| atual_baixo | atual_medio | test | -1.4 | [-8.0; 3.9] |
| atual_baixo | atual_alto | test | 19.4 | [4.9; 35.7] |
| atual_medio | atual_alto | calibration | 2.5 | [-6.6; 12.0] |
| atual_medio | atual_alto | test | 20.8 | [6.8; 35.1] |
| cascata_0.3 | atual_medio | calibration | 2.5 | [-0.6; 6.2] |
| cascata_0.3 | atual_alto | calibration | 5.0 | [-5.6; 15.6] |
| cascata_0.3 | atual_medio | test | -1.4 | [-4.7; 0.0] |
| cascata_0.3 | atual_alto | test | 19.4 | [6.1; 32.4] |
| cascata_0.7 | atual_medio | calibration | -3.1 | [-8.6; 2.4] |
| cascata_0.7 | atual_alto | calibration | -0.6 | [-8.5; 8.0] |
| cascata_0.7 | atual_medio | test | -6.9 | [-18.3; 1.6] |
| cascata_0.7 | atual_alto | test | 13.9 | [2.5; 26.4] |
| cascata_0.9 | atual_medio | calibration | -4.4 | [-11.6; 2.1] |
| cascata_0.9 | atual_alto | calibration | -1.9 | [-9.7; 6.4] |
| cascata_0.9 | atual_medio | test | -13.9 | [-26.6; -1.4] |
| cascata_0.9 | atual_alto | test | 6.9 | [-3.1; 18.3] |
*Falhas = execuções com motivo de falha de provedor (inclusive recuperada por fallback) ou timeout.

## Limites de interpretação

Os limiares alteram somente level_confidence_min. Relevância, margem de direção, modelos e rubricas permanecem fixos. Baixo e alto mantêm as estratégias atuais. O braço atual_medio também representa a cascata no limiar 0.50.

Escolher limiares usando apenas calibração e conferir a escolha no teste reservado. A base é pequena, já usada no desenvolvimento das rubricas e não mede generalização para textos reais. Uma única repetição não demonstra estabilidade. Confiança JEV não é probabilidade empírica de acerto. Variações entre chamadas e condições de rede podem quebrar a monotonicidade observada. Limiares maiores não garantem maior acurácia.

Não foi alterada a configuração de produção nem atribuídos novos níveis automaticamente.

## Como repetir

Na raiz do projeto, com o ambiente Python da API:

```powershell
.\app\api\.venv\Scripts\python.exe app/api/scripts/benchmark_reasoning.py
.\app\api\.venv\Scripts\python.exe -u app/api/scripts/benchmark_reasoning.py --live --repeats 2
.\app\api\.venv\Scripts\python.exe app/api/scripts/benchmark_reasoning.py --summarize PASTA_DA_EXECUCAO
```

Sem --live, o script só mostra o plano. --summarize recalcula o CSV e o relatório sem API. --live usa as credenciais locais JEV/Maritaca e consome chamadas. --thresholds, --limit, --max-http-calls e --output permitem limitar a execução.

São gerados somente três arquivos por execução: results.jsonl (resultados, aquecimento e metadados), summary.csv e report.md. O JSONL preserva inclusive rodadas incompletas; o resumo usa somente rodadas iniciais completas quando disponíveis.
