# Implementação e validação do plano de similaridade semântica

Data: 16/09/2026. Plano de origem: `plano_investigacao_similaridade_semantica.md`.

O protocolo está implementado em `investigacao/`, com entrada de leitura dos
resultados em `Investigacao_Similaridade.ipynb`. O `TCC.ipynb` original, que já
continha alterações locais, foi preservado. As referências e adaptações de cada
função estão vinculadas a `investigacao/METODOLOGIA.md`.

## Entregas e estado empírico

| Etapa | Implementação | Execução nesta sessão |
|---|---|---|
| Proveniência e separação dos alvos | Fontes, hashes, revisões, sementes, partições, custos e previsões | Manifestos salvos em `execucoes/` |
| B0/B2/margem e B3/B4/B5 | Âncoras literais extraídas por AST; calibração leave-one-pair-out | E5 real, 70 perguntas, 116 relações pergunta-eixo; B3a e B3b |
| Corpus externo | Contrato texto-alvo e adaptador UstanceBR r3, auditoria de autoria/duplicatas/famílias | README, licença e 12 CSVs verificados; 11.264 registros de IDs/rótulos, sem textos |
| Encoder congelado e ajuste contrastivo | Classificador compartilhado condicionado ao alvo, cabeça L2, dev separado, 3 sementes, pares de treino, IC por grupos | Laço real de treinamento e cabeça testados em fixture pequena; treinamento E5 externo pendente |
| NLI específico versus âncoras | Mesmo mDeBERTa, escores E/C/N preservados; ablação com e sem contradição | Executado nos templates controlados, saídas salvas |
| Recuperação controlada | Inserção com offsets e origem/família, rank/MRR/recall@k da inserção | 8 contextos executados com E5 |
| Aplicação documental | Recuperação por pergunta, evidências/offsets, deduplicação, conflito/abstenção, cobertura | Piloto no texto 6x1, todas as 70 perguntas, duas segmentações |
| Modelo escolhido no dev | Carregamento de seleção congelada e transferência às mesmas evidências | Sem execução empírica: depende do corpus externo |
| Sabiá fixo | Importador por pergunta e verificação de hash documental/modelo/prompt/temperatura | Não executado: não há referência normalizada e verificada nesta sessão |

## Resultados observados

### Diagnóstico E5

Revisão: `d128750597153bb5987e10b1c3493a34e5a4502a`; prefixo `query:` e
normalização de espaços. A média abaixo dá o mesmo peso aos quatro eixos.

| Método | Limiar | BA econômica | BA diplomática | BA Estado | BA sociedade | Média |
|---|---|---:|---:|---:|---:|---:|
| B0 | zero | 0,5556 | 0,6250 | 0,6522 | 0,6611 | 0,6235 |
| B0 | transferido B3b | 0,4573 | 0,6250 | 0,5224 | 0,6611 | 0,5665 |
| B2 | zero | 0,5171 | 0,5000 | 0,4792 | 0,5833 | 0,5199 |
| B2 | transferido B3b | 0,5171 | 0,5000 | 0,5240 | 0,6222 | 0,5408 |

Fonte: `execucoes/diagnostico_e5_20260916/diagnostico_metricas.json`.
As previsões individuais, MCC e matrizes de confusão estão nos JSONs adjacentes.
A margem foi mantida como forma equivalente de B0, não como descoberta independente.

B3b contém oito pares por eixo. B0 ordenou corretamente 8/8, 8/8, 6/8 e 8/8
pares, respectivamente econômico, diplomático, Estado e sociedade. B2 obteve
7/8, 8/8, 4/8 e 8/8. Calibração agrupada melhora alguns sinais absolutos, mas a
transferência não é uniforme. Não usar estes números como acurácia documental.

Não é possível atribuir a diferença frente às saídas históricas somente ao
prefixo: esta execução também explicita normalização de espaços, revisão e
ambiente. O protocolo comum foi reexecutado justamente para remover dependência
do estado global/ordem histórica do notebook. A duração registrada do diagnóstico
(6,33 s) abrange os cálculos após carregar o encoder, não o carregamento.

### Testes controlados

Oito declarações explícitas de apoio/oposição a quatro alvos satisfizeram 8/8
expectativas NLI. Nos oito contextos construídos, recall da passagem inserida
foi 1,0 em @1/@3/@5; todas as inserções couberam em alguma janela. Estes casos
são deliberadamente simples e não demonstram generalização. Os distratores
não têm anotação exaustiva de relevância.

Arquivos: `execucoes/controlados_20260916/`, incluindo `templates_nli.json`,
`contextos.json` e `ablacao_nli.json`. Tempo registrado: 16,23 s, incluindo
carregamento dos modelos. Templates e gerador ficam identificados nos exemplos.

### Documento 6x1

Texto: `content/Escala 6x1.txt`. NLI: mDeBERTa revisão
`8adb042d524ecd5c26d3e3ba0e3fbcf7e2d0864c`, float32. Configuração inicial:
janela de 100 palavras, sobreposição 20, top-3 por pergunta, limiar 0,7,
margem E−C 0,2. Segunda segmentação: 160 palavras/sobreposição 32.

- 49 itens incertos, 14 contrários, 6 favoráveis e 1 conflito.
- 70/70 resultados invariantes à mudança de espaços.
- 70/70 resultados invariantes à duplicação e à ordem **na agregação das evidências**.
- 54/70 estados iguais entre segmentações; 16/70 mudaram (22,9%).
- Cobertura direcional ponderada declarada: 15,4% econômico; 31,1% diplomático;
  35,9% Estado; 17,1% sociedade. Isso não mede recall contra humanos.
- 420 pares NLI únicos, 114.868 tokens NLI contabilizados, sem truncamento;
  238,39 s; RSS final de aproximadamente 3,37 GB, não pico.

O custo de espaços repetidos não aumenta chamadas graças ao cache normalizado.
As decisões contrárias/favoráveis permanecem hipóteses do sistema. Sem gabarito,
não se estimaram acurácia, F1 ou recall documental. A sensibilidade à segmentação
é evidência de fragilidade, não motivo para escolher a segmentação que “parece certa”.

**Intensidade adiada:** direção binária não autoriza atribuir +/-1 como resposta
forte. `response` permanece ausente. A função de pontuação está implementada e
testada, mas a pontuação integral neste piloto continua com intervalo [0,100].
Zero imputado seria 50; isso não demonstra centrismo. `direction_coverage` é
separada da cobertura de respostas em escala compatível.

## Validação de engenharia

Comando: `.venv/Scripts/python.exe -m unittest discover -s tests -v`.
Resultado: **14 testes aprovados**, sem erros ou testes ignorados, registrado em
`execucoes/validacao_testes_20260916.json`.

Cobertura: identidade geométrica; direção nula; métricas conhecidas; folds por
pares; vazamento de autor/duplicata/família; componentes transitivos; pares
contrastivos no mesmo alvo e apenas treino; offsets e deduplicação; estados NLI;
intervalos de ausência; recuperação de passagem contrária; importação do formato
r3; join do comparador por ID; pipeline documental e treinamento real.

O teste de treinamento usa BoW+Dense pequeno e a mesma loss/otimizador/cabeça
para verificar atualização de pesos, limpeza de cache e seleção de C. **Não é
treinamento ou avaliação externa do E5**. O notebook de relatório foi executado
na geração: cinco células de leitura/análise, sem depender de variáveis do TCC.

A primeira execução NLI expôs soma de probabilidades em float16 fora da
tolerância. Corrigiu-se o carregamento e o softmax para float32; o piloto acima
é da execução corrigida. Avisos de depreciação das bibliotecas ficaram visíveis;
não impediram a execução. Versões efetivas: Python 3.14.7, NumPy 2.5.3,
Torch 2.14.0 CPU, Transformers 5.17.0, SentenceTransformers 6.0.1,
scikit-learn 1.9.1.

## Dados externos e pendências objetivas

O [README oficial do UstanceBR](https://docs.google.com/document/d/1BSEkItPbt1plDybsT4fXXgF14hUT0TxyrPh9hcKyUjs/export?format=txt)
foi lido e salvo em `ustancebr_readme.txt`. Ele declara CC BY 4.0 e distribuição
por IDs, exigindo obtenção dos textos via Twitter/X. O ZIP r3 foi baixado e
inspecionado sem extrair arquivos: todos os CSVs têm somente `Tweet_ID;Polarity`.
As contagens, URLs e hash do arquivo estão em `acesso_corpora.json`.

BRmoral foi investigado como primeira preferência. Não se obteve download e
licença verificáveis; a [declaração de disponibilidade de um artigo dos autores](https://www.tandfonline.com/doi/full/10.1080/13614568.2022.2092655)
informa obtenção junto aos autores. Isso não prova indisponibilidade pública.
Não foram enviados pedidos de acesso nem mensagens aos autores.

Faltam, portanto, textos/autoria do corpus para executar a comparação externa,
e saídas Sabiá com configuração/documento identificados para medir concordância.
Nenhum pseudorrótulo substituiu essas referências. A aplicação documental foi
um piloto no arquivo 6x1, não execução de todos os PDFs locais. Os demais arquivos
podem ser processados pelo mesmo comando após conversão explícita para UTF-8.

ASSIN 2 e cinco intensidades permanecem fora desta primeira execução, conforme
seu caráter auxiliar/adiado no plano. Treinar o encoder, selecionar no dev e
reexecutar a transferência não pode ser declarado concluído antes de obter os dados.

## Reproduzir

Consulte `investigacao/README.md`. Os comandos executados foram:

```powershell
python -m investigacao diagnostic --output analises/execucoes/diagnostico_e5_20260916
python -m investigacao documents --text 'content/Escala 6x1.txt' --output analises/execucoes/documento_6x1_20260916 --top-k 3
python -m investigacao.controlados --output analises/execucoes/controlados_20260916
python -m investigacao.relatorio
python -m unittest discover -s tests -v
```

Escolha novos diretórios ao repetir os experimentos. O CLI recusa sobrescrever
execuções. Para usar o interpretador deste projeto, substitua `python` por
`.venv/Scripts/python.exe`. O notebook e o relatório leem os resultados preservados.
# Atualização de acesso e avaliação — 17/09/2026

O impedimento de obtenção do BRmoral descrito no registro original abaixo foi
resolvido. Corpus original v5.10 obtido com licença CC BY 4.0, importador e
partições por autor/duplicata validados, baselines E5/NLI executados na GPU.
Resultados completos: [rodada BRmoral](resultados_brmoral_gpu_20260917.md).
O ajuste contrastivo completo continua pendente por memória de GPU; a seleção
desta rodada está explicitamente marcada como comparação parcial.
