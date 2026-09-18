# Melhoria de generalização — 17/09/2026

A cabeça logística sobre representações conjuntas do BGE congelado atingiu o
critério provisório de BA média por tema >=0,75 e pior BA >=0,60. O critério foi
escolhido localmente antes desta busca, não é padrão científico nem meta explícita
do usuário. O resultado satisfatório diz respeito a temas reservados do BRmoral,
não à validade de um perfil 8values produzido a partir de documentos.

## Método e busca

BGE-m3-zeroshot-v2.0 congelado, entrada texto/hipótese positiva de concordância,
representação de 1.024 dimensões anterior à projeção final, normalização L2,
regressão logística ponderada por tema/classe. Inferência FP16 em GTX 1060 3 GB;
cabeça ajustada em CPU. Não é o ajuste contrastivo E5 inicialmente planejado.

Triagem exclusivamente em treino/desenvolvimento; cada tema do desenvolvimento
foi excluído do treino. BA = acurácia balanceada. Valores arredondados:

| Alternativa | BA média entre temas | Pior BA |
|---|---:|---:|
| Busca NLI bilateral (melhor: hipótese unilateral anterior) | 0,7314 | 0,6019 |
| TF-IDF lexical | 0,6236 | 0,5083 |
| BGE zero-shot | 0,7335 | 0,6643 |
| Média fixa BGE/mDeBERTa | 0,7276 | 0,6574 |
| BGE com limiar ajustado no treino | 0,7370 | 0,6678 |
| BGE com cabeça conjunta, C=10 | **0,7802** | **0,6583** |

As alternativas que não atingiram a meta foram preservadas. Não se reduziu a
meta após observar as falhas. A política seletiva da rodada anterior também
não foi promovida por não sustentar o acerto desejado.

## Teste exploratório em temas reservados

641 textos, 102 grupos de autoria. Oito cabeças independentes; cada tema foi
excluído do treino e do desenvolvimento usado para selecionar C. Todas as
seleções escolheram C=10 antes da inferência no teste. Autores disjuntos entre
as partições. O teste histórico já foi consultado nas rodadas anteriores.

| Método no mesmo teste com tema reservado | Macro-F1 |
|---|---:|
| E5 com cabeça anterior | 0,5230 |
| NLI sobre posição do autor | 0,7036 |
| BGE com cabeça conjunta | **0,7855** |

BA global: 0,7865; BA média entre temas: 0,7800; pior tema: 0,7034;
MCC: 0,5717. Matriz de confusão (linhas/colunas contra, favor):
`[[233, 62], [75, 271]]`.

Bootstrap pareado por grupos, 1.000 repetições, seed 13:
- Ganho de macro-F1 sobre E5: 0,2625; IC95% [0,2217; 0,3034].
- Ganho sobre NLI: 0,0819; IC95% [0,0431; 0,1184].

Os intervalos são condicionais ao teste histórico e não corrigem a seleção
adaptativa de métodos. Não representam uma confirmação independente cega.
Aborto segue fraco em macro-F1 (0,5905), apesar da BA 0,7034. Casamento tem
somente quatro exemplos contrários no teste, limitando a precisão por classe.
As tabelas completas por tema estão no notebook, seção D6, e em metrics.json.

## Transferência para 8values

A cabeça final usa os 2.060 exemplos de treino, C escolhido no desenvolvimento,
sem ajuste com rótulos de teste ou documentos. Nos 280 templates conhecidos de
concordância/discordância, acertou 280/280, com cobertura 100% ao limiar 0,7.
São exemplos artificiais simples e conhecidos: não estimam acurácia documental.
O limiar não fornece uma garantia de confiança probabilística calibrada.

No documento 6x1, usando as evidências já recuperadas, as 70 perguntas receberam
18 estados favoráveis, 11 contrários e 41 incertos. Não há gabarito humano;
nenhuma intensidade ou pontuação final 8values foi inferida. A próxima etapa
científica depende de documentos independentes anotados por humanos, incluindo
relevância das evidências, posição, conflito e ausência de informação.

## Reprodução, rastreabilidade e validação

Código: investigacao/crossencoder_head.py e crossencoder_application.py.
Fontes e adaptações detalhadas: investigacao/METODOLOGIA.md, R4 (Kapoor e
Narayanan, vazamento), R5 (Ribeiro et al., testes comportamentais), R6 (Tunstall
et al., representação/cabeça), R8 (Dror et al., comparação estatística) e R10
(Laurer et al., pares de inferência). O uso de features cruzadas congeladas é
adaptação local, não reprodução de SetFit.

Fonte primária R10: https://arxiv.org/abs/2312.17543, §2 e Figura 1.
Modelo: https://huggingface.co/MoritzLaurer/bge-m3-zeroshot-v2.0, licença MIT,
revisão 9abf1c8aaeb82a2447809c20753ed0b106b76652. Hashes dos pesos em
analises/bge_model_provenance.json. BRmoral original permanece sob CC BY 4.0.

Execuções preservadas em analises/execucoes/:
- crossencoder_head_dev_20260917: features, seleção e triagem.
- crossencoder_head_test_20260917: cabeças, IDs congelados, previsões, métricas,
  intervalos, manifesto e artifact_audit.json.
- crossencoder_application_20260917: cabeça final, diagnóstico, evidências e manifesto.

Comandos executados (as etapas GPU recusam sobrescrever saídas existentes):

```powershell
.venv-gpu/Scripts/python.exe -m investigacao.crossencoder_head
.venv-gpu/Scripts/python.exe -m investigacao.crossencoder_head --evaluate-test
.venv-gpu/Scripts/python.exe -m investigacao.crossencoder_application
.venv-gpu/Scripts/python.exe -m investigacao.notebook_brmoral
.venv-gpu/Scripts/python.exe -m unittest discover -s tests -q
```

25 testes aprovados. Auditoria adicional confirmou exclusão dos temas, separação
de autores, 641 IDs/rótulos de teste, recálculo das métricas, 2.570 vetores finitos
normalizados e uso exclusivo do treino na cabeça final. BRmoral.ipynb atualizado:
50 células, 22 de código executadas sequencialmente com captura de stdout; não
se executou um kernel Jupyter nem se repetiram os modelos ao gerar o notebook.
O treinamento contrastivo E5 segue pendente por restrição de memória do protocolo
original; esta melhoria não deve ser apresentada como resultado desse ajuste.
