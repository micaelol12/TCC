# Passo a passo — versão normal

Guia para rodar o site, a API e a extensão no Windows com PowerShell.
Os comandos consideram o projeto em `C:\Users\User\Desktop\TCC`.
Se você mover o projeto, ajuste os caminhos.

## 1. Conferir os requisitos

Instale Node.js 22.18 ou superior (recomendado 24+), Python 3.11 ou superior
e Chrome 116+ ou Edge com suporte ao painel lateral.

Abra o PowerShell e confira:

```powershell
node --version
npm --version
python --version
```

## 2. Instalar as dependências

Faça esta etapa na primeira execução. Repita a instalação quando as dependências
do projeto forem atualizadas.

Dependências do site e da extensão:

```powershell
cd C:\Users\User\Desktop\TCC\app
npm ci
```

Ambiente Python da API:

```powershell
cd C:\Users\User\Desktop\TCC\app\api
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Nas atualizações, basta repetir o comando de instalação com `pip`; não é preciso
recriar o ambiente. Os comandos usam diretamente seu Python, sem ativar a `.venv`.

## 3. Configurar as chaves

Abra `C:\Users\User\Desktop\TCC\app\api\.env` em um editor.
Se o arquivo ainda não existir, crie uma cópia do exemplo sem sobrescrever um existente:

```powershell
cd C:\Users\User\Desktop\TCC\app\api
if (-not (Test-Path -LiteralPath .env)) {
    Copy-Item -LiteralPath .env.example -Destination .env
}
```

Preencha as chaves, preservando as outras configurações:

```dotenv
TYPESAFE_API_KEY=sua_chave_typesafe
MARITACA_API_KEY=sua_chave_maritaca
```

As chaves ficam no servidor. Não as coloque nos arquivos da extensão nem em
variáveis `VITE_`.

| Modo | Chaves necessárias na configuração atual |
|---|---|
| Classificação direta (`low`) | TypeSafe |
| Classificação com revisão (`medium`) | TypeSafe e Maritaca |
| Modelo de linguagem (`high`) | Maritaca e TypeSafe, pois a checagem semântica está habilitada |

O modelo LLM configurado atualmente é `sabia-4`. Se a checagem semântica for
desabilitada em `api/analysis-config.json`, o modo alto deixa de exigir TypeSafe.
Gemini também pode ser configurado; veja [CONFIGURACAO.md](CONFIGURACAO.md).

A API carrega automaticamente os arquivos de ambiente. A prioridade é:
variáveis do processo > `app/api/.env` > `.env` da raiz do TCC.
Sem chaves, o questionário funciona e a análise de texto fica indisponível.

## 4. Iniciar a API — terminal 1

```powershell
cd C:\Users\User\Desktop\TCC\app
npm run api
```

Mantenha esse terminal aberto. O script usa o ambiente `api/.venv` e inicia a API em
`http://127.0.0.1:8000`.

Abra no navegador:

- [Saúde da API](http://127.0.0.1:8000/api/health): deve retornar `{"status":"ok"}`.
- [Configuração e modos disponíveis](http://127.0.0.1:8000/api/capabilities): confira `modes`.

Um modo habilitado indica que as chaves necessárias estão presentes; a validade
das credenciais e o acesso ao modelo são verificados ao fazer uma análise.

## 5. Iniciar o site — terminal 2

Abra outro PowerShell:

```powershell
cd C:\Users\User\Desktop\TCC\app
npm run dev
```

Acesse [http://127.0.0.1:5173](http://127.0.0.1:5173).
Mantenha os terminais da API e do site abertos durante o uso.

## 6. Compilar e instalar a extensão — terminal 3

```powershell
cd C:\Users\User\Desktop\TCC\app
npm run build
```

Esse comando compila o site e a extensão. Depois:

1. Abra `chrome://extensions` ou `edge://extensions` no navegador.
2. Ative **Modo de desenvolvedor**.
3. Clique em **Carregar sem compactação** ou **Carregar descompactado**.
4. Selecione `C:\Users\User\Desktop\TCC\app\extension\dist`.
5. Clique no ícone da extensão para abrir o painel.
6. Use **Verificar conexão e modos**.

Para analisar uma seleção:

1. Abra uma página HTTP/HTTPS comum.
2. Selecione um texto e clique com o botão direito.
3. Escolha **Analisar com 8values**.
4. Revise o trecho no painel, escolha o modo e clique em **Analisar texto**.

A extensão usa a API na porta **8000**. A análise no painel funciona sem o site
aberto. Para comparar com seu questionário, abra **Meu resultado** no site e clique
em **Usar resultado na extensão**, usando o mesmo navegador. Use o endereço exato
`http://127.0.0.1:5173` e recarregue o site após instalar ou recarregar a extensão.

Para gerar um ZIP opcional:

```powershell
cd C:\Users\User\Desktop\TCC\app
npm run package:extension
```

O ZIP fica em `app\extension\artifacts`. Extraia-o antes de carregar como extensão
descompactada, ou use diretamente a pasta `dist` já gerada.

## 7. Iniciar nas próximas vezes

Com as dependências e a extensão instaladas, execute:

```powershell
# Terminal 1
cd C:\Users\User\Desktop\TCC\app
npm run api
```

```powershell
# Terminal 2
cd C:\Users\User\Desktop\TCC\app
npm run dev
```

Abra o site em `http://127.0.0.1:5173` ou use a extensão instalada.
Para encerrar, pressione `Ctrl+C` em cada terminal dos servidores.

## 8. Resolver problemas comuns

| Problema | O que fazer |
|---|---|
| `node`, `npm` ou `python` não reconhecido | Confira a instalação e o PATH; reabra o terminal após instalar. |
| PowerShell bloqueia `npm.ps1` | Use `npm.cmd` no lugar de `npm` nos comandos deste guia. |
| Módulo Python não encontrado | Repita a instalação de `requirements.txt` usando `api\.venv\Scripts\python.exe`. |
| Porta 8000 ou 5173 ocupada | Encerre a instância anterior ou o serviço que ocupa a porta e tente novamente. |
| API não conecta | Confira o terminal da API e teste `/api/health` na porta 8000. |
| Modos indisponíveis | Confira as chaves e o modelo configurado, reinicie a API e use **Verificar conexão e modos**. |
| Chave alterada sem efeito | Reinicie a API; variáveis já definidas no processo têm prioridade sobre os arquivos `.env`. |
| Extensão mostra uma versão antiga | Execute `npm run build` e clique em **Recarregar** no gerenciamento da extensão. |
| Perfil não chega à extensão | Use o mesmo navegador, a edição normal e a origem exata `http://127.0.0.1:5173`; recarregue o site. |

Os parâmetros do algoritmo ficam em `app/api/analysis-config.json`.
Após alterá-los, reinicie a API. A versão normal só grava a análise no banco
quando o usuário confirma o envio de um report.

Para a outra edição, consulte [PASSO_A_PASSO_LAB.md](PASSO_A_PASSO_LAB.md).
