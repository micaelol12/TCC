# BRmoral natural — temas e autores reservados

## Protocolo e fontes

Oito rodadas: em cada uma, um tema é excluído do treino e do desenvolvimento;
o teste contém somente esse tema, usando as partições de autoria já fixadas.
Os 641 exemplos originais de teste são avaliados uma vez por método.
Encoder E5 congelado; regressão logística com C escolhido apenas no dev dos
outros temas, grade {0,01; 0,1; 1; 10}, seed 13. O resultado agregado reúne
oito cabeças distintas; não é a avaliação de um único modelo final.

NLI não é treinado. Duas hipóteses fixadas antes da inferência: proposição
normativa do tema versus “O autor concorda com a seguinte afirmação: {proposição}”.
As oito proposições estão em `protocol.json`; não são novos rótulos dos textos.
São verbalizações locais dos temas, sujeitas a ambiguidades. Neutros permanecem
excluídos. Confiança 0,7 e margem NLI 0,2 permanecem fixas.

Fundamentação: Silva e Paraboni (2023), *Politically-oriented information inference
from text*, §§3–4.1.2, pp.575–578, artigo em `artigos/`; Kapoor e Narayanan
(2023), DOI 10.1016/j.patter.2023.100804; Tunstall et al. (2022), §3.1,
https://arxiv.org/abs/2209.11055; Yin et al. (2019), §3,
https://aclanthology.org/D19-1404/; Dror et al. (2018), §§2–3 e 5,
https://aclanthology.org/P18-1128/. As divisões por tema e o bootstrap por
autoria são adaptações locais descritas em `investigacao/METODOLOGIA.md`.

**Limite:** o teste já foi consultado. Esta rodada é exploratória, não um teste
cego novo. “Tema não visto” refere-se ao ajuste da cabeça, não ao pré-treino
dos modelos. Não há alegação de ausência desses temas no pré-treino.

## Resultados globais

| Método | Macro-F1 | BA | Cobertura direcional | Acerto entre decisões aceitas |
|---|---:|---:|---:|---:|
| E5, tema reservado | 0,5230 | 0,5235 | 47,4% | 54,6% |
| Maioria do treino de cada rodada | 0,2654 | 0,2988 | 100% | 31,8% |
| NLI, proposição literal | 0,6905 | 0,6903 | 59,6% | 75,9% |
| NLI, concordância do autor | 0,7036 | 0,7084 | 53,0% | 73,8% |

A macro-F1 binária força favor/contra comparando os escores. Cobertura e acerto
seletivo aplicam os limiares; não devem ser confundidos com as métricas binárias.
O baseline de maioria usa apenas os outros temas do treino, sem consultar a
distribuição do tema retido. Seu desempenho baixo reflete essa mudança de distribuição.

Diferença NLI autor − proposição: **+0,0131**, IC percentil de 95%
**[-0,0225; 0,0503]**, bootstrap pareado com 1.000 repetições, 102 componentes
de autoria. Como inclui zero, esta comparação não sustenta vantagem clara da
nova hipótese. O intervalo é condicional a estes temas, corpus e partições.

## Resultados por tema — macro-F1

| Tema | E5 reservado | NLI literal | NLI autor |
|---|---:|---:|---:|
| Casamento entre pessoas do mesmo sexo | 0,2620 | 0,7270 | 0,6784 |
| Cotas raciais | 0,4726 | 0,6793 | 0,6357 |
| Isenção de impostos para igrejas | 0,1431 | 0,6335 | 0,6124 |
| Legalização das drogas | 0,7075 | 0,6518 | 0,6177 |
| Legalização do aborto | 0,5756 | 0,4725 | 0,4324 |
| Legalização do porte de armas | 0,2842 | 0,6883 | 0,7317 |
| Pena de morte | 0,6288 | 0,6710 | 0,6842 |
| Redução da maioridade penal | 0,6785 | 0,4290 | 0,6491 |

O ganho do NLI sobre concordância não é uniforme: piora em cinco temas e melhora
em três. Seu aumento global não deve ser apresentado como melhora geral.

## Conclusões

1. **O bom resultado supervisionado com temas conhecidos não transferiu bem.**
   Macro-F1 da cabeça passou de 0,8436 no protocolo anterior para 0,5230 neste.
   Além de remover o tema, reduzimos o volume de treino/dev e retreinamos cabeças;
   logo, a diferença não isola uma causa única nem prova um mecanismo de atalho.
2. **O sucesso em templates não se repetiu na mesma magnitude em textos naturais.**
   NLI autor marcou 0,9803 nos templates e 0,7036 aqui. São tarefas/conjuntos
   distintos, não uma ablação causal direta. A pequena vantagem sobre NLI literal
   é incerta e vem com menor cobertura e menor acerto entre decisões aceitas.
3. **A transferência ao 8values continua não validada.** Os resultados não
   sustentam pontuação final, cinco intensidades ou confiança documental calibrada.
4. **Não calibrar pelo teste.** Antes de nova seleção, definir validação interna
   com temas reservados no treino/dev, preservando o teste para relato transparente.
   Ajuste contrastivo completo ainda depende de memória adicional ou protocolo
   alternativo documentado; o diagnóstico atual não resolve essa etapa.

## Execução e validação

GTX 1060 3 GB, CUDA 11.8: 105,55 s; pico alocado 1.232.597.504 bytes. E5 e NLI
em GPU, cabeças na CPU. E5 registrou 3 entradas truncadas e NLI 2 pares,
com máximo 512 tokens. Sem alteração de limiares depois dos resultados.

**20 testes aprovados**, incluindo isolamento de tema/autoria e métricas seletivas.
Auditoria adicional das oito partições persistidas confirmou 641 IDs únicos de
teste, sem tema ou autor do teste no ajuste da respectiva cabeça.

```powershell
.venv-gpu/Scripts/python.exe -m investigacao.temas_reservados --data analises/dados/brmoral_20260917 --output analises/execucoes/temas_reservados_gpu_nova
.venv-gpu/Scripts/python.exe -m unittest discover -s tests -q
.venv-gpu/Scripts/python.exe -m investigacao.notebook_brmoral
```

Artefatos: `analises/execucoes/temas_reservados_gpu_20260917/` contém protocolo,
manifesto, cabeças, IDs das partições, seleção de C, previsões, métricas e intervalo.
Notebook: `BRmoral.ipynb`, seção D3.
