# Modelos de rastreabilidade e validação

Use somente as seções pertinentes ao trabalho atual.

## Registro de decisão metodológica

```markdown
### Fundamentação — <etapa ou bloco>

- Referência: SOBRENOME, Nome et al. (ano). Título.
- Localização: `artigos/<arquivo>.pdf`, p. X–Y, seção Z.
- Decisão sustentada: <o que a fonte justifica>.
- Aplicação no TCC: <como a decisão foi implementada>.
- Adaptações e limites: <diferenças em relação à fonte e consequências>.
```

Se a fonte for externa, substitua o caminho por DOI ou URL persistente. Nunca informe página ou seção sem conferi-la.

## Docstring curta para código reutilizável

```python
def nome_da_funcao(...):
    """Descreva propósito, entradas, saída e pressupostos.

    Fundamentação:
        Autor et al. (ano), Título, `artigos/arquivo.pdf`, seção/página.
        Explique qual decisão foi derivada da referência e qual adaptação foi feita.

    Validação:
        Indique o teste, invariante ou experimento que demonstra o comportamento.
    """
```

Use comentários adicionais somente para decisões locais não óbvias. Em notebook, prefira o registro de decisão em Markdown para não sobrecarregar a célula de código.

## Matriz mínima de validação

| Tipo de código | Evidência mínima | Verificações adicionais quando relevantes |
|---|---|---|
| Ingestão e limpeza | amostra conhecida, contagens antes/depois e invariantes | duplicatas, ausentes, codificação e rastreabilidade de exclusões |
| Extração de atributos | exemplos controlados com saída esperada | ablação, cobertura, estabilidade e comparação com a fonte |
| Estatística | dados sintéticos ou resultado conhecido | pressupostos, diagnóstico, intervalo de confiança e sensibilidade |
| ML/NLP supervisionado | conjunto separado e baseline | vazamento, desbalanceamento, métricas por classe, sementes e análise de erros |
| Embeddings/agrupamento | casos semanticamente controlados | métrica de distância, estabilidade, sensibilidade e avaliação humana |
| LLM | conjunto de exemplos rotulados e critério objetivo | versão/modelo, prompt, temperatura, consistência, erros e concordância humana |
| Visualização | conferência dos dados agregados e rótulos | escalas, incerteza, acessibilidade e risco de interpretação enganosa |
| Utilitário/orquestração | teste de comportamento e caso-limite | idempotência, mensagens de erro e integração com a etapa científica |

## Registro de execução

```markdown
### Validação executada

- Comando ou procedimento: `<comando ou descrição reproduzível>`
- Dados usados: <fixture, amostra, partição ou versão do conjunto>
- Resultado observado: <saída, métricas e limiares>
- Estado: aprovado | reprovado | parcial
- Limitações ou pendências: <o que ainda não foi demonstrado>
```

Um comando que apenas termina sem erro comprova execução, não validade científica. Relacione cada evidência ao risco que ela reduz.

## Resumo final da tarefa

Ao entregar uma alteração, sintetize:

1. arquivos e blocos alterados;
2. referências acadêmicas usadas e a decisão sustentada por cada uma;
3. validações realmente executadas e resultados;
4. limitações ou pendências restantes.
