# Experimento: nove níveis com polo primeiro

O objetivo é testar nove níveis sem deixar a divisão das intensidades de um polo produzir, por si só, uma decisão de ausência de posição. A opção `regra_decisao="polo_primeiro"` é experimental. A regra anterior permanece disponível como `"nivel"` e continua sendo o padrão da API.

## Regra

1. Some os valores retornados nos níveis do polo A, polo B e sem posição, separadamente. Compare os três grupos, incluindo sem posição.
2. Escolha o grupo com maior soma. Empate entre grupos produz decisão indeterminada, sem converter o empate em 50.
3. Dentro de A ou B, escolha o nível mais provável. Empate entre intensidades também permanece indeterminado. Se o grupo sem posição vencer, escolha o centro.
4. A direção é sinalizada como incerta quando a diferença entre o grupo vencedor e o segundo fica abaixo de `margem_direcao_minima` (`direction_margin_min` na API).
5. A intensidade é sinalizada como incerta quando o suporte condicional `P(nível) / P(polo)` fica abaixo de `confianca_nivel_minima` (`level_confidence_min` na API). Neste modo, esse limiar tem interpretação diferente da confiança original do SDK, que continua preservada para auditoria.

Os limiares apenas sinalizam incerteza no modo baixo/sem fallback. No modo médio, acionam o LLM. Uma pontuação com incerteza é preliminar. O parecer de evidência continua observacional e não muda a regra. No modo alto, a classificação é feita pelo LLM e o seletor da regra JEV fica inativo.

## Uso

No Lab, selecione nove níveis, escolha Score ou Choice e, em **Regra de decisão do JEV**, selecione **Polo primeiro · experimental**. Para comparar apenas a regra, mantenha o texto, a escala, a primitiva, os modelos e os demais parâmetros iguais. O modo baixo evita a revisão pelo LLM.

Na API Lab:

```json
{"processing_level":"low","text":"Seu texto","experiment_config":{"regra_decisao":"polo_primeiro","primitiva_polaridade":"choice"}}
```

O servidor usa nove níveis por padrão; o snapshot `escala` pode ser enviado para escolher outra escala. `JEV_DECISION_RULE=nivel` mantém o comportamento histórico do servidor. A opção e as distribuições iniciais ficam na configuração efetiva e em `axes[].jev_diagnostics`, acompanhando histórico, comparação, reports e registros de execução.

No notebook, reexecute as definições atualizadas (a primeira célula já as carrega) e a configuração do playground:

```python
CONFIG_PIPELINE_PLAYGROUND["cascata"].update(
    escala=ESCALA_9_NIVEIS.model_dump(mode="json"),
    regra_decisao="polo_primeiro",  # Troque por "nivel" para comparar.
    primitiva_polaridade="choice",
    usar_fallback=False,
)
```

Depois, reexecute a análise que recria `pipeline_playground`. As saídas já salvas no notebook são históricas; editar a configuração não as recalcula automaticamente.

## Replay sem novas chamadas

Para separar o efeito da regra da variação entre chamadas do modelo, reaproveite a distribuição já salva no fluxograma. Execute a partir da raiz TCC:

```powershell
.venv/Scripts/python.exe scripts/replay_decision_rules.py runs/playground/fluxograma-20261023T031042309812Z.html runs/playground/fluxograma-20261023T031246051077Z.html --output runs/playground/comparacao-regras-nacionalismo.json
```

O arquivo de saída precisa ser novo. O comando não consulta provedores nem modifica os fluxogramas originais. Por padrão, compara o eixo diplomático; use `--axis economic|diplomatic|state|society` para outro eixo.

As distribuições registradas do parágrafo de nacionalismo produzem:

| Escala | Regra anterior | Polo primeiro | Incerteza em polo primeiro |
|---|---|---|---|
| 9 níveis | nível 0, índice A 50 | nível −3, índice A 12,5 | Intensidade incerta: suporte condicional 28/68 = 41,2%, abaixo de 50% |
| 5 níveis | nível −2, índice A 0 | nível −2, índice A 0 | Nenhum dos novos critérios acionado com os limiares atuais |

O resultado de nove níveis favorece Nação pela soma de 68% contra 32% de sem posição, mas não resolve a dúvida entre forte (28%) e muito forte (26%). O índice A 12,5 decorre do nível escolhido; não é confiança nem probabilidade de acerto.

## Limites da conclusão

Este replay comprova o comportamento do código sobre as mesmas entradas, não a correção da classificação. Agrupar categorias pode favorecer os polos com mais alternativas, e as distribuições do JEV não foram calibradas para esta tarefa. O experimento precisa ser comparado à regra anterior em vários exemplos anotados, incluindo textos descritivos, negações, posições equilibradas e ausências de posição. Uma etapa futura pode perguntar diretamente por A, B ou sem posição antes da intensidade, em vez de somar a distribuição ordinal.

O trecho sobre nacionalismo é uma definição. Identificar conteúdo associado ao polo Nação não comprova que o autor o endossa. A regra experimental mantém a rubrica de posições defendidas; não altera esse objetivo de medição.
