# Rastreabilidade da implementação

## Decisão seletiva usando desenvolvimento

`calibracao_seletiva.py` usa isolamento R4 e probabilidades NLI R7. É ajuste de
limiares, **não calibração probabilística**. Política local pré-especificada:
limiares {0,5; 0,6; 0,7; 0,8; 0,9; 0,95}, margens {0; 0,1; 0,2; 0,3; 0,4},
duas hipóteses NLI. Maximiza cobertura no dev sujeita a acerto empírico ≥80%,
cobertura ≥25% e pelo menos dez aceitos de cada classe verdadeira. Essas metas
não vêm dos artigos e não constituem garantia de risco; são critérios exploratórios.
Empates usam acerto, menor limiar/margem e ordem fixa das hipóteses.

Para avaliar um tema, somente os outros temas do dev escolhem a política. Se
nenhuma opção satisfaz os requisitos, a política se abstém integralmente.
As seleções são persistidas antes de carregar as previsões de teste da rodada
natural, cujo corpus é conferido por hash. O teste já foi consultado, portanto
continua exploratório. Cada tema tem seleção própria; não é um modelo final único.
Relatamos acertos, erros, abstenções, cobertura e acerto condicional, inclusive
ausência de decisões. Não se converte abstenção em neutralidade/intensidade.

## Temas reservados no BRmoral

`temas_reservados.py` usa R3/R4/R6/R7/R8: Silva e Paraboni (2023), §§3–4.1.2,
fundamentam a unidade texto/alvo; prevenção de vazamento R4 orienta preservar
autores/duplicatas. Adaptação local: oito rodadas, cada uma excluindo um tema
de treino e desenvolvimento; o teste usa somente esse tema e autores originais
do teste. C da cabeça é escolhido nos outros temas do dev, grade original,
seed 13. Encoder congelado e batch 1 CUDA; cabeça logística na CPU.

Yin et al. (2019), §3 (R7), motiva duas hipóteses fixadas antes da inferência:
proposição normativa sobre o tema e concordância do autor com essa proposição.
As oito verbalizações estão no protocolo; não alteram os rótulos naturais do
corpus. São adaptações e podem não cobrir todas as nuances do tema. Nenhuma
calibração é feita no teste. Neutros permanecem excluídos pelo protocolo anterior.

O conjunto de teste já foi consultado: esta é avaliação exploratória, não teste
cego novo. O resultado agregado da cabeça reúne oito modelos distintos, cada
um predizendo seu tema reservado; não representa um único modelo final. NLI não
treina e não recebe uma divisão artificial por tema. IC pareado R8 reamostra
componentes de autoria para a diferença entre hipóteses NLI, condicional a este
corpus/split, sem sustentar generalização a todos os temas/documentos.

## Ablação do formato 8values

`format_cases`, R5/CheckList §2, cruza presença de aspas com posição do marcador
de concordância/discordância (antes/depois). São 560 casos em 70 famílias.
Remover aspas **não remove a repetição literal** da proposição: é teste de
superfície, não paráfrase ou texto natural. Rótulos e conteúdo ficam constantes.
R7/Yin et al. §3 motiva uma segunda hipótese NLI, sobre concordância do autor,
comparada com a proposição literal. Essa adaptação foi definida antes da execução
e não é escolhida/calibrada para uso documental a partir destes resultados.
O hash do head é registrado. A comparação é descritiva e pareada por caso;
não tratamos as variações como amostras independentes.

## Transferência comportamental ao 8values

`transferencia_8values.py` aplica R3/R5/R7: Ribeiro et al. (2020), CheckList,
§2, e Yin et al. (2019), §3, citados abaixo. Duas famílias de templates
(concordância/discordância e defesa/rejeição) envolvem a pergunta literal em
uma declaração explícita. São 280 expectativas por construção em 70 grupos,
sem anotação manual ou treino. Não se cria a frase oposta inserindo negação
na proposição; o sinal de `effect` nunca determina o rótulo favor/against.

A cabeça BRmoral e os limiares permanecem congelados: probabilidade máxima
0,7; NLI usa a pergunta literal como hipótese, confiança 0,7 e margem 0,2.
O protocolo é salvo antes da inferência. Macro-F1 binário, cobertura, acerto
incluindo abstenções, acerto condicional, ordenação e acerto de ambos os lados
são diagnósticos distintos. As 280 frases não são observações independentes.
Não se estimam acurácia documental ou cinco intensidades a partir delas.

Este módulo implementa o protocolo de `analises/plano_investigacao_similaridade_semantica.md`.
As referências abaixo são vinculadas às unidades lógicas pelas chaves nas docstrings.
Configuração, serialização e CLI são infraestrutura de reprodução de R4, não métodos
estatísticos atribuídos ao artigo. Fórmulas de cobertura e ausência são derivações
do plano (§7), não resultados publicados por Duan et al.

| Chave | Fonte e trecho conferido | Decisão e adaptação neste projeto |
|---|---|---|
| R1 | Chen, Walker e Saligrama (2023), *Ideology Prediction from Scarce and Biased Supervision*, `artigos/2023.acl-long.530.pdf`, pp. 9531–9532, §§3–4 | Separar tema e posição; preservar B0/B2 como diagnósticos. Não reproduz a decomposição treinada BBBG nem apresenta B6 como refutação. |
| R2 | Duan et al. (2025), *Constructing Vec-tionaries to Extract Message Features from Texts*, `artigos/constructing-vec-tionaries-to-extract-message-features-from-texts-a-case-study-of-moral-content.pdf`, pp. 429–430, §3.1 | Geometria normalizada e separação conceitual de força/direção/ambivalência. Aqui as âncoras são as do notebook, sem otimização vec-tionary e sem interpretação do cosseno como probabilidade. |
| R3 | Silva e Paraboni (2023), *Politically-oriented information inference from text*, `artigos/Politically-oriented information inference from text.pdf`, pp. 575–577, §§3.2 e 4.1.2 | Unidade texto-alvo separada de ideologia autoral; não importar left/right como quatro eixos. Macro-F1, BA e MCC são os diagnósticos previstos no plano; não replicação das tarefas T2/T4 do artigo. |
| R4 | Kapoor e Narayanan (2023), *Leakage and the reproducibility crisis in machine-learning-based science*, [DOI](https://doi.org/10.1016/j.patter.2023.100804); leitura complementar de Dror (R8), §5 | Separação treino/dev/teste, auditoria de autores/duplicatas/famílias, hashes e manifesto. A verificação não detecta todas as paráfrases nem garante independência de tópicos. |
| R5 | Ribeiro et al. (2020), *Beyond Accuracy: Behavioral Testing of NLP Models with CheckList*, [artigo](https://aclanthology.org/2020.acl-main.442.pdf), §2 | Testes de invariância e expectativa por construção. Janelas, deduplicação e contextos com passagem inserida são adaptações locais, não benchmark documental validado. |
| R6 | Tunstall et al. (2022), *Efficient Few-Shot Learning Without Prompts*, [artigo](https://arxiv.org/pdf/2209.11055), §3.1, p. 3; Gao, Yao e Chen (2021), *SimCSE: Simple Contrastive Learning of Sentence Embeddings*, [artigo](https://aclanthology.org/2021.emnlp-main.552.pdf), §4 | Treino em duas etapas (pares + regressão logística), adaptado para pares do mesmo alvo; posições opostas fornecem negativos difíceis. Usa CosineSimilarityLoss do SetFit, **não** a loss InfoNCE do SimCSE. Cabeça L2 idêntica nas duas alternativas supervisionadas; C escolhido no desenvolvimento. |
| R7 | Yin, Hay e Roth (2019), *Benchmarking Zero-shot Text Classification: Datasets, Evaluation and Entailment Approach*, [artigo](https://aclanthology.org/D19-1404.pdf), §3, pp. 3918–3919 | Texto como premissa, alvo como hipótese. Aqui se preserva E/C/N; neutral não é resposta neutra ao questionário. O artigo não valida estes limiares nem os templates políticos portugueses. |
| R8 | Dror et al. (2018), *The Hitchhiker’s Guide to Testing Statistical Significance in NLP*, [artigo](https://aclanthology.org/P18-1128.pdf), §§2–3 e 5 | Comparação pareada e atenção à dependência por autor/documento. IC percentil por componentes de autoria/duplicação/família é uma adaptação explícita; poucos grupos limitam inferência. |

## Decisões operacionais

- B0: projeção na direção normalizada entre polos. Margem de cossenos é proporcional
  a B0 e aparece com nome explícito de equivalência. B2: mediana das projeções pareadas.
- B4: leave-one-pair-out, sem expor os lados do par retido ao ajuste do limiar.
  B5 transfere um limiar ajustado em todos os pares B3b. B3 e questionário continuam
  desenvolvimento conhecido; não são teste externo.
- O E5 recebe `query:` em comparações simétricas e `query:`/`passage:` em recuperação.
  Isso segue a [ficha técnica](https://huggingface.co/intfloat/multilingual-e5-base).
  Espaços são normalizados uma vez; revisões efetivas constam no manifesto.
- No corpus público, apenas `favor`/`against` entram neste primeiro protocolo binário.
  Exclusões de other/neutral precisam ser documentadas pelo importador. Não se cria
  uma classe negativa a partir desses rótulos. Ausência de autoria é um metadado obrigatório.
- Na aplicação documental: 100 palavras/20 de sobreposição versus 160/32;
  top-3 por pergunta, limiar NLI 0,7 e margem E−C de 0,2, fixos exploratórios.
  Top-k não valida relevância absoluta. `incerta` conserva ausência de inferência;
  `sem_evidencia` corresponde à ausência de candidatos; `conflito` exige sinais
  aceitos dos dois lados. Não há detector validado de neutralidade explícita.
- Direção não determina intensidade: `response=null`. `direction_coverage` é a
  cobertura de decisões direcionais declaradas. O quiz só usa respostas em escala
  compatível fornecidas explicitamente; retorna escore com zero imputado,
  escore condicional, cobertura e intervalo de identificação. Não são ICs.
- Duplicação/permutação são verificadas na agregação das evidências. Não se presume
  invariância de segmentação de um texto reordenado com dependências discursivas.
- Comparador Sabiá é importado com modelo/prompt/temperatura fixos e identificado
  por pergunta. Nenhuma chamada paga à API é necessária; concordância não é gabarito.

## Limites deliberados

A execução GPU em placa de 3 GB usa `--batch-size 1 --low-vram`: apenas o
modelo ativo permanece na GPU, e o outro vai para RAM. Essa adaptação de
engenharia ligada à reprodução (R4) preserva pesos, float32 do NLI, prefixos,
segmentação e limiares; não é um novo método científico. Manifestos registram
dispositivo, CUDA e pico de alocação/reserva. A comparação com CPU verifica
diferenças numéricas; mudança de runtime/batch impede atribuir tempos somente
ao hardware. `low-vram` limita inferência, não promete viabilizar treinamento.

Não há cinco intensidades aprendidas, corpus novo anotado manualmente, 70 classificadores,
reescrita por LLM, reprodução de B6 ou seleção de configuração pelo teste externo.
ASSIN 2 é auxiliar opcional do plano e não foi usado como corpus de stance.
O BRmoral original foi obtido em 17/09/2026; os baselines externos podem ser
executados com `--baselines-only`. Essa opção registra uma comparação parcial,
sem permitir alegar ganho empírico do ajuste contrastivo ainda não executado.

## R9 — importação BRmoral e execução parcial

Santos, W.; Paraboni, I. (2019). *Moral Stance Recognition and Polarity
Classification from Twitter and Elicited Text*, §3.1, p.1071.
DOI: https://doi.org/10.26615/978-954-452-056-4_123. Trecho lido: opiniões
elicitadas recebem classes por escores 0/1, 2/3 e 4/5. O artigo descreve uma
versão anterior; os campos da versão 5.10 seguem seu próprio README no ZIP.
Pavan et al., *Morality Classification in Natural Language Text*,
https://doi.org/10.1109/TAFFC.2020.3034050 é a referência solicitada pelo corpus.

`import_brmoral` lê CP1252/semicolon, preserva `sid` como autoria e valida `st.*`
contra `s.*`. Exclui neutral e ausências, registrando contagens. Não usa perfis
demográficos nem orientação política como features/rótulos. O campo histórico
`gun-control` corresponde a porte de armas, conforme exemplos originais e R3;
não se inverte seu rótulo por tradução literal do nome da coluna.

Adaptação de avaliação R4: componentes conexos por autor/duplicata, 64/16/20%
dos grupos, seed 42, sem escolher split por desempenho. Este teste inclui temas
vistos no treino, com autores distintos; não mede generalização para temas novos.
Testes em `test_brmoral.py` verificam exclusões, inconsistência de rótulos,
determinismo e isolamento transitivo; dados artificiais não estimam acurácia.

`external(..., baselines_only=True)` preserva C={.01,.1,1,10}, seleção por macro-F1
no dev e seeds 13/42/77. Apenas embeddings e NLI usam CUDA; a cabeça logística
usa CPU. A comparação fica explicitamente incompleta sem ajuste contrastivo.
O bootstrap compara congelado e sem ajuste por componentes do teste (R4).
