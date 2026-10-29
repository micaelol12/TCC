# Avaliação de usabilidade do 8values + textos segundo Nielsen

Data: 29 de outubro de 2026. Escopo: versão comum do site, componentes compartilhados e código da extensão. A edição Lab não foi avaliada como produto separado.

**Atualização após a implementação:** os seis problemas listados nesta inspeção receberam correções, descritas ao final deste documento. As seções de avaliação e problemas abaixo registram a versão anterior às correções. A validação com participantes continua necessária para medir os cinco atributos de usabilidade.

**Parecer: aderência parcial aos princípios de Nielsen.** O aplicativo possui recursos consistentes de orientação, feedback e controle, mas apresenta problemas de prevenção de erros, preservação do trabalho e linguagem. As evidências não sustentam uma afirmação de conformidade integral nem uma porcentagem de conformidade.

## Referencial e método

Em *Usability Engineering*, a usabilidade compreende aprendizagem, eficiência, memorização, erros e satisfação. O livro também trata do ciclo de desenvolvimento, da avaliação heurística e de testes com usuários. Esta análise usa a organização das dez heurísticas do capítulo 5, apresentada no [sumário publicado pela Nielsen Norman Group](https://www.nngroup.com/books/usability-engineering/). A [lista de heurísticas reformulada em 1994](https://www.nngroup.com/articles/ten-usability-heuristics/) é uma referência complementar; seus títulos não são idênticos aos do livro.

Foram realizadas leitura do código e inspeção do site no Chrome, com navegação pela página inicial, questionário, guia dos eixos, formulário de análise e resultado sem perfil. Um texto fictício foi usado para verificar a preservação de rascunhos. A API estava desligada: foi observado o estado de indisponibilidade, sem execução de análises ou envio a provedores.

Os resultados de análise, a revisão final do questionário, o envio de relatos de classificação e a extensão foram avaliados pelo código. Esses fluxos não foram integralmente executados. A inspeção visual ocorreu em desktop; não houve validação em celular, com leitor de tela ou com participantes. As gravidades abaixo são estimativas de uma única inspeção, sujeitas a revisão após observação de usuários.

## Avaliação das dez heurísticas do livro

“Favorável” significa que foram encontrados mecanismos pertinentes no escopo examinado. “Parcial” indica mecanismos positivos acompanhados de lacunas. Nenhum desses termos equivale a certificação.

| Heurística do capítulo 5 — tradução descritiva | Resultado | Evidência e ressalva |
|---|---|---|
| 1. Diálogo simples e natural | Parcial | A página inicial explica o fluxo e o questionário apresenta uma pergunta por vez. A tela de análise expõe siglas e informações de implementação que dificultam a leitura por iniciantes. |
| 2. Falar a linguagem do usuário | Parcial | A interface está em português e explica os polos. Entretanto, usa JEV, LLM, JSON e “report”; os modos Baixo/Médio/Alto não explicam claramente a consequência da escolha. |
| 3. Minimizar a carga de memória | Parcial | Há histórico, texto original e alternativas visíveis. A revisão do teste apresenta números de perguntas, sem enunciado e resposta selecionada no resumo. |
| 4. Consistência | Parcial | Site e extensão compartilham componentes e eixos. Há diferenças na proteção dos rascunhos, rótulos de reanálise e mensagens da edição comum que mencionam o Lab. |
| 5. Feedback | Favorável, com ressalva | O questionário mostra quantidade respondida; o código prevê status, cronômetro, erros e recibo de envio. A gravação do histórico web pode falhar silenciosamente. Latência real não foi medida. |
| 6. Saídas claramente indicadas | Parcial | Há Voltar, Fechar, Cancelar e Descartar. Cancelar a análise preserva o texto enquanto a tela permanece montada; sair da rota de análise perde o rascunho. |
| 7. Atalhos | Parcial | O formulário oferece Ctrl/Cmd + Enter, reuso de texto e transferência do perfil. Falta uma ação direta para retornar ao resumo após editar uma resposta do teste. |
| 8. Boas mensagens de erro | Parcial | Várias mensagens explicam o problema e oferecem nova tentativa. Outras orientam iniciar o servidor, mencionam configurações do Lab ou exibem códigos internos sem tradução. |
| 9. Prevenir erros | Parcial | Bloqueia avanço sem resposta, envio vazio ou excessivo e relato sem consentimento. Descartar o teste e apagar dados são ações imediatas, sem confirmação ou desfazer. |
| 10. Ajuda e documentação | Parcial | O guia dos eixos, os avisos de IA e as explicações de evidências são pontos positivos. Falta ajuda contextual acessível para escolher o processamento e resolver indisponibilidade como usuário final. |

## Problemas e prioridades

A escala adotada segue a [proposta de severidade de Nielsen](https://www.nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/): 1, cosmético; 2, menor; 3, maior; 4, catastrófico. A classificação considera impacto e persistência previstos; a frequência real ainda não foi medida.

### 1. Rascunho de análise desaparece ao navegar — gravidade estimada 3

**Confirmado no navegador.** Digitar um texto em Analisar texto, abrir Meu resultado e retornar à análise deixa o campo vazio, sem aviso anterior. Título e texto são estados locais de `AnalysisPage`, e somente análises concluídas entram no histórico.

Evidência: [AnalysisPage.tsx](C:/Users/User/Desktop/TCC/app/web/src/features/analysis/AnalysisPage.tsx), estados nas linhas 24–25 e persistência do histórico na linha 37.

Recomendação: preservar título, texto e modo durante a sessão e restaurá-los ao voltar. Avisar quando o armazenamento falhar; oferecer descarte explícito. Preservar o rascunho também reduz a perda decorrente da saída durante uma requisição.

### 2. Descarte e exclusões sem recuperação — gravidade estimada 3

**Confirmado no código.** `discard()` remove as respostas e retorna ao início imediatamente. Apagar meus dados locais também limpa perfil, rascunho do teste e histórico de análises. A extensão apaga perfil ou histórico diretamente. Os efeitos destrutivos não foram acionados nesta inspeção.

Evidências: [QuizPage.tsx](C:/Users/User/Desktop/TCC/app/web/src/features/quiz/QuizPage.tsx), linhas 63–65; [App.tsx](C:/Users/User/Desktop/TCC/app/web/src/App.tsx), linha 31; [ResultPage.tsx](C:/Users/User/Desktop/TCC/app/web/src/features/quiz/ResultPage.tsx), linha 20; [ExtensionApp.tsx](C:/Users/User/Desktop/TCC/app/extension/src/sidepanel/ExtensionApp.tsx), ações de exclusão.

Recomendação: apresentar confirmação com o escopo exato dos dados apagados e opção de cancelar, ou implementar desfazer onde adequado. Priorizar a proteção de um teste com respostas já preenchidas.

### 3. Revisão exige memória e navegação repetitiva — gravidade estimada 2

**Confirmado no código.** O resumo contém apenas botões numerados. Ao selecionar uma pergunta, a interface sai da revisão; não há botão para voltar diretamente ao resumo. Depois de editar uma pergunta inicial, o caminho disponível dentro do questionário é avançar novamente até a última.

Evidência: [QuizPage.tsx](C:/Users/User/Desktop/TCC/app/web/src/features/quiz/QuizPage.tsx), ação `index`, grade na linha 74 e controles finais.

Recomendação: mostrar enunciado resumido e resposta escolhida, com Editar e Voltar à revisão. Manter o contexto da revisão após uma alteração.

### 4. Escolha do processamento depende de siglas — gravidade estimada 2

**Observado no navegador e no código.** Os rótulos Baixo/Médio/Alto são explicados por JEV e LLM. Isso informa o mecanismo, mas exige conhecimento prévio para decidir. A nomenclatura pode sugerir uma escala de qualidade que a interface não demonstra.

Evidência: [analysisApi.ts](C:/Users/User/Desktop/TCC/app/shared/src/api/analysisApi.ts), linhas 9–11; [AnalysisComposer.tsx](C:/Users/User/Desktop/TCC/app/shared/src/components/AnalysisComposer.tsx), grupo Processamento.

Recomendação: explicar o que cada modo faz em linguagem comum, com detalhes técnicos opcionais. Descrever diferenças de tempo ou custo apenas quando houver medições; evitar prometer maior precisão pelo nome do modo.

### 5. Erros e diagnósticos misturam públicos — gravidade estimada 2

**Observado parcialmente no navegador e confirmado no código.** Sem API, o site orienta o usuário a iniciar o servidor. No cliente compartilhado, o erro 413 recomenda ajustar tokens no Lab, inclusive quando usado pela versão comum. A seção de motivos mostra `reason_codes` diretamente, e avisos não mapeados também aparecem como códigos.

Evidências: [AnalysisPage.tsx](C:/Users/User/Desktop/TCC/app/web/src/features/analysis/AnalysisPage.tsx), linha 36; [analysisApi.ts](C:/Users/User/Desktop/TCC/app/shared/src/api/analysisApi.ts), mapa de mensagens HTTP; [AnalysisEvidence.tsx](C:/Users/User/Desktop/TCC/app/shared/src/components/AnalysisEvidence.tsx), linha 154; [AnalysisResult.tsx](C:/Users/User/Desktop/TCC/app/shared/src/components/AnalysisResult.tsx), linha 30.

Recomendação: separar instruções de desenvolvimento das orientações ao usuário, traduzir códigos conhecidos e explicar ações viáveis, como reduzir o texto, escolher outro modo ou tentar novamente.

### 6. Falha de gravação do histórico não é comunicada — gravidade estimada 2

**Confirmado no código; não provocado no navegador.** `saveAnalysisHistory()` mantém cópia em memória quando `sessionStorage` falha, sem informar que o histórico pode ser perdido ao recarregar. O questionário já possui um aviso equivalente para falha de gravação do rascunho.

Evidência: [analysisHistory.ts](C:/Users/User/Desktop/TCC/app/web/src/features/analysis/analysisHistory.ts), linhas 27–30.

Recomendação: retornar o estado da gravação e exibir um aviso discreto sobre a preservação apenas em memória.

## O que se pode concluir sobre os cinco atributos

| Atributo | Conclusão permitida por esta inspeção | Validação ainda necessária |
|---|---|---|
| Aprendizagem | O fluxo inicial e o guia dos eixos ajudam; as siglas criam barreiras potenciais. | Observar iniciantes completando as tarefas sem auxílio. |
| Eficiência | Há atalhos e reuso; a revisão pode exigir passos desnecessários. | Medir tempo e passos depois da aprendizagem. |
| Memorização | A navegação estável e os rótulos visíveis oferecem apoio. | Repetir tarefas após um intervalo sem uso. |
| Erros | Há validação de entradas, mas existem caminhos de perda de trabalho. | Medir frequência, impacto e recuperação dos erros. |
| Satisfação | Não determinada. A aparência da interface não comprova satisfação. | Coletar avaliação dos participantes após as tarefas. |

A distinção entre esses atributos e sua avaliação por tarefas está descrita em [Usability 101, de Nielsen](https://www.nngroup.com/articles/usability-101-introduction-to-usability/).

Para a próxima rodada, usar participantes do público-alvo em tarefas de responder e revisar o teste, interpretar um resultado, analisar e comparar um texto, recuperar-se de uma falha e utilizar a extensão. Registrar conclusão, tempo, necessidade de ajuda, erros e percepção de facilidade. Definir metas antes da coleta e repetir a avaliação após corrigir os problemas prioritários. Testes automatizados de funcionamento não substituem essas medidas.

## Formulação sugerida para o TCC

> A inspeção da interface e do código identificou aderência parcial aos princípios de usabilidade de Nielsen. O sistema oferece orientação, feedback, revisão de respostas e mecanismos de controle, mas apresenta limitações na prevenção de perdas de trabalho, na eficiência da revisão e na linguagem utilizada. Esses resultados caracterizam uma avaliação preliminar de usabilidade; a aprendizagem, a eficiência, a memorização, os erros e a satisfação deverão ser investigados por meio de testes com usuários representativos.

## Nota bibliográfica

A referência informada pelo autor do projeto é “NIELSEN, J. Usability Engineering. Amsterdam: Morgan Kaufmann, 1994”. A página da NN/G registra o livro em 1993 e menciona Morgan Kaufmann, San Francisco, para a edição em brochura. Conferir ano, local e editora na folha de rosto e no verso da edição efetivamente consultada antes de ajustar a referência. A lista reformulada de heurísticas de 1994 deve ser citada separadamente se for usada com seus títulos atuais.

## Correções implementadas em 29 de outubro de 2026

| Problema identificado | Comportamento implementado |
|---|---|
| Rascunho perdido ao navegar | Título, texto e modo são salvos na sessão da aba e restaurados após navegar ou recarregar, inclusive quando já há análises no histórico. |
| Descarte e exclusão sem proteção | Confirmações descrevem o alcance da ação no site e na extensão, com foco inicial em Cancelar e fechamento por Escape. O formulário também oferece descarte explícito e protege a substituição de outro rascunho. |
| Revisão com números e navegação repetitiva | A revisão exibe enunciado e resposta, oferece Editar por pergunta e Voltar à revisão. O contexto da revisão é restaurado após recarregar. |
| Siglas na escolha de processamento | Os modos passam a se chamar Classificação direta, Classificação com revisão e Modelo de linguagem. Há descrições em linguagem comum e ajuda contextual, sem promessa de maior precisão. O contrato técnico continua usando `low`, `medium` e `high`. |
| Erros e diagnósticos técnicos | Mensagens orientam ações viáveis ao usuário. A versão comum não recomenda configurações do Lab. Limitações são traduzidas; códigos permanecem apenas em detalhes para suporte. Relatos e arquivos do teste recebem rótulos mais claros. |
| Falha silenciosa de armazenamento | A tela informa quando rascunho ou histórico não puderam ser guardados. A cópia em memória preserva o estado ao navegar sem restaurar uma cópia antiga do armazenamento. |

A verificação em tela pequena também identificou e corrigiu a altura do cabeçalho, que fazia a navegação se sobrepor ao conteúdo.

Validação automatizada: 122 testes unitários aprovados; compilação do site e da extensão; fluxos de usabilidade, relatos, extensão e transferência de perfil no Chrome com perfil temporário e API simulada, sem erros de página. O teste específico de usabilidade cobre navegação, recarga, edição e retorno à revisão, preenchimento das 70 perguntas, cancelamento e confirmação de exclusão, falha de gravação e layout em desktop e tela de 380 pixels. Os testes não utilizam dados pessoais nem chamam provedores de IA.

Resultados detalhados e imagens de verificação são gerados em `app/test-results` por `npm run test:usability`. A interpretação metodológica permanece a de uma inspeção com verificação funcional; não foram coletadas medidas de satisfação, memorização ou desempenho com usuários representativos.
