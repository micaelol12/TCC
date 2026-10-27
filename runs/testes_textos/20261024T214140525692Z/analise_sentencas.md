# Comparação da estratégia por sentenças

Rodada analisada: `20261024T214140525692Z`.
Referência: `20261024T184909667917Z`, a rodada anterior com os mesmos parâmetros de classificação.

## Conclusão

A estratégia mostra ganhos locais na organização dos blocos, mas esta rodada não demonstra melhora geral da qualidade da classificação. A segmentação mudou em apenas 2 dos 28 textos. Entre esses dois, um manteve todos os índices e o outro apresentou uma pequena mudança no eixo estatal e uma nova classificação social com sustentação semântica insuficiente na auditoria.

Os resultados também mostram variação entre execuções com entradas idênticas. Por isso, a diferença entre as duas rodadas não pode ser interpretada integralmente como efeito da segmentação.

## Base da comparação

Foram lidos o relatório HTML e seus arquivos de origem: `protocolo.json`, `comparacao.csv`, `entrada.json`, `resultado.json` e `segmentacao.csv`. Não foram feitas novas chamadas aos modelos nem alterações no código.

- Os 28 textos originais e seus metadados são iguais nas duas rodadas.
- Modelos: JEV 1.13.0 e Sabiá-4; temperatura do LLM igual a zero.
- A comparação recursiva dos protocolos encontrou diferenças somente no identificador da rodada e na configuração de segmentação: `max_tokens=600` passou a `estrategia=sentencas, tokens_alvo=600`.
- As rubricas, a escala, os limiares e as opções de auditoria permaneceram iguais nos protocolos.
- A estratégia anterior usa divisão recursiva com preferência por parágrafos e quebras de linha; não corta exclusivamente a cada 600 tokens. Isso ajuda a explicar por que tantos blocos permaneceram idênticos.
- Não há rótulos humanos de referência nesses arquivos para calcular acurácia ou erro da classificação.

## Resultados observados

| Medida | Anterior | Sentenças |
|---|---:|---:|
| Textos concluídos | 28/28 | 28/28 |
| Trechos | 59 | 58 |
| Chamadas principais ao JEV | 59 | 58 |
| Chamadas ao LLM | 37 | 35 |
| Chamadas JEV de evidências | 81 | 85 |
| Soma das chamadas registradas | 177 | 178 |
| Decisões direcionais com citação literal verificada | 45/54 | 45/54 |
| Auditorias semânticas com resultado `sustenta` | 42 | 41 |
| Auditorias semânticas com resultado `insuficiente` | 4 | 5 |

A soma de chamadas não representa custo monetário: os tipos de chamada e os tamanhos de entrada diferem. Os totais globais também incluem variação em textos cuja segmentação não mudou.

Os cortes ficaram idênticos em 26/28 textos, incluindo todos os 18 textos curtos. Os índices finais ficaram iguais em 22/28 textos. Das seis mudanças de índices, cinco ocorreram em textos curtos com blocos idênticos.

Na rodada nova, nenhum dos 58 trechos excedeu o alvo de 600 tokens. Isso confirma o respeito ao alvo nesta amostra, mas não demonstra que todas as fronteiras sejam linguisticamente corretas.

## Textos em que os cortes mudaram

### textos_grandes_006 — telessaúde

Foram mantidos três trechos. A estratégia nova deslocou os títulos “Liberdade de decisão” e “Ponto rejeitado” para o início dos blocos que contêm seus respectivos conteúdos. Na estratégia anterior, esses títulos ficavam no fim do bloco anterior.

Esse é um ganho concreto de organização e contexto. Os índices permaneceram iguais: Liberdade 75 e Progresso 50, este último registrado como `sem_posicao`. As três chamadas ao LLM também permaneceram iguais.

### textos_grandes_010 — Resolução TSE nº 23.732/2024

- Trechos: 22 → 21.
- Chamadas ao LLM: 7 → 7.
- Chamadas JEV de evidências: 37 → 38.
- Índice Liberdade: 45,2381 → 43,125, diferença de −2,1131 pontos.
- Cobertura no eixo estatal: 21/22 (95,45%) → 20/21 (95,24%).
- Citações literais verificadas no eixo estatal: 18 nas duas rodadas.
- IC95 do índice Liberdade: [33,5227; 58,75] → [33,125; 53,5714]. A sobreposição é ampla. Esses intervalos não constituem um teste pareado de superioridade das estratégias.

O resultado continua próximo do centro, com inclinação para Autoridade. Um índice menor não significa uma classificação melhor: seria necessário compará-lo a uma referência humana.

Surgiu Progresso 75, baseado em apenas um dos 21 trechos, sobre o “percentual do programa destinado a candidatas mulheres, a candidatas negras e a candidatos negros”. A citação existe literalmente, mas a própria auditoria semântica registrou `insuficiente`, com probabilidades 0,54 para insuficiente e 0,46 para sustenta. Isso torna o achado inconclusivo como ganho de qualidade.

No código atual, a auditoria semântica é observacional e não altera os níveis nem a agregação (`app/api/app/pipeline/evidence.py`). Portanto, `evidencia_verificada=true` deve ser interpretado como presença literal da citação, não como aprovação semântica da conclusão.

Persistem duas fronteiras problemáticas na segmentação nova, com numeração de trechos a partir de 1:

- Trecho 8 termina em `“Art.` e trecho 9 começa em `9º-H A remoção...`.
- Trecho 13 termina em `“Art.` e trecho 14 começa em `29-A. A live eleitoral...`.

A busca de evidências usa ainda outro sentenciador, baseado em expressão regular (`sentence_spans`), que também separa abreviações: há uma citação aceita terminando em “previsto no art.”. Melhorar a segmentação dos blocos, por si só, não resolve a segmentação das passagens usadas como evidência.

## Variação sem mudança de entrada

O caso mais expressivo é `textos_pequenos_014`: “O programa propõe retirar o Brasil do BRICS e buscar ingresso na OCDE mediante reformas institucionais.”

O bloco é exatamente igual nas duas rodadas. Mesmo assim, o índice Globo mudou de 12,5 para 87,5, invertendo o polo. Na rodada anterior houve encaminhamento ao LLM por intensidade ambígua; na nova, a decisão foi aceita diretamente do JEV. A variação já aparece, portanto, na decisão e no encaminhamento anteriores à resposta do LLM.

Também mudaram índices em `textos_pequenos_006`, `007`, `016` e `017`, todos com os mesmos blocos nas duas rodadas. Esses casos funcionam como controles que evidenciam a limitação de uma única execução por estratégia. Não permitem identificar a causa operacional da variação do provedor.

## Próximo experimento recomendado

1. Manter a estratégia como candidata, corrigindo primeiro as fronteiras de referências jurídicas, inclusive nas passagens de evidência.
2. Montar um conjunto com mais textos cujos cortes realmente diferem entre as duas estratégias, incluindo sentenças longas, negação, citações e enumerações jurídicas.
3. Congelar entradas, rubricas, configuração e versão do código. Reutilizar respostas de blocos idênticos para isolar o efeito dos cortes e medir separadamente a variação entre chamadas repetidas.
4. Repetir as duas condições, alternando sua ordem, para estimar a variação da execução.
5. Comparar com rótulos humanos por eixo e evidência; medir erro ordinal, inversão de polo, relevância, abstenção e sustentação semântica. Registrar também tokens, custo e latência.

Formulação adequada para o TCC: “A segmentação por sentenças apresentou ganhos pontuais de organização dos blocos, sem evidência suficiente de melhora global da classificação na amostra avaliada. A interpretação é limitada pela pequena quantidade de textos com cortes efetivamente alterados e pela variação observada entre execuções com entradas idênticas.”
