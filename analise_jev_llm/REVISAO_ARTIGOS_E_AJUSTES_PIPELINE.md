# Revisão dos artigos de referência e ajustes da pipeline

**Atualização de foco:** para avaliar a pipeline de pesquisa, use primeiro o [parecer centrado em Pipeline - Passo a Passo.ipynb](REVISAO_PIPELINE_PASSO_A_PASSO.md). Ele detalha os recursos já implementados, reavalia a rodada salva de 70 perguntas e identifica uma inconsistência de preparação reproduzível. As diferenças da API discutidas neste documento são questões de integração; não são limitações internas do notebook.

Data: 29/10/2026. Escopo: referências locais em `tcc`, notebook passo a passo, integração com `TCC.ipynb` e réplica da API.

**Parecer:** a arquitetura JEV → revisão por LLM é uma hipótese de pesquisa coerente e pode ser preservada. O maior ganho agora é tornar a medição e a comparação experimental consistentes. As mudanças mais defensáveis são explicitar o objeto medido, separar ausência de posição de mistura de posições, harmonizar as configurações e validar em textos brasileiros anotados. Resumo por eixo e exemplos balanceados são os dois experimentos novos com apoio mais direto nas referências.

Este parecer não demonstra aumento de acurácia: não houve inferência remota, cobrança de APIs nem alteração do algoritmo. Foram feitos inspeção de código, leitura dirigida das referências e diagnósticos locais com entradas sintéticas. As páginas citadas abaixo são posições no PDF, começando em 1; podem diferir da paginação impressa.

## 1. Referências consideradas e limites da leitura

Foram inventariados e extraídos 23 PDFs da raiz de `tcc`, correspondentes a 22 obras distintas. Os dois arquivos de Schwartz são idênticos, com SHA-256 `4b84ab71727ab37c895e1fd6c59379669de432275ac8a460f9e427d858eea81e`. A coleção contém artigos, revisões, dissertações, relatório e um dicionário; não deve ser apresentada como 23 estudos independentes.

A leitura priorizou problema, método, validação e limitações, com aprofundamento nas obras mais próximas da pipeline. No dicionário de 1.358 páginas, a consulta foi temática, sobretudo aos verbetes Igualdade, Liberalismo e Autoritarismo; não houve leitura integral. Os PDFs legislativos e planos em subpastas são possíveis dados de aplicação, não artigos metodológicos desta revisão. Os DOCX e JSON não foram tratados como publicações científicas adicionais. Não foi feita atualização bibliográfica na internet nem verificação externa do status editorial dos manuscritos.

| Referência local | Contribuição aproveitável | Limite para este TCC |
|---|---|---|
| [Benoit et al., Using large language models to analyze political texts through natural language understanding](<../tcc/American J Political Sci - 2026 - Benoit - Using large language models to analyze political texts through natural language.pdf>) | Resumo por dimensão, escala com âncoras substantivas, exemplos, comparação com especialistas e avaliação de repetibilidade. Pp. 3–8 e 12. | Seus seis temas e referências de especialistas não são os quatro eixos do 8values; o resultado do ensemble não valida JEV ou Sabiá. |
| [Haroon et al., Whose Side Are You On?](<../tcc/Whose Side Are You On.pdf>) | Seleção de demonstrações relevantes e balanceadas por classe; experimento com informação da fonte. Pp. 3–8 e 16. | Notícias e vídeos em outro contexto; metadados podem melhorar o acerto do benchmark e, simultaneamente, induzir atalhos incompatíveis com medir apenas conteúdo. |
| [Kato e Cochrane, KOKKAI DOC](<../tcc/KOKKAI DOC.pdf>) | Filtragem, resumo de posições, padronização do resumo, validação externa e análise temporal. Pp. 9–11. | Pré-print na cópia local; discursos japoneses, embeddings e eixos de controvérsia, com objeto diferente do conteúdo de uma notícia brasileira. |
| [Kato et al., L(u)PIN: LLM-based Political Ideology Nowcasting](<../tcc/LLM-based Political Ideology Nowcasting.pdf>) | Separação de frases opinativas, referências antagônicas e comparação com avaliação externa. Pp. 1–4 e 7. | Filtrar opiniões pode eliminar descrições que a pipeline atual pretende classificar. Referências sintéticas não são rótulos independentes. |
| [Parschan e Jakob, Computational Measurement of Political Positions](<../tcc/Computational Measurement of Political Positions.pdf>) | Distingue geração, captura e agregação da variação textual; orienta validação e transferência entre contextos. Pp. 5–6, 16–17 e 27–31. | Revisão de métodos, não demonstração de superioridade de um pipeline específico. A cópia se identifica como manuscrito aceito. |
| [Duan et al., Constructing Vec-tionaries](<../tcc/constructing-vec-tionaries-to-extract-message-features-from-texts-a-case-study-of-moral-content.pdf>) | Diferencia força, valência e ambivalência; evita reduzir distribuições diferentes à mesma média. Pp. 7–8. | Construtos morais e projeções de palavras; as fórmulas não devem ser transplantadas para 8values como se já fossem validadas. |
| [Chen, Walker e Saligrama, Ideology Prediction from Scarce and Biased Supervision](<../tcc/2023.acl-long.530.pdf>) | Distingue contexto temático e posição; testa transferência para temas e perfis diferentes. Pp. 1–2. | Modelo supervisionado próprio; não comprova que adicionar uma etapa semelhante por prompt terá o mesmo efeito. |
| [Németh, A scoping review on the use of natural language processing in research on political polarization](<../tcc/A scoping review on the use of natural language processing.pdf>) | Discute viés de contexto, gênero, período e governo/oposição e a necessidade de conhecimento de domínio. Pp. 1 e 19. | Polarização, posição e alinhamento com usuário são objetos distintos. |
| [Slapin e Proksch, A Scaling Model for Estimating Time-Series Party Positions from Texts](<../tcc/A Scaling Model for Estimating Time-Series Party.pdf>) | WORDFISH como comparação de escalonamento textual e verificação de robustez. Pp. 1 e 4. | Eixo latente relativo ao corpus; não corresponde automaticamente a quatro eixos fixos nem a uma escala absoluta de 0–100. |
| [Figueredo, Mueller e Cajueiro, A natural language measure of ideology in the Brazilian Senate](<../tcc/A natural language measure.pdf>) | Aplicação brasileira, classificação textual e comparação com WORDFISH e levantamentos. Pp. 11–16. | Rótulos e unidade parlamentar não equivalem à posição de uma proposta; não copiar a divisão aleatória de discursos se o objetivo for novos documentos/autores. |
| [Carvalho et al., Assessing the Alignment of Brazilian Local Government Plans](<../tcc/Assessing the Alignment of Brazilian Local Government Plans.pdf>) | Extração de itens de agenda e comparação semântica de planos com alvos definidos. P. 7. | Similaridade com ODS é afinidade temática; não demonstra apoio, rejeição, intensidade ou oposição ideológica. |
| [Orellana e Bisgin, Using Natural Language Processing to Analyze Political Party Manifestos from New Zealand](<../tcc/Using_Natural_Language_Processing_to_Analyze_Polit.pdf>) | Separa similaridade documental, tópicos e sentimento como análises complementares. Pp. 1–4. | Nenhuma dessas três medidas, isoladamente, substitui posição política num eixo. |
| [Silva e Paraboni, Politically-oriented information inference from text](<../tcc/Politically-oriented information inference from text.pdf>) | Compara representações e combinação de BERT com dependências sintáticas. Pp. 1–2. | Um resultado supervisionado não implica benefício de simplesmente acrescentar análise sintática aos prompts atuais. |
| [Buscemi e Proverbio, Large Language Models’ Detection of Political Orientation in Newspapers](<../tcc/LLM Detection of Political Orientation in Newspapers.pdf>) | Motiva medir discordância entre modelos, em vez de presumir que um LLM sempre arbitra corretamente. P. 1. | Discordância entre LLMs não identifica, por si, qual resposta está correta; não invalida os resultados de outros protocolos. |
| [Sakhawat et al., Political Alignment in Large Language Models: A Multidimensional Audit](<../tcc/comparacao politica modelos.pdf>) | Separa respostas psicométricas do modelo e comportamento de classificação; examina assimetrias e variações de prompt. Pp. 1 e 7–8. | Não autoriza escolher ou corrigir um classificador pela suposta ideologia do modelo. O status editorial não foi verificado. |
| [Patankar, Bose e Khanna, A Bias Aware News Recommendation System](<../tcc/A Bias Aware News Recommendation System.pdf>) | Inspiração para transparência e comparação de notícias do mesmo tema. P. 1. | Sistema de recomendação com resultados preliminares; não oferece validação direta do escore 8values. |
| [Streb e Wiesner, Personality and Political Orientation in Germany](<../tcc/Personality-and-Political-Orientation-in-Germany-A-NLP-based-Analysis-using-Twitter-Data.pdf>) | Exemplo de associação entre linguagem, perfis e múltiplas dimensões políticas. Pp. 1 e 3. | Traços de personalidade inferidos de Twitter e serviço externo não são substitutos para posições expressas em propostas. |
| [Souza, Graça e Silva, Politics on the Web](<../tcc/Politics on the Web.pdf>) | Estima posições brasileiras a partir de relações de seguir perfis. P. 1. | Mede rede de relações, não conteúdo textual; possível triangulação em outro estudo, não rótulo-verdade desta pipeline. |
| [Welter, Método de identificação de padrões em discurso político a partir da descoberta de conhecimento](<../tcc/PEGC0679-D.pdf>) | Organização de dados e discussão da necessidade de validação específica do problema. Pp. 8 e 55. | Identificar padrões discursivos não equivale a validar intensidade ordinal nos quatro eixos. |
| [Santos, Análise de discursos parlamentares na Câmara dos Deputados](<../tcc/ANALISE DE DISCURSOS PARLAMENTARES NA C ´ AMARA DOS DEPUTADOS.pdf>) | Contexto brasileiro e modelagem exploratória de tópicos. P. 6. | Tópico descoberto não determina direção política. |
| [Schwartz, Análise do discurso parlamentar por meio da técnica do processamento de linguagem natural](<../tcc/analise_discurso_schwartz.pdf>) | Exploração e classificação de discursos brasileiros, incluindo comparação PT/PSDB. | Classificar partido não valida o construto 8values. A [segunda cópia](<../tcc/ANÁLISE DO DISCURSO PARLAMENTAR POR MEIO DA TÉCNICA DO PROCESSAMENTO DE LINGUAGEM NATURAL ABORDAGEM ESTATÍSTICA E APRENDIZAGEM DE MÁQUINA.pdf>) não é evidência independente. |
| [Bobbio, Matteucci e Pasquino, Dicionário de Política](<../tcc/Dicionario_de_Politica_Norberto_Bobbio.pdf>) | Fundamentação de conceitos e de suas diferenças: Igualdade p. 607, Liberalismo p. 696, Autoritarismo p. 104. | Um dicionário fundamenta definições; não valida a escolha de eixos bipolares, âncoras de intensidade ou limiares do algoritmo. |

## 2. O que a implementação já resolveu

A revisão anterior em `ANALISE_PIPELINE_JEV_LLM.md` descreve problemas do protótipo antigo. Não se deve reaplicar integralmente seu diagnóstico à versão atual.

Hoje existem:

- Relevância separada da posição e possibilidade de `null`/abstenção.
- Rubricas ordinais compartilhadas entre JEV e LLM; probabilidades não são diretamente convertidas em intensidade no escore final.
- Escalas com snapshot e hash, inclusive com espaçamento numérico configurável.
- Registro de decisões JEV e decisões finais no notebook; diagnósticos JEV também aparecem na API.
- Validação de citações literais do LLM; busca e parecer semântico opcionais.
- Índice ausente quando não há trechos com nível e contagens por alternativa.
- Segmentador por sentenças disponível, com tratamento de referências jurídicas.
- Infraestrutura para testes de sensibilidade, reuso de registros e comparação de escalas.

Esses recursos devem ser preservados. A questão é validar o que medem e garantir que os experimentos usem a mesma configuração.

## 3. Ajustes prioritários

### P0. Explicitar conteúdo político, autoria e uso na comparação com o usuário

**Evidência do código.** `CONTEXTO_POSICAO_POLITICA`, em `app/api/app/polarity.py:795` e na célula de contrato do notebook, pede classificação das posições expressas, incluindo falas de terceiros e definições, sem exigir adesão do narrador. Isso é uma escolha explícita e coerente para classificar conteúdo. Não é evidência de que o autor defenda a posição.

**Implicação.** Uma notícia sobre um projeto conservador pode conter muito conteúdo conservador sem que o jornalista, o veículo ou todo participante mencionado seja conservador. Se o resultado entra numa comparação com preferências pessoais, o produto deve dizer que compara o perfil do usuário com o conteúdo selecionado. Para estimar a posição de um ator, é necessário identificar quais posições são atribuídas a esse ator e como ele as endossa, rejeita ou condiciona.

**Ajuste proposto.** Manter o objetivo atual e acrescentar atribuição auditável quando necessária: `ator`, `tipo_de_enunciado`, `apoio_rejeicao`, `citacao`, `alvo_da_posicao`. Se houver demanda por posição do autor, criar um modo separado e uma anotação separada. Não inverter silenciosamente a regra atual nem reutilizar rótulos de endosso como referência para conteúdo.

A frase inicial de que os textos “apresentam sempre posições políticas de alguém” também merece ablação: sua generalização pode incentivar uma posição onde há apenas tramitação ou informação técnica. É uma hipótese a testar com controles negativos, não um erro semântico demonstrado nesta leitura.

**Base bibliográfica.** A revisão de Parschan e Jakob e a de Németh mostram que ator, gênero e construto importam; L(u)PIN/KOKKAI medem posições de representantes a partir de opiniões, com objeto distinto da interpretação atual da pipeline.

### P0. Evitar que estados diferentes sejam resumidos como uma única centralidade

**Evidência do código.** `SITUACAO_SEM_POSICAO` reúne diagnóstico, descrição sem escolha e combinação dos polos sem predominância. Na agregação, essa categoria contribui com 50. Isso é diferente de irrelevância, que é excluída, mas ainda mistura situações relevantes distintas. Uma posição intermediária explícita também não é necessariamente ausência de posição.

O diagnóstico local confirmou:

| Decisões da escala de nove níveis | Índice A | O que precisa ser preservado |
|---|---:|---|
| `[0, 0]` | 50 | Dois trechos classificados como sem posição |
| `[-4, +4]` | 50 | Dois trechos direcionais opostos e extremos |
| 16 repetições de `0` | 50 | Repetição suficiente para ativar `sufficient_evidence`, sem prova de informação independente |

As contagens atuais já distinguem parte dessas situações. O aprimoramento é torná-las centrais à interpretação, em vez de depender apenas do número ou de rótulos como “Centrista”.

**Ajuste proposto.** Registrar separadamente, conforme a anotação permitir: `relevante_sem_posicao`, `posicoes_mistas`, `posicao_intermediaria_explicita`, `posicao_indeterminada` e `irrelevante`. Informar junto ao índice as proporções A/B, proporção sem posição e dispersão/heterogeneidade. A distribuição de unidades expressa heterogeneidade do texto; não prova ambivalência psicológica do autor.

Há uma variante útil a avaliar: média apenas entre unidades direcionais, lado a lado com a média atual. O notebook já calcula `índice A entre posicionados`. Não substituir uma pela outra sem declarar a mudança de significado. Se nenhuma unidade for direcional, a média direcional fica ausente.

**Base bibliográfica.** Duan et al. distinguem força, valência e ambivalência no domínio moral. A adaptação aqui é conceitual: posição média, presença do tema e coexistência de posições são informações diferentes. Não se propõe copiar suas fórmulas de embeddings para a escala ordinal.

### P0. Harmonizar protocolo, configuração e intervalo entre notebook e aplicação

O estado salvo contém pelo menos três protocolos diferentes:

| Item | Notebook, configuração inicial | Notebook, seção de testes de textos | API, arquivo oficial |
|---|---|---|---|
| Escala | Cinco níveis, `ESCALA_ATUAL` | Nove níveis, substituição explícita | Nove níveis |
| Primitiva ordinal | `choice` | Herda `choice` | `score` |
| Regra | `nivel` | `polo_primeiro` | `nivel` |
| Segmentação | Tokens, alvo 600 | Sentenças, alvo 600 | Tokens, alvo 600 |
| Auditoria semântica/busca | Desligadas | Ligadas | Desligadas |
| Intervalo | Bootstrap de blocos móveis | Mesmo agregador do notebook | Reamostragem independente dos valores válidos |
| Suficiência | Sem corte fixo no resumo atual | Mesmo resumo | Corte de 16 trechos válidos |

As células 2 e 171 do notebook, em índices começando em zero, atribuem valores diferentes a `CONFIG_CHUNKS`. As células 172 e 173 especializam os testes de textos. Isso torna a execução parcial sensível ao estado do kernel. A descrição em `docs/SEGMENTACAO_SENTENCAS.md` não representa sozinha a configuração inicial atualmente salva.

**Reprodução local.** Com a mesma sequência de 23 decisões — dez extremos B, três ausências e dez extremos A — e 2.000 réplicas, semente 42:

- Índice A: **50** em ambos.
- Cobertura: **20/23** em ambos.
- IC95 API: **[30,00; 70,00]**.
- IC95 notebook: **[13,04; 85,71]**.

A diferença está no procedimento e não demonstra que o intervalo mais largo seja mais correto. O notebook preserva sequência e ausências; a API reamostra somente os valores válidos. Para texto sequencial, blocos são uma escolha plausível, ainda dependente de tamanho do bloco e hipótese de amostragem. Em um documento observado integralmente, esses intervalos devem ser descritos como sensibilidade à reamostragem textual, sem promessa de cobertura do verdadeiro posicionamento.

**Ajuste proposto.** Publicar um protocolo-base único e versionado, passado explicitamente para preparação, classificação e agregação. Fazer comparações entre API e notebook com o mesmo snapshot completo, incluindo método de intervalo e sua parametrização. Testar paridade das estatísticas que se pretende declarar equivalentes. Distinguir configurações experimentais por nome, sem redefinir uma variável global compartilhada.

O corte de 16 não tem validação demonstrada pelas referências. Recomenda-se mostrar número de unidades, cobertura, diversidade e distribuição; se o corte for mantido, chamá-lo de regra operacional e avaliar seu comportamento em notícias e trechos curtos. Repetir 16 vezes a mesma informação não cria 16 evidências independentes.

### P0. Criar referência humana independente para o alvo atual

**Evidência disponível.** As 70 perguntas do 8values permitem verificar coerência de direção com o instrumento. Não rotulam intensidade de propostas, atribuição de fala nem qualidade da agregação de documentos. Efeito zero de uma pergunta não é prova semântica de que um eixo seja irrelevante.

`app/api/scripts/benchmark_reasoning.py:95` conta irrelevância como acerto nos efeitos zero para a métrica conjunta. O relatório do próprio script explica essa convenção, mas o nome da métrica, isolado, pode sugerir uma referência de relevância independente que não existe. Convém apresentar esse número como aderência ao mapeamento do questionário.

Existe `tcc/d0_manual_validation_avaliado.csv`, com 66 trechos e quatro colunas de rótulos binários 0/1. Ele pode ser reaproveitado depois de conferir o significado dos códigos, origem e processo de anotação. Sua estrutura atual não documenta direção ordinal, intensidade, ator ou concordância entre avaliadores.

**Ajuste proposto.** Construir um piloto estratificado de aproximadamente 200–300 unidades de documentos diversos, como faixa prática inicial, não cálculo de amostra suficiente. Incluir planos, notícias e legislação se a alegação do TCC abranger esses três gêneros. Para uma conclusão restrita a planos, reservar notícias/leis como teste de transferência.

Dois anotadores devem avaliar independentemente ao menos uma parcela substancial do piloto, idealmente todo ele. Anotar relevância, direção, intensidade quando distinguível, estado misto/sem posição e evidência literal. Registrar discordância antes de adjudicar. Calcular concordância por eixo e tipo de tarefa, inclusive medida apropriada à ordem das categorias. Intensidade pouco confiável entre humanos é sinal para revisar as âncoras ou reduzir categorias.

Separar desenvolvimento, validação e teste por documento e, conforme a alegação, por autor/candidato e período. Trechos vizinhos e paráfrases ficam na mesma partição. Um conjunto de casos difíceis criado durante depuração é útil como regressão, mas não deve ser a única estimativa de desempenho em uso real.

**Base bibliográfica.** Benoit et al. validam suas estimativas em referências externas, reconhecem variação entre especialistas e avaliam repetibilidade; Németh e Parschan/Jakob reforçam a validade contextual. Esses resultados não tornam concordância com outro modelo equivalente a validação humana.

### P1. Tratar segmentação e agregação como decisões de mensuração

Hoje um trecho relevante com nível recebe o mesmo peso de qualquer outro, independentemente de tamanho e número de propostas. Logo, o índice mede a média dos trechos resultantes daquele segmentador. Dividir uma proposta em várias unidades pode aumentar sua influência; reunir posições opostas num chunk pode fazê-las desaparecer como “sem posição”.

**Ajuste proposto.** Comparar primeiro os dois segmentadores já existentes mantendo o alvo de 600. Depois, numa amostra anotada, comparar com parágrafos ou unidades de proposta. Preservar seção, página e offsets; usar título e contexto adjacente para interpretação, sem contá-los repetidamente como evidência.

Usar sentença completa ajuda a preservar negações e referências, mas sentença não equivale necessariamente a proposta. Uma frase pode conter duas posições; vários períodos podem formular a mesma proposta. Não existe tamanho ótimo de 600 tokens demonstrado nos artigos locais.

Para a média, declarar a unidade de peso: proposta, trecho, seção ou extensão de texto. Ponderar por tokens mede ênfase textual e pode privilegiar verbosidade; ponderar por confiança mistura força política com certeza do classificador. Nenhuma dessas mudanças deve ser aplicada como correção automática. Comparar as opções contra o alvo humano correspondente.

### P1. Calibrar o encaminhamento e avaliar se o LLM realmente corrige

Os limiares atuais de relevância, confiança e direção são parâmetros operacionais. Nem a literatura analisada nem o diagnóstico local comprovam que 0,60/0,50/0,20 sejam os melhores valores para esta tarefa.

**Ajuste proposto.** Reutilizar as mesmas respostas JEV para todas as regras candidatas. Escolher limiares na validação, com orçamento declarado, e medir no teste:

- Erro conjunto de relevância/direção, intensidade e abstenção por eixo.
- Erros corrigidos e acertos estragados pelo fallback nos mesmos casos.
- Curva de risco versus cobertura e taxa de encaminhamento.
- Falsos negativos de relevância, incluindo amostra auditada de rejeições de alta confiança.
- Chamadas e tentativas, tokens/uso quando disponíveis, custo efetivo e latências p50/p95.

Auditar apenas os casos incertos pode deixar invisíveis erros confiantes. Amostras selecionadas para auditoria precisam ter sua seleção registrada; não estimar qualidade global diretamente a partir de uma amostra concentrada em casos difíceis.

Comparar JEV isolado, LLM isolado e cascata com as mesmas rubricas, dados e decisões de referência. No benchmark atual, cada braço faz sua própria inferência JEV; isso é adequado para observar execuções independentes, mas não isola perfeitamente o efeito do roteamento. Para a ablação do fallback, partir de uma inferência JEV congelada e preservada.

`polo_primeiro` já existe como experimento. No diagnóstico sintético, com P(A)=0,56, P(B)=0,20 e P(sem posição)=0,24 distribuídos entre as alternativas, o MAP global escolhe o centro e a regra por grupo escolhe A. Isso mostra uma diferença de função de decisão, não prova erro do MAP nem superioridade de agrupar.

Somar probabilidades de categorias de um polo é uma marginalização legítima se a distribuição representar adequadamente as categorias. Ter mais alternativas em um polo não prova, por si, viés; o problema empírico é a validade e calibração das probabilidades produzidas nesta rubrica. Uma ablação posterior pode perguntar diretamente A/B/sem predominância e depois intensidade, contabilizando o custo adicional. Não interpretar uma confiança nativa de Score como equivalente à de Choice ou a uma probabilidade empírica de acerto sem verificação.

### P1. Revisar as âncoras antes de aumentar a resolução

A escala de nove níveis é mais detalhada, mas pode produzir precisão aparente se os avaliadores não distinguirem, por exemplo, leve, moderado e forte. As âncoras atuais associam intensidade ao alcance/profundidade da mudança. Uma proposta abrangente de um governo já privatizado ou já estatizado não tem necessariamente a mesma distância ideológica de uma proposta semelhante em outro contexto. Posição e tamanho da mudança são propriedades relacionadas, mas diferentes.

**Ajuste proposto.** Documentar o que cada nível significa no contexto brasileiro e testar casos-limite humanos. Usar cinco níveis como comparação simples; manter nove como hipótese até demonstrar confiabilidade/validade adicional. A média de valores ordinais é um índice convencionado, não prova de distâncias ideológicas iguais entre níveis; os espaçamentos configuráveis já permitem análise de sensibilidade.

Benoit et al. adotam sete pontos com interpretação substantiva de cada ponto e relatam desempenho pior no protótipo com onze pontos e apenas duas âncoras. Isso favorece âncoras claras, não uma regra universal de sete pontos nem a conclusão de que menos níveis sempre vencem.

Revisar também a composição dos eixos: soberania nacional e disposição militar não são a mesma propriedade; redistribuição e mecanismos de mercado podem coexistir; investimento em tecnologia não basta para indicar progressismo cultural. A rubrica atual já possui ressalvas para soberania setorial, tecnologia e programas públicos; a prioridade é testar sua aplicação e resolver contradições residuais, não simplesmente repetir essas ressalvas.

Os rótulos em `app/shared/src/domain/axisInterpretation.ts` incluem “Comunista”, “Totalitário” e “Anarquista”. Uma evidência restrita sobre um tema não fundamenta automaticamente esses diagnósticos amplos. Preferir apresentação principal pelo eixo e pela rubrica, deixando a classificação ideológica exploratória identificada como tal.

## 4. Experimentos novos mais promissores

### A. Resumo por eixo para planos longos

**O que o artigo demonstra.** Benoit et al., pp. 5–6, usam resumos por dimensão antes da classificação e relatam que retirar essa etapa piorou seus resultados de prototipagem. O protocolo final descrito no corpo usa resumos de 300–400 palavras, sete pontos ancorados, zero/few-shot e ensemble de três sumarizadores por três classificadores. O resultado principal agrega 18 estimativas por documento/dimensão. KOKKAI também usa resumo, e mostra que variação de formato pode introduzir ruído nos embeddings.

**Adaptação proposta, ainda não validada aqui:**

1. Recuperar do plano as passagens pertinentes ao eixo, preservando origem e contexto.
2. Produzir resumo estruturado em português, com propostas, posições opostas, condições e IDs das passagens.
3. Estimar a posição com a mesma rubrica ordinal do comparador granular; permitir ausência de informação.
4. Conferir fidelidade e omissões do resumo contra o original, e comparar a nota com avaliação humana do documento.

Em documentos maiores que a capacidade prática do modelo, uma síntese hierárquica é uma adaptação de engenharia, não reprodução exata do artigo. Manter rastreabilidade até o texto original. Não usar citações do resumo como se fossem citações do documento.

Comparar esse método com a média dos trechos como **estimadores distintos**: um tenta captar a posição global integrada; o outro resume posições locais sob a segmentação escolhida. Não combinar ambos numa média híbrida antes de definir qual estimando interessa.

Começar com um sumarizador e um classificador é viável como piloto, mas não autoriza atribuir-lhe a confiabilidade observada no ensemble de 18 estimativas do artigo. Esse caminho é prioritário para planos completos; em frases curtas pode acrescentar custo e distorção sem benefício.

### B. Exemplos reais balanceados no prompt

**O que o artigo demonstra.** Haroon et al. comparam seleção de exemplos e usam classes balanceadas. Benoit et al. também incluem exemplos com referência externa em suas escalas. Esses exemplos são demonstrações completas texto → decisão, mais informativas que uma lista abstrata de situações.

**Adaptação proposta.** Montar um banco pequeno, independente do teste, com exemplos brasileiros anotados: A, B, sem posição, misto, irrelevante e incerto, além de negação e citação. Comparar prompt atual com um conjunto fixo balanceado. Recuperação dinâmica por similaridade pode vir depois; selecionar só exemplos semelhantes sem balanceamento pode enviesar a decisão para o tema ou polo dominante do banco.

A primeira experiência deve ter orçamento fixo e poucas variações. Manter comparabilidade das rubricas entre JEV e LLM e explicitar quando os exemplos só estiverem disponíveis a um dos métodos. O ganho observado em inglês/notícias não é uma estimativa do ganho esperado em português.

### C. Robustez a nomes, fonte, formato e repetição

Haroon et al. mostram que informação da fonte pode mudar previsões inclusive em conteúdo pouco político; Benoit et al. fazem um teste com nomes partidários removidos. A revisão de Chen et al. evidencia a importância de separar tema e posição.

Testar versões pareadas do mesmo texto: nomes originais/anonimizados, outro partido com conteúdo idêntico, ordem dos polos invertida, paráfrase preservando sentido e descrição técnica sem posição. Anonimizar só quando não remover informação necessária à atribuição ou ao significado. O objetivo é medir dependência indevida de identidade, não presumir que toda diferença seja erro.

O relatório existente `outputs/testes_textos_20261024/analise_estabilidade.md` já identifica textos sensíveis, incluindo mudança de polo e efeito de configurações. Aproveitá-lo para escolher casos de regressão. Como as configurações variam, ele não é teste de repetibilidade com parâmetros fixos nem prova de acurácia da versão atual.

## 5. Evidências e explicabilidade

A validação literal do LLM já recusa paráfrases e exige uma passagem contínua de pelo menos quatro palavras. Isso é útil para rastreabilidade. Confirmar que uma frase existe não confirma que ela sustenta o nível, seja a fala correta ou represente o documento.

As opções `jev_evidence_search` e `semantic_evidence_check` já existem. Não é necessário implementar outra busca semelhante. Antes de ligá-las por padrão, medir custo, cobertura de citações, apoio real à decisão, atribuição e erros de intensidade. Uma segunda avaliação pelo mesmo ecossistema de modelos pode reproduzir o erro inicial.

Para decisões mistas, uma única citação pode ser insuficiente: registrar mais de uma passagem quando houver apoio aos dois polos. Usar offsets globais, identificação de seção/página e versão do texto limpo. Manter separados: validação literal, parecer semântico automático e avaliação humana.

## 6. Protocolo experimental enxuto recomendado

Evitar um produto cartesiano de escalas, segmentadores, modelos, prompts e limiares. A sequência abaixo permite localizar a origem do ganho:

| Etapa | Comparação | O que fica fixo | Critério principal |
|---|---|---|---|
| 1 | Concordância humana e revisão das rubricas | Objeto da medição e unidades | Relevância/direção e intensidade distinguíveis |
| 2 | JEV, LLM e cascata atuais | Mesmos documentos, rubricas, escala e segmentação | Qualidade por eixo, custo e abstenção |
| 3 | Tokens vs. sentenças | Modelo, alvo 600 e regra | Preservação semântica e erro na anotação |
| 4 | Cinco vs. nove níveis | Unidades e protocolo de classificação | Concordância ordinal e ganho substantivo |
| 5 | Sem exemplos vs. exemplos balanceados | Conjunto de teste e orçamento | Ganho pareado e erros por classe |
| 6 | Média granular vs. resumo por eixo | Documentos longos e referência documental | Validade da posição global e fidelidade |

Para os classificadores, relatar precisão/recall/F1 de relevância, direção nos alvos humanos relevantes, desempenho conjunto com abstenções explícitas e confusões ordinais. Para intensidade, usar concordância ordinal e, se usar MAE, declarar o espaçamento numérico adotado. Para documentos, combinar erro/distribuição de escores, concordância/ranking e revisão qualitativa; correlação alta pode coexistir com deslocamento sistemático.

Intervalos das diferenças devem preservar os grupos pertinentes: documentos para a aplicação documental, perguntas para o diagnóstico do questionário. Várias decisões de eixo de uma mesma pergunta ou vários chunks de um plano não são observações independentes.

Escolher antecipadamente uma meta: minimizar custo sob uma perda máxima aceitável de qualidade, ou maximizar qualidade sob um orçamento. Definir a tolerância com o objetivo de uso e os dados de validação. Não declarar superioridade apenas porque uma execução tem maior percentual de acertos.

## 7. O que não priorizar

- Treinar uma arquitetura nova de embeddings, replicar BBBG ou construir vec-tionaries antes de existir referência humana suficiente.
- Substituir posição por sentimento, similaridade temática ou identificação partidária.
- Acrescentar tradução como etapa geral: Benoit et al. não encontraram vantagem em traduzir antes de resumir no protocolo estudado; isso não resolve automaticamente o caso brasileiro.
- Adicionar vários LLMs ao roteador antes de medir o ganho de um único fallback.
- Usar a “ideologia do LLM” inferida por questionário para corrigir numericamente seus resultados.
- Exigir raciocínio textual longo como solução geral: Haroon et al. não encontraram ganho com CoT no teste relatado, enquanto outros métodos usam estratégias diferentes. É hipótese específica, com custo, não melhoria garantida.
- Trocar todos os parâmetros de uma vez e interpretar a diferença como efeito de uma única melhoria.

## 8. Ordem prática dos ajustes

1. **Antes da próxima rodada:** congelar protocolo, resolver a redefinição de configuração, registrar o método de intervalo e alinhar o significado do resultado apresentado ao usuário.
2. **Para tornar a avaliação defensável:** revisar a categoria central, auditar as âncoras e ampliar a anotação independente; manter o 8values como diagnóstico de coerência.
3. **Para otimizar a cascata:** reaproveitar respostas JEV, calibrar o encaminhamento na validação e medir correções, regressões e custo.
4. **Para testar ganho metodológico novo:** exemplos anotados balanceados e resumo por eixo em planos longos, cada mudança isoladamente.

O conjunto de referências sustenta esse programa de validação e oferece alternativas concretas. Ele não determina sozinho um melhor número de níveis, limiar, tamanho de chunk ou provedor para esta implementação.

## 9. Evidência reproduzível desta revisão

Arquivos acrescentados, sem alteração de pipeline:

- [Diagnóstico local](diagnostico_revisao_artigos.py): importa apenas regras locais e definições explicitamente exportadas do notebook; usa decisões sintéticas.
- [Resultado do diagnóstico](diagnostico_revisao_artigos.json): exemplos, intervalos, configurações encontradas e hashes das fontes de código.
- [Inventário das referências](inventario_referencias.json): arquivos, páginas, hashes e cópias identificáveis.

Execução realizada na raiz:

```powershell
.\.venv\Scripts\python.exe analise_jev_llm\diagnostico_revisao_artigos.py
```

O script concluiu com sucesso. Ele verifica a coexistência de configurações, a perda de informação na média e a divergência dos procedimentos de bootstrap. Não testa classificação semântica, não certifica qualidade dos modelos e não executa o notebook completo. As recomendações experimentais permanecem hipóteses até comparação com referência independente.
