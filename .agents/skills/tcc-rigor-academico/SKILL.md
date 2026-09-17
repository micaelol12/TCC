---
name: tcc-rigor-academico
description: Criar, alterar ou revisar código neste projeto de TCC com rastreabilidade acadêmica, explicação das decisões e validação reproduzível. Use em notebooks, scripts, consultas, modelos, análises e testes do repositório; não se aplica a tarefas puramente editoriais sem código.
---

# Rigor acadêmico do TCC

Trate fundamentação, explicação e validação como partes do código, não como documentação opcional.

## Fluxo obrigatório

1. Antes de implementar, inspecione `artigos/` e procure trabalhos que sustentem o método, a métrica, o pré-processamento ou a decisão algorítmica em questão.
2. Leia no documento a página, seção ou trecho relevante. Não atribua uma ideia a uma fonte com base apenas no título, no nome do arquivo ou no resumo.
3. Se `artigos/` não contiver suporte suficiente, use outra publicação acadêmica primária ou revisada por pares. Dê preferência à fonte original do método. Não invente referências.
4. Registre a fonte junto do bloco lógico correspondente e explique como ela foi traduzida para a implementação. Declare adaptações, simplificações e divergências.
5. Execute validação proporcional ao comportamento e ao risco do código. Guarde ou relate comandos, dados de teste, métricas e resultados observados.
6. Antes de concluir, confira a definição de pronto abaixo e apresente um resumo que relacione código, referências e evidências de validação.

## Granularidade da rastreabilidade

Todo código novo ou materialmente alterado precisa de referência acadêmica verificável. A unidade mínima é cada função, classe, etapa de pipeline ou célula de notebook com lógica própria; não é necessário repetir a citação em cada linha.

- Em notebooks, use uma célula Markdown imediatamente antes do código ou uma seção metodológica inequivocamente vinculada às células.
- Em arquivos-fonte, use docstrings ou documentação adjacente. Comentários devem explicar apenas decisões que não estejam claras no código.
- Células de importação, configuração e orquestração podem apontar para a referência da etapa que viabilizam, desde que o vínculo seja explícito.
- Testes devem apontar para o método ou requisito científico que verificam e explicar o critério de aceitação.

Cada registro deve conter, no mínimo:

- citação identificável: autores, ano e título;
- localização: caminho em `artigos/` e página/seção, quando local; DOI ou URL persistente, quando externa;
- decisão sustentada pela fonte;
- adaptação feita neste projeto.

Uma referência genérica não valida automaticamente todo o arquivo. Não use uma fonte para sustentar afirmações que ela não faz.

## Explicação exigida

Explique o propósito do código, entradas e saídas, pressupostos, decisões metodológicas e limitações. Em notebooks, prefira narrativa Markdown antes da implementação; em módulos reutilizáveis, prefira docstrings concisas. Explique o raciocínio e a relação com a literatura, não a sintaxe óbvia.

## Validação exigida

Valide duas dimensões quando aplicáveis:

- **Engenharia:** execução real, testes unitários ou de integração, casos-limite, invariantes, tratamento de dados ausentes, determinismo e ausência de regressões.
- **Científica:** baseline, divisão adequada dos dados, prevenção de vazamento, métricas justificadas pela literatura, análise de erros, sensibilidade/robustez e reprodutibilidade por sementes e versões.

Para alterações pequenas, use o menor teste que demonstre o comportamento. Para NLP, estatística, aprendizado de máquina ou uso de LLM, não se limite a verificar que o código executa: avalie a qualidade do resultado e os riscos metodológicos relevantes. Nunca declare uma validação bem-sucedida sem tê-la executado. Se algo não puder ser validado, identifique exatamente o que falta, o motivo e o impacto.

Consulte [modelos de rastreabilidade e validação](references/modelos.md) ao criar ou revisar código. Adapte os modelos ao artefato; não os copie mecanicamente.

## Definição de pronto

Considere a tarefa concluída somente quando:

- cada bloco lógico criado ou alterado tem fonte acadêmica rastreável;
- a implementação e suas diferenças em relação à fonte estão explicadas;
- as validações relevantes foram executadas e seus resultados estão registrados;
- limitações, falhas e validações pendentes estão explícitas;
- a resposta final informa arquivos alterados, referências usadas e evidências de validação.
