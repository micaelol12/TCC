# 8values Lab — versão de teste

Todos os parâmetros do algoritmo também podem ser definidos na versão oficial pelo arquivo [`api/analysis-config.json`](api/analysis-config.json). O Lab continua usando configuração por análise e padrões próprios; veja o [guia de configuração oficial](CONFIGURACAO.md) para transferir um preset.

O site e a extensão Lab permitem alterar os parâmetros da próxima análise, escolher modelos permitidos, salvar/importar/exportar configurações e comparar quaisquer análises diferentes do histórico, inclusive de textos distintos. O nome **Versão de teste**, a configuração efetiva e seu identificador acompanham os resultados experimentais.

## Iniciar

Na pasta `app`, com as dependências instaladas pelo README principal:

```powershell
# Terminal 1: API Lab em http://127.0.0.1:8001
npm run api:lab

# Terminal 2: site Lab em http://127.0.0.1:5174
npm run dev:lab
```

Para gerar o site compilado e a extensão instalável:

```powershell
npm run build:lab
npm run package:lab
```

Carregue `app/extension/dist-lab` como extensão descompactada no Chrome ou Edge. O ZIP é `app/extension/artifacts/8values-extension-0.1.0-lab.zip`; extraia antes de carregar. O build do site fica em `app/web/dist-lab`, servido pela API Lab na porta 8001 quando essa pasta existe. Para desenvolvimento e transferência de perfil, use o site na porta 5174, configurada na extensão. `npm run preview:lab --workspace=8values-textos` também usa 5174 com proxy para a API Lab.

Para usar o site servido pela API em vez da porta 5174, defina `VITE_WEB_BASE_URL=http://127.0.0.1:8001` em `app/extension/.env.lab.local` e recompile a extensão Lab. A conexão de perfil exige origem e edição correspondentes.

## Chaves e padrões

Copie `app/api/.env.lab.example` para `app/api/.env.lab` se quiser padrões próprios para o Lab. O launcher define `APP_ENV=lab` e habilita os controles experimentais. Para iniciar manualmente na pasta `app/api`:

```powershell
$env:APP_ENV='lab'
$env:EXPERIMENTAL_CONFIG_ENABLED='true'
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Para configurações que não são credenciais, a prioridade é: variáveis do processo > `app/api/.env.lab` > `app/api/.env` > `.env` da raiz. O arquivo Lab só é carregado quando `APP_ENV=lab` foi selecionado pelo processo ou por um dos arquivos comuns de ambiente. Reinicie a API depois de editar as variáveis e use **Verificar conexão e modos** no painel.

Abra **Configuração da análise → API keys** no site ou na extensão. Cole sua chave TypeSafe, Maritaca ou Gemini e clique em **Salvar chave**. Os modelos do provedor ficam disponíveis imediatamente, sem reiniciar a API. As chaves são enviadas à API local e mantidas somente na memória de uma sessão de até 8 horas. O campo é limpo após salvar; o navegador conserva apenas um token opaco: `sessionStorage` no site e `chrome.storage.local` na extensão. Fechar e reabrir o painel preserva a sessão da extensão, inclusive entre janelas; expirar a sessão, reiniciar a API ou limpar as chaves exige novo cadastro. As chaves não entram no banco, presets, histórico ou pacote. Site e extensão têm sessões independentes: cadastre a chave na interface em que vai analisar.

**Desabilitar** remove o acesso ao provedor naquela sessão; **Limpar chaves da sessão** encerra a sessão e bloqueia todos os modos até um novo cadastro. Após reiniciar a API ou expirar a sessão, cadastre novamente. A presença da chave libera a seleção, mas não comprova acesso ao modelo; uma chave inválida produz aviso de autenticação na análise.

O Lab inicia sem nenhuma chave pré-cadastrada e ignora `TYPESAFE_API_KEY`, `MARITACA_API_KEY` e `GEMINI_API_KEY` do processo e dos arquivos de ambiente. Cada usuário precisa cadastrar suas chaves na sessão do site ou da extensão. O modo baixo exige TypeSafe; o modo médio exige TypeSafe e o provedor LLM selecionado; o modo alto exige o provedor LLM selecionado e também TypeSafe quando a checagem semântica de evidências estiver ativa. Sem essas chaves, as análises ficam bloqueadas tanto na interface quanto na API. A edição comum mantém sua configuração de chaves no servidor.

`JEV_MODEL` e `LLM_MODEL` definem os modelos padrão. O Lab oferece `sabia-4` e `sabiazinho-4` pela Maritaca e `gemini-3.1-flash-lite` e `gemini-3.7-flash` pelo Google. `ALLOWED_LLM_MODELS` acrescenta modelos Maritaca; `ALLOWED_GEMINI_MODELS` define a lista Gemini. É possível escolher o modelo LLM antes de cadastrar a chave; modelos sem chave recebem a indicação **chave ausente**, e a análise nos modos médio e alto permanece bloqueada até o cadastro. No modo baixo, a escolha fica preparada para os modos que usam LLM. Durante uma análise, os parâmetros ficam bloqueados. O provedor é identificado pelo catálogo da API e não por uma URL fornecida pelo usuário.

O Google informa que `gemini-3.7-flash` é redirecionado para `gemini-3.8-flash`. A escolha solicitada e o modelo efetivamente retornado ficam registrados separadamente. [Gemini 3.7 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.7-flash), [modelos Maritaca](https://docs.maritaca.ai/pt/modelos). O adaptador Gemini usa o endpoint REST de geração com JSON Schema e valida a saída com o mesmo contrato de eixos e evidências do Sabiá. [Referência de geração Gemini](https://ai.google.dev/api/generate-content).

| Variável | Padrão | Efeito |
|---|---|---|
| `CHUNK_TOKENS` | 600 | Tamanho aproximado dos trechos, de 100 a 2.000 tokens |
| `JEV_POLARITY_PRIMITIVE` | score | Classificação da polaridade pelo JEV: `score` ou `choice` |
| `JEV_DECISION_RULE` | nivel | Regra JEV: `nivel` (MAP global) ou `polo_primeiro` (experimental) |
| `JEV_RELEVANCE_MARGIN_MIN` | 0.60 | Relevância ambígua abaixo da margem |
| `JEV_LEVEL_CONFIDENCE_MIN` | 0.50 | Nível com confiança insuficiente abaixo do limiar |
| `JEV_DIRECTION_MARGIN_MIN` | 0.20 | Direção ambígua abaixo da margem |
| `MIN_VALID_CHUNKS` | 16 | Corte para indicar evidência suficiente |
| `BOOTSTRAP_SAMPLES` | 2000 | Reamostragens do intervalo entre trechos, de 200 a 10.000 |
| `BOOTSTRAP_SEED` | 42 | Semente do bootstrap, de 0 a 2³² − 1 |

Os limiares JEV acionam revisão no modo médio e motivos de incerteza no modo baixo. No modo alto, eles não se aplicam. O corte de evidência suficiente não muda a média. A semente reproduz o bootstrap, mas não garante respostas idênticas dos provedores. As faixas permitidas são limites de engenharia; mudar valores não equivale a validar cientificamente um novo método.

O painel substitui os padrões somente para a próxima requisição. A configuração de uma análise em andamento é fixa. Limites totais, concorrência, prazo, orçamento diário e limites horários continuam definidos pelo servidor. Trechos menores podem gerar mais chamadas ou ultrapassar `MAX_CHUNKS`.

Em **Parâmetros → Estratégia de segmentação**, o Lab usa **Sentenças** (`"sentencas"`) por padrão, equivalente a `preparacao_e_exibicao.chunks.estrategia` no notebook. A API recebe `experiment_config.chunk_strategy`. O segmentador português Punkt usa recursos locais e as mesmas regras de sentenças, parágrafos, títulos e listas de `tcc_lib/segmentacao.py`. O tamanho em tokens é um alvo: frases longas permanecem inteiras, mesmo acima dele. O texto original, inclusive espaços e quebras de linha, é preservado nos trechos para conferir evidências e reports. A opção **Tokens** (`"tokens"`) reproduz o corte anterior do app. A escolha acompanha presets, histórico, comparação, hash e registros de execução; presets antigos sem esse campo mantêm `tokens`. A edição comum mantém a segmentação por tokens. Após atualizar, instale `api/requirements.txt` e reinicie a API Lab.

Em **Parâmetros → Classificação da polaridade no JEV**, selecione **Score · níveis ordenados** ou **Choice · escolha entre níveis**. A relevância continua usando Choice. O seletor se aplica aos modos baixo e médio; no alto, a classificação é feita pelo LLM. A API Lab aceita `experiment_config.primitiva_polaridade` com `"score"` ou `"choice"`, e registra a opção na configuração efetiva, hash, histórico, comparação, presets e reports. Presets anteriores sem esse campo usam `score`, o comportamento histórico do app. Para mudar o padrão do servidor, defina `JEV_POLARITY_PRIMITIVE` e reinicie a API.

## Evidências experimentais

Em **Parâmetros → Regra de decisão do JEV**, o experimento **Polo primeiro** soma os níveis por polo A, B e sem posição antes de escolher a intensidade. A regra anterior continua como padrão. O Lab registra a distribuição inicial por trecho em `axes[].jev_diagnostics`, inclusive quando o LLM revisa o resultado. Intensidades incertas são sinalizadas no resultado; a pontuação correspondente é preliminar. Veja o [procedimento, limiares e replay sem chamadas](../docs/experimento-polo-primeiro.md).

Em **Configuração da análise → Parâmetros → Evidências experimentais**, há duas opções independentes, inicialmente desligadas no site e na extensão:

| Opção | Comportamento |
|---|---|
| Verificar apoio semântico da citação | O JEV verifica se a citação, no contexto integral, sustenta, contradiz ou é insuficiente para a posição e intensidade atribuídas. Funciona com citações do LLM e com citações recuperadas pela busca do JEV. |
| Buscar citações do JEV por ID | Nos modos baixo e médio, procura uma passagem para cada decisão final do JEV. Um teste separado de existência precisa atingir o limiar configurado (padrão 0,70). A citação é recuperada diretamente do texto original pelo ID selecionado. |

Os pareceres aparecem em **Distribuição e evidências** de cada eixo, com trecho, nível avaliado, modelo, confiança e, quando aplicável, ID e posições da citação. Uma contradição fica registrada para revisão, sem alterar nível, relevância, fallback ou pontuação. A busca também não filtra os chunks usados na média. Citação localizada literalmente e apoio semântico são verificações distintas; a confiança do modelo não representa uma taxa de acerto validada.

São até duas chamadas lógicas JEV adicionais por chunk, agrupadas por etapa para os eixos elegíveis. Sem citação elegível, a checagem semântica não chama o provedor. O orçamento diário reserva o máximo adicional antes de iniciar; a contagem no resultado informa as chamadas efetivamente tentadas. Falhas e respostas inválidas do verificador aparecem no registro de auditoria sem apagar a classificação. Cancelamento e prazo global da análise continuam valendo.

Os IDs são locais ao chunk. As posições usam caracteres Unicode e permitem recuperar a passagem original. A divisão em frases é uma heurística; acima de 200 passagens, frases adjacentes são agrupadas para respeitar o limite de alternativas sem omitir partes do texto.

As configurações `semantic_evidence_check`, `jev_evidence_search` e `evidence_existence_min` acompanham presets, comparação, histórico, reports e registros de execução. Presets anteriores recebem as opções desligadas ao serem importados. Os pareceres ficam em `axes[].evidence_audit` no resultado salvo e na exportação das execuções. A API comum continua recusando configurações experimentais.

No [Pipeline - Passo a Passo.ipynb](../Pipeline%20-%20Passo%20a%20Passo.ipynb), a seção **Evidências experimentais: presença literal e apoio à posição** explica a integração e contém uma demonstração simulada. Para usar com modelos reais, ajuste os mesmos três campos em `CONFIG_PIPELINE_PLAYGROUND["cascata"]`; a configuração geral também é herdada pelas análises de propostas. Reinicie o kernel e execute as definições atualizadas antes de analisar. O notebook e a API usam o mesmo módulo `api/app/pipeline/evidence.py`.

Para comparar, analise o mesmo texto com as opções desligadas e depois ligadas, mantendo os demais parâmetros. Os modelos podem variar entre chamadas; os testes automatizados verificam a preservação da pontuação sobre decisões fixas. A qualidade dos novos pareceres ainda exige avaliação em textos reais com anotação humana.

## Presets, histórico e reports

Cada alteração válida guarda automaticamente a última configuração neste navegador, separada por origem da API/site, mesmo sem chaves cadastradas. Ao reabrir, essa configuração é restaurada. Valores inválidos ou incompletos não substituem a última configuração válida. **Exportar JSON** e **Importar configuração JSON** usam um formato versionado sem credenciais e com limite de 200 KB. Importações e presets salvos são revalidados contra os modelos e faixas da API atual. **Restaurar padrões** e importar um preset também atualizam automaticamente a configuração persistente.

Os resultados Lab exibem uma cópia de todos os parâmetros, os modelos retornados e o hash da configuração pública. No site e na extensão, **Comparar análises** permite selecionar qualquer outra análise do histórico, do mesmo texto ou de textos diferentes; a própria análise fica excluída das opções. As duas versões mostram um resumo gráfico dos quatro eixos, com marcadores distintos para as duas análises, pontuações, cobertura e diferenças em pontos. Eixos sem estimativa ficam sem marcador. O Lab também mostra as configurações, os modelos e as chamadas lógicas lado a lado. A versão oficial exibe somente o resumo gráfico comparativo. A comparação fica na aba **Comparação**, em **Entre análises**.

Reports mantêm os metadados da configuração junto do snapshot e continuam exigindo consentimento. O banco Lab padrão é `app/api/data/reports-lab.sqlite3`. Para alterá-lo, use `LAB_REPORTS_DB_PATH`; o Lab não herda `REPORTS_DB_PATH` do ambiente comum. Não configure as duas variáveis para o mesmo banco. Reports Lab são rejeitados pela API comum e vice-versa. O hash detecta inconsistências de configuração, mas não autentica uma classificação enviada pelo cliente.

**Toda execução de análise do Lab é gravada automaticamente**, sem depender de um report, na tabela `lab_executions` desse mesmo banco. O registro inclui UUID, datas UTC, cliente, texto, modo, parâmetros solicitados/efetivos, resultado completo, duração, status HTTP e um código de falha sem mensagens brutas dos provedores. Sucessos, resultados com avisos, entradas rejeitadas, falhas, timeouts e cancelamentos ficam registrados. Entradas acima do limite são limitadas no armazenamento; uploads cujo corpo excede 250 KB recebem um registro sem texto.

A gravação inicial acontece antes das chamadas externas. Falha no banco impede iniciar a análise; falha na confirmação final retorna erro, preservando o registro inicial. Registros deixados em andamento por uma interrupção do servidor passam a `interrupted` na próxima inicialização. Não há duplicação automática de análise: cada nova tentativa recebe outro UUID. As respostas bem-sucedidas mostram **Execução gravada no banco** e seu identificador. Limpar o histórico no navegador mantém os registros do servidor.

Para exportar todas as execuções sem alterar o banco, execute na pasta `app/api`:

```powershell
.venv/Scripts/python.exe scripts/export_lab_executions.py --output execucoes-lab.jsonl
# Opcional: --database CAMINHO --status failed|cancelled|completed|all
```

O exportador recusa sobrescrever arquivos existentes. Tokens de sessão e chaves não são registrados nem exportados. As exportações contêm os textos e resultados das execuções e ficam sob administração de quem opera o Lab.

As edições usam portas, pastas e chaves de armazenamento distintas. O site e a extensão enviam perfis somente para a edição correspondente. Resultados antigos permanecem legíveis e aparecem com **Configuração não registrada**.

## Verificação

```powershell
# app: contratos, builds, navegador e pacote
npm test
npm run build
npm run build:lab
npm run package:lab
npm run verify:lab
npm run test:lab -- chrome
npm run test:lab -- edge

# app/api: provedores simulados, incluindo concorrência e reports
.venv/Scripts/python.exe -m unittest discover -s tests -v

# Raiz do TCC: compila o notebook e exercita apenas demonstrações simuladas
.venv/Scripts/python.exe analise_jev_llm/test_evidencias_pipeline.py

# Raiz: escalas de cinco/nove/sete níveis, sem provedores
.venv/Scripts/python.exe scripts/check_local_notebook_demos.py
.venv/Scripts/python.exe scripts/check_local_notebook_demos.py --nine
.venv/Scripts/python.exe scripts/validate_notebook_scales.py

# app/api: verificação explícita com texto sintético e provedores reais
# Consome até uma análise curta por modo, além das retentativas do pipeline.
.venv/Scripts/python.exe scripts/validate_lab_providers.py --live
```

Os testes de navegador usam perfis temporários, o site e as extensões compilados e uma API simulada. Capturas e relatórios ficam em `app/test-results`. `verify:lab` procura arquivos de ambiente e as credenciais fictícias usadas para validar o build; ele não atesta validade das chaves reais. A verificação real grava um resumo de integração e, como qualquer análise do Lab, registra a execução sintética no banco. Use `--llm-model sabiazinho-4` ou `--llm-model gemini-3.1-flash-lite` para verificar apenas o modo alto com aquele modelo; o script solicita as chaves sem exibi-las e as cadastra em uma sessão temporária. Deixe um campo vazio para pular esse provedor. Nenhuma chave é carregada do ambiente.

Esta edição foi preparada para uso local: os builds Lab exigem origens locais, e o launcher da API usa loopback. Hospedagem remota, contas persistentes, outros provedores e edição livre de prompts/rubricas exigem etapas adicionais.

## Validação realizada em 13/10/2026

- Builds comum e Lab gerados; pacote Lab contém 11 arquivos e foi inspecionado sem arquivos de ambiente ou chaves fictícias.
- Fluxo Lab verificado em Chrome 155.0.8059.40 e Edge 155.0.4283.45: parâmetros, presets, importação/exportação, comparação, histórico, report, largura de tela e transferência de perfil para a edição correta.
- Regressão de transferência de perfil da edição comum verificada no Chrome; regressão de captura, cancelamento, recuperação, histórico e isolamento de janelas verificada no Edge.
- Integração real com texto sintético: modo baixo usou JEV, modo médio usou JEV e Sabiá, e modo alto usou Sabiá. Todos retornaram HTTP 200, sem avisos de erro, com configuração registrada. Modelos: `jev-1.13.0` e `sabia-4`.
- Atualização com API keys e persistência: 66 testes TypeScript e 42 testes da API passaram. Chrome e Edge exercitaram cadastro, liberação dos modelos por chave, seleção Gemini/Sabiazinho, isolamento das sessões e recibo de execução. O adaptador Gemini foi validado com transporte HTTP simulado; uma chamada real depende de uma chave Gemini configurada.
- A chamada real ao `sabiazinho-4` retornou HTTP 200. Houve aviso `evidencia_nao_verificada`: a estimativa apoiada nessa citação foi descartada e a execução ficou registrada como `completed_with_warnings`, preservando a validação de evidências.

Esses checks confirmam a integração e os fluxos exercitados; a avaliação de qualidade dos parâmetros experimentais continua dependendo de um conjunto de textos e critérios de pesquisa.

## Validação da integração de evidências

- 56 testes da API e 71 testes TypeScript passaram, incluindo preservação da pontuação, falhas do verificador, limite de chamadas, chave TypeSafe no modo alto, presets anteriores e offsets Unicode.
- O teste Chrome do Lab exercitou as opções e os pareceres no site e na extensão, exportação/importação, histórico, reports e identificação dos provedores. Nenhum erro de página foi registrado.
- Todas as células do notebook foram compiladas. As demonstrações e a integração da cascata foram executadas com dublês; a nova demonstração tem a saída salva no notebook.

Essa validação usa provedores simulados. Não foi executado um novo benchmark com APIs reais para avaliar a qualidade das evidências nesta integração.
