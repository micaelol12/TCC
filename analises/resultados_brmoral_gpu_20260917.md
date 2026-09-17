# Avaliação externa BRmoral — 17/09/2026

O bloqueio de acesso ao corpus foi resolvido. A comparação parcial foi executada
na GTX 1060 de 3 GB: embeddings E5 e inferência NLI em CUDA, regressão logística
na CPU. Não foi executado ajuste contrastivo do encoder.

## Origem e auditoria

- [Página oficial de downloads](https://ivandreparaboni.wixsite.com/research/downloads).
- [ZIP original](https://drive.google.com/file/d/1GnkfkZzeO9YqQLlsIangzGb5mPscFBEG/view),
  versão 5.10, setembro de 2019; licença CC BY 4.0 no README interno.
- ZIP preservado em `brmoral_original.download`; documentação extraída em
  `brmoral_dataset_readme.txt`; SHA-256 em `acesso_corpora.json` e metadados.
- 510 participantes × 8 temas = 4.080 registros potenciais. Excluídos 861
  neutros e 8 registros com escore ausente, apesar da classe derivada preenchida.
- 3.211 exemplos binários. Partições fixas por componentes de autor/duplicata:
  treino 2.060, desenvolvimento 510, teste 641; seed 42. Auditoria sem vazamento.
- 508 componentes; proporções 64/16/20% por componentes, aproximadas por exemplos.
  O teste contém 102 componentes. Temas são compartilhados entre partições.
- `s.*` determina posição perante o tema, conferida contra `st.*`; `politics`
  não é usado. `gun-control` é interpretado como legalização do porte de armas,
  conforme textos originais e descrição de R3, sem inversão dos rótulos.

Fundamentação: Santos e Paraboni (2019), §3.1, p.1071,
[DOI](https://doi.org/10.26615/978-954-452-056-4_123), e README da versão obtida.
Referência solicitada pelos autores: Pavan et al., *Morality Classification in
Natural Language Text*, [DOI](https://doi.org/10.1109/TAFFC.2020.3034050).
O artigo de 2019 descreve uma versão anterior; não foi usado para inferir o
tamanho da distribuição atual. Métodos e adaptações estão em
`../investigacao/METODOLOGIA.md`, R3/R4/R6/R7/R8/R9.

## Resultados em teste

| Método | Macro-F1 | Acurácia balanceada | MCC |
|---|---:|---:|---:|
| E5 sem ajuste, templates fixos | 0,4991 | 0,5607 | 0,1927 |
| E5 congelado + regressão logística | 0,8436 | 0,8455 | 0,6889 |
| NLI relacional | 0,6583 | 0,6620 | 0,3238 |

A cabeça usou somente treino; C=10 foi escolhido pela macro-F1 no desenvolvimento
(0,8349), na grade previamente fixada {0,01; 0,1; 1; 10}. O baseline sem ajuste
obteve 0,5390 no desenvolvimento. NLI é comparador, não candidato nesta seleção.
Seeds 13, 42 e 77 produziram as mesmas previsões da cabeça logística; essas
repetições não representam três amostras independentes ou splits distintos.

Diferença congelado − sem ajuste: **+0,3446** de macro-F1; intervalo percentil de
95% **[0,2994; 0,3904]**, bootstrap pareado por 102 componentes, 1.000 repetições.
Esse intervalo é condicional a este treinamento/split, sem variação entre treinos.
O resultado sustenta melhorar a fronteira de decisão neste corpus; não demonstra
ganho do ajuste contrastivo, nem acurácia em documentos políticos longos.

O agregado esconde limitações por tema: para isenção de impostos de igrejas,
macro-F1=0,4533, com **0/13 exemplos favoráveis recuperados**; para aborto,
macro-F1=0,6111. Portanto o valor global de 0,8436 não representa desempenho
uniforme entre temas. Casamento possui apenas quatro exemplos contra no teste,
o que também limita a precisão da avaliação por classe nesse tema.

Execução externa: 110,08 segundos registrados pelo manifesto; pico CUDA alocado
1.232.597.504 bytes e reservado 1.293.942.784 bytes. E5 registrou 3 entradas
truncadas entre 3.227 codificadas, NLI 1 entre 641 pares. O aviso de comprimento
vem da contagem sem truncamento; a inferência limita entradas a 512 tokens.

Artefatos completos em `execucoes/brmoral_baselines_gpu_20260917/`: métricas
globais/por tema, previsões, heads, seleção no dev, partições, intervalos e manifesto.
`frozen_selection.json` declara `comparison_complete=false`.

## Validação e reprodução

`python -m unittest discover -s tests -v`: **16 testes aprovados**, incluindo
novo teste de importação BRmoral (exclusões, inconsistências, determinismo e
agrupamento de autores conectados por duplicata). A execução real validou o
ramo de baselines, modelos locais, CUDA e persistência dos resultados.
Comandos reproduzíveis estão em `../investigacao/README.md`.

## Pendência de hardware

O ajuste atual treina todo o E5 com float32 e AdamW. A contagem de tensores do
checkpoint indica cerca de 278 milhões de parâmetros: aproximadamente 4,45 GB
para pesos, gradientes e dois estados do otimizador, antes de ativações e buffers.
Isso excede os 3 GB da placa. A verificação está em `brmoral_training_memory.json`;
não houve tentativa de treinamento completo nem erro OOM apresentado como resultado.

Para concluir a comparação original, é necessário um ambiente com memória
suficiente para esse treinamento. Adaptação com parâmetros parcialmente treináveis
seria outro experimento e precisaria ser documentada e comparada separadamente.
O teste desta rodada já foi consultado: futuras decisões de hiperparâmetros devem
continuar restritas ao treino/dev, preservando transparência sobre esse uso.

## Transferência ao documento 6×1

Execução `execucoes/documento_6x1_brmoral_gpu_20260917/`, comando:

```powershell
.venv-gpu/Scripts/python.exe -m investigacao documents --text 'content/Escala 6x1.txt' --selected-run analises/execucoes/brmoral_baselines_gpu_20260917 --output analises/execucoes/documento_6x1_brmoral_gpu_20260917 --device cuda --batch-size 1 --low-vram
```

70 perguntas processadas; cabeça escolhida no dev, seed 13, limiar exploratório
0,7 já definido no pipeline. Resultado: 64 favoráveis, 2 contrárias e 4 incertas.
Essa concentração de sinais favoráveis requer cautela: os temas e o formato das
perguntas diferem dos alvos nominais do BRmoral. Não há gabarito documental para
determinar acerto, nem calibração de confiança nesse domínio. Todos os campos
`response` permanecem ausentes; não foi produzida escala de intensidade.
Evidências, offsets, probabilidades, configuração e seleção parcial estão
preservados em `transferencia_externa.json`. Execução total: 43,90 segundos.
