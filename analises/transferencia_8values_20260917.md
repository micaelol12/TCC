# Transferência BRmoral → 8values: diagnóstico comportamental

## Protocolo

Execução real na GPU, cabeça BRmoral escolhida anteriormente no desenvolvimento,
sem treino, recalibração ou seleção pelos resultados deste diagnóstico. Fontes:
Ribeiro et al. (2020), *Beyond Accuracy: Behavioral Testing of NLP Models with
CheckList*, §2, https://aclanthology.org/2020.acl-main.442/; Yin et al. (2019),
*Benchmarking Zero-shot Text Classification*, §3, https://aclanthology.org/D19-1404/.
Adaptações e vínculo com unidade texto/alvo em `investigacao/METODOLOGIA.md`.

70 perguntas × 2 templates × apoio/oposição = 280 casos. Templates declaram
concordância/discordância ou defesa/rejeição, citando a proposição inteira.
Nenhuma frase é invertida pela inserção de “não”. `effect` permanece metadado,
não gabarito de posição. Rótulos têm origem `construcao_controlada`.
Não são textos naturais anotados nem 280 observações independentes.

Comando:

```powershell
.venv-gpu/Scripts/python.exe -m investigacao.transferencia_8values --selected-run analises/execucoes/brmoral_baselines_gpu_20260917 --output analises/execucoes/transferencia_8values_gpu_20260917
```

## Resultados

| Indicador | Cabeça BRmoral | NLI, pergunta literal |
|---|---:|---:|
| Macro-F1 binário | 0,7785 | 0,3333 |
| Acurácia balanceada | 0,7786 | 0,5000 |
| Ordenação apoio > oposição | 100% | 36,4% |
| Pares com ambos os lados corretos | 55,7% | 0% |
| Cobertura direcional após limiares | 51,8% | 100% |
| Acerto entre decisões aceitas | 88,3% | 50% |

Cabeça BRmoral: 218/280 classificações binárias corretas. Com probabilidade
máxima ≥0,7, são 145 decisões aceitas: 128 corretas e 17 erradas; 135 abstenções.
Não se deve confundir 88,3% de acerto condicional com acerto sobre todos os casos.
O acerto incluindo abstenções como não satisfeitas é 128/280 = 45,7%.

NLI: todos os casos foram classificados como apoio, inclusive as 140 rejeições,
mesmo com confiança ≥0,7 e margem entailment−contradiction ≥0,2. A hipótese
literal e a citação compartilhada são uma possível explicação, não uma causa
isolada experimentalmente. O achado é restrito a estes templates.

## Conclusão e próximo trabalho

Há sensibilidade relativa à mudança de posição na cabeça BRmoral, mas a decisão
absoluta não transfere de maneira suficientemente consistente. Não atribuímos
uma causa definitiva a isso; calibração e dependência do conteúdo são hipóteses.
Não é apropriado converter essas saídas diretamente em cinco respostas/intensidades
do 8values. O NLI também não resolve automaticamente essa transferência.

O próximo diagnóstico deve separar o efeito da citação do conteúdo proposicional,
com formas de expressão adicionais e avaliação em textos naturais de posição
rotulada. Se houver calibração, será necessário reservar famílias de desenvolvimento
e avaliação antes de ajustar parâmetros. Estes casos já foram consultados e não
podem virar teste cego. A tarefa contrastiva original continua pendente por memória.

## Artefatos e validação

- `investigacao/transferencia_8values.py`: construção, execução CUDA e métricas.
- `tests/test_transferencia_8values.py`: preservação de proposição/agrupamento,
  distinção entre abstenção e acerto, rejeição de IDs repetidos.
- `analises/execucoes/transferencia_8values_gpu_20260917/`: protocolo anterior à
  inferência, 280 casos, 560 previsões, métricas e manifesto.
- `BRmoral.ipynb`: nova seção D1 com resultados e interpretação.

Suite: **17 testes aprovados**. Modelo de cabeça e limiares não foram alterados.
