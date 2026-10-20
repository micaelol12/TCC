# 8values + textos

Para experimentar parâmetros do algoritmo, modelos e chaves da API na edição **8values Lab**, consulte [o guia da versão de teste](LAB.md). Inicie com `npm run api:lab` e `npm run dev:lab` em terminais separados; gere o pacote com `npm run build:lab` e `npm run package:lab`.

O Lab possui uma aba **API keys** para chaves Maritaca e Gemini por sessão e registra automaticamente todas as execuções de análise em `lab_executions`, no banco Lab, incluindo texto e resultado. Os parágrafos abaixo sobre armazenamento somente por report descrevem a edição comum. [Chaves, modelos e registros do Lab](LAB.md).

Aplicativo React + TypeScript e API FastAPI para o questionário 8values e análise de textos políticos em quatro eixos. Implementação do MVP descrito em [`../PLANO_APP_8VALUES.md`](../PLANO_APP_8VALUES.md).

O guia dos oito valores na aba do teste adapta as descrições do [8values original](https://8values.github.io/). A ideologia mais próxima usa os 52 perfis de [`../tcc/ideologies.json`](../tcc/ideologies.json) e a distância definida em [`../TCC.ipynb`](../TCC.ipynb): quadrado das diferenças nos eixos econômico e civil, e expoente `1.73856063` nos eixos diplomático e social. É uma correspondência exploratória, menos precisa que os quatro eixos segundo o próprio 8values. Na análise de texto ela só aparece quando os quatro eixos têm estimativa; as classificações feitas por IA podem conter erros.

## Rodar localmente

Requisitos: Node.js 22.18+ (recomendado 24+), Python 3.11+ e acesso aos serviços para os modos de análise. Na pasta `app`:

```powershell
npm ci
npm run dev
```

Em outro terminal, na pasta `app/api`:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

A API carrega automaticamente o `.env` na raiz do projeto TCC e, se existir, `app/api/.env`. Configure `TYPESAFE_API_KEY` e `MARITACA_API_KEY` nesses arquivos. A prioridade é: variáveis já definidas no processo, depois `app/api/.env`, depois o `.env` da raiz. Não é necessário exportar as chaves no terminal. Reinicie a API depois de alterar o arquivo; no painel da extensão, use **Verificar conexão e modos**.

O Vite abre o frontend e encaminha `/api` à porta 8000. O workspace reúne `web`, `shared` e `extension`; instale as dependências na pasta `app`. Para servir um único pacote web, execute `npm run build --workspace=8values-textos` em `app` e inicie a API; ela servirá `web/dist` quando a pasta existir. `GET /api/capabilities` indica quais modos estão disponíveis conforme as chaves configuradas. Sem chaves, o questionário funciona e a análise fica indisponível.

## Extensão Chrome e Edge

A extensão oferece **Analisar com 8values** no menu de seleção de textos de páginas HTTP/HTTPS. O painel lateral recebe o trecho para revisão; somente o botão **Analisar texto** envia o texto e o modo para a API. Componentes, eixos, questionário e cliente HTTP são compartilhados com o site.

Na pasta `app`, execute:

```powershell
npm run build
npm run package:extension
```

Carregue `app/extension/dist` como extensão descompactada em `chrome://extensions` ou `edge://extensions`, com o modo de desenvolvedor ativado. O pacote ZIP fica em `app/extension/artifacts`. Inicie a API na porta 8000 antes de analisar. [Instalação, configuração e dados da extensão](extension/README.md).

Para comparar com seu teste, abra **Meu resultado** no site e clique em **Usar resultado na extensão**. O painel de **Comparação** recebe o perfil automaticamente, sem exportar arquivos. Marque **Manter meu resultado salvo na extensão** para guardar entre sessões; o padrão é temporário. Após atualizar a extensão, recarregue também o site. A exportação e importação JSON continuam disponíveis. O perfil não é enviado à API.

| Modo | Serviço | Variáveis necessárias |
|---|---|---|
| Baixo | JEV | `TYPESAFE_API_KEY` |
| Médio | JEV e revisão Sabiá quando necessária | `TYPESAFE_API_KEY`, `MARITACA_API_KEY` |
| Alto | Sabiá | `MARITACA_API_KEY` |

`JEV_MODEL` e `LLM_MODEL` permitem substituir os padrões `jev-1.13.0` e `sabia-4`. Confira a disponibilidade e o contrato das contas antes de usar. A API não contém modo de demonstração com classificações inventadas.

## Limites e dados

Por padrão, um envio admite 60.000 caracteres, 12.000 tokens e 20 trechos de cerca de 600 tokens, com prazo total de 120 segundos. Há até dois trechos em paralelo por análise, três análises simultâneas, 30 requisições por hora no processo e orçamento de 1.000 chamadas lógicas de provedores por dia. Configure `MAX_CHARS`, `MAX_TOKENS`, `MAX_CHUNKS`, `ANALYSIS_TIMEOUT_SECONDS`, `CONCURRENT_CHUNKS`, `CONCURRENT_REQUESTS`, `HOURLY_REQUESTS` e `DAILY_PROVIDER_CALLS`. Contadores em memória reiniciam com o processo e não substituem proteção no proxy de produção.

As respostas individuais do teste ficam apenas em `sessionStorage` durante o preenchimento. O resultado agregado pode ficar em `localStorage` ou somente em memória, conforme escolha ao concluir. O histórico de análises fica em `sessionStorage` durante a sessão da aba, inclusive ao navegar pelo app ou recarregar a página. O corpo de `POST /api/analyze` contém somente `text` e `processing_level`; o servidor não recebe respostas, perfil ou comparação. A análise comum não é gravada no banco; o armazenamento ocorre quando o usuário confirma um report. O vocabulário do tokenizador está incluído no pacote, sem download durante requisições.

## Reports de classificação

No site e na extensão, **Reportar classificação** abre uma confirmação com prévia do texto, análise completa e comentário opcional de até 2.000 caracteres. O aviso declara que o trecho, a análise e o comentário serão armazenados no banco para posterior avaliação pela equipe responsável. A caixa **Estou ciente e concordo com o envio e o armazenamento desses dados** começa desmarcada; somente **Enviar report** faz o envio. Cancelar não envia dados.

`POST /api/reports` recebe `submission_id` (UUID), `text`, `analysis`, `comment`, `client` (`web` ou `extension`), `storage_consent: true` e `notice_version: "1"`. Usa o texto original associado ao resultado selecionado e não chama provedores novamente. Perfil, respostas do questionário, comparação, título e domínio/URL de origem não entram no report. O resultado é um snapshot enviado pelo cliente, sem garantia de autenticidade da classificação.

A rota retorna `201` com `report_id`, `received_at` (UTC) e `status: "pending"` após confirmar a transação. Uma tentativa repetida com o mesmo UUID e conteúdo retorna `200` com o recibo original; conteúdo diferente com o mesmo UUID retorna `409`. A interface preserva o identificador em tentativas manuais enquanto o resultado estiver aberto, inclusive ao fechar e reabrir o modal. Editar o comentário após uma tentativa cria um novo report. Fechar o painel, recarregar ou trocar o resultado reinicia esse estado da interface; não há reenvio automático.

SQLite cria o arquivo `app/api/data/reports.sqlite3` e a tabela `classification_reports` no primeiro report aceito. `REPORTS_DB_PATH` permite usar outro caminho persistente. Há limite de 2 MB para o corpo, os limites configurados de texto/trechos e `REPORTS_HOURLY_REQUESTS=60` tentativas válidas por hora no processo, independentemente do orçamento de análises. Falha de armazenamento retorna `503`, sem confirmar sucesso ou expor conteúdo. A base é ignorada pelo Git e não é servida pelo frontend.

Para exportar reports pendentes em JSONL, execute na pasta `app/api`:

```powershell
python scripts/export_reports.py --output reports.jsonl
# Opcional: --database CAMINHO --status pending|reviewed|all
```

A exportação abre o banco somente para leitura e recusa sobrescrever uma saída existente. A equipe consulta os dados localmente; não existe rota pública de listagem. O status inicial é `pending`; um painel e fluxo de revisão ficam para uma etapa posterior. Limpar histórico, dados locais ou desinstalar a extensão não apaga reports já enviados. Configure retenção, acesso restrito e backup do banco e das exportações conforme o ambiente antes da distribuição pública; o limite por processo deve ser acompanhado pela proteção do serviço publicado.

O texto enviado vai para TypeSafe no modo baixo, TypeSafe e eventualmente Maritaca no médio, ou Maritaca no alto. A aplicação não controla a retenção feita por esses provedores. Antes da publicação, revise políticas, contratos, transferência internacional, HTTPS, configuração do proxy e logs de infraestrutura. O corte de 16 trechos válidos por eixo para evidência suficiente é uma escolha metodológica do notebook, mantida aqui mesmo em textos curtos.

## Testar

Para comparar os níveis atuais com a cascata em diferentes limiares de confiança JEV, use [benchmark_reasoning.py](api/scripts/benchmark_reasoning.py). Na raiz do projeto, execute `python app/api/scripts/benchmark_reasoning.py` para mostrar o plano; `--live --repeats 2` executa as chamadas reais. O script gera somente resultados JSONL, resumo CSV e relatório Markdown, com acurácia conjunta, relevância, direção, chamadas e latência. `--summarize PASTA` recalcula o resumo e o relatório sem chamar provedores.

```powershell
# app — site, cliente compartilhado e extensão
npm run build
npm test

# navegadores instalados; perfis temporários, API simulada, sem uso de provedores
npm run test:browser -- chrome
npm run test:browser -- edge
# Report no site e na extensão, com API simulada
npm run test:reports -- chrome
npm run test:reports -- edge

# app/api, no ambiente Python com requirements-test.txt instalado
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
```

Os testes usam provedores simulados; nenhuma chamada externa é feita. A validação real de custo, latência, modelos e qualidade dos três modos depende de credenciais e de textos independentes das perguntas e das rubricas. Veja [avisos de terceiros](THIRD_PARTY_NOTICES.md) para atribuições do questionário e do tokenizador.
