# Parâmetros da versão oficial

O site e a extensão oficiais usam **`api/analysis-config.json`**, lido pela API ao iniciar. O arquivo contém todos os campos de `ExperimentConfig` usados no Lab, incluindo o contexto do prompt, a escala completa e suas rubricas. Edite o JSON e reinicie a API para aplicar aos dois clientes, sem recompilar. Recarregue o site/painel ou use **Verificar conexão e modos** para atualizar as capacidades exibidas.

Para usar outro arquivo, defina `ALGORITHM_CONFIG_PATH` no ambiente da API. Caminhos relativos partem de `app/api`, independentemente da pasta de inicialização. Use JSON UTF-8 (com ou sem BOM), sem comentários. Arquivos ausentes, JSON inválido, campos desconhecidos e valores fora do contrato impedem a inicialização.

Os valores padrão abaixo correspondem ao conteúdo atual de [`api/analysis-config.json`](api/analysis-config.json). Os padrões internos do contrato e os do Lab podem ser diferentes; substituições por variáveis de ambiente seguem a prioridade descrita adiante.

| Campo | Valor padrão no JSON atual | Explicação | Opções / limites |
|---|---|---|---|
| `contexto_posicao_politica` | Texto atual sobre posições expressas, definições, citações e críticas | Contexto do prompt compartilhado pelo JEV, pelo LLM e pela auditoria de evidências. Editável também no Lab; registrado em `effective_config`, no hash e nos presets. | Texto não vazio, até 20.000 caracteres |
| `escala` | `ordinal_9_v1`, versão `1`, com nove níveis e rubricas completas | Define os níveis de posição e intensidade, sua conversão em pontuação e as situações e exemplos usados na classificação de cada eixo. | Objeto validado com níveis e rubricas; aceita cinco níveis e outras escalas válidas do contrato |
| `primitiva_polaridade` | `score` | Escolhe como o JEV classifica a polaridade: `score` usa níveis ordenados; `choice` escolhe entre alternativas de nível. A relevância continua usando Choice. Aplica-se aos modos baixo e médio. | `score`, `choice` |
| `regra_decisao` | `nivel` | Define como converter a distribuição do JEV em um nível: `nivel` escolhe o nível individual mais provável; `polo_primeiro` soma as probabilidades por polo A, B e sem posição, escolhe o grupo mais provável e depois a intensidade dentro dele. | `nivel`, `polo_primeiro` |
| `chunk_tokens` | `500` | Define o tamanho dos trechos em tokens. Na estratégia `sentencas`, funciona como alvo: frases longas permanecem inteiras e podem ultrapassá-lo. Trechos menores podem aumentar o número de chamadas. | Inteiro de 100 a 2.000, até `MAX_TOKENS` |
| `chunk_strategy` | `sentencas` | Escolhe como dividir o texto: `sentencas` agrupa frases preservando seus limites; `tokens` corta pela contagem de tokens e pode dividir frases. | `tokens`, `sentencas` |
| `relevance_margin_min` | `0.60` | Margem mínima entre as probabilidades de relevante e não relevante no JEV. Abaixo dela, sinaliza `relevancia_ambigua`. | 0 a 1 |
| `level_confidence_min` | `0.50` | Com `nivel`, confiança mínima informada pelo JEV para o nível; abaixo dela, sinaliza `baixa_confianca_nivel`. Com `polo_primeiro`, é o suporte condicional mínimo da intensidade dentro do polo escolhido; abaixo dele, sinaliza `intensidade_ambigua`. | 0 a 1 |
| `direction_margin_min` | `0.20` | Com `nivel`, diferença mínima entre as probabilidades totais dos polos A e B para uma posição direcional. Com `polo_primeiro`, margem mínima entre os dois grupos mais prováveis (A, B ou sem posição). Abaixo dela, sinaliza `direcao_ambigua`. | 0 a 1 |
| `min_valid_chunks` | `1` | Quantidade mínima de trechos relevantes com nível válido por eixo para indicar evidência suficiente. Abaixo desse número, a estimativa disponível recebe o aviso `evidencia_limitada`; o corte não altera a média. | Inteiro positivo, até `MAX_CHUNKS` |
| `bootstrap_samples` | `2000` | Número de reamostragens com reposição dos valores válidos por eixo para calcular o intervalo de 95% da média. O intervalo é calculado quando há pelo menos dois valores válidos. | Inteiro de 200 a 10.000 |
| `bootstrap_seed` | `42` | Semente do gerador aleatório do bootstrap. Reproduz o intervalo para os mesmos valores de entrada; não garante respostas idênticas dos provedores. | Inteiro de 0 a 2³² − 1 |
| `jev_model` | `jev-1.13.0` | Modelo TypeSafe usado na classificação dos modos baixo e médio e nas etapas de busca e verificação de evidências quando habilitadas. | Modelo JEV permitido no servidor |
| `llm_model` | `sabia-4` | Modelo usado para revisar os casos sinalizados pelo JEV no modo médio e para classificar diretamente no modo alto. No modo baixo, não é usado. | Modelo Maritaca ou Gemini permitido no servidor |
| `semantic_evidence_check` | `true` | Ativa a verificação pelo JEV de que a citação, no contexto do trecho, sustenta a posição e a intensidade atribuídas. Registra apoio, contradição ou insuficiência na auditoria, sem alterar a classificação ou a pontuação. Exige TypeSafe também no modo alto. | `true`, `false` |
| `jev_evidence_search` | `true` | Nos modos baixo e médio, busca uma citação para cada decisão final do JEV e recupera a passagem do texto original pelo ID selecionado. A busca não filtra os trechos usados na média. | `true`, `false` |
| `evidence_existence_min` | `0.70` | Limiar mínimo do teste de existência de evidência para aceitar uma passagem encontrada na busca do JEV. Só tem efeito quando `jev_evidence_search` está ativo. | 0 a 1 |

Os três limiares de classificação do JEV (`relevance_margin_min`, `level_confidence_min` e `direction_margin_min`) produzem avisos de incerteza no modo baixo e acionam revisão pelo LLM no modo médio. Eles não se aplicam à classificação direta do modo alto.

O objeto `escala` contém os seguintes campos. As listas completas de níveis, situações e exemplos permanecem no JSON, que é a referência para os valores textuais.

| Campo dentro de `escala` | Valor padrão no JSON atual | Explicação |
|---|---|---|
| `id` | `ordinal_9_v1` | Identificador da escala registrada na configuração e nos resultados. |
| `versao` | `1` | Versão da definição da escala. |
| `niveis` | Nove níveis, do polo B muito forte ao polo A muito forte, com `sem_posicao` no centro | Lista ordenada de posições e intensidades disponíveis para classificação. |
| `niveis[].chave` | De `polo_B_muito_forte` a `polo_A_muito_forte`, incluindo `sem_posicao` | Identificador textual de cada nível, também usado para associar suas rubricas. |
| `niveis[].codigo` | `-4`, `-3`, `-2`, `-1`, `0`, `1`, `2`, `3`, `4` | Identificador numérico do nível retornado pela classificação. A pontuação é definida por `valor`. |
| `niveis[].rotulo` | Rótulos do JSON, como `polo B muito forte`, `sem posicao` e `polo A muito forte` | Nome exibido para o nível. |
| `niveis[].polo` | `B` nos quatro primeiros níveis, `null` no centro e `A` nos quatro últimos | Grupo ao qual o nível pertence; `null` representa ausência de posição entre os polos. |
| `niveis[].valor` | `0.0`, `0.125`, `0.25`, `0.375`, `0.5`, `0.625`, `0.75`, `0.875`, `1.0` | Valor normalizado convertido em 0–100 para o polo A e usado na média do eixo. A pontuação do polo B é o complemento para 100. |
| `rubricas_por_eixo` | `economic`, `diplomatic`, `state`, `society`, cada um com os nove níveis | Regras de classificação específicas dos eixos econômico, diplomático, estatal e social. |
| `rubricas_por_eixo.<eixo>.<chave>.situacao` | Texto específico de cada combinação de eixo e nível no JSON | Descreve a posição e o alcance da mudança que caracterizam aquele nível. |
| `rubricas_por_eixo.<eixo>.<chave>.exemplos` | Dois exemplos por combinação de eixo e nível no JSON | Ilustra propostas ou posições que correspondem à situação descrita na rubrica. |

Para levar parâmetros do Lab à versão oficial, use o objeto **`config`** de um preset exportado, ou **`effective_config`** de uma análise, como conteúdo do arquivo. Não copie o envelope do preset (`format`, `environment` etc.). O arquivo oficial já contém todos os campos como referência. Veja o comportamento das opções de evidência no [guia do Lab](LAB.md#evidências-experimentais).

Desde `jev-escalas-ordinal-12`, altere `contexto_posicao_politica` para experimentar outra interpretação sem editar Python. O campo substitui o contexto geral; as instruções de saída e as rubricas específicas continuam compondo o prompt. Para alterar o significado de `sem_posicao` ou dos níveis, ajuste também `escala.rubricas_por_eixo` para manter as regras coerentes. Configurações sem esse campo usam o contexto padrão do contrato; presets antigos importados no Lab recebem o padrão publicado pela API. Resultados anteriores preservam seus hashes e não recebem um contexto retroativamente no JSON.

As chaves ficam no ambiente do servidor: `TYPESAFE_API_KEY`, `MARITACA_API_KEY` e `GEMINI_API_KEY`. Nunca entram no JSON público nem no pacote da extensão. `ALLOWED_JEV_MODELS` e `ALLOWED_LLM_MODELS` restringem os modelos JEV e Maritaca; quando ausentes, incluem o modelo padrão configurado. `ALLOWED_GEMINI_MODELS` controla o catálogo Gemini. A edição oficial usa o provedor do modelo escolhido no arquivo; a interface informa esse destino antes do envio.

A prioridade dos parâmetros é: **processo > `api/.env` > `.env` da raiz > JSON > padrões do contrato**. Para concentrar os parâmetros no JSON, remova as substituições correspondentes dos arquivos de ambiente. São elas `CONTEXTO_POSICAO_POLITICA`, `JEV_MODEL`, `LLM_MODEL`, `JEV_POLARITY_PRIMITIVE`, `JEV_DECISION_RULE`, `CHUNK_TOKENS`, `CHUNK_STRATEGY`, `JEV_RELEVANCE_MARGIN_MIN`, `JEV_LEVEL_CONFIDENCE_MIN`, `JEV_DIRECTION_MARGIN_MIN`, `MIN_VALID_CHUNKS`, `BOOTSTRAP_SAMPLES`, `BOOTSTRAP_SEED`, `SEMANTIC_EVIDENCE_CHECK`, `JEV_EVIDENCE_SEARCH` e `EVIDENCE_EXISTENCE_MIN`. A escala é definida pelo objeto `escala` no JSON.

Limites operacionais continuam no ambiente: `MAX_CHARS`, `MAX_TOKENS`, `MAX_CHUNKS`, `ANALYSIS_TIMEOUT_SECONDS`, `CONCURRENT_CHUNKS`, `CONCURRENT_REQUESTS`, `HOURLY_REQUESTS`, `DAILY_PROVIDER_CALLS` e `REPORTS_HOURLY_REQUESTS`. Eles restringem o arquivo e não são parâmetros de experimento do Lab.

A API publica os parâmetros em `GET /api/capabilities` (`analysis_defaults`) e inclui o snapshot efetivamente utilizado e seu hash em cada resultado e report. O arquivo é lido na inicialização; alterações exigem reiniciar a API. A edição oficial mantém os parâmetros por servidor e recusa `experiment_config` enviado pelo cliente. O Lab conserva seus presets e parâmetros por análise; só lê um JSON de servidor se `ALGORITHM_CONFIG_PATH` for definido explicitamente para ele.
