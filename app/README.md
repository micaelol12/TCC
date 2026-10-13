# 8values + textos

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

Para comparar com seu teste, abra **Meu resultado** no site, use **Exportar perfil para a extensão** e importe o JSON na aba **Comparação** do painel. Escolha uso temporário ou salvamento local. O perfil não é enviado à API.

| Modo | Serviço | Variáveis necessárias |
|---|---|---|
| Baixo | JEV | `TYPESAFE_API_KEY` |
| Médio | JEV e revisão Sabiá quando necessária | `TYPESAFE_API_KEY`, `MARITACA_API_KEY` |
| Alto | Sabiá | `MARITACA_API_KEY` |

`JEV_MODEL` e `LLM_MODEL` permitem substituir os padrões `jev-1.13.0` e `sabia-4`. Confira a disponibilidade e o contrato das contas antes de usar. A API não contém modo de demonstração com classificações inventadas.

## Limites e dados

Por padrão, um envio admite 60.000 caracteres, 12.000 tokens e 20 trechos de cerca de 600 tokens, com prazo total de 120 segundos. Há até dois trechos em paralelo por análise, três análises simultâneas, 30 requisições por hora no processo e orçamento de 1.000 chamadas lógicas de provedores por dia. Configure `MAX_CHARS`, `MAX_TOKENS`, `MAX_CHUNKS`, `ANALYSIS_TIMEOUT_SECONDS`, `CONCURRENT_CHUNKS`, `CONCURRENT_REQUESTS`, `HOURLY_REQUESTS` e `DAILY_PROVIDER_CALLS`. Contadores em memória reiniciam com o processo e não substituem proteção no proxy de produção.

As respostas individuais do teste ficam apenas em `sessionStorage` durante o preenchimento. O resultado agregado pode ficar em `localStorage` ou somente em memória, conforme escolha ao concluir. O histórico de análises fica em `sessionStorage` durante a sessão da aba, inclusive ao navegar pelo app ou recarregar a página. O corpo de `POST /api/analyze` contém somente `text` e `processing_level`; o servidor não recebe respostas, perfil ou comparação. A API não grava análises em arquivos. O vocabulário do tokenizador está incluído no pacote, sem download durante requisições.

O texto enviado vai para TypeSafe no modo baixo, TypeSafe e eventualmente Maritaca no médio, ou Maritaca no alto. A aplicação não controla a retenção feita por esses provedores. Antes da publicação, revise políticas, contratos, transferência internacional, HTTPS, configuração do proxy e logs de infraestrutura. O corte de 16 trechos válidos por eixo para evidência suficiente é uma escolha metodológica do notebook, mantida aqui mesmo em textos curtos.

## Testar

```powershell
# app — site, cliente compartilhado e extensão
npm run build
npm test

# navegadores instalados; perfis temporários, API simulada, sem uso de provedores
npm run test:browser -- chrome
npm run test:browser -- edge

# app/api, no ambiente Python com requirements-test.txt instalado
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
```

Os testes usam provedores simulados; nenhuma chamada externa é feita. A validação real de custo, latência, modelos e qualidade dos três modos depende de credenciais e de textos independentes das perguntas e das rubricas. Veja [avisos de terceiros](THIRD_PARTY_NOTICES.md) para atribuições do questionário e do tokenizador.
