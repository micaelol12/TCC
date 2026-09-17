# Formato e hipótese na transferência ao 8values

## Método

560 casos: 70 perguntas × aspas presentes/ausentes × marcador antes/depois ×
concordância/discordância. Mesmos modelos e limiares das rodadas anteriores;
nenhum ajuste de pesos ou calibração. A proposição é repetida literalmente em
todos os casos: sem aspas não significa sem repetição ou texto natural.

Fontes: Ribeiro et al. (2020), *Beyond Accuracy: Behavioral Testing of NLP Models
with CheckList*, §2, https://aclanthology.org/2020.acl-main.442/; Yin et al. (2019),
*Benchmarking Zero-shot Text Classification*, §3,
https://aclanthology.org/D19-1404/. Adaptação local: fatorial de superfície e duas
hipóteses NLI pré-definidas, proposição literal versus concordância do autor.
Não usamos `effect` como rótulo de stance. Não há anotação humana nova.

A rodada principal é `execucoes/ablacao_formato_8values_gpu_20260917_v2`.
A primeira rodada, sem sufixo, continha “Discordo com” em vez de “Discordo da”;
foi preservada e substituída após correção gramatical para alinhar o controle ao
teste anterior. A alteração não foi seleção de template por desempenho.

## Resultados principais — macro-F1 binário

| Formato | Cabeça BRmoral | NLI proposição | NLI concordância do autor |
|---|---:|---:|---:|
| Aspas, marcador antes | 0,7786 | 0,3333 | 0,9857 |
| Aspas, marcador depois | 0,8212 | 0,4081 | 0,9499 |
| Sem aspas, marcador antes | 0,7272 | 0,3333 | 0,9929 |
| Sem aspas, marcador depois | 0,8214 | 0,3939 | 0,9929 |
| Agregado | 0,7875 | 0,3681 | 0,9803 |

O NLI com a proposição literal acertou apenas 9/280 rejeições. Com a hipótese
“O autor concorda com a seguinte afirmação: {pergunta}”, acertou 269/280 rejeições
e 280/280 apoios. É a mesma premissa e o mesmo modelo: a hipótese faz grande
diferença neste conjunto. Cobertura após limiares: 56,25% na cabeça BRmoral,
96,96% no NLI literal e 97,68% no NLI sobre concordância do autor.

## Interpretação

1. **Retirar aspas, sozinho, não resolve a falha do NLI.** Com marcador antes,
   macro-F1 literal continua 0,3333 com ou sem aspas.
2. **Formular a hipótese sobre a posição do autor melhora muito estes casos.**
   A proposição em si e a concordância do autor são tarefas distintas. Esse
   resultado apoia investigar o enquadramento relacional da hipótese.
3. **A cabeça BRmoral é sensível ao formato.** Macro-F1 varia de 0,7272 a 0,8214.
   O resultado anterior não era explicado exclusivamente pelas aspas.
4. **0,9803 não é acurácia documental.** Os textos declaram posição explicitamente
   e compartilham a pergunta literal; há somente 70 famílias. O novo NLI não foi
   promovido a solução final nem usado para escolher parâmetros por este teste.

Próximo passo: testar essa hipótese em exemplos naturais com posição existente,
incluindo temas reservados no BRmoral e controle de autoria. Só então decidir
sobre calibração/abstenção. Paráfrases sem repetição da pergunta continuam pendentes;
o teste atual isola formato e hipótese, não resolve essa generalização.
Nenhuma pontuação final ou escala de intensidade 8values foi produzida.

## Reprodução e validação

```powershell
.venv-gpu/Scripts/python.exe -m investigacao.transferencia_8values --selected-run analises/execucoes/brmoral_baselines_gpu_20260917 --output analises/execucoes/ablacao_formato_8values_gpu_nova --format-ablation
.venv-gpu/Scripts/python.exe -m unittest discover -s tests -q
.venv-gpu/Scripts/python.exe -m investigacao.notebook_brmoral
```

18 testes passaram. A execução real CUDA preserva protocolo, hash do head,
casos, 1.680 previsões, métricas e manifesto. Novo teste confere que remover
aspas preserva o restante do texto e o rótulo. `BRmoral.ipynb` contém seção D2.
