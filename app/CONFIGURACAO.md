# Parâmetros da versão oficial

O site e a extensão oficiais usam **`api/analysis-config.json`**, lido pela API ao iniciar. O arquivo contém os mesmos 17 campos de `ExperimentConfig` usados no Lab, incluindo a escala completa e suas rubricas. Edite o JSON e reinicie a API para aplicar aos dois clientes, sem recompilar. Recarregue o site/painel ou use **Verificar conexão e modos** para atualizar as capacidades exibidas.

Para usar outro arquivo, defina `ALGORITHM_CONFIG_PATH` no ambiente da API. Caminhos relativos partem de `app/api`, independentemente da pasta de inicialização. Use JSON UTF-8 (com ou sem BOM), sem comentários. Arquivos ausentes, JSON inválido, campos desconhecidos e valores fora do contrato impedem a inicialização.

| Campo | Padrão oficial | Opções / limites |
|---|---|---|
| `escala` | `ordinal_9_v1`, snapshot completo | Objeto validado com níveis e rubricas; aceita cinco níveis e outras escalas válidas do contrato |
| `primitiva_polaridade` | `score` | `score`, `choice` |
| `regra_decisao` | `nivel` | `nivel`, `polo_primeiro` |
| `chunk_tokens` | `600` | Inteiro de 100 a 2.000, até `MAX_TOKENS` |
| `chunk_strategy` | `tokens` | `tokens`, `sentencas` (padrão do Lab) |
| `relevance_margin_min` | `0.60` | 0 a 1 |
| `level_confidence_min` | `0.50` | 0 a 1 |
| `direction_margin_min` | `0.20` | 0 a 1 |
| `min_valid_chunks` | `16` | Inteiro positivo, até `MAX_CHUNKS` |
| `bootstrap_samples` | `2000` | Inteiro de 200 a 10.000 |
| `bootstrap_seed` | `42` | Inteiro de 0 a 2³² − 1 |
| `jev_model` | `jev-1.13.0` | Modelo JEV permitido no servidor |
| `llm_model` | `sabia-4` | Modelo Maritaca ou Gemini permitido no servidor |
| `semantic_evidence_check` | `false` | Verificar apoio semântico da citação; exige TypeSafe também no modo alto |
| `jev_evidence_search` | `false` | Buscar citações do JEV por ID nos modos baixo/médio |
| `evidence_existence_min` | `0.70` | Limiar da busca, de 0 a 1 |

Para levar parâmetros do Lab à versão oficial, use o objeto **`config`** de um preset exportado, ou **`effective_config`** de uma análise, como conteúdo do arquivo. Não copie o envelope do preset (`format`, `environment` etc.). O arquivo oficial já contém todos os campos como referência. Veja o comportamento das opções de evidência no [guia do Lab](LAB.md#evidências-experimentais).

As chaves ficam no ambiente do servidor: `TYPESAFE_API_KEY`, `MARITACA_API_KEY` e `GEMINI_API_KEY`. Nunca entram no JSON público nem no pacote da extensão. `ALLOWED_JEV_MODELS` e `ALLOWED_LLM_MODELS` restringem os modelos JEV e Maritaca; quando ausentes, incluem o modelo padrão configurado. `ALLOWED_GEMINI_MODELS` controla o catálogo Gemini. A edição oficial usa o provedor do modelo escolhido no arquivo; a interface informa esse destino antes do envio.

A prioridade dos parâmetros é: **processo > `api/.env` > `.env` da raiz > JSON > padrões do contrato**. Para concentrar os parâmetros no JSON, remova as substituições correspondentes dos arquivos de ambiente. São elas `JEV_MODEL`, `LLM_MODEL`, `JEV_POLARITY_PRIMITIVE`, `JEV_DECISION_RULE`, `CHUNK_TOKENS`, `CHUNK_STRATEGY`, `JEV_RELEVANCE_MARGIN_MIN`, `JEV_LEVEL_CONFIDENCE_MIN`, `JEV_DIRECTION_MARGIN_MIN`, `MIN_VALID_CHUNKS`, `BOOTSTRAP_SAMPLES`, `BOOTSTRAP_SEED`, `SEMANTIC_EVIDENCE_CHECK`, `JEV_EVIDENCE_SEARCH` e `EVIDENCE_EXISTENCE_MIN`. A escala é definida pelo objeto `escala` no JSON.

Limites operacionais continuam no ambiente: `MAX_CHARS`, `MAX_TOKENS`, `MAX_CHUNKS`, `ANALYSIS_TIMEOUT_SECONDS`, `CONCURRENT_CHUNKS`, `CONCURRENT_REQUESTS`, `HOURLY_REQUESTS`, `DAILY_PROVIDER_CALLS` e `REPORTS_HOURLY_REQUESTS`. Eles restringem o arquivo e não são parâmetros de experimento do Lab.

A API publica os parâmetros em `GET /api/capabilities` (`analysis_defaults`) e inclui o snapshot efetivamente utilizado e seu hash em cada resultado e report. O arquivo é lido na inicialização; alterações exigem reiniciar a API. A edição oficial mantém os parâmetros por servidor e recusa `experiment_config` enviado pelo cliente. O Lab conserva seus presets e parâmetros por análise; só lê um JSON de servidor se `ALGORITHM_CONFIG_PATH` for definido explicitamente para ele.
