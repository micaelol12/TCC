# Passo a passo — 8values Lab

Guia para rodar o site, a API e a extensão Lab no Windows com PowerShell.
Os comandos consideram o projeto em `C:\Users\User\Desktop\TCC`.
Se você mover o projeto, ajuste os caminhos.

O Lab permite experimentar parâmetros, modelos e presets. As chaves são
cadastradas pela interface, por sessão. Toda execução de análise é registrada
automaticamente no banco local, incluindo texto e resultado.

## 1. Conferir os requisitos

Instale Node.js 22.18 ou superior (recomendado 24+), Python 3.11 ou superior
e Chrome 116+ ou Edge com suporte ao painel lateral.

```powershell
node --version
npm --version
python --version
```

## 2. Instalar as dependências

Faça esta etapa na primeira execução. Se já preparou a versão normal neste
checkout, o Lab usa as mesmas dependências e o mesmo ambiente Python.

```powershell
cd C:\Users\User\Desktop\TCC\app
npm ci
```

```powershell
cd C:\Users\User\Desktop\TCC\app\api
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Nas atualizações das dependências, repita `npm ci` e o comando de instalação com
`pip`; não é necessário recriar a `.venv`. Os comandos usam diretamente o Python
do ambiente, sem precisar ativá-lo.

## 3. Entender a configuração do Lab

Não é necessário preencher chaves em `.env` para o Lab. Ele ignora as chaves
TypeSafe, Maritaca e Gemini dos arquivos de ambiente e do processo. O cadastro
é feito no site ou na extensão, conforme a etapa 6.

Opcionalmente, para personalizar variáveis do servidor, crie o arquivo
`app/api/.env.lab` caso ainda não exista:

```powershell
cd C:\Users\User\Desktop\TCC\app\api
if (-not (Test-Path -LiteralPath .env.lab)) {
    Copy-Item -LiteralPath .env.lab.example -Destination .env.lab
}
```

Edite esse arquivo apenas se precisar de configurações próprias.
Para variáveis que não são credenciais, a prioridade é:
variáveis do processo > `app/api/.env.lab` > `app/api/.env` > `.env` da raiz.
O script de inicialização já seleciona a edição Lab.

Os padrões do algoritmo vêm de `app/api/analysis-config.json`, compartilhado com
a versão normal. No Lab, a interface permite substituições por análise.

## 4. Iniciar a API Lab — terminal 1

```powershell
cd C:\Users\User\Desktop\TCC\app
npm run api:lab
```

Mantenha esse terminal aberto. A API Lab usa a porta **8001**.

Abra [http://127.0.0.1:8001/api/health](http://127.0.0.1:8001/api/health).
A resposta esperada é `{"status":"ok"}`.

Em [http://127.0.0.1:8001/api/capabilities](http://127.0.0.1:8001/api/capabilities),
confira `environment: "lab"` e `experimental.enabled: true`.
Essa consulta direta não contém o token da sessão da interface; use o próprio
site ou painel para verificar os modos liberados pelas chaves cadastradas.

Se a política do PowerShell bloquear `start-api-lab.ps1`, inicie manualmente
neste mesmo terminal, usando o Python do ambiente:

```powershell
cd C:\Users\User\Desktop\TCC\app\api
$env:APP_ENV = 'lab'
$env:EXPERIMENTAL_CONFIG_ENABLED = 'true'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Use uma das duas formas de inicialização por vez.

## 5. Iniciar o site Lab — terminal 2

Abra outro PowerShell:

```powershell
cd C:\Users\User\Desktop\TCC\app
npm run dev:lab
```

Acesse [http://127.0.0.1:5174](http://127.0.0.1:5174).
Mantenha os terminais da API e do site abertos.

## 6. Cadastrar as chaves e analisar pelo site

1. Abra **Configuração da análise → API keys**.
2. Cole a chave do provedor desejado e clique em **Salvar chave**.
3. Cadastre os demais provedores necessários para o modo escolhido.
4. Confira o modelo e os parâmetros da análise.
5. Insira um texto, selecione o modo disponível e clique em **Analisar texto**.

| Modo | Chaves necessárias |
|---|---|
| Classificação direta (`low`) | TypeSafe |
| Classificação com revisão (`medium`) | TypeSafe e o provedor LLM selecionado: Maritaca ou Gemini |
| Modelo de linguagem (`high`) | Provedor LLM selecionado; também TypeSafe se a checagem semântica estiver ativa |

O cadastro libera o uso na sessão; credenciais inválidas ou sem acesso ao modelo
podem produzir erro ao analisar. As chamadas usam os serviços reais dos provedores.

As chaves ficam na memória da API, em uma sessão de até 8 horas. Reiniciar a API,
expirar a sessão ou limpar suas chaves exige novo cadastro. Elas não entram nos
presets, histórico, banco ou pacote da extensão.

## 7. Compilar e instalar a extensão Lab — terminal 3

```powershell
cd C:\Users\User\Desktop\TCC\app
npm run build:lab
```

Depois:

1. Abra `chrome://extensions` ou `edge://extensions` no navegador.
2. Ative **Modo de desenvolvedor**.
3. Clique em **Carregar sem compactação** ou **Carregar descompactado**.
4. Selecione `C:\Users\User\Desktop\TCC\app\extension\dist-lab`.
5. Confirme que a extensão se chama **8values Lab**.
6. Abra o painel pelo ícone e cadastre suas chaves em **Configuração da análise → API keys**.

O site e a extensão têm sessões independentes. Uma chave salva no site precisa
ser cadastrada também na extensão para analisar pelo painel.

Para analisar uma seleção:

1. Abra uma página HTTP/HTTPS comum.
2. Selecione um texto e clique com o botão direito.
3. Escolha **Analisar com 8values**.
4. Revise o trecho no painel Lab, confira os parâmetros e o modo e clique em **Analisar texto**.

Se as duas edições estiverem instaladas e o menu ficar ambíguo, desative
temporariamente a extensão normal no gerenciamento do navegador.

A extensão Lab usa a API na porta **8001**. Para transferir o perfil, faça o teste
no site Lab em `http://127.0.0.1:5174`, abra **Meu resultado** e clique em
**Usar resultado na extensão**. Use o mesmo navegador e recarregue o site após
instalar ou recarregar a extensão.

Para gerar um ZIP opcional:

```powershell
cd C:\Users\User\Desktop\TCC\app
npm run package:lab
```

O ZIP Lab fica em `app\extension\artifacts`, com sufixo `-lab.zip`.
Extraia-o antes de carregar como extensão descompactada, ou use diretamente `dist-lab`.

## 8. Iniciar nas próximas vezes

```powershell
# Terminal 1
cd C:\Users\User\Desktop\TCC\app
npm run api:lab
```

```powershell
# Terminal 2
cd C:\Users\User\Desktop\TCC\app
npm run dev:lab
```

Abra `http://127.0.0.1:5174` ou o painel da extensão Lab e cadastre novamente
as chaves após reiniciar a API. Para encerrar, pressione `Ctrl+C` nos terminais.

## 9. Consultar os registros locais

Toda execução de análise Lab é registrada automaticamente em `lab_executions`,
incluindo texto, parâmetros, resultado e status. O banco padrão fica em:

```text
C:\Users\User\Desktop\TCC\app\api\data\reports-lab.sqlite3
```

Limpar o histórico do navegador não apaga esses registros.
Para exportar as execuções em JSONL:

```powershell
cd C:\Users\User\Desktop\TCC\app\api
.\.venv\Scripts\python.exe scripts/export_lab_executions.py --output execucoes-lab.jsonl
```

A exportação recusa sobrescrever uma saída existente; escolha outro nome se necessário.
`LAB_REPORTS_DB_PATH` permite configurar outro caminho para o banco Lab.

## 10. Resolver problemas comuns

| Problema | O que fazer |
|---|---|
| `node`, `npm` ou `python` não reconhecido | Confira instalação e PATH e reabra o terminal. |
| PowerShell bloqueia `npm.ps1` | Use `npm.cmd` no lugar de `npm`. Se bloquear o script da API Lab, use a inicialização manual da etapa 4. |
| Porta 8001 ou 5174 ocupada | Encerre a instância anterior ou o serviço que ocupa a porta e tente novamente. |
| API não conecta | Confira o terminal e teste `/api/health` na porta 8001. |
| Chaves no `.env` não liberam os modos | Cadastre as chaves na aba **API keys** da interface Lab em uso. |
| Site funciona, mas a extensão não analisa | Cadastre as chaves também na extensão e confira se ela foi carregada de `dist-lab`. |
| Sessão expirou ou API reiniciou | Cadastre novamente as chaves. |
| Modo alto indisponível | Confira a chave do modelo selecionado e a chave TypeSafe se a checagem semântica estiver ativa. |
| Falha ao registrar a execução | Confira acesso de escrita ao caminho do banco e o erro no terminal; o Lab exige o registro para iniciar a análise. |
| Extensão mostra versão antiga | Execute `npm run build:lab` e clique em **Recarregar** no gerenciamento da extensão. |
| Perfil não chega à extensão | Use o mesmo navegador, a edição Lab e a origem exata `http://127.0.0.1:5174`; recarregue o site. |

Mais detalhes: [LAB.md](LAB.md).
Para a versão normal, consulte [PASSO_A_PASSO_NORMAL.md](PASSO_A_PASSO_NORMAL.md).
