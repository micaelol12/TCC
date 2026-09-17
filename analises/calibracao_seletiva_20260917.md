# Seleção de limiares e abstenção — 17/09/2026

## Pergunta e protocolo

É possível reduzir erros em temas novos ajustando decisão e abstenção somente
no desenvolvimento? Usamos as duas hipóteses NLI anteriores, sem ajuste de pesos.
Isso é seleção de limiares, **não calibração das probabilidades**.

Antes da inferência, foi fixada a grade de confiança {0,5; 0,6; 0,7; 0,8; 0,9;
0,95} e margem {0; 0,1; 0,2; 0,3; 0,4}. Para cada tema reservado, os demais
temas do desenvolvimento escolhem a maior cobertura sujeita a acerto empírico
≥80%, cobertura ≥25% e dez exemplos aceitos de cada classe verdadeira.
Sem candidato elegível, abstenção total. Empates são resolvidos por acerto,
menor confiança/margem e ordem fixa das hipóteses. Critérios locais, não garantias.

510 textos de desenvolvimento foram inferidos na GPU para cada hipótese.
Todas as seleções foram persistidas antes de carregar as previsões dos 641 textos
de teste da rodada natural anterior. Partições por autores e duplicatas preservadas;
o tema avaliado não entra na seleção. Esse teste já havia sido consultado, portanto
a avaliação continua exploratória. A política varia por tema reservado e não
constitui uma configuração final única para o 8values.

Fundamentação: Kapoor e Narayanan (2023), *Leakage and the reproducibility crisis
in machine-learning-based science*, DOI 10.1016/j.patter.2023.100804; Yin et al.
(2019), *Benchmarking Zero-shot Text Classification*, §3,
https://aclanthology.org/D19-1404/. As metas, grade e fallback são adaptações
de engenharia/avaliação do projeto, não resultados atribuídos a essas fontes.
Unidade texto-alvo segue Silva e Paraboni (2023), §§3–4.1.2, artigo local.

## Resultado em teste

| Política | Aceitos / 641 | Acertos | Erros | Cobertura | Acerto entre aceitos |
|---|---:|---:|---:|---:|---:|
| NLI literal, fixo 0,7/0,2 | 382 | 290 | 92 | 59,6% | 75,9% |
| NLI autor, fixo 0,7/0,2 | 340 | 251 | 89 | 53,0% | 73,8% |
| Seleção pelo desenvolvimento | 274 | 192 | 82 | 42,7% | 70,1% |

A seleção reduziu o número absoluto de erros, mas recusou muito mais casos e
teve menor acerto condicional. Não constitui melhora do compromisso entre
cobertura e acerto observado frente às duas políticas fixas. A comparação
seleciona tanto hipótese quanto limiares; não isola o efeito de um só parâmetro.

## Política selecionada por tema

| Tema reservado | Hipótese | Confiança | Margem | Acerto dev aceitos | Aceitos teste | Acerto teste aceitos |
|---|---|---:|---:|---:|---:|---:|
| Casamento entre pessoas do mesmo sexo | autor | 0,95 | 0 | 82,4% | 33 | 90,9% |
| Cotas raciais | autor | 0,95 | 0 | 80,6% | 27 | 66,7% |
| Isenção de impostos para igrejas | literal | 0,9 | 0 | 81,1% | 56 | 80,4% |
| Legalização das drogas | autor | 0,5 | 0 | 80,4% | 47 | 63,8% |
| Legalização do aborto | literal | 0,5 | 0 | 80,6% | 53 | 60,4% |
| Porte de armas | literal | 0,9 | 0 | 80,5% | 22 | 90,9% |
| Pena de morte | abstenção total | — | — | sem candidato | 0 | não definido |
| Redução da maioridade penal | literal | 0,5 | 0,4 | 80,1% | 36 | 47,2% |

O dev de cada linha contém outros temas. A meta de 80% no desenvolvimento não
se transferiu uniformemente. Ausência de decisões em pena de morte não é acerto
nem neutralidade: é o fallback definido antes de observar os resultados.

## Conclusão

Esta estratégia de seleção não resolveu a generalização para temas novos.
Não substituímos os limiares anteriores no pipeline documental nem produzimos
uma pontuação 8values. O resultado desaconselha continuar alterando limiares
com base neste mesmo teste. O próximo avanço deve investigar a representação
e a formulação texto-alvo com validação interna por tema no treino/dev; ajuste
contrastivo permanece pendente por memória da GPU. Uma alternativa de treinamento
com menor consumo precisaria ser registrada como mudança de protocolo.

## Validação e reprodução

21 testes aprovados, incluindo rejeição de dados de teste e tema reservado na
seleção, seleção em fixture perfeita e abstenção em fixture incompatível.
Inferência de desenvolvimento real na GTX 1060: 44,76 s registrados. Previsões
de teste reutilizadas sem repetir modelos; origem e código registrados por hash.

```powershell
.venv-gpu/Scripts/python.exe -m investigacao.calibracao_seletiva --data analises/dados/brmoral_20260917 --natural-run analises/execucoes/temas_reservados_gpu_20260917 --output analises/execucoes/calibracao_seletiva_gpu_nova
.venv-gpu/Scripts/python.exe -m unittest discover -s tests -q
.venv-gpu/Scripts/python.exe -m investigacao.notebook_brmoral
```

Artefatos em `analises/execucoes/calibracao_seletiva_gpu_20260917/`: protocolo,
previsões do dev, grades completas, seleções congeladas, decisões de teste,
métricas e manifesto. Notebook `BRmoral.ipynb`, seção D4.
