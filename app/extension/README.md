# Extensão 8values + textos

Extensão Manifest V3 para Chrome e Edge. Permite revisar e analisar texto selecionado, consultar os quatro eixos e suas evidências e comparar com um perfil 8values importado. A API FastAPI do projeto continua responsável pela classificação.

## Instalar para uso local

Requisitos: Node.js 22.18+ (recomendado 24+), Chrome 116+ ou Edge com suporte ao painel lateral, e API do projeto configurada. As versões efetivamente testadas estão em [VALIDACAO.md](VALIDACAO.md).

Na pasta `app`:

```powershell
npm ci
npm run build
```

1. Abra `chrome://extensions` ou `edge://extensions`.
2. Ative **Modo de desenvolvedor**.
3. Clique em **Carregar sem compactação** / **Carregar descompactado**.
4. Selecione a pasta `app/extension/dist`.
5. Inicie a API em `http://127.0.0.1:8000`, conforme o README principal.
6. Selecione um texto em uma página HTTP/HTTPS, clique com o botão direito e escolha **Analisar com 8values**.
7. Revise o trecho no painel, escolha um modo disponível e clique em **Analisar texto**.

O ícone da extensão abre o painel para colar texto ou recuperar o rascunho. Ele não recaptura a seleção da página. Após recompilar, use o botão de recarga da extensão na página de gerenciamento.

Sem chaves de provedores na API, os modos aparecem indisponíveis. A API carrega automaticamente o `.env` da raiz do TCC e o arquivo opcional `app/api/.env`, preservando as variáveis já definidas no processo. Reinicie a API após alterar esses arquivos e use **Verificar conexão e modos** no painel. A extensão não contém resultados de demonstração nem credenciais de provedores. Os resultados simulados usados nos testes ficam fora do pacote.

## Configurar os endereços

Os padrões locais são API `http://127.0.0.1:8000` e site `http://127.0.0.1:5173`. Para substituir, crie `app/extension/.env.local` com as variáveis do arquivo `.env.example` e recompile.

O endereço deve conter somente a origem, sem caminho `/api`, parâmetros, fragmentos ou credenciais. O cliente acrescenta `/api/capabilities` e `/api/analyze`.

Para gerar o pacote de produção, crie `.env.production.local` contendo as **origens HTTPS reais**:

```text
VITE_API_BASE_URL=https://api.seu-dominio.example
VITE_WEB_BASE_URL=https://seu-dominio.example
```

Esses endereços são exemplos e devem ser substituídos. Depois, na pasta `app`:

```powershell
npm run package:production --workspace=8values-extension
```

O build de produção recusa configuração ausente, HTTP, localhost, caminho, parâmetros e credenciais embutidas. URL base, permissão de host e política de conexão são geradas juntas. Chaves TypeSafe e Maritaca ficam exclusivamente no servidor.

O build local usa o modo de configuração `development`, mas produz um bundle compilado para instalação, sem depender do servidor Vite. A configuração de produção é uma preparação para distribuição: o projeto não publica uma API nem envia o pacote às lojas automaticamente.

## Uso, cancelamento e histórico

Cada envio é independente. A seleção apenas preenche o painel; o POST contém `text` e `processing_level`. Os resultados não classificam a página inteira ou o autor.

Se chegar outra seleção com um rascunho existente, escolha **Usar nova seleção** ou **Manter rascunho**. Durante uma análise, a seleção nova fica pendente e o texto enviado permanece fixo. O histórico e as seleções são separados por janela.

O painel executa a requisição HTTP. Cancelar aborta a espera; chamadas já recebidas por provedores podem ter sido processadas. Se o documento do painel for fechado ou recarregado durante a requisição, ao reabrir o texto é recuperado como análise interrompida, sem reenvio automático. O prazo do cliente considera o prazo declarado pela API e 15 segundos de margem de rede.

O histórico guarda até 10 resultados e um orçamento de 700 KB por janela. Entradas mais antigas podem ser removidas para manter esse orçamento; uma seleção ou rascunho grande demais gera aviso. Falhas de armazenamento também são informadas. Não se solicita armazenamento ilimitado.

## Perfil pessoal

No site, conclua o questionário, abra **Meu resultado** e exporte o perfil JSON. Na extensão, abra **Comparação** e importe o arquivo de até 10 KB. A versão, o hash do instrumento, a data e os quatro valores são validados; campos extras são descartados.

O padrão é uso temporário. A opção **Salvar o próximo perfil neste navegador** permite guardar a próxima importação localmente. **Apagar perfil** remove as cópias temporária e permanente da extensão. O site conserva sua própria cópia; as duas origens têm armazenamentos independentes.

## Permissões e dados

| Permissão | Uso |
|---|---|
| `contextMenus` | Ação explícita sobre texto selecionado |
| `sidePanel` | Interface de análise |
| `storage` | Dados temporários e preferências |
| Host da API | Consultar capacidades e analisar o texto revisado |

Não há script injetado, leitura automática de páginas, acesso ao histórico de navegação ou sincronização dos textos. A navegação anônima fica desabilitada para esta versão.

O rascunho, a seleção e o histórico usam `chrome.storage.session`, apagado em reinício do navegador, recarga, atualização ou desativação da extensão. **Limpar histórico e rascunhos** limpa os dados da janela atual. O modo preferido e o perfil salvo por escolha explícita ficam em `chrome.storage.local`. Desinstalar a extensão remove esses dados.

Somente o texto vai para os serviços indicados antes do envio: TypeSafe no baixo; TypeSafe e eventualmente Maritaca no médio; Maritaca no alto. Domínio de origem, perfil, título e histórico não integram o POST. O aplicativo não controla a retenção dos provedores. A API existente não grava textos em arquivos.

## Verificar e empacotar

Na pasta `app`:

```powershell
npm test
npm run build
npm run test:browser -- chrome
npm run test:browser -- edge
npm run package:extension
```

Os testes de navegador usam perfis novos em `app/test-results`, carregam a extensão real via CDP e interceptam a API com respostas simuladas. Não utilizam credenciais de provedores. O teste de espera acima de 30 segundos ocorre no Chrome. Os testes de captura da seleção e ordem da abertura do painel exercitam os listeners do service worker com APIs simuladas.

O script usa os caminhos padrão do Chrome/Edge no Windows. Em outra instalação, defina `BROWSER_EXECUTABLE`. Ele exige um navegador que exponha a API CDP de carregamento de extensões para teste, além da versão mínima suportada pelo produto.

Para concluir a validação de uso, confira manualmente o menu nativo em uma página normal, uma página dinâmica e um iframe. O pacote ZIP deve ser extraído antes de carregá-lo como extensão descompactada.

## Antes da distribuição pública

É necessário disponibilizar a API HTTPS e definir controle de acesso e consumo. Os limites atuais são globais por processo e não substituem proteção do serviço publicado. Não colocar uma chave compartilhada secreta dentro da extensão.

Preparar políticas e descrição dos dados coerentes com os provedores e com a infraestrutura real, usar o pacote de produção e concluir a revisão das lojas. Essas etapas dependem do ambiente público escolhido.
