# Comparação das rodadas de classificação de textos

Rodada nova: `20261102T224147973988Z`. Referência principal: `20261029T225701730206Z`.

**Conclusão:** o resultado é misto. Houve mudança em 13 de 112 combinações texto–eixo (11,6%), afetando 10 de 28 textos. Os 28 textos originais e os 58 trechos são idênticos entre essas duas rodadas. A nova configuração aumenta algumas detecções de Autoridade e remove um indício indevido de Progresso, mas também produz inversões diplomáticas discutíveis e mantém decisões sem evidência selecionada.

A base não contém gabarito humano. Mudança de pontuação, maior confiança ou um parecer de evidência favorável não demonstram, isoladamente, melhoria de acurácia.

## Fontes e método

Foram comparados os arquivos `protocolo.json`, `comparacao.csv`, `entrada.json`, `registros.jsonl` e os snapshots de rubricas nos `fluxograma.html`. O HTML agregado foi tratado como apresentação dos resultados; os números foram calculados sobre os arquivos estruturados da mesma pasta. Não houve chamadas novas a provedores.

- [Resultado novo](<C:/Users/User/Desktop/TCC/runs/testes_textos/20261102T224147973988Z/resultados_textos.html>)
- [Resultado anterior](<C:/Users/User/Desktop/TCC/runs/testes_textos/20261029T225701730206Z/resultados_textos.html>)
- [Protocolo novo](<C:/Users/User/Desktop/TCC/runs/testes_textos/20261102T224147973988Z/protocolo.json>)
- [Protocolo anterior](<C:/Users/User/Desktop/TCC/runs/testes_textos/20261029T225701730206Z/protocolo.json>)

A ausência de `contexto_posicao_politica` no protocolo antigo não significa ausência de contexto no prompt: o contexto está presente nas instruções congeladas dos fluxogramas. Esses snapshots foram inspecionados para comparar o prompt efetivo.

## Parâmetros

| Parâmetro | 29/10 | 02/11 |
|---|---|---|
| Modelo JEV | jev-1.13.0 | igual |
| Modelo LLM | sabia-4 | igual |
| Temperatura LLM | 0 | igual |
| Timeout / tentativas LLM | 360 s / 3 | igual |
| Regra / primitiva | polo_primeiro / choice | igual |
| Relevância / intensidade / direção | 0,60 / 0,50 / 0,20 | igual |
| Busca e checagem semântica | ambas ativas | igual |
| Limiar de existência de evidência | 0,70 | igual |
| Segmentação | sentenças, alvo 600, overlap 0, cl100k_base | igual |
| Escala numérica | 9 níveis, códigos −4 a +4, valores 0 a 1 | igual |
| Identificador da escala | ordinal_9_v1 | ordinal_9_teste_prompt_rubricas_v1 |
| Rubricas | “propõe” / “defende”; centro inclui descrições sem defesa | “propõe ou caracteriza” / “expressa ou caracteriza”; descrição não implica centro |

O contexto novo acrescenta a distinção entre defender e rejeitar uma posição. A pergunta de polaridade passa a perguntar pela proposta, ideia, modelo ou arranjo apresentado. A intensidade passa a considerar também o alcance do modelo caracterizado. A relevância passa a mencionar explicitamente ideias, definições e modelos. Foram alteradas as 36 situações dos quatro eixos e adicionados dois exemplos descritivos nos extremos do eixo estatal. Logo, a comparação testa um conjunto de mudanças de prompt e rubricas; não isola o efeito de cada frase.

## Métricas

| Métrica | 29/10 | 02/11 |
|---|---:|---:|
| Textos | 28 | 28 |
| Trechos | 58 | 58 |
| Erros de execução por texto | 0 | 0 |
| Combinações documento–eixo com índice | 30 | 32 |
| Chamadas LLM | 35 | 33 |
| Eixos encaminhados ao LLM | 46 | 45 |
| Chamadas JEV de classificação | 58 | 58 |
| Chamadas JEV de evidências | 84 | 82 |
| Decisões finais direcionais por trecho–eixo | 55 | 54 |
| Decisões finais “sem posição” por trecho–eixo | 2 | 5 |
| Decisões finais sem evidência temática por trecho–eixo | 173 | 171 |
| Decisões com citação não verificada | 2 | 2 |
| Latência média por trecho | 1,13 s | 1,23 s |

Os estados de decisão são contados sobre 58 × 4 = 232 pares trecho–eixo, enquanto os índices do documento são contados sobre 28 × 4 = 112 pares documento–eixo. Os 99 pares documento–eixo sem mudança incluem 78 ausências em ambas as rodadas e 21 índices numéricos iguais. Dos 13 pares alterados, 7 mudaram de valor e 6 mudaram a disponibilidade do índice.

As chamadas LLM caíram de 35 para 33 (−5,7%). Isso não trouxe redução observada de latência: a média por trecho subiu aproximadamente 8,7%. As latências são as registradas nos wrappers; não representam um benchmark controlado de desempenho. Na auditoria, `semantic/sustenta` foi de 47 para 50, `semantic/insuficiente` ficou em 4 e `search/not_selected` caiu de 6 para 5.

## Casos que merecem atenção

### União homoafetiva: nova direção final veio do limiar da cascata

`textos_pequenos_006`: no eixo estatal, passou de ausência de índice para Liberdade 37,5 / Autoridade 62,5. O JEV já atribuía nível −1 em ambas as rodadas. Antes, a probabilidade condicional da intensidade era 0,4066 e acionava o LLM, que devolvia ausência de evidência no eixo. Agora ela é 0,5158, acima do corte 0,50: o nível −1 do JEV foi mantido. No eixo social, Tradição subiu de 87,5 para 100; também houve mudança de uma decisão revisada pelo LLM para aceitação direta do JEV. Eu revisaria o alcance dessa intensidade máxima: o texto trata de um tema específico e a rubrica máxima fala em imposição ampla de normas tradicionais.

`textos_pequenos_017`: o eixo estatal também passou a Autoridade 62,5. O nível JEV continuou −1; a probabilidade condicional passou de 0,4789 para 0,5217. A busca de evidência ficou abaixo do corte (0,63 < 0,70), e o índice foi mantido mesmo sem passagem selecionada. A direção é plausível pela restrição de direitos, mas a nova detecção não comprova que o sistema passou a compreender melhor descrições: nos dois exemplos o JEV já dava a mesma direção anteriormente.

### BRICS / OCDE: a revisão de intensidade inverteu a direção

`textos_pequenos_014`: Globo 87,5 virou Globo 12,5 / Nação 87,5. O JEV escolheu +3 nas duas rodadas; na nova, sua probabilidade total de Globo inclusive subiu de 0,54 para 0,74. Porém, a probabilidade condicional do nível escolhido caiu de 0,5185 para 0,4865. Isso acionou o LLM por intensidade ambígua, e o LLM devolveu −3. O trecho combina saída de um bloco com entrada em outro: eu revisaria ambos os extremos fortes, pois a mera troca de organismo não estabelece, sozinha, predominância clara entre autonomia nacional e integração. A auditoria semântica marcou apoio tanto para a antiga direção A quanto para a nova B.

### Negação e multilateralismo: possível regressão

`textos_pequenos_015`: Globo 75 virou Globo 37,5 / Nação 62,5. Em ambas as rodadas houve revisão por direção ambígua. O LLM antigo citava “fortalecer organismos multilaterais para enfrentar conflitos”; o novo cita a rejeição à subordinação a pressões estrangeiras. Há conteúdo dos dois polos, mas a nova resposta dá precedência à rejeição de pressão e perde a defesa explícita do multilateralismo. Esse caso merece revisão humana antes de afirmar melhora no tratamento de negações.

### Relevância social: uma remoção adequada e novas entradas discutíveis

`textos_grandes_008` (Eletrobras): o índice social de Progresso 75 desapareceu. Antes, o LLM o sustentava com uma passagem sobre mudanças climáticas e energia limpa. A remoção é coerente com a própria rubrica, que não considera ambiente/tecnologia, isoladamente, posição sobre costumes.

`textos_pequenos_013` (cestas de agricultura familiar na escola): surgiu índice social 50. O eixo econômico permaneceu 75. O trecho não explicita valores ou costumes; há possível excesso de relevância social. A busca de evidência da nova decisão central retornou apenas 0,12, sem selecionar passagem.

`textos_grandes_004` (envelhecimento populacional) passou de ausência a centro social 50. `textos_grandes_006` (telessaúde) fez o movimento inverso, de centro social 50 para ausência. Esses movimentos mostram que o limiar de relevância continua sensível mesmo quando não existe uma mudança de direção ideológica.

## Todas as alterações frente a 29/10

Todos os valores abaixo são índices do **polo A**: Igualdade, Globo, Liberdade e Progresso. “—” indica ausência de índice; 50 indica centro classificado. Não são probabilidades de acerto.

| Texto | Eixo | Antes | Agora | Variação (p.p.) |
|---|---|---:|---:|---:|
| [textos_grandes_002](<C:/Users/User/Desktop/TCC/runs/testes_textos/20261102T224147973988Z/textos_grandes_002/fluxograma.html>) | economic | 31,25 | 25 | -6,25 |
| [textos_grandes_008](<C:/Users/User/Desktop/TCC/runs/testes_textos/20261102T224147973988Z/textos_grandes_008/fluxograma.html>) | economic | 50 | 41,67 | -8,33 |
| [textos_pequenos_014](<C:/Users/User/Desktop/TCC/runs/testes_textos/20261102T224147973988Z/textos_pequenos_014/fluxograma.html>) | diplomatic | 87,5 | 12,5 | -75 |
| [textos_pequenos_015](<C:/Users/User/Desktop/TCC/runs/testes_textos/20261102T224147973988Z/textos_pequenos_015/fluxograma.html>) | diplomatic | 75 | 37,5 | -37,5 |
| [textos_grandes_006](<C:/Users/User/Desktop/TCC/runs/testes_textos/20261102T224147973988Z/textos_grandes_006/fluxograma.html>) | state | 68,75 | 62,5 | -6,25 |
| [textos_grandes_010](<C:/Users/User/Desktop/TCC/runs/testes_textos/20261102T224147973988Z/textos_grandes_010/fluxograma.html>) | state | 40,62 | 44,08 | 3,45 |
| [textos_pequenos_006](<C:/Users/User/Desktop/TCC/runs/testes_textos/20261102T224147973988Z/textos_pequenos_006/fluxograma.html>) | state | — | 37,5 | — |
| [textos_pequenos_017](<C:/Users/User/Desktop/TCC/runs/testes_textos/20261102T224147973988Z/textos_pequenos_017/fluxograma.html>) | state | — | 37,5 | — |
| [textos_grandes_004](<C:/Users/User/Desktop/TCC/runs/testes_textos/20261102T224147973988Z/textos_grandes_004/fluxograma.html>) | society | — | 50 | — |
| [textos_grandes_006](<C:/Users/User/Desktop/TCC/runs/testes_textos/20261102T224147973988Z/textos_grandes_006/fluxograma.html>) | society | 50 | — | — |
| [textos_grandes_008](<C:/Users/User/Desktop/TCC/runs/testes_textos/20261102T224147973988Z/textos_grandes_008/fluxograma.html>) | society | 75 | — | — |
| [textos_pequenos_006](<C:/Users/User/Desktop/TCC/runs/testes_textos/20261102T224147973988Z/textos_pequenos_006/fluxograma.html>) | society | 12,5 | 0 | -12,5 |
| [textos_pequenos_013](<C:/Users/User/Desktop/TCC/runs/testes_textos/20261102T224147973988Z/textos_pequenos_013/fluxograma.html>) | society | — | 50 | — |

## Histórico das rodadas

| Rodada (UTC) | Textos | Trechos | LLM | Erros | Documento–eixos com índice |
|---|---:|---:|---:|---:|---:|
| 20261102T224147973988Z | 28 | 58 | 33 | 0 | 32 |
| 20261029T225701730206Z | 28 | 58 | 35 | 0 | 30 |
| 20261026T223034117817Z | 28 | 58 | 35 | 0 | 30 |
| 20261024T214140525692Z | 28 | 58 | 35 | 0 | 33 |
| 20261024T184909667917Z | 28 | 59 | 37 | 0 | 31 |
| 20261023T014240545881Z | 28 | 59 | 45 | 0 | 32 |
| 20261020T010032139196Z | 28 | 59 | 38 | 0 | 33 |
| 20261019T233334959801Z | 28 | 59 | 37 | 0 | 33 |

As rodadas de 26/10 e 29/10 têm os mesmos 28 textos e 58 trechos, mas os prompts efetivos não são iguais: a de 29/10 já acrescentava o contexto de posições expressas, definições e terceiros. Entre elas mudaram 12 pares documento–eixo em 9 textos. A rodada atual mudou 13 pares em 10 textos frente a 29/10. Isso não constitui medição de variabilidade sob prompt fixo.

As rodadas de 24/10 às 21:41 UTC e 26/10 registram os mesmos prompts no snapshot inspecionado, porém há diferença de trechos em dois documentos (`textos_grandes_005` e `textos_grandes_010`). As rodadas mais antigas têm 59 trechos; em 19/10 o LLM configurado era `sabiazinho-4`, e a regra de decisão não estava registrada em algumas versões. Elas servem como histórico, sem permitir atribuir diferenças somente às novas rubricas.

## Limites e próximo teste

O trecho original sobre ditadura, com Duverger e Bobbio, **não aparece entre os 28 textos desta rodada**. Assim, este lote não verifica diretamente o caso que motivou a revisão. Eu incluiria esse trecho e pares de controle (definição, defesa explícita, rejeição explícita e posição mista), mantendo entradas e configurações congeladas e usando gabarito humano de relevância, direção e intensidade. Como prompt e rubricas mudaram juntos, também seria útil separar essas alterações em variantes próprias.

## Arquivos desta comparação

- [Mudanças por texto e eixo (CSV)](<C:/Users/User/Desktop/TCC/runs/comparacoes/20261102_prompt_rubricas/mudancas_por_texto_e_eixo.csv>)
- [Métricas e comparações históricas (JSON)](<C:/Users/User/Desktop/TCC/runs/comparacoes/20261102_prompt_rubricas/dados_comparacao.json>)
- [Parâmetros e prompts efetivos comparados (JSON)](<C:/Users/User/Desktop/TCC/runs/comparacoes/20261102_prompt_rubricas/parametros_e_prompts.json>)
