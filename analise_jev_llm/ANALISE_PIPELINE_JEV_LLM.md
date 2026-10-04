# Análise do pipeline JEV + LLM

Data: 04/10/2026. Fonte: `TCC.ipynb`, código e saídas salvas. As referências a células usam o índice JSON, começando em zero; os nomes das funções ajudam a localizá-las na interface.

O pipeline é um protótipo de mensuração de posições expressas em textos políticos. A arquitetura de cascata é uma hipótese de pesquisa adequada: avaliar se decisões inicialmente feitas pelo JEV podem ser melhoradas por um LLM com custo controlado. O principal trabalho pendente é alinhar o significado das saídas e o protocolo de avaliação antes de ampliar o roteamento entre modelos.

Esta análise não executou o notebook inteiro, não fez inferência remota e não alterou o notebook. Um diagnóstico local extraiu por AST apenas definições necessárias para testar funções puras com entradas sintéticas. O Python da `.venv` não iniciou no ambiente desta análise; foi usado Python 3.12.14 e Pydantic 2.13.5 do runtime disponível. Portanto, não houve validação integral do ambiente original. A consulta externa usou a documentação oficial via ferramenta web, pois a verificação de conectividade do Firecrawl falhou.

## 1. O que vale preservar

- Contrato comum de clientes LLM e respostas estruturadas.
- Separação entre classificação de chunks e agregação documental.
- Registro da decisão original do JEV e da decisão após fallback.
- Agrupamento dos eixos ambíguos por modelo, evitando uma chamada por eixo.
- Benchmark compartilhado com identificadores e validações.
- Reconhecimento explícito de que as perguntas do 8Values medem concordância interna, sem provar validade externa em planos de governo.
- Infraestrutura anterior de anotação, avaliação por eixo e bootstrap em blocos: `create_annotation_template`, `evaluate_axis_classifiers`, `predict_two_stage` e `bootstrap_plan_score_intervals`. Reaproveitar suas ideias e contratos, adaptando-os à cascata; não é necessário reconstruir tudo.

## 2. Prioridades metodológicas

### P0 — Separar relevância, posição e incerteza

Localização: `EstimateResultModel` (29), `_decisao_fallback` e `_agregar_resultados` (294), `_converter_values_para_previsoes_benchmark` (296).

O prompt aceita 50 como neutralidade, equilíbrio ou ausência de evidência. O fallback considera neutro o intervalo [45, 55]. Já o adaptador considera relevante qualquer escore cuja distância de 50 seja maior que 0,5. Com `descartar_neutros=True`, decisões neutras são descartadas antes dessa avaliação; com `False`, podem reaparecer como relevantes.

Reprodução: escore 52 gera classe `neutro`; sua agregação é 50 com descarte e 52 sem descarte; o adaptador considera 52 relevante. Além disso, as distribuições `(0,5; 0,5; 0)` e `(0; 0; 1)` para polo A, polo B e irrelevância geram o mesmo escore 50. Não é possível recuperar a relevância original a partir desse número.

Proposta: manter campos separados para relevância e posição. Distinguir posição central explícita, posições contraditórias, evidência insuficiente e ausência de conteúdo sobre o eixo. Avaliar classes diretamente; calcular o escore documental depois. Quando não houver evidência para um eixo, retornar `null`/`sem_evidencia`, com cobertura zero. Não atribuir automaticamente centralidade nem uma ideologia mais próxima.

### P0 — Evitar que probabilidades de classe sejam interpretadas como intensidade ideológica

Localização: `calcular_valor_esperado` e `_decisao_fallback` (294).

No JEV, o valor esperado combina probabilidades de polos e irrelevância. No LLM, o número é uma estimativa direta de posição. Esses números podem ter a mesma escala visual sem medir a mesma coisa. Uma probabilidade alta de pertencer ao polo A não estabelece, por si só, uma posição extrema dentro desse polo.

O fallback também calcula `confianca = abs(valor - 50) / 50` e transforma o escore em uma distribuição entre polos. Isso faz uma posição extrema parecer certa e uma posição moderada parecer incerta por construção.

Proposta: escolher um estimando comum. Para uma primeira versão, classificar direção e agregar balanço de posições. Se intensidade for necessária, definir uma rubrica ordinal explícita, por exemplo −2, −1, 0, +1, +2, e aplicá-la aos dois modelos. Guardar incerteza em outro campo. Não chamar o resultado de percentual de ideologia ou equivalência ao questionário respondido por uma pessoa sem validação adicional.

### P0 — Fazer uma comparação que isole o benefício do fallback

Localização: `AXIS_SPECS` (250), `criar_perguntas_jev` (268), `EIXOS_8VALUES` (294).

O JEV isolado usa perguntas separadas de relevância e polaridade, com descrições extensas. A cascata Choice usa uma pergunta de três classes por eixo, com descrições diferentes. Assim, comparar suas acurácias mistura mudanças de rubrica, estrutura das perguntas, conversão de scores e uso do LLM.

Proposta: centralizar as rubricas e executar a ablação JEV versus JEV + LLM sobre as mesmas respostas iniciais do JEV, preferencialmente em cache. Adotar o mesmo contrato de decisão e a mesma avaliação final para todos os sistemas. Os efeitos do 8Values são referências do instrumento: efeito zero não é prova independente de irrelevância semântica.

## 3. Confiança e roteamento

Segundo a [documentação oficial de confiança](https://docs.typesafe.ai/confidence), Choice usa `c = (p_max − 1/n) / (1 − 1/n)`; Noul não fornece esse campo. O código cria para Noul uma medida própria, usando `min(p_relevante, p_polo)` quando relevante. Portanto, os valores não são diretamente equivalentes.

Reprodução: relevância 0,8 e polaridade condicional `(0,75; 0,25)` geram distribuição conjunta `(0,6; 0,2; 0,2)`. A implementação Noul atribui confiança 0,75; a fórmula atual de Choice aplicada à mesma distribuição resulta em 0,40. Um limiar comum de 0,70 decide rotas diferentes.

Ainda sob a fórmula atual, em Choice com três classes, confiança ≥ 0,70 implica `p_max ≥ 0,80` e margem entre as duas maiores probabilidades ≥ 0,60. Nesse cenário, o limiar adicional de margem 0,20 não muda a aceitação. Confirmar a correspondência com a versão efetivamente usada nos experimentos antes de aplicar essa conclusão às execuções antigas.

Recomendações:

1. Registrar a confiança nativa sem reinterpretá-la como probabilidade empírica de acerto.
2. Preservar relevância e polaridade Noul/Choice separadamente e calibrar regras de encaminhamento próprias.
3. Avaliar taxa de erro por faixa de confiança e curvas de risco versus cobertura. Usar Brier/log-loss para distribuições probabilísticas apropriadas, não para intensidades políticas.
4. Escolher limiares na validação. Com poucos exemplos, começar com uma regra simples; só adotar limiares por eixo quando houver amostra suficiente.
5. Medir se o LLM corrige casos encaminhados, incluindo os que ele piora. Baixa confiança do JEV não garante que outro modelo resolverá o caso.
6. Permitir abstenção após o fallback, em vez de exigir uma posição sem evidência.

A distinção entre confiança reportada e probabilidade de acerto é a motivação da literatura de calibração; [Guo et al. (2017)](https://proceedings.mlr.press/v70/guo17a.html) oferecem uma referência metodológica. Isso não demonstra descalibração do JEV neste corpus: ela precisa ser medida.

As faixas da célula 317 são escolhas experimentais, não evidência de que cada modelo seja melhor naquela região. O comentário de que confiança ≥ 70% sempre fica no JEV não representa a regra geral do código, que também testa margem. Os resultados salvos do roteador mostram apenas Sabiá e Sabiazinho, portanto não demonstram contribuição do Sonnet.

## 4. Resultados salvos: leitura provisória

| Experimento | Célula | Acertos conjuntos salvos |
|---|---:|---:|
| JEV isolado Choice | 275 | 216/280 — 77,1% |
| JEV isolado Noul | 280 | 205/280 — 73,2% |
| Cascata Choice + Sabiá | 298 | 225/280 — 80,4% |
| Cascata Noul + Sabiá | 315 | 221/280 — 78,9% |
| Cascata com roteamento | 318 | 221/280 — 78,9% |

São registros existentes, não resultados reproduzidos nesta análise. A diferença aparente de 3,2 pontos percentuais entre a primeira e a terceira linha não pode ser atribuída isoladamente ao fallback, devido às diferenças de protocolo.

Há também inconsistência entre saídas da cascata: a célula 299 registra 49 perguntas/chamadas ao LLM, enquanto a 300 registra 50. Ambas registram 67 decisões de eixo. Seus contadores de execução são diferentes, e a célula 298 não tem contador. Isso é compatível com saídas de execuções distintas, mas não identifica a causa exata. Gerar tabelas a partir de um único artefato identificado por `run_id` antes de usar números no TCC.

Os 280 pares vêm de apenas 70 perguntas e quatro eixos. Não tratar os pares como 280 observações independentes. O benchmark também processa cada pergunta como um único chunk, de modo que não avalia a segmentação nem a agregação de documentos longos.

Na polaridade, a classe C aparece apenas nas previsões e tem suporte real zero. O Macro-F1 automático inclui essa classe, alterando sua interpretação. Definir previamente as classes: apresentar desempenho nos polos A/B, contar abstenções nos casos relevantes como falhas na avaliação integral e informar sua taxa separadamente. Não remover silenciosamente as abstenções para melhorar o resultado.

## 5. Agregação e segmentação

O pipeline dá o mesmo peso a cada chunk, apesar de tamanhos diferentes; chunks com sobreposição podem contabilizar a mesma evidência mais de uma vez. Janelas de 500–1000 tokens usadas na aplicação podem reunir várias propostas. A configuração padrão da função, por sua vez, é 1000–2000 tokens: registrar a configuração realmente executada.

Proposta: usar proposta ou unidade argumentativa como unidade de medição. Preservar título/seção como contexto e identificar offsets, página e trecho central. Contexto sobreposto pode ajudar a interpretar, mas cada unidade deve contribuir uma única vez para a agregação. `cl100k_base` deve ser tratado como contagem aproximada para provedores com outros tokenizadores; verificar o limite real do endpoint sem presumir equivalência.

Uma agregação inicial interpretável seria `S_e = 50 × (1 + média(z_i))`, com `z_i` em [−1, 1] segundo uma rubrica previamente definida, considerando apenas unidades relevantes com posição identificável. Essa é uma proposta de índice do documento, não a pontuação original do questionário. Informar junto ao escore: total de unidades, unidades relevantes, unidades com posição definida, abstenções, cobertura e proporções em cada polo. Não transformar baixa cobertura em 50. Não usar confiança como peso político sem justificar e testar esse estimando.

Comparar unidade argumentativa, parágrafo e janela de tokens como análise de sensibilidade. Avaliar também remoção de cabeçalhos, falhas de extração, negação, citação de adversários e propostas condicionais. Reaproveitar o bootstrap em blocos já presente, observando que ele mede variabilidade da amostragem textual; não captura sozinho erro de classificação nem validação do construto.

## 6. Problemas concretos de engenharia

| Prioridade | Localização | Evidência e proposta |
|---|---|---|
| Alta | `dividir_texto_em_chunks_caracteres`, 294 | Uma linha de 3001 caracteres retorna inteira com limite 1500. Dividir linhas longas e validar o tamanho final. |
| Alta | Filtro `if 10 in ...`, 310 | Seleciona 35 perguntas; `abs(efeito) == 10` selecionaria 69 no arquivo atual. Se o objetivo é magnitude, corrigir; se é o polo positivo, renomear e declarar a seleção. |
| Alta | `Result`, `DecisaoEixo`, 7/294 | Não impõem intervalos. Entrada sintética 120 no fallback produz confiança 1,4 e probabilidade −0,2. Validar valores finitos, intervalos, classes e soma da distribuição. |
| Alta | `processar_documento_com_jev`, 294 | Retorna apenas `Values`, perdendo rastreabilidade documental. Retornar também decisões por chunk, cobertura, configuração, uso, erros e métricas. |
| Média | Instrumentação do benchmark, 296 | Troca uma função em `globals()` durante execução assíncrona. Substituir por dependência explícita, callback ou retorno estruturado; evita interferência entre execuções concorrentes. |
| Média | Agregação de latências, 319 | A latência da pergunta inteira é atribuída a cada modelo após `explode`. Isso não mede latência individual; cronometrar chamadas JEV e LLM separadamente, incluindo filas e tentativas. |
| Média | `asyncio.gather`, 294 | Falha propagada pode interromper o lote, sem checkpoint dos sucessos. Persistir por unidade, limitar concorrência por provedor, definir timeouts e política de repetição para erros transitórios. Falha técnica não deve virar neutralidade. |
| Média | `_extrair_decisao_jev`, 294 | Funciona com atributos; um dicionário válido vira neutro com confiança zero. Não comprova falha do retorno atual do SDK, mas impede reuso direto de JSON/cache. Aceitar os dois formatos ou validar estritamente um deles. |
| Média | Cliente global, 294 | Injetar `jev_client` e separar inicialização de credenciais das definições. `os.environ[...] = os.getenv(...)` falha quando a variável está ausente. |
| Média | Dependências | `requirements.txt` não fixa versões e omite `typesafe-sdk`, instalado via `%pip`. Fixar o ambiente relevante e registrar versões de modelo, SDK, prompt, dados e configuração. |

O diagnóstico reproduzível está em `diagnostico_local.py`. Ele testa o comportamento original selecionado, sem chamar APIs. Os casos sintéticos demonstram possibilidades do código; não afirmam que entradas inválidas ou respostas em dicionário ocorreram nas inferências salvas.

## 7. Arquitetura proposta

```text
Documento + metadados de origem
  → extração e verificação do texto
  → unidades argumentativas com offsets e contexto
  → JEV: relevância e posição por eixo, sob rubrica comum
  → regra de encaminhamento escolhida na validação
      → aceitar JEV
      → LLM: reavaliar eixos encaminhados e indicar evidência textual
      → abster-se quando a evidência continuar insuficiente
  → decisões auditáveis por unidade
  → agregação com cobertura e incerteza
  → avaliação e visualização
```

Contrato sugerido por unidade/eixo: `document_id`, `unit_id`, `axis`, `relevant`, `position`, `status`, `evidence_spans`, `native_confidence`, `probabilities`, `method`, `model`, `routing_reason`, `run_id`. Distinguir metadados de confiança de posição ordinal; incluir probabilidades apenas quando produzidas pelo mecanismo apropriado. O fallback deve usar a mesma rubrica do JEV e responder apenas sobre eixos encaminhados, agrupados em uma chamada quando possível. Evidência textual serve para auditoria; não é prova automática de correção.

## 8. Experimento viável para o TCC

Pergunta de pesquisa sugerida: **Uma cascata JEV + LLM mantém ou melhora a classificação de posições políticas com menor custo que um LLM aplicado a todas as unidades?**

1. **Desenvolvimento:** manter as 70 perguntas como teste de coerência com o instrumento, sem apresentá-las como validação de planos. Agrupar todas as versões/traduções de uma pergunta no mesmo conjunto. Evitar ajustar prompts repetidamente no conjunto usado como teste final.
2. **Corpus externo:** anotar trechos de diferentes planos e documentos, com distribuição suficiente de eixos, polos e casos sem evidência. Dimensionar a amostra conforme recursos; um piloto serve para estimar dificuldades e suporte de cada classe. Anotação por dois avaliadores em ao menos uma parcela permite medir concordância e refinar a rubrica. Distinguir rótulos humanos de sementes geradas por IA.
3. **Separação:** dividir por documento, não por chunks vizinhos. Separar desenvolvimento/validação/teste; se houver poucos documentos, considerar avaliação agrupada ou deixar um documento de fora. Se a alegação for generalização a novos candidatos ou períodos, agrupar também nessas dimensões.
4. **Comparações mínimas:** classe majoritária, JEV apenas, LLM apenas, JEV + um LLM. Usar as mesmas unidades, rubricas, referência e métricas. Deixar múltiplos modelos, tradução e Noul como ablações posteriores para conter o escopo.
5. **Qualidade:** relevância por eixo; polaridade nos casos realmente relevantes; desempenho conjunto; abstenção e cobertura. Para score documental, comparar com anotação agregada ou referência externa adequada. Relatar estabilidade separadamente de validade.
6. **Benefício do fallback:** contar erro→acerto, acerto→erro e erros mantidos nos mesmos pares. Fazer comparação pareada e intervalos por reamostragem da pergunta ou documento, preservando dependências. Não usar acurácia condicional do fallback como se fosse a acurácia do LLM em todo o corpus.
7. **Eficiência:** chamadas, tokens faturados quando disponíveis, custo efetivo, latência por estágio e p50/p95. Redução de decisões delegadas não equivale automaticamente à mesma redução de chamadas ou dinheiro.
8. **Reprodutibilidade:** respostas brutas e decisões por unidade em JSONL/Parquet; configuração e hashes em manifesto; gráficos derivados desses arquivos. Calcular novas faixas a partir de dados em cache quando possível, sem repetir inferências desnecessariamente.

Critério de escolha: declarar antes da avaliação se o objetivo é maior qualidade sob um orçamento ou menor custo com perda máxima tolerada de qualidade. Selecionar na validação e reportar o teste final uma vez, com intervalos. Não afirmar superioridade com base apenas no maior percentual observado.

## 9. Ordem recomendada de implementação

1. Unificar o contrato de relevância/posição e remover a reconstrução de classes a partir do score final.
2. Centralizar rubricas, corrigir limites/filtro/validações e preservar o rastro completo.
3. Produzir uma execução identificada e reconciliar todas as tabelas existentes.
4. Comparar JEV, LLM e cascata de um único fallback no mesmo protocolo.
5. Validar em textos anotados, calibrar o encaminhamento e medir cobertura/custo.
6. Só então ampliar segmentação, Noul e roteamento entre vários LLMs como ablações.

O ganho mais defensável para o TCC está em demonstrar quando a cascata ajuda, quanto custa e onde ela deve se abster, com uma mensuração consistente e auditável.
