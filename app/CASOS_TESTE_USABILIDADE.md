# Casos de teste das alterações de usabilidade

Execução: 29/10/2026, 19:31:26 (horário de Brasília). 16 de 16 casos aprovados no Chrome. Perfil temporário, dados fictícios e API simulada; nenhuma chamada a provedores de IA. Os casos avaliam o funcionamento das alterações, sem substituir testes com usuários.

## Como executar

Na pasta `C:\Users\User\Desktop\TCC\app`:

```powershell
npm run build
npm run test:usability
```

Para acompanhar o navegador enquanto os casos são executados:

```powershell
npm run test:usability:visual
```

O teste usa uma sessão independente e encerra o navegador ao concluir. Para testar exclusões manualmente, use apenas uma sessão com dados fictícios que possam ser apagados. Os casos com erro HTTP e armazenamento bloqueado são preparados automaticamente pela suíte, sem exigir alterações nas configurações do seu navegador.

## Índice

| Caso | Verificação | Resultado |
|---|---|---|
| CT-01 | Preservar texto, título e modo ao navegar e recarregar | Aprovado |
| CT-02 | Restaurar um rascunho quando já existe histórico | Aprovado |
| CT-03 | Entender as opções de processamento | Aprovado |
| CT-04 | Receber orientação quando o serviço recusa o tamanho do texto | Aprovado |
| CT-05 | Ler limitações da análise sem códigos internos | Aprovado |
| CT-06 | Cancelar a substituição de um rascunho | Aprovado |
| CT-07 | Cancelar e confirmar o descarte de um rascunho | Aprovado |
| CT-08 | Revisar perguntas e respostas com contexto | Aprovado |
| CT-09 | Editar uma resposta e voltar diretamente à revisão | Aprovado |
| CT-10 | Preservar o contexto da revisão ao recarregar | Aprovado |
| CT-11 | Proteger o descarte do teste e permitir cancelar pelo teclado | Aprovado |
| CT-12 | Concluir o questionário depois de revisar e editar | Aprovado |
| CT-13 | Cancelar e confirmar a exclusão dos dados do site | Aprovado |
| CT-14 | Verificar que os dados apagados não reaparecem | Aprovado |
| CT-15 | Preservar o texto em memória quando a gravação falha | Aprovado |
| CT-16 | Navegar e revisar em tela pequena | Aprovado |

## CT-01 — Preservar texto, título e modo ao navegar e recarregar

**Resultado da execução:** Aprovado.

**Pré-condição:** Página Analisar texto aberta, sem rascunho anterior.

**Passos:**

1. Preencher título e texto e escolher Classificação direta.
2. Abrir Meu resultado e voltar a Analisar texto.
3. Recarregar a página.

**Resultado esperado:** Título, texto e modo continuam preenchidos. Navegar e recarregar não enviam uma análise automaticamente.

**Evidência:** [Abrir captura](C:/Users/User/Desktop/TCC/app/test-results/usability-draft-restored.png).

## CT-02 — Restaurar um rascunho quando já existe histórico

**Resultado da execução:** Aprovado.

**Pré-condição:** Uma análise concluída no histórico da sessão.

**Passos:**

1. Abrir Editar e reanalisar e escrever um texto diferente.
2. Fechar o formulário, abrir Nova análise e recarregar a página.

**Resultado esperado:** O formulário mostra o novo rascunho. A análise anterior continua no histórico.

**Evidência:** [Abrir captura](C:/Users/User/Desktop/TCC/app/test-results/usability-draft-with-history.png).

## CT-03 — Entender as opções de processamento

**Resultado da execução:** Aprovado.

**Pré-condição:** Formulário de análise aberto.

**Passos:**

1. Ler os três nomes e suas descrições.
2. Expandir Como escolher o processamento?.

**Resultado esperado:** A tela explica os métodos em português e informa que nenhum modo garante uma classificação correta.

**Evidência:** [Abrir captura](C:/Users/User/Desktop/TCC/app/test-results/usability-processing-help.png).

## CT-04 — Receber orientação quando o serviço recusa o tamanho do texto

**Resultado da execução:** Aprovado.

**Pré-condição:** API de teste configurada para devolver HTTP 413; a suíte prepara essa resposta.

**Passos:**

1. Preencher um texto e clicar em Analisar texto.

**Resultado esperado:** A mensagem orienta reduzir o texto, sem instruções de configuração do Lab. O texto permanece no formulário.

**Evidência:** [Abrir captura](C:/Users/User/Desktop/TCC/app/test-results/usability-size-error.png).

## CT-05 — Ler limitações da análise sem códigos internos

**Resultado da execução:** Aprovado.

**Pré-condição:** Análise simulada com uma falha conhecida e um código de limitação desconhecido.

**Passos:**

1. Concluir a análise simulada.
2. Ler as limitações e expandir Motivos registrados na análise.

**Resultado esperado:** As limitações são descritas em português; o código desconhecido recebe uma explicação genérica. Os códigos ficam apenas nos detalhes técnicos.

**Evidência:** [Abrir captura](C:/Users/User/Desktop/TCC/app/test-results/usability-translated-diagnostics.png).

## CT-06 — Cancelar a substituição de um rascunho

**Resultado da execução:** Aprovado.

**Pré-condição:** Uma análise no histórico e um rascunho com texto diferente.

**Passos:**

1. Fechar o formulário e clicar em Editar e reanalisar na análise anterior.
2. Ler a confirmação e clicar em Cancelar.
3. Abrir Nova análise.

**Resultado esperado:** A confirmação explica a substituição. Cancelar mantém o rascunho original.

**Evidência:** [Abrir captura](C:/Users/User/Desktop/TCC/app/test-results/usability-overwrite-confirmation.png).

## CT-07 — Cancelar e confirmar o descarte de um rascunho

**Resultado da execução:** Aprovado.

**Pré-condição:** Formulário com título ou texto e uma análise no histórico.

**Passos:**

1. Clicar em Descartar rascunho e depois Cancelar.
2. Conferir que o texto permanece.
3. Reabrir a confirmação e clicar em Sim, descartar rascunho.

**Resultado esperado:** Cancelar preserva o texto. Confirmar esvazia o formulário e mantém o histórico.

**Evidência:** [Abrir captura](C:/Users/User/Desktop/TCC/app/test-results/usability-draft-discard-confirmation.png).

## CT-08 — Revisar perguntas e respostas com contexto

**Resultado da execução:** Aprovado.

**Pré-condição:** Questionário iniciado com pelo menos uma resposta.

**Passos:**

1. Marcar Neutro ou incerto na primeira pergunta.
2. Clicar em Revisar respostas.

**Resultado esperado:** A revisão mostra os enunciados, a resposta selecionada e a indicação Ainda não respondida para as perguntas pendentes.

**Evidência:** [Abrir captura](C:/Users/User/Desktop/TCC/app/test-results/usability-review-before-edit.png).

## CT-09 — Editar uma resposta e voltar diretamente à revisão

**Resultado da execução:** Aprovado.

**Pré-condição:** Resumo de revisão aberto.

**Passos:**

1. Usar Editar na primeira pergunta.
2. Trocar a resposta para Concordo.
3. Clicar em Voltar à revisão.

**Resultado esperado:** A revisão reaparece com a resposta atualizada, sem percorrer novamente as demais perguntas.

**Evidência:** [Abrir captura](C:/Users/User/Desktop/TCC/app/test-results/usability-review-desktop.png).

## CT-10 — Preservar o contexto da revisão ao recarregar

**Resultado da execução:** Aprovado.

**Pré-condição:** Resumo de revisão aberto após uma alteração.

**Passos:**

1. Recarregar a página enquanto o resumo de revisão está aberto.

**Resultado esperado:** A página volta ao resumo e mantém as respostas preenchidas.

**Evidência:** [Abrir captura](C:/Users/User/Desktop/TCC/app/test-results/usability-review-desktop.png).

## CT-11 — Proteger o descarte do teste e permitir cancelar pelo teclado

**Resultado da execução:** Aprovado.

**Pré-condição:** Teste com respostas preenchidas.

**Passos:**

1. Clicar em Descartar teste.
2. Verificar que Cancelar recebe o foco inicial.
3. Pressionar Escape.

**Resultado esperado:** A confirmação explica o que seria apagado. Escape fecha a confirmação sem apagar as respostas.

**Evidência:** [Abrir captura](C:/Users/User/Desktop/TCC/app/test-results/usability-confirmation-mobile.png).

## CT-12 — Concluir o questionário depois de revisar e editar

**Resultado da execução:** Aprovado.

**Pré-condição:** Questionário com a primeira resposta já revisada.

**Passos:**

1. Responder às demais perguntas com dados fictícios.
2. Revisar e clicar em Concluir teste.

**Resultado esperado:** A tela Meu resultado mostra os quatro eixos, sem erros de execução.

**Evidência:** [Abrir captura](C:/Users/User/Desktop/TCC/app/test-results/usability-completed-result.png).

## CT-13 — Cancelar e confirmar a exclusão dos dados do site

**Resultado da execução:** Aprovado.

**Pré-condição:** Perfil fictício, histórico e rascunho presentes na sessão de teste.

**Passos:**

1. Em Meu resultado, clicar em Apagar meus dados locais.
2. Cancelar e voltar a Analisar texto para conferir o rascunho.
3. Voltar a Meu resultado, reabrir a confirmação e confirmar a exclusão.

**Resultado esperado:** Cancelar mantém os dados. Confirmar apaga os dados do site e retorna ao início. A confirmação informa que arquivos, perfil da extensão e relatos enviados não são apagados.

**Evidência:** [Abrir captura](C:/Users/User/Desktop/TCC/app/test-results/usability-delete-site-confirmation.png).

## CT-14 — Verificar que os dados apagados não reaparecem

**Resultado da execução:** Aprovado.

**Pré-condição:** Exclusão dos dados do site confirmada na sessão com dados fictícios.

**Passos:**

1. Abrir Analisar texto e conferir o formulário e o histórico.
2. Recarregar a página.
3. Abrir Meu resultado.

**Resultado esperado:** O formulário permanece vazio, o histórico não contém análises e Meu resultado informa que o teste ainda não foi concluído.

**Evidência:** [Abrir captura](C:/Users/User/Desktop/TCC/app/test-results/usability-cleared-session.png).

## CT-15 — Preservar o texto em memória quando a gravação falha

**Resultado da execução:** Aprovado.

**Pré-condição:** A suíte simula falha de gravação apenas na página de teste, sem mudar configurações do navegador.

**Passos:**

1. Abrir Analisar texto e preencher o rascunho.
2. Ler os avisos de armazenamento.
3. Navegar até Meu resultado e voltar.

**Resultado esperado:** A tela avisa que recarregar ou fechar pode perder os dados. O rascunho continua disponível durante a navegação no app.

**Evidência:** [Abrir captura](C:/Users/User/Desktop/TCC/app/test-results/usability-storage-warning-mobile.png).

## CT-16 — Navegar e revisar em tela pequena

**Resultado da execução:** Aprovado.

**Pré-condição:** Janela de 380 × 900 pixels e janela de desktop de 1280 × 1000 pixels.

**Passos:**

1. Abrir a revisão, uma confirmação e o formulário de análise.
2. Usar os links de navegação em tela pequena.
3. Verificar se há rolagem horizontal na revisão e no formulário.

**Resultado esperado:** O cabeçalho não se sobrepõe ao conteúdo; a navegação funciona e as telas verificadas não têm rolagem horizontal.

**Evidência:** [Abrir captura](C:/Users/User/Desktop/TCC/app/test-results/usability-review-mobile.png).

## Extensão e envio de relatos

Os testes complementares do projeto verificam proteção das exclusões no painel lateral, transferência do perfil e consentimento para envio de relatos:

```powershell
npm run test:browser -- chrome
npm run test:profile-transfer -- chrome
npm run test:reports -- chrome
```

Essas suítes também usam perfis temporários e serviços simulados. O painel visual deste relatório documenta os 16 casos do site listados acima.
