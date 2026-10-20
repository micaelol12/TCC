# Avaliação dos resultados dos textos de teste

Os resultados são promissores para identificar posições explícitas, sobretudo no eixo econômico. A confiabilidade é menor em textos que combinam polos, reproduzem falas de diferentes pessoas ou contêm regras e descrições institucionais. Há problemas verificáveis de sustentação das citações e indícios de intensidade excessiva. Eu trataria esta rodada como avaliação exploratória de comportamento, ainda sem validação de acurácia.

A análise usa exclusivamente os resultados persistidos da rodada `20261019T233334959801Z`, o texto de entrada e as rubricas atuais de `Pipeline - Passo a Passo.ipynb`. Não houve novas chamadas às APIs, alteração dos scores nem verificação externa da atualidade das fontes. As apreciações de coerência abaixo são julgamento qualitativo em relação à rubrica; não são rótulos independentes de referência. As classes `claro`, `ambiguo` e `dificil` são metadados dos exemplos, não gabarito de relevância, direção ou intensidade.

[Consultar textos, gráficos e painéis completos](resultados_textos.html).

| Medida da rodada | Resultado observado |
|---|---:|
| Textos concluídos | 28/28 |
| Trechos analisados | 59 |
| Decisões trecho × eixo | 236 |
| Decisões finais direcionais | 55 |
| Decisões finais com nível zero | 4 |
| Decisões finais irrelevantes | 174 |
| Abstenções por citação não verificada | 3 |
| Chamadas lógicas ao LLM | 37 em 59 trechos (62,7%) |
| Decisões de eixo processadas pelo LLM | 48/236 (20,3%) |
| Decisões alteradas após o LLM | 28/48 encaminhadas (58,3%) |
| Chamadas JEV auxiliares de evidência | 76 |
| Decisões com nível que entram nos índices | 59 |
| Dessas, com citação literal validada | 42/59 (71,2%) |
| Dessas, sem citação literal validada | 17/59 (28,8%) |
| Auditorias semânticas registradas | 42 |
| Pareceres semânticos | 38 sustenta; 3 insuficiente; 1 contradiz |
| Pares documento × eixo com score disponível | 33/112 |
| Pares disponíveis sustentados por um único trecho | 26/33 (78,8%) |

Conferi os 112 pares documento × eixo: a quantidade de níveis válidos e a média recalculadas dos registros coincidem com as tabelas de cobertura. Essa consistência comprova a agregação dos dados, não a correção semântica das classificações. Não há status final `falha_llm` nesta rodada; isso não prova ausência de tentativas de transporte ou de custos adicionais.

O fallback alterou a relevância em 25 decisões: 21 passaram de relevante a irrelevante, três viraram abstenção e uma passou de irrelevante a relevante. Outras três mudaram o nível mantendo relevância. Das 48 decisões encaminhadas, 20 mantiveram o mesmo par relevância/nível. Portanto, mudança não pode ser apresentada como ganho de acurácia. O JEV tinha 19 níveis zero; 14 foram removidos como irrelevantes, quatro permaneceram zero e um virou −1. Essa concentração de remoções exige deixar explícita a fronteira entre assunto presente sem posição e ausência de relevância.

Os exemplos mais convincentes são privatização ampla → Mercado, estatização setorial → Igualdade, tributação progressiva → Igualdade, limitação de vigilância → Liberdade e fortalecimento da ONU → Globo. Há também boas remoções de associações indevidas: o fallback retirou Autoridade da estatização, Progresso do imposto sobre fortunas e Progresso da simples digitalização. Para descrição de tramitação legislativa, todos os eixos ficaram sem score, uma resposta prudente para o conteúdo apresentado.

O problema mais direto está na diferença entre localizar uma frase e justificar um nível. Em P01, a frase de privatização foi usada para atribuir Liberdade 75, apesar do parecer `insuficiente` (probabilidade registrada 0,93). Em G08, trecho 2, a citação “privatização da Eletrobras é uma medida radical e extemporânea” acompanha nível −1, favorável ao Mercado, embora a frase critique a privatização; o parecer foi `contradiz` (0,68). P17 tem dois pareceres `insuficiente`. Os quatro níveis permaneceram na agregação. Essas probabilidades são saídas do modelo, não probabilidades calibradas de acerto. A implementação atual faz auditoria informativa, o que explica a permanência; o painel deve deixar claro quando um índice contém evidência contestada.

No caso G08, Igualdade 50 é a média de 25 e 75; nenhum dos dois trechos que compõem a média recebeu nível zero. Um terceiro trecho foi excluído por citação não literal. Se apenas o nível cuja citação foi marcada contraditória fosse retirado, o índice iria de 50 a 75, com um único trecho restante. Isso é uma análise de sensibilidade, não uma correção validada. A matéria registra debate com múltiplos participantes; o resultado não deve ser tratado como ideologia única do autor ou da instituição que publicou a notícia.

P12 e P14 são exemplos relevantes de posição mista. P12 combina privatizações com transferência permanente de renda, mas recebe Mercado 75 sem justificar predominância. P14 propõe sair do BRICS e entrar na OCDE; JEV e LLM dão direções diplomáticas opostas, embora a frase reúna saída e adesão. Em ambos, uma posição única exige justificativa adicional. No eixo social, G06 parece associar telessaúde a Progresso, contrariando a ressalva que exclui mera tecnologia. Em G07, o LLM elevou a defesa específica do domingo de descanso de Tradição moderada para forte, sem uma proposta ampla de imposição moral; a própria âncora ordinal favorece revisar essa intensidade.

Os resultados documentais têm base pequena. Em G10, Progresso 75 vem de um único trecho sobre representação de mulheres e pessoas negras: cobertura de 4,5% (1/22). Já Liberdade 45 usa 20/22 trechos, mas seu IC95 de variabilidade entre trechos é aproximadamente [32,1;59,2] e atravessa o centro. Isso impede uma leitura segura de predominância direcional a partir da média. O IC não estima a probabilidade de a classificação estar certa. Em G09, três níveis idênticos geram [75;75], sem que isso elimine erro do modelo ou viés da rubrica. Além disso, G10 responde por 22/59 trechos (37,3%) e 21/59 níveis válidos (35,6%); resumos por trecho precisam ser acompanhados de resumos por documento para esse texto não dominar a leitura do conjunto.

As três abstenções por citação rejeitada foram P15/diplomacia, G08/trecho 1/economia e G10/trecho 1/Estado. O mecanismo evita aceitar como evidência uma passagem que não é contínua no texto. Não é correto converter esses casos em prova de irrelevância nem ignorá-los como se a exclusão não pudesse alterar o índice.

A tabela a seguir avalia cada entrada. Os números são sempre os **índices do polo A**, com a quantidade de trechos válidos entre parênteses: economia = Igualdade; diplomacia = Globo; Estado = Liberdade; sociedade = Progresso. `—` significa ausência de score; zero é resultado válido. P identifica texto pequeno e G identifica texto grande.

| Texto | Economia | Diplomacia | Estado | Sociedade | Avaliação qualitativa |
|---|---:|---:|---:|---:|---|
| [P01](../runs/testes_textos/20261019T233334959801Z/textos_pequenos_001/resultado.json) | 0,0 (1) | — | 75,0 (1) | — | Mercado 100 é coerente com privatização ampla. Liberdade 75 é extrapolação: propriedade estatal não estabelece, por si, posição sobre liberdades civis; a auditoria marcou a citação como insuficiente. |
| [P02](../runs/testes_textos/20261019T233334959801Z/textos_pequenos_002/resultado.json) | — | — | 25,0 (1) | — | Autoridade 75 é plausível para endurecimento penal. O LLM retirou Progresso 75 sem apoio social claro; a direção estatal ficou sem citação selecionada. |
| [P03](../runs/testes_textos/20261019T233334959801Z/textos_pequenos_003/resultado.json) | 100,0 (1) | — | — | — | Igualdade 100 acompanha a âncora de estatizar setores inteiros. O LLM retirou Autoridade 100, evitando confundir intervenção econômica com coerção civil. |
| [P04](../runs/testes_textos/20261019T233334959801Z/textos_pequenos_004/resultado.json) | — | — | 75,0 (1) | 75,0 (1) | Liberdade 75 e Progresso 75 são plausíveis para ampliação de autonomia e direitos. A retirada do eixo econômico é discutível por também haver oferta pública; não há gabarito para decidir. |
| [P05](../runs/testes_textos/20261019T233334959801Z/textos_pequenos_005/resultado.json) | — | — | 75,0 (1) | — | Liberdade 75 é coerente com limitação de vigilância indiscriminada. A retirada do eixo social evita inferir costumes a partir de tecnologia. |
| [P06](../runs/testes_textos/20261019T233334959801Z/textos_pequenos_006/resultado.json) | — | — | 25,0 (1) | 0,0 (1) | A direção de Autoridade e Tradição é plausível para restrição do reconhecimento familiar. Tradição 100 parece intensa para uma medida específica e merece comparação com P17. |
| [P07](../runs/testes_textos/20261019T233334959801Z/textos_pequenos_007/resultado.json) | — | 75,0 (1) | — | — | Globo 75 é coerente com fortalecimento de organismo multilateral; há citação literal registrada. |
| [P08](../runs/testes_textos/20261019T233334959801Z/textos_pequenos_008/resultado.json) | — | 25,0 (1) | 50,0 (1) | — | Nação 75 é plausível para autonomia perante interferência externa. Liberdade 50 é leitura temática sem direção, e não comprova centrismo do autor. |
| [P09](../runs/testes_textos/20261019T233334959801Z/textos_pequenos_009/resultado.json) | — | — | — | — | Não impor direção a uma expressão genérica de política fiscal é prudente. Há dúvida de contrato entre irrelevância e tema relevante sem posição, que o JEV marcou como zero. |
| [P10](../runs/testes_textos/20261019T233334959801Z/textos_pequenos_010/resultado.json) | — | — | — | — | Não inferir Progresso só por digitalização de serviços é coerente com a nota da rubrica social. |
| [P11](../runs/testes_textos/20261019T233334959801Z/textos_pequenos_011/resultado.json) | — | — | — | — | Não inferir Autoridade por melhoria de gestão da segurança é coerente com a ressalva da rubrica estatal. A fronteira entre irrelevância e nível zero precisa ser explicitada. |
| [P12](../runs/testes_textos/20261019T233334959801Z/textos_pequenos_012/resultado.json) | 25,0 (1) | — | — | — | Mercado 75 é questionável: privatizações e transferência permanente de renda aparecem juntas, sem predominância demonstrada. A rubrica prevê nível zero quando polos se combinam sem predominância. |
| [P13](../runs/testes_textos/20261019T233334959801Z/textos_pequenos_013/resultado.json) | 75,0 (1) | — | — | — | Igualdade 75 é plausível pela política focalizada de proteção alimentar. Soberania alimentar não foi convertida em nacionalismo; ponto favorável. Não foi selecionada citação de apoio. |
| [P14](../runs/testes_textos/20261019T233334959801Z/textos_pequenos_014/resultado.json) | — | 25,0 (1) | — | — | A troca BRICS → OCDE reúne saída e adesão a organismos. A inversão Globo 75 → Nação 75 não pode ser validada só por essa frase; o caso pede tratamento de posição mista. |
| [P15](../runs/testes_textos/20261019T233334959801Z/textos_pequenos_015/resultado.json) | — | — | — | — | A abstenção evita aceitar uma citação descontínua. É falha de evidência da resposta, não prova de que o texto seja irrelevante ou não contenha uma posição diplomática. |
| [P16](../runs/testes_textos/20261019T233334959801Z/textos_pequenos_016/resultado.json) | — | — | 75,0 (1) | 50,0 (1) | Liberdade 75 é defensável pelas salvaguardas contra rastreamento e punição automática, apesar da autorização de identificação facial. Sociedade 50 é questionável diante da exclusão explícita de mera tecnologia na rubrica. |
| [P17](../runs/testes_textos/20261019T233334959801Z/textos_pequenos_017/resultado.json) | — | — | 25,0 (1) | 25,0 (1) | A direção tradicional é plausível pela preferência expressa do relator, mas as duas citações de apoio foram marcadas como insuficientes. Tradição 75 contrasta com 100 em P06 para proibição semelhante. |
| [P18](../runs/testes_textos/20261019T233334959801Z/textos_pequenos_018/resultado.json) | — | — | — | — | Nenhum eixo recebe nível. A ausência social é plausível; a irrelevância estatal é questionável porque o texto menciona obrigação de aviso e remoção de conteúdo. O alvo é a classificação do trecho, não a validade da norma. |
| [G01](../runs/testes_textos/20261019T233334959801Z/textos_grandes_001/resultado.json) | 75,0 (1) | — | — | — | Igualdade 75 é coerente com tributo progressivo e justificativa redistributiva. A remoção de Progresso evita transportar política econômica para costumes. |
| [G02](../runs/testes_textos/20261019T233334959801Z/textos_grandes_002/resultado.json) | 25,0 (2) | — | 75,0 (1) | — | Mercado 75 é plausível pela desregulação. Liberdade 75 pede revisão para distinguir autonomia econômica de liberdade civil. |
| [G03](../runs/testes_textos/20261019T233334959801Z/textos_grandes_003/resultado.json) | — | — | 25,0 (2) | 75,0 (1) | Autoridade 75 é plausível pelo endurecimento penal. Progresso 75 é discutível: finalidade de proteção a mulheres não basta, sozinha, para estabelecer revisão de costumes. |
| [G04](../runs/testes_textos/20261019T233334959801Z/textos_grandes_004/resultado.json) | — | — | — | — | Nenhum eixo recebe nível. A cautela é plausível para diagnóstico demográfico; propostas de cuidado devem ser avaliadas sem deduzir automaticamente orientação ideológica. |
| [G05](../runs/testes_textos/20261019T233334959801Z/textos_grandes_005/resultado.json) | — | — | — | — | Nenhum eixo recebe nível. Resultado adequado como controle de descrição institucional sem defesa explícita de um polo. |
| [G06](../runs/testes_textos/20261019T233334959801Z/textos_grandes_006/resultado.json) | — | — | 75,0 (1) | 75,0 (1) | Liberdade 75 tem apoio textual em autonomia e consentimento do paciente. Progresso 75 parece vazamento de tecnologia para valores sociais, e a busca de evidência não selecionou passagem para esse nível. |
| [G07](../runs/testes_textos/20261019T233334959801Z/textos_grandes_007/resultado.json) | 12,5 (2) | — | 62,5 (2) | 0,0 (1) | Mercado 87,5 é plausível para liberalização econômica. Tradição 100 se apoia em defesa localizada de descanso dominical e oração, sem transformação moral ampla; intensidade excessiva é provável. A notícia reúne falas divergentes. |
| [G08](../runs/testes_textos/20261019T233334959801Z/textos_grandes_008/resultado.json) | 50,0 (2) | — | — | — | Igualdade 50 resulta de dois níveis opostos, não de consenso neutro. A citação usada para Mercado 75 critica a privatização; a auditoria marcou contradição. O primeiro trecho foi excluído por citação não literal. |
| [G09](../runs/testes_textos/20261019T233334959801Z/textos_grandes_009/resultado.json) | 75,0 (3) | — | — | — | Igualdade 75 é coerente com tributação de fortunas para reduzir desigualdade. O IC [75;75], com três níveis iguais, reflete apenas essa discretização e não certeza de classificação. |
| [G10](../runs/testes_textos/20261019T233334959801Z/textos_grandes_010/resultado.json) | — | — | 45,0 (20) | 75,0 (1) | Liberdade 45 resume 20 trechos sobre restrições e garantias, com IC aproximado [32,1;59,2]. Não sustenta rótulo global seguro. Progresso 75 vem de um único trecho de representação política (1/22); extrapolar ao documento inteiro é inadequado. |

Antes de alterar limiares, eu priorizaria quatro medidas:

1. **Definir o alvo e o gabarito.** Separar posição da proposta citada, posição do interlocutor e posição do autor do documento. Anotar relevância, nível, evidência e posição mista por eixo, preferencialmente com dois avaliadores e adjudicação. Só então medir acurácia de relevância, cobertura/abstenção, erro ordinal e ganho pareado do fallback.
2. **Tratar os alertas de evidência como parte da interpretação.** Distinguir “citação encontrada” de “citação sustenta o nível”. Definir uma política para contradição e insuficiência — revisão, sinalização ou abstenção — e validar essa política antes de simplesmente excluir qualquer parecer desfavorável. O verificador também pode errar e usa o mesmo JEV das decisões iniciais; não equivale a validação humana independente.
3. **Revisar as fronteiras entre eixos e as âncoras de intensidade.** Usar P01/P03/G02/G07 para separar economia de liberdade civil, P10/P16/G06 para separar tecnologia de costumes, P06/P17/G07 para consistência de intensidade e P12/P14/G08 para mistura de posições. Os pares com falas opostas também precisam de exemplos positivos de nível zero e de identificação de vozes.
4. **Validar estabilidade e dependência da segmentação.** Repetir casos críticos, avaliar trechos por unidade argumentativa e verificar se mudanças de tamanho e limites dos chunks alteram os índices. Mostrar sempre quantidade de níveis, cobertura e polarização interna. Sem gabarito, essas análises medem sensibilidade, não acurácia.

A conclusão sustentada por esta rodada é que a cascata identifica sinais explícitos e frequentemente elimina associações temáticas indevidas. Permanecem falhas relevantes de evidência, separação de eixos, mistura de vozes e intensidade ordinal. Os números são úteis para inspeção e desenvolvimento; ainda não demonstram uma medida validada de ideologia do documento ou equivalência com respostas humanas ao 8values.
