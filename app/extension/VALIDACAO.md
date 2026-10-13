# Validação da extensão

Execução local em 13/10/2026. Resultados de classificação nos testes são simulados; nenhuma chamada a TypeSafe ou Maritaca foi necessária.

## Automação executada

- Build do site e da extensão com React/TypeScript/Vite.
- 34 testes TypeScript aprovados: questionário, ideologias, histórico, perfil, cliente HTTP, estado da sessão, fila de gravação, preferências, listener do menu e configuração de produção.
- 11 testes Python existentes da API aprovados, incluindo contrato HTTP, limites, tokenização e estratégias dos três modos.
- Extensão instalada em perfis temporários: Chrome 155.0.8059.40 e Edge 155.0.4283.45.
- Documento compilado do painel executado com APIs reais de armazenamento da extensão.
- Revisão antes do envio, POST contendo somente texto e modo, estimativas parciais, evidências, recarga de rascunho e histórico, HTTP 429, cancelamento, seleção pendente, recuperação de interrupção sem reenvio, isolamento entre janelas, importação/exclusão de perfil, limpeza, limite de caracteres e exibição segura de texto.
- Resposta HTTP simulada após 31 segundos no Chrome, sem depender da duração do service worker.
- Inspeção visual das capturas em largura de 380 px, sem transbordamento horizontal.
- ZIP verificado por leitura e CRC, com manifest, scripts, estilos, ícones e avisos de terceiros; sem arquivos de configuração de credenciais.

Relatórios JSON e capturas ficam em `app/test-results`. Os scripts criam perfis isolados; não modificam os perfis pessoais do usuário. O pacote usa somente três permissões funcionais e o host da API local.

## Verificação manual restante

O teste automatizado abre o documento do painel da extensão como uma página do navegador e alimenta capturas via armazenamento. Ele não interage com o menu nativo do botão direito nem confirma o gesto de abertura do painel na interface visível do navegador.

Verificar após carregar o pacote:

1. Selecionar um parágrafo em uma página HTTP/HTTPS e usar o menu **Analisar com 8values**; conferir o trecho no painel nativo.
2. Repetir em página dinâmica e em um iframe, incluindo acentos e quebras de linha.
3. Abrir pelo ícone da extensão e navegar entre abas, mantendo o resultado e sua origem.
4. Conferir teclado, foco e anúncios com leitor de tela na interface nativa.
5. Com provedores configurados, validar uma análise real em cada modo disponível.

API pública, controle de acesso e publicação nas lojas ainda dependem da configuração de distribuição. Não foram implantados por estes testes.
