# Parecer centrado no notebook Pipeline - Passo a Passo

Data: 29/10/2026. Referência principal: [Pipeline - Passo a Passo.ipynb](<../Pipeline - Passo a Passo.ipynb>). Este documento refina o [parecer bibliográfico](REVISAO_ARTIGOS_E_AJUSTES_PIPELINE.md), distinguindo a pipeline de pesquisa das diferenças de sua réplica no aplicativo.

**Conclusão ajustada:** o notebook já incorpora boa parte das práticas recomendadas nas referências. A prioridade é avaliar melhor suas decisões e resolver uma inconsistência de configuração reproduzível. Não há fundamento para reconstruir a arquitetura, acrescentar outro bootstrap ou tratar o corte de 16 trechos da API como deficiência deste notebook.

Os índices de células abaixo começam em zero e correspondem ao JSON salvo. Não foi executado o notebook completo nem feita nova inferência. O SHA-256 do notebook analisado é `2fe1f3ef37e3133a63ac48fed18738555bc8aa14b7e81cf05a6c90d3fe7e5be2`.

## 1. O que já está contemplado

| Recurso | Onde está | Consequência para a recomendação |
|---|---|---|
| Escalas de cinco/nove níveis, rubricas por eixo, valores e hash | Células 6–10 | Avaliar âncoras e resolução; não implementar novamente uma escala ordinal. |
| Relevância, ausência de posição e abstenção distintas | `decidir_jev`, `decidir_llm`, `estado_da_decisao`; células 34, 70 e 96 | A distinção básica já existe. Separar descrição, mistura e centro explícito seria um refinamento adicional. |
| Regra `polo_primeiro` e intensidade condicional | `_normalizar_polaridade_ordinal` e `motivos_fallback`; células 32 e 40 | Comparar a regra com `nivel`; não recomendá-la como funcionalidade ausente. |
| JEV inicial e cascata nas mesmas entradas | `classificar_texto`, `avaliar_registros`; células 77 e 96 | A ablação pareada básica já existe e é adequada. O problema do script separado da API não se aplica a esta comparação. |
| Registro de razões, tentativas e latências | Células 60, 77 e 127 | Aproveitar os registros para medir benefício do encaminhamento. |
| Citações literais e auditoria de posição/intensidade | Células 64, 70 e 74 | A auditoria já existe; falta avaliar quando suas discordâncias justificam intervenção. |
| Segmentação por sentenças, diagnóstico e preservação estrutural | Células 106–110 e `tcc_lib/segmentacao.py` | Comparar o recurso disponível com o modo de tokens, após resolver a configuração. |
| Média, contagens, cobertura e média só entre direcionais | `resumir_eixo_ordinal`, célula 119 | Usar a informação já calculada para interpretar o centro; não propor a média direcional como recurso novo. |
| Bootstrap em blocos preservando ausências | Células 115–119 | Preservar e avaliar sensibilidade ao bloco; o bootstrap independente está na API. |
| Resultado com um trecho, sem corte fixo de suficiência | Células 115 e 119 | O limiar de 16 trechos é da aplicação, não deste resumo. |
| Escada de intensidade explicitamente descrita como diagnóstico sintético | Células 139 e 150 | Complementar com anotação independente; a limitação já é reconhecida. |
| Prévia congelada, manifesto, exportação incremental e relatórios | Células 100–102, 127 e 175–178 | Fortalecer a comparação entre rodadas, preservando essa infraestrutura. |

Não se deve interpretar os comentários de limitação do notebook como ausência de implementação. Em vários pontos, ele já registra a ressalva metodológica correta.

## 2. A configuração efetiva depende da seção

O arquivo inicializa `ESCALA_ATUAL` com cinco níveis, mas especializa as seções experimentais:

| Seção | Escala | Regra | Fallback LLM | Busca/auditoria de evidências |
|---|---|---|---|---|
| Benchmark 8values, célula 92 | Nove níveis | `polo_primeiro` | Ligado | Desligadas |
| Playground, células 161–162 | Nove níveis | `polo_primeiro` | **Desligado** | Ligadas |
| Testes de textos, células 172–173 | Nove níveis | `polo_primeiro` | Ligado pela configuração herdada | Ligadas |

As três configurações usam polaridade `choice` no estado salvo. O playground seleciona `sabiazinho-4` na célula 162, mas com `usar_fallback=False` esse modelo não decide as classificações. As chamadas de busca/verificação são do JEV. Não apresentar esse playground como evidência do desempenho de uma cascata com Sabiazinho.

Ter configurações experimentais diferentes é legítimo. Para compará-las, explicitar qual variável está mudando. O benchmark avalia uma pergunta por unidade, sem testar segmentação e agregação de planos longos.

### Inconsistência reproduzida: dois nomes para o alvo de tokens

Na célula 2, `CONFIG_CHUNKS` contém `max_tokens=600`. Na célula 161, `CONFIG_PLAYGROUND['chunks']` expande essa configuração e acrescenta `tokens_alvo=600`. O segmentador recusa os dois simultaneamente:

```text
ValueError: Use tokens_alvo ou o alias antigo max_tokens, não os dois.
```

O erro foi reproduzido localmente com a função exportada do próprio notebook. É um bloqueio de preparação quando a configuração do playground herda a configuração inicial. Se a célula 171 tiver sido executada antes, ela redefine `CONFIG_CHUNKS` somente com `tokens_alvo`, alterando esse comportamento. Isso explica a dependência do estado do kernel; não prova que uma saída histórica tenha sido gerada com erro.

**Ajuste concreto recomendado:** padronizar o nome `tokens_alvo` na configuração inicial e dar nomes próprios às configurações de seção. Conferir a preparação do playground num kernel limpo antes de inferências. Essa correção ainda não foi aplicada nesta análise.

## 3. O que os resultados salvos realmente mostram

Reanalisei a rodada [20261029T175131246256Z](../runs/benchmark_8values/20261029T175131246256Z/benchmark_comparacao.csv), referenciada nas saídas do notebook. Foram conferidos:

- As 70 perguntas e sua ordem contra o manifesto e o JSONL.
- O hash das perguntas.
- A configuração e a escala dos registros contra o manifesto.
- O hash das rubricas reconstruídas pelo código atual contra o hash da rodada: **coincidem**.

Os números abaixo são recálculos dos registros existentes pela função `avaliar_registros`, sem repetir chamadas aos provedores.

| Medida | JEV inicial | Cascata final |
|---|---:|---:|
| Acertos conjuntos, 280 pares | 216/280 — 77,14% | 219/280 — 78,21% |
| Direção correta, nos 116 pares relevantes pelo instrumento | 62/116 — 53,45% | 62/116 — 53,45% |
| Relevantes detectados, nos 116 esperados | 79/116 — 68,10% | 74/116 — 63,79% |
| Irrelevantes corretos, nos 164 esperados | 154/164 — 93,90% | 157/164 — 95,73% |

O ganho líquido de três acertos conjuntos vem do saldo de acertos nos pares esperados como irrelevantes; o total de direções corretas permanece igual. Isso não quer dizer que os mesmos pares mantiveram a direção: existem correções e regressões que se compensam.

| Eixo | Acertos conjuntos JEV → cascata | Direções corretas JEV → cascata |
|---|---:|---:|
| Econômico | 62 → 61, de 70 | 15 → 13, de 22 |
| Diplomático | 59 → 58, de 70 | 15 → 14, de 24 |
| Estado | 44 → 49, de 70 | 14 → 17, de 37 |
| Sociedade | 51 → 51, de 70 | 18 → 18, de 33 |

Na avaliação conjunta pareada, houve **9 erros corrigidos e 6 acertos transformados em erro**. A diferença global é +1,07 ponto percentual. Um bootstrap pareado de 10.000 réplicas, reamostrando perguntas completas com seus quatro eixos, produziu intervalo de aproximadamente **−1,43 a +3,93 p.p.** para essa diferença. Ele inclui zero e não sustenta uma conclusão firme de superioridade global. É uma análise de desenvolvimento, sem corrigir os efeitos de ajustes prévios no instrumento.

Foram encaminhados 63 pares pergunta/eixo em 43 perguntas, resultando em 43 chamadas lógicas ao LLM e 43 tentativas registradas pelo código. Não confundir os 22,5% dos pares encaminhados com a proporção de chamadas: 43/70 perguntas, ou 61,4%, recorreram ao LLM. Esses registros não estabelecem o custo faturado nem a qualidade de um LLM aplicado a todas as perguntas, braço ausente desta rodada.

**Implicação:** medir benefício por eixo e motivo de encaminhamento é mais útil agora do que acrescentar outro modelo à cascata. O eixo Estado concentra o ganho observado, mas uma única rodada de desenvolvimento não justifica uma regra de produção específica para ele.

## 4. Cuidado antes de interpretar toda divergência como erro do classificador

O próprio notebook explica que efeito zero equivale a irrelevância somente por convenção do benchmark. Existe também uma questão nos efeitos não nulos: alguns ligam uma opinião a valores do questionário por associação, enquanto a rubrica atual exige evidência substantiva sobre o tema do eixo.

Exemplos em `tcc/questions.json`:

- Pergunta 6, sobre tarifas para incentivar a produção local, recebe `govt=-10`; a rubrica atual de Estado trata principalmente de liberdade civil e autoridade estatal.
- Pergunta 18, sobre apoiar uniões regionais, recebe efeitos nos quatro eixos; o conteúdo explícito é sobretudo diplomático.
- Pergunta 69, sobre tratamento igual independentemente de cultura ou sexualidade, recebe +10 nos quatro eixos; igualdade de tratamento não implica necessariamente redistribuição econômica explícita.

Esses exemplos exigem revisão humana à luz do objeto medido. Não demonstram automaticamente erro do questionário nem correção de uma resposta específica do modelo. Mostram por que aderência aos efeitos do instrumento e acurácia semântica não são a mesma medida.

Há 37 falsos negativos de relevância do JEV **em relação a esse mapeamento**, e 28 não foram encaminhados ao LLM. É um ponto de auditoria, mas **não se deve simplesmente relaxar o limiar para recuperar todos**: parte pode refletir o desacordo conceitual acima. Primeiro construir um gabarito humano compatível com as rubricas; depois calibrar sensibilidade e custo.

## 5. Melhorias que permanecem recomendadas à luz dos artigos

### Prioridade imediata: consistência e diagnóstico

1. Resolver o conflito `max_tokens`/`tokens_alvo` e separar configurações de seção.
2. Acrescentar às tabelas do benchmark ganho/regressão pareados e decomposição de relevância/direção, reaproveitando os registros que já existem.
3. Avaliar separadamente encaminhamentos por relevância, direção e intensidade. Os motivos podem se sobrepor; não somar suas contagens como casos independentes.
4. Usar rótulos humanos independentes para distinguir erro semântico de divergência com o questionário.

### Prioridade metodológica: validar a resolução e o significado do índice

- **Cinco versus nove níveis:** já são configuráveis. Falta demonstrar que os níveis adicionais são distinguíveis por humanos e úteis na tarefa. A escada derivada dos próprios exemplos da rubrica é diagnóstico de consistência, não essa demonstração.
- **Centro e heterogeneidade:** já existem contagens e `índice A entre posicionados`. Expô-los lado a lado. Se necessário, acrescentar um campo que separe mistura de polos de descrição temática sem posição; isso amplia o contrato atual.
- **Conteúdo e autoria:** o notebook escolhe explicitamente classificar posições expressas, inclusive por terceiros. Preservar essa escolha. Só acrescentar atribuição/endosso se a pergunta de pesquisa exigir posição de um ator; não transformar isso num pré-requisito obrigatório para classificar conteúdo.
- **Auditoria semântica:** a função registra contradição/insuficiência sem alterar classificação, relevância ou fallback. Isso está documentado e é uma escolha conservadora. Uma evolução possível é comparar “só registrar” com “pedir revisão ou abster-se”, após validar o verificador contra humanos. Não descartar resultados automaticamente porque um segundo modelo discordou.

### Experimentos adicionais: executar depois do protocolo-base

| Referência | Experimento que acrescenta algo ao notebook | Limite |
|---|---|---|
| Benoit et al. | Comparar média granular com resumo por eixo seguido de classificação em planos completos | É outro estimador; não substitui o caminho atual sem avaliação documental. |
| Haroon et al. | Usar demonstrações completas anotadas e balanceadas, além das situações/exemplos das âncoras | As demonstrações devem vir do desenvolvimento, sem consultar o teste. |
| Duan et al. | Tornar a distribuição e a coexistência de posições visíveis junto à média | Adaptar a distinção conceitual; não transplantar a fórmula de ambivalência moral. |
| Chen et al. e Németh | Testar transferência entre temas, gêneros e autores e versões com identidade ocultada | Manter informações necessárias ao sentido e à atribuição. |
| KOKKAI DOC | Padronizar o formato de resumos se o experimento de síntese for adotado | Filtrar somente opiniões mudaria o alvo atual, que inclui descrições e definições. |

As fontes e páginas estão no parecer bibliográfico. Nenhuma dessas referências valida diretamente os limiares atuais ou estabelece que outro provedor resolveria os erros observados.

## 6. Recomendação final para esta versão

Manter a arquitetura, as rubricas explícitas, o rastreamento das duas etapas, as abstenções e o bootstrap em blocos. Trabalhar primeiro no protocolo-base e na referência de avaliação. O benchmark salvo oferece um bom mecanismo de depuração, mas seu pequeno ganho global não é evidência suficiente para intensificar o uso do LLM ou ampliar modelos.

A diferença API/notebook continua relevante para transportar resultados ao aplicativo, porém pertence à etapa de integração. O corte de 16 e o bootstrap independente não devem ocupar o lugar das prioridades internas do notebook.

Reprodução desta reavaliação:

```powershell
.\.venv\Scripts\python.exe analise_jev_llm\avaliacao_notebook_referencias.py
```

[Código de análise local](avaliacao_notebook_referencias.py) e [resultados completos](avaliacao_notebook_referencias.json). O código verifica hashes, reavalia os registros, calcula diferenças pareadas e reproduz a inconsistência de preparação. Nenhuma célula de APIs é executada. O notebook e os registros originais permanecem inalterados.
