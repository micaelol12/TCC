# 4 RESULTADOS

Esta seção apresenta os resultados da avaliação do sistema de análise de textos políticos nos quatro eixos do 8values. A subseção 4.1 analisa a classificação dos enunciados do questionário e compara as decisões iniciais do JEV com as decisões finais da cascata, que utiliza o Sabiá para revisar casos de incerteza. A subseção 4.2 apresenta os resultados obtidos com textos de diferentes extensões e discute exemplos de classificação. Por fim, a subseção 4.3 examina o tempo de processamento, o acionamento dos modelos e a disponibilidade de evidências textuais.

Foram considerados os registros mais recentes disponíveis para cada avaliação. Nos testes com textos, foi utilizada a última execução completa, composta por 28 documentos. Para o questionário, foram analisadas a última execução completa, com 70 enunciados, e a execução posterior, que continha 22 enunciados processados. Os resultados dessa execução parcial são apresentados separadamente, pois a diferença de composição impede sua comparação direta com os resultados do questionário completo.

## 4.1 TESTES E RESULTADOS DA CLASSIFICAÇÃO DOS ENUNCIADOS DO 8VALUES

Para avaliar a classificação, foram utilizados os 70 enunciados do questionário 8values, considerando os eixos econômico, diplomático, estatal e social. Cada enunciado foi analisado nos quatro eixos, totalizando 280 pares de avaliação. A referência foi obtida a partir dos efeitos associados às perguntas no próprio questionário: efeitos positivos e negativos indicaram as direções esperadas, enquanto efeitos iguais a zero foram considerados ausência de relevância para o eixo. Por essa regra, 116 pares foram considerados relevantes e 164 irrelevantes.

Essa referência permite verificar a concordância com a estrutura do 8values, mas possui uma limitação: um efeito igual a zero na pontuação do teste não garante que o enunciado não contenha qualquer relação temática com o eixo. Além disso, o sinal do efeito fornece uma referência de direção, sem estabelecer uma correspondência validada com a intensidade da escala de nove níveis utilizada pelo sistema. Assim, a avaliação quantitativa concentrou-se na relevância e na direção, sem medir acerto de intensidade.

Foram consideradas três métricas. A taxa de acerto de relevância corresponde à proporção de pares cuja presença ou ausência de relação com o eixo foi identificada conforme a referência. A taxa de acerto de direção considera apenas os 116 pares esperados como relevantes e exige a identificação do polo correspondente; ausência de posição, irrelevância ou abstenção nesses pares são contabilizadas como insucesso. O acerto conjunto exige relevância correta e, quando o par é esperado como relevante, também a direção correta. A Tabela 1 apresenta os resultados por eixo da execução completa.

Tabela 1 - Resultados por eixo na avaliação dos 70 enunciados

| Eixo | Pares relevantes | Relevância final | Direção final | Acerto conjunto JEV | Acerto conjunto cascata |
| --- | --- | --- | --- | --- | --- |
| Econômico | 22 | 90,00% | 63,64% | 87,14% | 88,57% |
| Diplomático | 24 | 84,29% | 54,17% | 82,86% | 82,86% |
| Estatal | 37 | 72,86% | 43,24% | 65,71% | 70,00% |
| Social | 33 | 78,57% | 51,52% | 75,71% | 72,86% |

Fonte: elaborado pelo autor com base nos registros da execução completa do questionário.

Nota: cada eixo possui 70 pares. Relevância e acerto conjunto usam esse denominador; a direção utiliza somente os pares relevantes indicados na segunda coluna. JEV corresponde à decisão inicial e cascata à decisão final após a revisão seletiva pelo Sabiá.

O eixo econômico apresentou o maior acerto conjunto final, com 88,57%, e o maior acerto de direção entre os pares relevantes, com 63,64%. O eixo estatal apresentou o menor acerto conjunto final, de 70,00%, apesar de ter recebido o maior ganho após a revisão, de 4,29 pontos percentuais. No eixo diplomático, o acerto conjunto permaneceu em 82,86%. No eixo social, ocorreu redução de 75,71% para 72,86%, indicando que a revisão pelo modelo de linguagem não trouxe benefício uniforme entre os eixos.

No conjunto dos 280 pares, o JEV inicial obteve 218 acertos conjuntos, equivalentes a 77,86%, enquanto a cascata alcançou 220, correspondentes a 78,57%. A diferença foi de dois acertos, ou 0,71 ponto percentual. Como referência, uma estratégia que classificasse todos os pares como irrelevantes obteria 164 acertos, equivalentes a 58,57%. A Tabela 2 reúne os indicadores globais.

Tabela 2 - Comparação global entre a decisão inicial e a decisão final

| Métrica | JEV inicial | Cascata final |
| --- | --- | --- |
| Acerto de relevância em 280 pares | 82,86% (232) | 81,43% (228) |
| Acerto de direção em 116 pares relevantes | 54,31% (63) | 51,72% (60) |
| Acerto conjunto em 280 pares | 77,86% (218) | 78,57% (220) |
| Pares classificados como irrelevantes | 194 | 207 |
| Pares com decisão direcional | 71 | 66 |

Fonte: elaborado pelo autor com base nos registros da execução completa do questionário.

O pequeno aumento do acerto conjunto ocorreu acompanhado da redução do acerto de relevância e de direção. A análise das decisões mostra que os falsos positivos de relevância diminuíram de nove para quatro, enquanto os pares relevantes classificados como irrelevantes aumentaram de 39 para 47. A cascata também apresentou uma abstenção em um par esperado como relevante. Portanto, a revisão tornou a classificação mais restritiva, reduzindo atribuições indevidas de relevância, mas também deixando de reconhecer parte dos conteúdos relevantes segundo a referência.

Na execução mais recente do questionário, foram encontrados resultados para os primeiros 22 enunciados, totalizando 88 pares, dos quais 34 eram esperados como relevantes. Nesse subconjunto, o acerto conjunto passou de 68 para 73 pares, ou de 77,27% para 82,95%, após a revisão. A decisão final obteve 75 acertos de relevância em 88 pares, equivalentes a 85,23%, e 21 acertos de direção em 34 pares relevantes, correspondentes a 61,76%. Esses valores descrevem apenas o subconjunto processado. Como os 48 enunciados restantes não estavam presentes nessa execução, os números não permitem afirmar que houve melhora em relação ao questionário completo.

## 4.2 TESTES E RESULTADOS DA ANÁLISE DE TEXTOS POLÍTICOS

A avaliação com textos utilizou 28 documentos organizados no corpus em dois grupos: 18 textos pequenos e dez textos grandes. Após a preparação e segmentação, os grupos produziram, respectivamente, 18 e 40 trechos, totalizando 58 unidades de análise. A configuração utilizou segmentação por sentenças, com alvo de 600 tokens e sem sobreposição entre trechos. Como cada trecho foi avaliado nos quatro eixos, foram obtidas 232 decisões. Todos os 28 documentos possuíam registro de conclusão sem erro de execução.

Na decisão final, 56 pares de trecho e eixo receberam classificação direcional, seis foram considerados relevantes sem posição predominante e 170 foram classificados como irrelevantes. Essas categorias corresponderam, respectivamente, a 24,14%, 2,59% e 73,28% das decisões. A predominância de irrelevância decorre do fato de cada trecho ser examinado em todos os eixos, mesmo quando seu conteúdo se concentra em apenas um deles. Como o corpus não dispõe de gabarito humano, essa distribuição descreve o comportamento do sistema e não representa uma medida de acurácia.

Na agregação dos documentos, foram produzidos índices em 33 dos 112 pares possíveis de documento e eixo: nove no econômico, quatro no diplomático, 11 no estatal e nove no social. A ausência de índice foi preservada quando não havia trechos válidos para a estimativa. Essa distinção é necessária porque um índice igual a 50 representa uma classificação central na escala, enquanto a ausência de índice indica insuficiência de conteúdo para estimar o eixo. A Tabela 3 apresenta exemplos extraídos dos resultados.

Tabela 3 - Exemplos de classificação dos textos do corpus

| Conteúdo do trecho | Eixo | Resultado final |
| --- | --- | --- |
| Privatização de todas as empresas estatais | Econômico | Igualdade 0; Mercado 100 |
| Nacionalização e estatização do sistema monetário, financeiro e bancário | Econômico | Igualdade 100; Mercado 0 |
| Redução da maioridade penal para 16 anos ou menos | Estatal | Liberdade 25; Autoridade 75 |
| Fortalecimento da ONU e ampliação de sua capacidade de interromper guerras | Diplomático | Globo 87,5; Nação 12,5 |
| Rejeição à subordinação estrangeira e respeito às leis brasileiras | Diplomático | Globo 25; Nação 75 |
| Consultas a distância e integração digital de registros de saúde | Todos | Ausência de índice nos quatro eixos |

Fonte: elaborado pelo autor com base na última execução completa do corpus de textos.

Nota: os valores são índices na escala de 0 a 100, derivados dos níveis atribuídos aos trechos. Não representam probabilidades de acerto. Os conteúdos da primeira coluna identificam os exemplos do corpus, sem constituir verificação externa das propostas mencionadas.

Os exemplos de privatização e estatização produziram direções opostas no eixo econômico, enquanto a proposta de redução da maioridade penal recebeu predominância de Autoridade. No eixo diplomático, os trechos sobre fortalecimento da ONU e rejeição à subordinação estrangeira também produziram direções opostas. Esses casos ilustram a diferenciação de posições explícitas. Por outro lado, o trecho sobre atendimento de saúde a distância não recebeu índice, mostrando que a simples presença de um tema de política pública não foi suficiente para gerar classificação ideológica nessa ocorrência.

Nos documentos com posições divergentes, a agregação exigiu uma interpretação mais cuidadosa. O texto sobre a privatização da Eletrobras foi dividido em três trechos e recebeu índice econômico de 41,67 para Igualdade e 58,33 para Mercado. Esse resultado resume as decisões dos trechos analisados e não permite atribuir uma posição única a todos os participantes citados. De forma semelhante, um texto que combina privatizações, concessões e transferência de renda recebeu índice de 87,5 para Mercado. Embora exista conteúdo relacionado aos dois polos, a classificação final privilegiou uma das direções, o que torna necessária a revisão de casos com propostas combinadas.

Também foram observadas classificações que merecem avaliação adicional. O trecho que propõe a saída do BRICS e o ingresso na OCDE recebeu Globo 12,5 e Nação 87,5, após a revisão pelo Sabiá inverter a direção inicialmente atribuída pelo JEV. Como o enunciado combina saída de uma organização e ingresso em outra, a direção não pode ser confirmada apenas pela existência de uma passagem citada. Outro caso foi o trecho que proíbe reconhecimento facial para vigilância em massa: além de Liberdade 75, o sistema atribuiu índice social 50, sem passagem selecionada para esse eixo. A pertinência dessa classificação social precisa ser examinada antes de considerá-la um acerto.

Esses resultados indicam que o sistema produz saídas diferenciadas para propostas explícitas e preserva ausências de índice em parte dos textos sem orientação identificada. Entretanto, a interpretação de conteúdos mistos e a delimitação da relevância temática continuam sendo limitações. Para quantificar a qualidade da classificação nesse corpus, seria necessária uma anotação independente que contemplasse relevância, direção e intensidade.

## 4.3 TEMPO DE PROCESSAMENTO E VERIFICAÇÃO DAS EVIDÊNCIAS

As execuções analisadas utilizaram o JEV na versão jev-1.13.0 e o modelo Sabiá na versão sabia-4, com temperatura igual a zero. A cascata realizou uma classificação inicial e encaminhou ao modelo de linguagem os eixos que atenderam aos critérios de revisão. A Tabela 4 apresenta os indicadores de processamento da execução completa do questionário e da última execução completa dos textos. Os tempos correspondem às latências registradas por trecho e não incluem todo o tempo de interação com a interface.

Tabela 4 - Indicadores de processamento das execuções completas

| Indicador | Questionário 8values | Corpus de textos |
| --- | --- | --- |
| Unidades de análise | 70 enunciados | 58 trechos de 28 documentos |
| Chamadas JEV de classificação | 70 | 58 |
| Chamadas ao Sabiá | 49 | 32 |
| Eixos encaminhados ao Sabiá | 65 | 44 |
| Chamadas JEV para evidências | 0 | 84 |
| Latência total média por unidade | 1,00 s | 1,15 s |
| Latência total mediana por unidade | 1,16 s | 1,14 s |
| Menor e maior latência por unidade | 0,24 s e 2,04 s | 0,22 s e 2,34 s |

Fonte: elaborado pelo autor com base nos registros das execuções analisadas.

O Sabiá foi acionado em 49 dos 70 enunciados do questionário, correspondentes a 70,00%, e em 32 dos 58 trechos do corpus, equivalentes a 55,17%. Portanto, 21 enunciados e 26 trechos foram processados sem acionar esse modelo. Como uma mesma chamada pode revisar mais de um eixo, o número de eixos encaminhados foi superior ao número de chamadas. Esse comportamento confirma o uso seletivo do modelo de linguagem nas execuções observadas, mas não permite quantificar economia financeira ou ganho de velocidade em relação a uma estratégia que utilizasse apenas esse modelo, pois essa comparação não foi executada sob condições equivalentes.

A execução dos textos habilitou a busca de passagens e a checagem semântica das evidências, que produziram 84 chamadas adicionais ao JEV. Essas etapas estavam desabilitadas na execução completa do questionário. Consequentemente, a diferença de latência entre os dois conjuntos também envolve configurações distintas e não pode ser atribuída somente ao tamanho ou à complexidade dos textos.

Entre as 62 decisões finais consideradas relevantes no corpus, incluindo as seis sem posição predominante, 57 possuíam evidência marcada como verificada e cinco não apresentavam essa marcação. A disponibilidade de passagem verificada correspondeu a 91,94%. Esse indicador trata da rastreabilidade textual e não mede, por si só, a correção da interpretação ideológica. O exemplo sobre BRICS e OCDE recebeu parecer semântico favorável à evidência, apesar de permanecer uma situação que exige revisão da direção atribuída.

As cinco decisões sem evidência marcada como verificada foram mantidas nos registros e devem ser consideradas na interpretação dos índices. Sua ocorrência mostra que a geração de uma pontuação não assegura a disponibilidade de justificativa textual para todas as decisões. Em textos maiores, também foi observada distribuição desigual das unidades de análise: um único documento, referente a uma resolução sobre propaganda eleitoral, produziu 21 dos 58 trechos. Essa concentração limita a representatividade das médias e das contagens agregadas.

O desempenho observado permitiu concluir o processamento dos 28 documentos e obter resultados em aproximadamente um segundo por trecho, em média, na configuração utilizada. A avaliação do questionário mostrou concordância parcial com a referência do 8values e efeitos diferentes da revisão entre os eixos. A validação da intensidade, da equivalência entre índices de texto e perfis de usuários e da qualidade das classificações em novos documentos permanece necessária para ampliar o alcance das conclusões.
