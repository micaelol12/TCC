# Plano de investigação: similaridade semântica e avaliação de textos no 8values

**Data:** 16 de setembro de 2026. **Revisão de escopo:** primeira fase sem nova anotação manual de documentos, conforme preferência do pesquisador. **Natureza:** parecer metodológico e plano de pesquisa; não corresponde à execução de novos experimentos.

**Material examinado:** código e saídas persistidas do [TCC.ipynb](</C:/Users/User/Desktop/Micael/code/TCC/TCC.ipynb>), triagem dos 24 PDFs de `artigos/`, leitura aprofundada das fontes pertinentes e pesquisa complementar em fontes acadêmicas primárias. Há 22 documentos distintos: o artigo ACL 2023 e o relatório de Schwartz aparecem duplicados. As métricas citadas foram extraídas das tabelas salvas em [evidencias_notebook.json](</C:/Users/User/Desktop/Micael/code/TCC/analises/evidencias_notebook.json>).

**Limite da auditoria:** `questions.json`, `ideologies.json`, os documentos de entrada e `d0_manual_validation_avaliado.csv` são carregados de caminhos do Google Drive e não estão nesta cópia local. Não reexecutei os modelos nem verifiquei a anotação original. As conclusões empíricas abaixo descrevem as saídas salvas; a ordem de execução e a correspondência entre todas as variáveis globais não puderam ser reconstituídas integralmente. Os índices de células mencionados começam em zero.

## 1. Parecer e pergunta de pesquisa

Minha recomendação é **manter a similaridade como mecanismo de representação e recuperação de evidências, mas aprender e avaliar separadamente a posição em relação a uma afirmação**. Antes de aumentar o número de descrições dos polos ou trocar de encoder, é necessário melhorar a definição do alvo e usar referências de avaliação que já existam ou expectativas controladas. A criação de um corpus documental anotado fica fora desta fase.

O notebook já contém descobertas úteis. A dificuldade está em reunir os experimentos numa pergunta cumulativa: **quais mudanças melhoram a representação de posição em referências existentes e a robustez do sistema, antes de validar sua acurácia em documentos brasileiros?**

A hipótese central é que parte dos erros atribuídos à similaridade decorre de três problemas distintos: representação predominantemente temática, transferência de limiares entre domínios e agregação de evidências sem posição identificável. Essa é uma interpretação dos resultados locais, apoiada pela distinção entre contexto e posição de [Chen, Walker e Saligrama (2023)](https://aclanthology.org/2023.acl-long.530/) e pela formulação de stance como relação entre texto e alvo de [Mohammad et al. (2016)](https://aclanthology.org/S16-1003/). Ainda precisa ser testada no seu corpus.

Preservaria a escolha do **Sabiá como comparador gerativo fixo**. O objetivo desta investigação é desenvolver uma alternativa baseada em representações semânticas e modelos discriminativos, com evidência própria de desempenho. Concordância com o Sabiá é uma medida secundária. Nesta fase, a avaliação de acerto usa rótulos de corpora existentes; o questionário e os testes controlados fornecem outras evidências, com limites diferentes. Documentos reais sem gabarito entram para análise de comportamento, não para estimar acurácia.

## 2. O que os experimentos existentes permitem concluir

### 2.1 Família B: há sinal de posição, mas a representação e a transferência são frágeis

As seguintes médias são calculadas sobre os quatro eixos, com o mesmo peso por eixo, a partir das saídas persistidas. Elas **não** são acurácias de respostas de documentos às 70 perguntas.

| Método | Conjunto avaliado | Balanced accuracy macro |
|---|---|---:|
| B0, descrição única | Sinal do `effect` das afirmações do 8values | 0,568 |
| B1, centroides de várias âncoras | Mesmo conjunto | 0,527 |
| B2, mediana das direções pareadas | Mesmo conjunto | 0,570 |
| C3, NLI com âncoras | Mesmo conjunto | 0,627 |
| C5, NLI com contradição | Mesmo conjunto | 0,616 |

**Evidência:** células 194, 200, 205, 294 e 307. Os tamanhos por eixo são 24, 22, 33 e 37, respectivamente para diplomático, econômico, sociedade e Estado; são 116 relações afirmação–eixo derivadas das 70 afirmações, não 116 textos independentes.

Multiplicar descrições em B1 não trouxe melhora uniforme. B2 melhora o econômico em relação a B0, mas o eixo Estado fica em balanced accuracy de 0,500. Isso desaconselha uma nova sequência extensa de variações de âncoras antes de corrigir o protocolo.

B3a mede sensibilidade a formulações próximas das próprias âncoras. B3b é mais exigente, mas ainda tem somente **oito pares por eixo**, construídos para o diagnóstico. B4 respeita os pares ao calibrar por leave-one-pair-out, o que é uma boa escolha; entretanto, oito pares não sustentam uma conclusão ampla de generalização. No eixo Estado, B1 passa de 0,500 em B3b para 0,8125 após calibração B4, mas B5, que transfere esse limiar para as afirmações do 8values, registra balanced accuracy de aproximadamente 0,498. **A calibração ajudou naquele conjunto; sua portabilidade não foi demonstrada.**

Há ainda uma equivalência algébrica que reduz a quantidade de hipóteses realmente diferentes. Para polos normalizados `p` e `n`, direção `u=(p−n)/||p−n||` e centro `c=(p+n)/2`:

\[
c^T u=\frac{\|p\|^2-\|n\|^2}{2\|p-n\|}=0.
\]

Logo, `(x−c)ᵀu=xᵀu`: a subtração do centro geométrico em B0/B1/B2 não aprende o ponto de neutralidade. B4, ao aprender um limiar com rótulos, é que introduz uma fronteira empírica. É uma dedução do código, válida quando os polos têm norma unitária e são distintos, e não um novo resultado de treinamento.

### 2.2 B6 não constitui refutação do artigo de decomposição

A célula 257 afirma que a tentativa demonstra formalmente a não transferência da premissa do artigo. Essa conclusão é mais forte que a evidência disponível.

O B6 ortogonaliza oito descrições temáticas e remove suas projeções do embedding. Já o artigo de Chen et al. aprende componentes de contexto e posição por treinamento, com restrições e perdas; ele não se limita à remoção de uma base fixa. Também discute representações além de GloVe. O resultado local permite dizer: **“a remoção do subespaço temático construído manualmente não melhorou consistentemente esta configuração”**. Não permite rejeitar a decomposição aprendida nem os modelos de embeddings em geral. [Chen et al., 2023](https://aclanthology.org/2023.acl-long.530/)

Eu preservaria B6 como resultado negativo exploratório e reduziria sua prioridade: a reprodução fiel do artigo acrescentaria complexidade antes de existir um benchmark documental suficientemente independente.

### 2.3 Família R: relevância relativa não equivale a evidência suficiente

O R2 calcula, para cada eixo, a similaridade com seu centroide menos a média das similaridades com os outros três. Se `s_a` é a similaridade bruta:

\[
r_a=s_a-\frac{1}{3}\sum_{b\ne a}s_b
=\frac{4}{3}(s_a-\bar{s}),\qquad \sum_a r_a=0.
\]

Portanto, o escore mede **destaque relativo do eixo dentro daquele trecho**. Um texto irrelevante para todos os eixos ainda terá diferenças relativas; um texto pertinente a vários eixos pode ter seu sinal reduzido. Limiar negativo permite várias decisões positivas, mas não elimina esse acoplamento. Esta é uma propriedade matemática de `score_r2`, não uma conjectura sobre o encoder.

O método pode ser útil como atributo auxiliar. Para evidência documental multirrótulo, recomendo comparar quatro decisões independentes de relevância e, sobretudo, relevância para cada afirmação do questionário.

R4 também altera a tarefa: exclui os efeitos intermediários e contrasta `|effect|=10` com `effect=0`. Desempenho melhor nessa seleção não significa melhora sobre a mesma população de R2/R3. Além disso, `effect=0` é um peso nulo no instrumento, não uma anotação humana independente de ausência de relação temática.

### 2.4 Família D: a calibração no domínio é promissora; a generalização permanece aberta

| Eixo econômico, 66 trechos | D0d: limiar vindo do questionário | D0e: calibração entre trechos documentais |
|---|---:|---:|
| Positivos manuais | 16 | 16 |
| Positivos previstos | 65 | 18 |
| Balanced accuracy | 0,510 | 0,856 |
| F1 | 0,395 | 0,765 |
| ROC-AUC | 0,885 | 0,885 |

**Evidência:** células 372 e 377. O ranking permanece igual e a decisão muda. Isso aponta para um problema de transferência da fronteira decisória no eixo econômico, sem provar que apenas um limiar resolverá os demais eixos.

Em sociedade, o D0d tem sete positivos manuais e sete previstos, mas **nenhum verdadeiro positivo**. A igualdade de prevalências não significou identificação correta. O D0e eleva o recall para 0,857, com precisão de 0,240: há uma troca substantiva entre recuperar evidências e incluir ruído.

A função de D0e usa `StratifiedKFold` por linha. O material exibido corresponde a 66 trechos de um documento, e o chunking usa sobreposição. Assim, não há teste de transferência entre documentos, e há risco adicional de conteúdo compartilhado entre as partições. O resultado é uma validação interna de calibração, não validação externa de generalização. Depois, `DOCUMENT_THRESHOLDS` é ajustado sobre todo `d0_external`; aplicá-lo novamente ao mesmo documento é demonstração de ajuste, não novo teste. A literatura sobre vazamento fundamenta a necessidade de separar grupos antes da seleção de modelos. [Kapoor e Narayanan, 2023](https://doi.org/10.1016/j.patter.2023.100804)

### 2.5 Família C e D1: o sinal pode ser praticamente zero e ainda virar posição

`calculate_nli_stance_scores` usa a mediana de cinco diferenças entre probabilidades de entailment. Um trecho que sustenta apenas uma das cinco facetas pode ter essa evidência abafada pelas outras quatro. Isso é uma hipótese causal a testar por ablação, não uma explicação já comprovada.

Na tabela D1, a mediana é 0,000711 no econômico, 0,000667 em sociedade e −0,000132 em Estado. Apesar disso, o código atribui polos por `score > 0`. A concordância entre sinais de âncoras também pode ser alta quando todas as diferenças são minúsculas. Ela não é, por si, confiança calibrada.

D1 usa rótulos humanos de **relevância**, mas suas tabelas não apresentam gabarito humano de **posição**. Portanto, D1 permite inspecionar previsões, mas ainda não estimar sua acurácia de stance.

Finalmente, C5 não ganha de C3 em todos os eixos: no econômico, a acurácia sobe de 0,636 para 0,727; em sociedade, cai de 0,636 para 0,515. Acrescentar contradição ao escore deve permanecer uma ablação controlada.

## 3. Definir exatamente o que será medido

Há dois alvos possíveis, que precisam ser identificados nas tabelas e no texto do TCC:

| Alvo | Unidade | Resultado legítimo |
|---|---|---|
| Posicionamento direto nos eixos | Documento × eixo | Uma escala própria, alinhada conceitualmente ao 8values e validada contra especialistas |
| Responder ao instrumento a partir do documento | Documento × afirmação do 8values | Respostas estimadas às perguntas, depois agregadas pelos pesos do questionário |

**Para seu objetivo, priorizaria o segundo alvo.** A arquitetura ficaria: documento → unidades de evidência → recuperação por afirmação → posição/intensidade → agregação conforme o questionário. A escala direta por eixo permanece como baseline e diagnóstico, sem receber automaticamente o mesmo significado dos percentuais oficiais. A documentação do [8values](https://8values.github.io/) define a pontuação a partir de respostas às afirmações, e a literatura de stance explicita a dependência do alvo. [Mohammad et al., 2016](https://aclanthology.org/S16-1003/)

Exemplo construído para o protocolo, não uma observação do corpus:

| Texto | Assunto tributário | Posição sobre “aumentar a progressividade tributária” |
|---|---|---|
| “Propomos ampliar a progressividade dos impostos.” | Sim | Favorável |
| “Propomos reduzir a progressividade dos impostos.” | Sim | Contrária |
| “O sistema tributário será objeto de estudos.” | Sim | Não identificável |
| “Há argumentos a favor e contra; o plano não adota uma proposta.” | Sim | Discussão sem compromisso assumido |

As duas primeiras frases podem ser muito próximas semanticamente e ter posições opostas. A terceira mostra por que relevância temática é insuficiente. A quarta exige distinguir o discurso do autor de posições apenas citadas.

Na representação interna dos resultados e nos casos controlados, separar: **sem evidência; posição favorável; posição contrária; neutralidade explicitamente sustentada; posições conflitantes; interpretação incerta**. A intensidade forte/moderada só será avaliada se uma fonte já rotulada oferecer uma escala compatível; caso contrário, fica adiada. Essas categorias são metadados analíticos: não precisam virar oito classes finais. Um `neutral` do NLI significa que a hipótese não foi inferida nem contradita; não equivale automaticamente a “neutro” do questionário. [Yin, Hay e Roth, 2019](https://aclanthology.org/D19-1404/)

Também é necessário revisar o alinhamento das âncoras ao instrumento. As âncoras diplomáticas atuais concentram-se em soberania versus cooperação, enquanto a descrição oficial inclui aspectos de força militar e paz. Em sociedade, predominam mudanças versus preservação de costumes, com pouca explicitação de secularismo, ciência e ambiente. Não é preciso aceitar essas escolhas teóricas como universais; é preciso explicitar se o alvo é reproduzir o instrumento ou propor sua revisão. [Descrição oficial dos polos](https://8values.github.io/)

## 4. Como aproveitar a bibliografia já reunida

| Fonte local | Contribuição aproveitável | Limite da transferência para este TCC |
|---|---|---|
| Chen et al., 2023, *Ideology Prediction from Scarce and Biased Supervision*; ACL | Contexto temático e posição podem exigir representações diferentes. | O treinamento proposto não é reproduzido por B6; o resultado não é sobre quatro eixos do 8values em português. |
| Duan et al., 2025, *Constructing Vec-tionaries*; Political Analysis, seções 3–4 | Eixos apoiados em referências validadas e separação entre força, direção e ambivalência. | O estudo usa fundamentos morais e palavras; sua transposição a sentenças políticas é uma adaptação a validar. |
| Kato et al., 2024, *L(u)PIN*; preprint, seções 3–4 e 7 | Selecionar segmentos opinativos antes de projetar embeddings em referências de posição. | Evidência em discursos japoneses e temas delimitados; não demonstra superioridade em português. |
| Carvalho et al., 2024, *Assessing the Alignment…*; Sustainability, seções 3.3–3.4 | Trabalhar com propostas extraídas, alvos concretos e revisão especializada em planos brasileiros. | Similaridade com metas dos ODS mede alinhamento/cobertura; não resolve automaticamente oposição política nem intensidade. |
| Silva e Paraboni, 2023, *Politically-oriented information inference from text*; J.UCS, seções 4–5 | Combinar representações e distinguir rótulos do texto de rótulos do autor; apresenta uso do BRmoral. | Ganhos dependem da tarefa; esquerda/direita e fundamento moral não são rótulos intercambiáveis com os eixos do 8values. |
| Figueredo, Mueller e Cajueiro, 2022, *A natural language measure…*; RBCP | Referência brasileira de validação e comparação entre operacionalizações de ideologia. | Classificação de discursos com rótulos dos senadores não equivale a posição explícita de cada trecho. |
| Parschan e Jakob, *Computational Measurement…*; manuscrito aceito local e publicação posterior | Organiza famílias de métodos e demanda comparação sobre bases comuns. | É revisão metodológica, não ranking que escolha um vencedor para seu corpus. |
| Németh, 2023, revisão de escopo; JCSS | Explicita limites de contexto, domínio e operacionalização em estudos de polarização. | Não oferece uma técnica pronta de classificação. |

As fontes estão identificadas com links na seção 10. A seleção de propostas/opiniões pode ser feita por anotação, regras ou classificador discriminativo; o uso de estudos com LLM não obriga a inserir geração de texto na inferência.

O **Dicionário de Política** de Bobbio, Matteucci e Pasquino é útil para a definição conceitual dos eixos. Não o trataria como banco automático de âncoras nem como gabarito dos pesos do 8values. Wordfish, redes de seguidores e perfis de personalidade podem fundamentar comparações conceituais, mas têm alvos diferentes e não seriam a próxima prioridade computacional.

## 5. Plano revisado: investigar sem anotar documentos

**Escopo adotado:** não criar rótulos manuais para documentos ou seus trechos. É possível reutilizar corpora já anotados por terceiros, o gabarito operacional do questionário e os testes já existentes. Não será necessário pedir ao pesquisador que revise uma nova coleção de exemplos sintéticos. A análise de D0d/D0e acima permanece como evidência histórica do notebook, mas sua anotação não é requisito para executar este plano.

A consequência metodológica é delimitar a alegação: podemos comparar capacidade de representar posição, reproduzir convenções do instrumento e medir robustez. **A acurácia da leitura de documentos políticos reais permanece não estimada sem referência independente adequada.** Isso não impede uma primeira fase de pesquisa útil.

### Etapa 0 — Separar as fontes de evidência

| Fonte | Uso nesta fase | O que não permite concluir |
|---|---|---|
| 70 afirmações e pesos do 8values | Concordância com a orientação codificada pelo instrumento | Acerto da resposta de um documento a cada pergunta |
| B3a/B3b já existentes | Diagnóstico de direção e ordenação de pares | Generalização para linguagem política natural |
| BRmoral ou UstanceBR, com rótulos existentes | Avaliação externa de posição perante alvos, no domínio do corpus | Validação automática dos quatro eixos ou das cinco intensidades |
| ASSIN 2 | Verificação auxiliar de similaridade e inferência em português | Validação específica de posição política |
| Testes controlados | Invariância, mudanças direcionais e recuperação de passagens inseridas | Desempenho em documentos naturais completos |
| Documentos reais sem rótulos | Estabilidade, sensibilidade, custo e comparação com Sabiá | Acurácia, F1 ou recall de evidências verdadeiras |

O `effect` identifica a contribuição prevista de concordar com uma afirmação, não uma verdade universal sobre ideologia. Sua magnitude não rotula intensidade textual, e `effect=0` não prova irrelevância semântica. Usar suas convenções explicitamente como alvo operacional. [8values](https://8values.github.io/)

As 70 questões e B3 já orientaram experimentos: devem ser tratados como **material de desenvolvimento conhecido**. Dividi-los agora ajuda a organizar comparações, mas não desfaz a exposição anterior nem produz um teste cego. Para evidência adicional, reservar um teste de corpus externo que ainda não tenha orientado decisões.

Na reutilização de bases, verificar acesso, licença, rótulos disponíveis, identificadores de autoria e partições antes de escolher a fonte principal. A existência dos artigos foi confirmada; o acesso integral às bases não foi realizado nesta revisão. Priorizar BRmoral se os textos e rótulos de posição por tema estiverem disponíveis; usar UstanceBR como alternativa. Isso é seleção de recurso existente, não coleta/anotação de novos documentos. [Silva e Paraboni, 2023](https://doi.org/10.3897/jucs.96652); [Pereira et al., 2026](https://doi.org/10.1007/s10579-025-09896-3).

### Experimento 1 — Verificar se os embeddings já separam posições

**Consolidar primeiro o que já existe, sem treinamento do encoder.** Fixar o E5 atual, os dados e as âncoras existentes. Reunir B0/B2 e as calibrações B4/B5 numa comparação comum; não repetir execuções que já respondem à mesma pergunta. A diferença de similaridades pode servir como forma interpretável do baseline, mas, com os mesmos polos normalizados, ela é proporcional à projeção B0 e não constitui uma técnica independente. Reexecutar apenas configurações alteradas ou resultados cuja reprodução seja necessária.

Avaliar duas tarefas separadamente: orientação das afirmações em relação aos eixos; e posição de textos em relação ao alvo nos dados públicos. Manter tabelas distintas: os rótulos dessas tarefas não são intercambiáveis. Quando um texto é avaliado por orientação ideológica, não usá-lo também como sua própria âncora. Na tarefa relacional, fornecer a afirmação como alvo é legítimo, mas não fornecer uma resposta que revele o rótulo.

Nos pares mínimos, medir ordenação, separação entre lados e decisão absoluta. Se a ordenação for razoável e o sinal absoluto ruim, há motivação para calibrar a fronteira. Se nem a ordenação responder à oposição, a prioridade passa à representação. Essa decisão aproveita diretamente a diferença entre B3 e B4 já observada.

Fazer uma única verificação dos prefixos do E5: `query:` em comparações simétricas; `query:`/`passage:` na recuperação. Os escores de cosseno elevados não são probabilidades. [Ficha do E5](https://huggingface.co/intfloat/multilingual-e5-base)

**Métricas:** balanced accuracy e MCC para direção, acerto de ordenação por par e resultados por eixo/alvo. Calibrar com rótulos do domínio de desenvolvimento e declarar a transferência: um limiar aprendido no questionário ou em tweets não pode ser chamado de limiar validado para planos de governo.

**Fundamentação:** a separação entre tópico e posição motiva o diagnóstico; dificuldades com negação e antônimos justificam os contrastes controlados. [Chen et al., 2023](https://aclanthology.org/2023.acl-long.530/); [Vahtola et al., 2022](https://aclanthology.org/2022.blackboxnlp-1.20/).

### Experimento 2 — Testar supervisão com rótulos já disponíveis

**Executar depois do diagnóstico, sem corpus próprio anotado.** Escolher uma base pública principal e comparar apenas três configurações: o baseline sem ajuste; encoder congelado com classificador regularizado; mesmo encoder com ajuste contrastivo, mantendo a cabeça e o protocolo comparáveis.

Treinar um modelo compartilhado condicionado ao alvo. Usar a posição anotada no texto, quando disponível, em vez de atribuir a todos os textos a ideologia autodeclarada do autor. Um alvo como uma pessoa ou instituição em UstanceBR não equivale automaticamente a uma proposição normativa do 8values: a passagem de um domínio ao outro será transferência exploratória.

Positivos contrastivos devem preservar alvo e posição; negativos difíceis são posições contrárias sobre o mesmo alvo. Separar treino/desenvolvimento/teste antes de construir os pares, mantendo textos do mesmo autor e duplicatas no mesmo grupo. Se o corpus não permitir controlar esse agrupamento, registrar a limitação. Não aproximar indiscriminadamente todos os rótulos “favorável” de assuntos diferentes. [SimCSE](https://aclanthology.org/2021.emnlp-main.552/); [SetFit](https://arxiv.org/abs/2209.11055).

Manter o teste público fora do treinamento e da seleção de parâmetros. Se forem criadas partições agrupadas diferentes das oficiais, apresentar resultados próprios sem compará-los diretamente como se fossem o mesmo benchmark publicado. Após escolher o modelo no desenvolvimento externo, aplicar a configuração congelada ao questionário conhecido e aos documentos sem rótulos.

**Critério de continuidade:** melhora no teste externo e comportamento coerente nos diagnósticos. Ganho no corpus público evidencia utilidade naquele domínio; a aplicação aos planos continua exploratória. Não treinar 70 classificadores nem converter rótulos de esquerda/direita de uma base em quatro eixos sem justificativa.

### Experimento 3 — Reformular o NLI e testar o sistema completo de forma controlada

Usar o mDeBERTa já presente como comparador: trecho como premissa, proposição específica como hipótese. Comparar com o esquema atual de âncoras amplas, sem trocar simultaneamente modelo, segmentação e agregação. Classificação por inferência tem precedente em [Yin et al. (2019)](https://aclanthology.org/D19-1404/).

Nos corpora que possuam rótulos compatíveis, medir acerto. Nos exemplos sem rótulo humano, medir apenas respostas esperadas por construção ou consistência. Probabilidade de entailment não representa intensidade de concordância; `neutral` não equivale ao centro político. A calibração/abstenção pode ser estudada nos dados públicos, mas sua garantia de erro não se transfere automaticamente para documentos.

Para testar recuperação sem anotar documentos, criar pequenos contextos artificiais a partir de passagens já rotuladas, registrando os offsets da passagem inserida. Acrescentar distratores de origem conhecida e medir a posição dessa passagem no ranking. Uma passagem contra a proposição continua relevante. **Recall da passagem inserida** é mensurável; recall de todas as evidências verdadeiras do contexto não é, se os distratores não tiverem sido rotulados exaustivamente.

Para geração automática, preferir templates de escopo limitado cujo comportamento seja definido pela construção. Não inverter arbitrariamente o rótulo ao inserir “não”, nem atribuir sinal oposto a toda frase contrária: rejeitar um polo pode deixar a posição indeterminada. Reformulações livres feitas pelo Sabiá serão dados sintéticos/pseudorrótulos; sem revisão, sua correção não está assegurada. Concordância de dois modelos também não cria um gabarito independente.

O princípio de testar invariâncias e alterações direcionais é inspirado em [CheckList, Ribeiro et al. (2020)](https://aclanthology.org/2020.acl-main.442/). A montagem de contextos é uma proposta diagnóstica para este projeto, não reprodução de um benchmark validado de documentos políticos.

## 6. Aplicação aos documentos reais sem anotação

Congelar as configurações escolhidas nas etapas anteriores e aplicá-las aos documentos disponíveis. Preservar passagens, offsets, escores e origem das decisões para que os resultados possam ser examinados futuramente. Não exigir revisão manual para concluir esta fase.

| Verificação automática | Resultado esperado ou hipótese | Limite |
|---|---|---|
| Mudança de espaços e formatação sem alterar conteúdo | Saída aproximadamente invariável | Estabilidade não comprova correção |
| Duplicação exata de uma passagem | Após deduplicação, a posição por item não deve ganhar peso adicional | A expectativa corresponde à política de agregação adotada |
| Permutação de unidades independentes | Baixa variação quando a agregação foi definida como independente da ordem | Não permutar passagens com anáforas ou dependência discursiva e presumir equivalência |
| Duas segmentações predefinidas | Quantificar variação e identificar eixos frágeis | Não escolher a mais “correta” sem referência |
| Sabiá com configuração fixa | Medir concordância por item/eixo e desacordos | Concordância mede proximidade ao comparador |
| Tempo, memória, tokens e número de pares NLI | Caracterizar custo e truncamento | Eficiência deve acompanhar qualidade nos testes rotulados |

O Sabiá permanece como referência comparativa. Se produzir pseudorrótulos de treinamento, avaliar o modelo treinado em teste público independente; concordância com o próprio professor mede sua reprodução. Não é necessário rotular todos os documentos com o Sabiá para iniciar a investigação.

D0d/D0e podem ser discutidos como resultados anteriores. A fase atual não depende de obter ou ampliar aquele CSV manual. Também não substituirá o gabarito faltante por partido, reputação de candidato ou posição que “parece correta”. A distinção entre texto e autor é discutida por [Silva e Paraboni (2023)](https://doi.org/10.3897/jucs.96652).

## 7. Métricas, agregação e limites de interpretação

Usar macro-F1/balanced accuracy nas bases com rótulos compatíveis; acerto de ordenação nos pares existentes; satisfação de propriedades nos testes controlados; variação e concordância nos documentos reais. Não reunir essas medidas em uma única “acurácia geral”. Para ASSIN 2, usar métricas de STS e entailment conforme a tarefa; seus rótulos entailment/none não fornecem uma classe explícita de contradição política. [ASSIN 2](https://sites.google.com/view/assin2/english)

Intervalos de comparação devem respeitar autoria, família textual ou pergunta de origem, conforme a unidade disponível. Repetir treinamentos estocásticos com sementes fixadas e limitar a seleção de parâmetros ao desenvolvimento. Testes já examinados não recuperam independência ao serem renomeados. [Kapoor e Narayanan, 2023](https://doi.org/10.1016/j.patter.2023.100804); [Dror et al., 2018](https://aclanthology.org/P18-1128/).

**Adiar a validação de cinco intensidades** se não houver uma base existente com escala compatível. Primeiro estudar direção e ausência de inferência. Não inventar limiares de intensidade a partir do cosseno ou do `effect`. CORAL permanece como opção futura de modelagem ordinal, não requisito desta fase. [Cao et al., 2020](https://doi.org/10.1016/j.patrec.2020.11.008)

A fórmula do questionário e o tratamento de ausência continuam importantes para as demonstrações. Deduplicar evidências e agregar primeiro por pergunta. Nos documentos sem rótulos, a cobertura abaixo é **cobertura declarada pelo sistema**, não sensibilidade medida contra humanos; o intervalo é condicional às respostas estimadas.

Para respostas estimadas `m_dq` em {−1, −0,5, 0, 0,5, 1}, a fórmula usada pela classe `Quiz8Values` é:

\[
S_{da}=50+50\frac{\sum_q w_{qa}m_{dq}}{\sum_q |w_{qa}|}.
\]

`w_qa` é o `effect` da afirmação no eixo. A magnitude desse peso é uma escolha do instrumento; não é o grau de intensidade identificado no texto. Separar claramente essas duas variáveis.

**Itens sem evidência exigem uma decisão metodológica explícita.** Imputar zero mantém a conta operacional, mas puxa o resultado para 50 e não demonstra centrismo. Recomendo armazenar ausência separadamente e apresentar cobertura ponderada por eixo:

\[
\mathrm{cobertura}_{da}=\frac{\sum_{q\in O_d}|w_{qa}|}{\sum_q|w_{qa}|}.
\]

Para quantificar o que falta, seja `K=Σ_observados w m`, `U=Σ_não observados |w|` e `M=Σ_todos |w|`. O intervalo algébrico compatível com respostas desconhecidas é:

\[
\left[50+50\frac{K-U}{M},\;50+50\frac{K+U}{M}\right].
\]

Esse intervalo é uma **análise de identificação por ausência de dados**, não um intervalo de confiança estatístico. Ele condiciona os itens observados às respostas estimadas e não inclui erros do classificador. Pode ser amplo — informação importante sobre o documento. Já renormalizar só pelos itens observados produz outro estimando; pode ser exibido como escore condicional, sem chamá-lo de pontuação integral do quiz.

Além da pontuação, relatar cobertura e conflito entre evidências. A motivação para não reduzir tudo a uma média aparece na distinção entre força, valência e ambivalência de [Duan et al. (2025)](https://doi.org/10.1017/pan.2025.6). As fórmulas acima são propostas específicas para este protocolo, derivadas da pontuação do notebook.

## 8. Ordem prática e entregas

| Ordem | Trabalho | Entrega |
|---|---|---|
| 1 | Consolidar B0/B2, margem de similaridade e calibração no mesmo protocolo | Tabela comparável de direção e ordenação, com origem dos rótulos |
| 2 | Verificar acesso a BRmoral/UstanceBR e fixar as partições de uma base principal | Avaliação externa reutilizando anotações existentes |
| 3 | Comparar encoder congelado e ajuste contrastivo; NLI como comparador | Ganhos e perdas atribuíveis a poucas mudanças |
| 4 | Aplicar configurações congeladas a contextos controlados e documentos reais | Robustez, custo, cobertura estimada e concordância com Sabiá |

Uma primeira rodada pode ser organizada em quatro semanas, uma por etapa, dependendo do acesso aos dados e dos recursos computacionais. É uma estimativa de planejamento, não prazo garantido. Se a base pública estiver indisponível, executar diagnósticos e aplicação exploratória sem alegar que isso substitui a avaliação externa.

**Próximo experimento novo recomendado:** depois de verificar acesso e rótulos, comparar E5 congelado com e sem classificador treinado em uma base pública de posição perante alvos. Usar B3/B4/B5 como diagnóstico já disponível para interpretar os resultados. A finalidade é decidir entre melhorar a fronteira de decisão e adaptar a representação, sem retomar a proliferação de âncoras.

Salvar por execução: versões dos dados e modelos, origem do rótulo (`instrumento`, `corpus_publico`, `construcao_controlada`, `pseudorrotulo` ou `sem_rotulo`), partições, configurações, previsões, sementes e custo. Para casos sintéticos, registrar ainda template, gerador e exemplo de origem, mantendo toda a família na mesma partição.

Um encoder novo, dependências sintáticas, resumo gerativo antes do embedding e reprodução integral de B6 ficam em segunda prioridade. Dados públicos tornam o ajuste supervisionado possível sem anotação própria, mas não justificam abrir todas essas alternativas ao mesmo tempo.

## 9. Contribuição científica possível nesta fase

A pergunta ajustada é: **“Quais estratégias de representação e calibração melhoram a identificação de posição em referências existentes e a robustez de uma avaliação textual baseada no 8values, sem nova anotação documental?”**

As entregas são uma comparação controlada, diagnóstico das falhas de oposição/negação e aplicação exploratória aos documentos. A melhora pode ser demonstrada onde há gabarito existente; nos planos de governo, as conclusões ficam restritas a comportamento, estabilidade e concordância entre métodos.

A anotação manual de documentos é uma possibilidade posterior, fora do escopo atual. Uma base documental externa com rótulos realmente compatíveis também poderia cumprir esse papel, caso seja encontrada. Nenhuma etapa agora exige que o pesquisador crie essa base.

O Sabiá mantém seu lugar de comparador. Sua estabilidade e eventual proximidade aos resultados não validam sozinhas o sistema semântico. O estudo de [Benoit et al. (2026)](https://doi.org/10.1111/ajps.70050) ajuda a distinguir comparação entre modelos de validação substantiva, sem fornecer resultados específicos para o Sabiá.

## 10. Referências e trilha de leitura

### Fontes locais centrais

1. **Chen, C.; Walker, D.; Saligrama, V. (2023).** *Ideology Prediction from Scarce and Biased Supervision: Learn to Disregard the “What” and Focus on the “How”!* ACL, pp. 9529–9549. Artigo de conferência. [Publicação](https://aclanthology.org/2023.acl-long.530/). Arquivos locais: `2023.acl-long.530.pdf` e `Ideology Prediction from Scarce and Biased Supervision.pdf`, idênticos. Leitura prioritária: seções 3–4.
2. **Duan, Z. et al. (2025).** *Constructing Vec-tionaries to Extract Message Features from Texts: A Case Study of Moral Content.* Political Analysis, 33, 425–445. [DOI](https://doi.org/10.1017/pan.2025.6). Arquivo local de mesmo título. Leitura prioritária: seções 3–4 e discussão. A [errata](https://doi.org/10.1017/pan.2025.9) corrige afiliações e financiamento, não as técnicas discutidas aqui.
3. **Kato, K.; Purnomo, A.; Cochrane, C.; Saqur, R. (2024).** *L(u)PIN: LLM-based Political Ideology Nowcasting.* Preprint arXiv, sem assumir revisão por pares. [Registro](https://arxiv.org/abs/2405.07320). Arquivo local: `LLM-based Political Ideology Nowcasting.pdf`. Leitura: metodologia e limitações.
4. **Carvalho, S. A. et al. (2024).** *Assessing the Alignment of Brazilian Local Government Plans with the United Nations’ Sustainable Development Goals.* Sustainability, 16, 10672. [DOI](https://doi.org/10.3390/su162310672). Arquivo local: `Assessing the Alignment of Brazilian Local Government Plans.pdf`. Leitura: seções 3.3–3.4.
5. **Silva, S. C.; Paraboni, I. (2023).** *Politically-oriented information inference from text.* Journal of Universal Computer Science, 29(6), 569–594. [DOI](https://doi.org/10.3897/jucs.96652). Arquivo local de mesmo título. Leitura: seções 3–5, especialmente BRmoral e distinção texto/autor.
6. **Figueredo, F. C.; Mueller, B.; Cajueiro, D. O. (2022).** *A natural language measure of ideology in the Brazilian Senate.* Revista Brasileira de Ciência Política, 37, e246618. [DOI](https://doi.org/10.1590/0103-3352.2022.37.246618). Arquivo local: `A natural language measure.pdf`.
7. **Parschan, P.; Jakob, C.** *Computational measurement of political positions: a review of text-based ideal point estimation algorithms.* Manuscrito aceito disponível na pasta; versão publicada em Quality & Quantity, 2026. [DOI](https://doi.org/10.1007/s11135-025-02500-4). Arquivo local: `Computational Measurement of Political Positions.pdf`. Leitura: discussão sobre teoria e benchmarking.
8. **Németh, R. (2023; publicação online em 2022).** *A scoping review on the use of natural language processing in research on political polarization: trends and research prospects.* Journal of Computational Social Science, 6, 289–313. [DOI](https://doi.org/10.1007/s42001-022-00196-2). Arquivo local: `A scoping review on the use of natural language processing.pdf`.
9. **Benoit, K. et al. (2026).** *Using large language models to analyze political texts through natural language understanding.* American Journal of Political Science. [DOI](https://doi.org/10.1111/ajps.70050). Artigo local identificado pelo autor e ano no nome.
10. **Kato, K.; Cochrane, C. (2025).** *KOKKAI DOC: An LLM-driven framework for scaling parliamentary representatives.* Preprint. [Registro](https://arxiv.org/abs/2505.07118). Arquivo local: `KOKKAI DOC.pdf`.

### Pesquisa complementar utilizada

11. **Mohammad, S. et al. (2016).** *SemEval-2016 Task 6: Detecting Stance in Tweets.* SemEval. [Publicação](https://aclanthology.org/S16-1003/).
12. **Vahtola, T.; Creutz, M.; Tiedemann, J. (2022).** *It Is Not Easy To Detect Paraphrases: Analysing Semantic Similarity With Antonyms and Negation Using the New SemAntoNeg Benchmark.* BlackboxNLP, workshop. [Publicação e benchmark SemAntoNeg](https://aclanthology.org/2022.blackboxnlp-1.20/).
13. **Yin, W.; Hay, J.; Roth, D. (2019).** *Benchmarking Zero-shot Text Classification: Datasets, Evaluation and Entailment Approach.* EMNLP-IJCNLP. [Publicação](https://aclanthology.org/D19-1404/).
14. **Gao, T.; Yao, X.; Chen, D. (2021).** *SimCSE: Simple Contrastive Learning of Sentence Embeddings.* EMNLP. [Publicação](https://aclanthology.org/2021.emnlp-main.552/).
15. **Tunstall, L. et al. (2022).** *Efficient Few-Shot Learning Without Prompts.* SetFit; preprint e trabalho no workshop ENLSP, não no evento principal NeurIPS. [Preprint](https://arxiv.org/abs/2209.11055).
16. **Cao, W.; Mirjalili, V.; Raschka, S. (2020).** *Rank consistent ordinal regression for neural networks with application to age estimation.* Pattern Recognition Letters, 140, 325–331. [DOI](https://doi.org/10.1016/j.patrec.2020.11.008).
17. **Fialho, P.; Coheur, L.; Quaresma, P. (2020).** *Benchmarking Natural Language Inference and Semantic Textual Similarity for Portuguese.* Information, 11(10), 484. [DOI](https://doi.org/10.3390/info11100484).
18. **Kapoor, S.; Narayanan, A. (2023).** *Leakage and the reproducibility crisis in machine-learning-based science.* Patterns, 4(9), 100804. [DOI](https://doi.org/10.1016/j.patter.2023.100804).
19. **Ribeiro, M. T. et al. (2020).** *Beyond Accuracy: Behavioral Testing of NLP Models with CheckList.* ACL. [Publicação](https://aclanthology.org/2020.acl-main.442/).
20. **Dror, R. et al. (2018).** *The Hitchhiker’s Guide to Testing Statistical Significance in Natural Language Processing.* ACL. [Publicação](https://aclanthology.org/P18-1128/).
21. **Pereira, C. et al. (2026).** *UstanceBR: a social media language resource for stance prediction.* Language Resources and Evaluation, 60, artigo 14. [DOI](https://doi.org/10.1007/s10579-025-09896-3).
22. **Silva, E. S. N. et al. (2026).** *NorBERTo: A ModernBERT Model Trained for Portuguese with 331 Billion Tokens Corpus.* PROPOR, pp. 183–193. [Publicação](https://aclanthology.org/2026.propor-1.18/).

**Documentação técnica, distinta de evidência acadêmica:** [8values](https://8values.github.io/), [multilingual-e5-base](https://huggingface.co/intfloat/multilingual-e5-base), [mDeBERTa-v3-base-mnli-xnli](https://huggingface.co/MoritzLaurer/mDeBERTa-v3-base-mnli-xnli), [ASSIN 2](https://sites.google.com/view/assin2/english).

**Escopo da busca:** revisão dirigida, não revisão sistemática exaustiva. Foram buscados trabalhos sobre similaridade versus posição, negação, representação contrastiva, calibração/validação, corpus em português e mensuração política. O Firecrawl não iniciou neste ambiente; a busca complementar foi feita pela ferramenta web, e os PDFs locais foram extraídos e conferidos diretamente. Nenhum ganho futuro foi apresentado como resultado já obtido.
