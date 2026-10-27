# Estabilidade das classificações diante das configurações testadas

Foram comparados os mesmos 28 textos e os mesmos 59 chunks nas quatro execuções completas, R2–R5. R1 foi excluída por não conter classificações concluídas. A análise descreve a sensibilidade observada nas configurações testadas, sem executar modelos novamente.

## Critério de estabilidade

Cada texto tem quatro eixos e três transições consecutivas (R2→R3, R3→R4, R4→R5): 12 oportunidades de mudança. Uma mudança é qualquer diferença no índice A ou no rótulo salvo, incluindo ganho e perda de evidência. Valores foram comparados com tolerância de arredondamento de 10⁻⁸. O ranking ordena pelo número de mudanças e, em empate, pela maior amplitude numérica. Não é um escore de qualidade.

Classificação estável significa que os quatro eixos mantiveram exatamente o resultado nas quatro execuções e houve índice em pelo menos um eixo. Textos sem evidência em todos os eixos e execuções aparecem separados. A amplitude é máximo menos mínimo dos índices numéricos do mesmo eixo; ausências permanecem ausências e nunca viram zero. Cruzamento de polos exige valores estritamente abaixo e acima de 50 no mesmo eixo.

## Resultado geral

| Métrica | Quantidade |
| --- | --- |
| textos | 28 |
| estaveis_com_classificacao | 8 |
| sempre_sem_evidencia | 4 |
| variaveis | 16 |
| total_mudancas | 39 |

## Classificações mais estáveis

| Texto | Tema / início | Eixos classificados e constantes | Mudanças internas de chunk |
| --- | --- | --- | --- |
| textos_grandes_001 | CCJ aprova criação do Imposto sobre Grandes Fortunas  A Comissão de Constituição e Justiça e de Cidadania aprovou há pouco o Proje | Econômico: Social (75,00) | 0 |
| textos_grandes_003 | Proposta aumenta pena de feminicídio para até 40 anos  O Projeto de Lei 4266/23 transforma o feminicídio em um crime autônomo, agr | Estado: Estatal (25,00); Sociedade: Progressista (75,00) | 1 |
| textos_grandes_009 | Imposto sobre fortunas pode entrar no debate sobre reforma tributária  Agência Câmara  Parlamentares da base do governo defendem u | Econômico: Social (75,00) | 0 |
| textos_pequenos_003 | Nacionalização e estatização do sistema monetário, financeiro e bancário | Econômico: Comunista (100,00) | 0 |
| textos_pequenos_004 | Legalização do aborto e garantia de atendimento na rede pública de saúde | Estado: Liberal (75,00); Sociedade: Progressista (75,00) | 0 |
| textos_pequenos_005 | O projeto proíbe o uso de reconhecimento facial para vigilância em massa ou monitoramento indiscriminado. | Estado: Liberal (75,00) | 0 |
| textos_pequenos_008 | Diante da pressão norte-americana, Lula afirmou que a atuação estrangeira no Brasil deve respeitar a Constituição e as leis brasil | Diplomático: Patriota (25,00); Estado: Moderado (50,00) | 0 |
| textos_pequenos_013 | O plano de Leonardo Péricles apresenta um programa de soberania alimentar escolar com cestas de produtos da agricultura familiar d | Econômico: Social (75,00) | 0 |

Sete desses oito textos também preservaram as decisões por chunk. `textos_grandes_003` manteve os índices agregados, mas uma decisão interna de chunk variou. A estabilidade da média não implica estabilidade de todos os trechos.

## Ausência de evidência persistente

| Texto | Tema / início |
| --- | --- |
| textos_grandes_004 | Comissão discute transição demográfica e envelhecimento da população brasileira  A Comissão de Defesa dos Direitos da Pessoa Idosa da Câmara dos Deputados realizará audiência públi |
| textos_grandes_005 | Conheça a tramitação de projetos de lei  1  APRESENTAÇÃO  Um projeto de lei pode ser apresentado por qualquer deputado ou senador, comissão da Câmara, do Senado ou do Congresso, pe |
| textos_pequenos_010 | O programa prevê consultas a distância e integração digital dos registros de atendimento em saúde. |
| textos_pequenos_011 | O plano de Lula propõe coordenar os órgãos de segurança e modernizar sua gestão para melhorar a eficiência. |

Esses casos têm saída constante, mas não sustentam a conclusão de que uma posição foi classificada de forma robusta.

## Textos que mais mudaram

| Texto | Complexidade | Mudanças /12 | Classificação (rótulo ou evidência) | Índice na mesma faixa | Eixos com evidência /4 | Maior amplitude (p.p.) | Situação |
| --- | --- | --- | --- | --- | --- | --- | --- |
| textos_grandes_010 | dificil | 6 | 3 | 3 | 2 | 75.0 | Classificação variável |
| textos_grandes_007 | dificil | 5 | 3 | 2 | 3 | 50.0 | Classificação variável |
| textos_pequenos_017 | dificil | 5 | 5 | 0 | 2 | 25.0 | Classificação variável |
| textos_pequenos_012 | ambiguo | 3 | 3 | 0 | 2 | 25.0 | Classificação variável |
| textos_pequenos_014 | dificil | 2 | 2 | 0 | 1 | 62.5 | Classificação variável |
| textos_grandes_006 | ambiguo | 2 | 2 | 0 | 2 | 25.0 | Classificação variável |
| textos_grandes_008 | dificil | 2 | 2 | 0 | 1 | 25.0 | Classificação variável |
| textos_pequenos_015 | dificil | 2 | 2 | 0 | 1 | 25.0 | Classificação variável |

## Trajetórias dos casos mais variáveis

### textos_grandes_010

RESOLUÇÃO Nº 23.732, DE 27 DE FEVEREIRO DE 2024  Altera a Res.-TSE nº 23.610, de 18 de dezembro de 2019, dispondo sobre a propaganda eleitoral.  O TRIBUNAL SUPERIOR ELEITORAL, no uso das atribuições que lhe conferem o inciso IX do art. 23 do Código Eleitoral e os arts. 57-J e 105 da Lei nº 9.504, de 30 de setembro de 1997,  RESOLVE:  Art. 1º A Res.

6 mudanças em 12 comparações. Eixos variáveis: Estado, Sociedade. Perfis completos distintos: 4/4.

| Eixo | R2 | R3 | R4 | R5 | Amplitude (p.p.) |
| --- | --- | --- | --- | --- | --- |
| Estado | Moderado (45,00) | Moderado (46,43) | Moderado (49,26) | Moderado (45,24) | 4.26 |
| Sociedade | Progressista (75,00) | Reacionário (0,00) | Progressista (75,00) | Sem evidência | 75.0 |

### textos_grandes_007

Câmara aprova texto-base da MP da Liberdade Econômica  O Plenário da Câmara dos Deputados aprovou nesta terça-feira (13) o texto-base da MP da Liberdade Econômica (Medida Provisória 881/19). Foram 345 votos a favor e 76 contra. Os destaques ficaram para esta quarta-feira (14) e serão todos votados pelo sistema eletrônico, fruto de um acordo com a o

5 mudanças em 12 comparações. Eixos variáveis: Econômico, Estado, Sociedade. Perfis completos distintos: 3/4.

| Eixo | R2 | R3 | R4 | R5 | Amplitude (p.p.) |
| --- | --- | --- | --- | --- | --- |
| Econômico | Capitalista (12,50) | Capitalista (12,50) | Capitalista (18,75) | Capitalista (18,75) | 6.25 |
| Estado | Liberal (62,50) | Liberal (75,00) | Libertário (87,50) | Libertário (87,50) | 25.0 |
| Sociedade | Reacionário (0,00) | Neutro (50,00) | Tradicional (25,00) | Tradicional (25,00) | 50.0 |

### textos_pequenos_017

Enquanto o PL 5167/09 procura impedir o reconhecimento familiar de uniões homoafetivas, o PL 580/07 admite um contrato de união entre pessoas do mesmo sexo. O relator recomenda o primeiro e rejeita o segundo.

5 mudanças em 12 comparações. Eixos variáveis: Estado, Sociedade. Perfis completos distintos: 3/4.

| Eixo | R2 | R3 | R4 | R5 | Amplitude (p.p.) |
| --- | --- | --- | --- | --- | --- |
| Estado | Estatal (25,00) | Sem evidência | Sem evidência | Estatal (25,00) | 0.0 |
| Sociedade | Tradicional (25,00) | Reacionário (0,00) | Muito Tradicional (12,50) | Tradicional (25,00) | 25.0 |

### textos_pequenos_012

O plano de Simone Tebet reúne privatizações e concessões com transferência permanente de renda voltada às famílias mais necessitadas.

3 mudanças em 12 comparações. Eixos variáveis: Econômico, Sociedade. Perfis completos distintos: 3/4.

| Eixo | R2 | R3 | R4 | R5 | Amplitude (p.p.) |
| --- | --- | --- | --- | --- | --- |
| Econômico | Mercado (25,00) | Centrista (50,00) | Sem evidência | Sem evidência | 25.0 |
| Sociedade | Sem evidência | Sem evidência | Progressista (62,50) | Progressista (62,50) | 0.0 |

### textos_pequenos_014

O programa propõe retirar o Brasil do BRICS e buscar ingresso na OCDE mediante reformas institucionais.

2 mudanças em 12 comparações. Eixos variáveis: Diplomático. Perfis completos distintos: 3/4.

| Eixo | R2 | R3 | R4 | R5 | Amplitude (p.p.) |
| --- | --- | --- | --- | --- | --- |
| Diplomático | Patriota (25,00) | Pacífico (75,00) | Nacionalista (12,50) | Nacionalista (12,50) | 62.5 |

### textos_grandes_006

Deputados aprovam projeto que regulamenta telessaúde  A Câmara dos Deputados aprovou nesta quarta-feira (27) o projeto de lei que autoriza e conceitua a prática da telessaúde em todo o território nacional, abrangendo todas as profissões da área da saúde regulamentadas. A proposta (PL 1998/20) será enviada ao Senado.  De autoria da deputada Adriana 

2 mudanças em 12 comparações. Eixos variáveis: Sociedade. Perfis completos distintos: 3/4.

| Eixo | R2 | R3 | R4 | R5 | Amplitude (p.p.) |
| --- | --- | --- | --- | --- | --- |
| Sociedade | Progressista (75,00) | Sem evidência | Neutro (50,00) | Neutro (50,00) | 25.0 |

### textos_grandes_008

Deputados e debatedores divergem sobre a privatização da Eletrobras  Parlamentares, representantes do governo, especialistas e dirigentes sindicais divergiram nesta sexta-feira (7) em debate na Câmara dos Deputados sobre a terceira tentativa de privatização da Eletrobras, estatal vinculada ao Ministério de Minas e Energia que responde por 30% da en

2 mudanças em 12 comparações. Eixos variáveis: Econômico. Perfis completos distintos: 2/4.

| Eixo | R2 | R3 | R4 | R5 | Amplitude (p.p.) |
| --- | --- | --- | --- | --- | --- |
| Econômico | Centrista (50,00) | Centrista (50,00) | Social (75,00) | Centrista (50,00) | 25.0 |

### textos_pequenos_015

Lula rejeita que o país se subordine a pressões estrangeiras, mas defende negociar em condições de igualdade e fortalecer organismos multilaterais para enfrentar conflitos.

2 mudanças em 12 comparações. Eixos variáveis: Diplomático. Perfis completos distintos: 3/4.

| Eixo | R2 | R3 | R4 | R5 | Amplitude (p.p.) |
| --- | --- | --- | --- | --- | --- |
| Diplomático | Sem evidência | Equilibrado (50,00) | Equilibrado (50,00) | Pacífico (75,00) | 25.0 |

## Síntese interpretativa

- Maior número de mudanças categóricas: `textos_pequenos_017`, com cinco trocas de rótulo ou de disponibilidade de evidência. Não mudou de lado no eixo Sociedade; variou na intensidade da posição tradicional e na relevância do eixo Estado.

- Maior oscilação de posição: `textos_grandes_010`, cuja classificação em Sociedade foi Progressista (75), Reacionário (0), Progressista (75), Sem evidência. No eixo Estado, os índices oscilaram só 4,26 p.p. e o rótulo Moderado permaneceu constante. Contar essas três variações numéricas como inversões de classificação exageraria o efeito.

- Caso grave com poucas mudanças: `textos_pequenos_014`, com trajetória diplomática 25 → 75 → 12,5 → 12,5. A amplitude de 62,5 p.p. e a alternância entre polos tornam o caso sensível, embora haja só duas mudanças.

- `textos_grandes_007` manteve a direção Mercado no eixo Econômico e Liberdade no eixo Estado. A intensidade e o eixo Sociedade foram mais sensíveis. Isso é estabilidade parcial por eixo.

- Os textos declarados difíceis concentram 25/39 mudanças (64,1%); 8 dos 9 variaram. Há apenas nove textos nesse grupo, sem controle de tema ou tamanho. O padrão é compatível com maior sensibilidade de textos difíceis, mas não demonstra causalidade.

- Para revisão qualitativa, priorizar grandes_010 e pequenos_014 para inversões de polo; pequenos_017 para intensidade e disponibilidade de evidência; pequenos_012 para relevância temática; grandes_007 para mudanças em múltiplos eixos.

## Ranking completo

| Texto | Complexidade | Mudanças /12 | Classificação (rótulo ou evidência) | Índice na mesma faixa | Eixos com evidência /4 | Maior amplitude (p.p.) | Situação |
| --- | --- | --- | --- | --- | --- | --- | --- |
| textos_grandes_010 | dificil | 6 | 3 | 3 | 2 | 75.0 | Classificação variável |
| textos_grandes_007 | dificil | 5 | 3 | 2 | 3 | 50.0 | Classificação variável |
| textos_pequenos_017 | dificil | 5 | 5 | 0 | 2 | 25.0 | Classificação variável |
| textos_pequenos_012 | ambiguo | 3 | 3 | 0 | 2 | 25.0 | Classificação variável |
| textos_pequenos_014 | dificil | 2 | 2 | 0 | 1 | 62.5 | Classificação variável |
| textos_grandes_006 | ambiguo | 2 | 2 | 0 | 2 | 25.0 | Classificação variável |
| textos_grandes_008 | dificil | 2 | 2 | 0 | 1 | 25.0 | Classificação variável |
| textos_pequenos_015 | dificil | 2 | 2 | 0 | 1 | 25.0 | Classificação variável |
| textos_grandes_002 | claro | 2 | 1 | 1 | 2 | 12.5 | Classificação variável |
| textos_pequenos_006 | claro | 2 | 2 | 0 | 2 | 12.5 | Classificação variável |
| textos_pequenos_002 | claro | 2 | 2 | 0 | 2 | 0.0 | Classificação variável |
| textos_pequenos_018 | dificil | 2 | 2 | 0 | 1 | — | Classificação variável |
| textos_pequenos_007 | claro | 1 | 1 | 0 | 1 | 12.5 | Classificação variável |
| textos_pequenos_001 | claro | 1 | 1 | 0 | 2 | 0.0 | Classificação variável |
| textos_pequenos_009 | ambiguo | 1 | 1 | 0 | 1 | 0.0 | Classificação variável |
| textos_pequenos_016 | dificil | 1 | 1 | 0 | 2 | 0.0 | Classificação variável |
| textos_grandes_001 | claro | 0 | 0 | 0 | 1 | 0.0 | Classificação estável |
| textos_grandes_003 | claro | 0 | 0 | 0 | 2 | 0.0 | Classificação estável |
| textos_grandes_004 | ambiguo | 0 | 0 | 0 | 0 | — | Sem evidência nas quatro execuções |
| textos_grandes_005 | ambiguo | 0 | 0 | 0 | 0 | — | Sem evidência nas quatro execuções |
| textos_grandes_009 | dificil | 0 | 0 | 0 | 1 | 0.0 | Classificação estável |
| textos_pequenos_003 | claro | 0 | 0 | 0 | 1 | 0.0 | Classificação estável |
| textos_pequenos_004 | claro | 0 | 0 | 0 | 2 | 0.0 | Classificação estável |
| textos_pequenos_005 | claro | 0 | 0 | 0 | 1 | 0.0 | Classificação estável |
| textos_pequenos_008 | claro | 0 | 0 | 0 | 2 | 0.0 | Classificação estável |
| textos_pequenos_010 | ambiguo | 0 | 0 | 0 | 0 | — | Sem evidência nas quatro execuções |
| textos_pequenos_011 | ambiguo | 0 | 0 | 0 | 0 | — | Sem evidência nas quatro execuções |
| textos_pequenos_013 | ambiguo | 0 | 0 | 0 | 1 | 0.0 | Classificação estável |

## Mudanças por comparação

| Comparação | Mudanças texto×eixo | Textos afetados |
| --- | --- | --- |
| R2 → R3 | 15 | 12 |
| R3 → R4 | 17 | 12 |
| R4 → R5 | 7 | 5 |

## Complexidade declarada dos textos

| Complexidade | Textos | Estáveis com índice | Sempre sem evidência | Variáveis | Mudanças |
| --- | --- | --- | --- | --- | --- |
| ambiguo | 8 | 1 | 4 | 3 | 6 |
| claro | 11 | 6 | 0 | 5 | 8 |
| dificil | 9 | 1 | 0 | 8 | 25 |

A complexidade é o metadado salvo na entrada. Essas contagens são descritivas e não isolam o efeito de tamanho, tema ou configuração.

## Limites da interpretação

- R2→R3 troca sabiazinho-4 por sabia-4 mantendo a escala de cinco níveis. R3→R4 amplia a escala para nove níveis. R4→R5 registra polo_primeiro, mantendo modelo e escala. A regra anterior não foi persistida e foi inferida como nível.
- As probabilidades do JEV e respostas do LLM também variaram entre execuções. Os dados não isolam causalmente o efeito de cada parâmetro.
- As escalas têm semânticas diferentes de intensidade. Na escala de cinco níveis, −2 equivale ao extremo 0. Na de nove, −2 equivale a 25. Parte das mudanças pode refletir essa alteração.
- Estabilidade não demonstra correção. Há somente uma execução por configuração e nenhum gabarito nos artefatos analisados.
- Comparar apenas R2 com R5 esconderia mudanças intermediárias. O ranking considera todas as três transições e preserva a sequência completa.
- Textos classificados em mais eixos têm mais oportunidades de variar. O ranking informa quantos eixos tiveram evidência para permitir essa leitura.

## Fontes

- R2: `runs/testes_textos/20261019T233334959801Z/<texto>/resultado.json`, `entrada.json` e `protocolo.json`.
- R3: `runs/testes_textos/20261020T010032139196Z/<texto>/resultado.json`, `entrada.json` e `protocolo.json`.
- R4: `runs/testes_textos/20261023T014240545881Z/<texto>/resultado.json`, `entrada.json` e `protocolo.json`.
- R5: `runs/testes_textos/20261024T184909667917Z/<texto>/resultado.json`, `entrada.json` e `protocolo.json`.
