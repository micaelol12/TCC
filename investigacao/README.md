# Investigação de similaridade semântica

Pipeline independente das variáveis globais de `TCC.ipynb`. O notebook original não
é alterado; âncoras e pares existentes são extraídos por AST, sem executar células.
Consulte `METODOLOGIA.md` para referências, pressupostos e diferenças em relação
aos artigos. As execuções persistidas ficam em `analises/execucoes/`.

## Executar

Na raiz do repositório, usando Python com as dependências do projeto:

```powershell
python -m pip install -r investigacao/requirements.txt
python -m unittest discover -s tests -v
python -m investigacao diagnostic --output analises/execucoes/diagnostico_novo
python -m investigacao documents --text 'content/Escala 6x1.txt' --output analises/execucoes/documento_novo
```

Por padrão, usa CPU, quatro threads e pesos do cache local. `--device cuda` habilita
GPU; `--download` permite baixar modelos. Cada execução exige uma saída nova para
preservar o histórico. `--question-limit 3` é apenas smoke test e marca o instrumento
como parcial. Para cobertura integral, omita essa opção.

Para a GTX 1060 de 3 GB, use o ambiente separado `.venv-gpu` e limite a memória
de inferência sem mudar as configurações científicas:

```powershell
.venv-gpu/Scripts/python.exe -m investigacao diagnostic --device cuda --batch-size 1 --low-vram --output analises/execucoes/diagnostico_gpu_novo
.venv-gpu/Scripts/python.exe -m investigacao documents --device cuda --batch-size 1 --low-vram --text 'content/Escala 6x1.txt' --output analises/execucoes/documento_gpu_novo
.venv-gpu/Scripts/python.exe -m investigacao.controlados --device cuda --batch-size 1 --low-vram --output analises/execucoes/controlados_gpu_novo
```

E5 e NLI alternam residência na GPU. CUDA indisponível provoca erro explícito;
não há fallback silencioso. O manifesto inclui nome da GPU e pico de VRAM do
processo PyTorch. O suporte de inferência com pouca VRAM não se aplica ao comando
de treinamento externo.

O runtime desta placa foi instalado com `investigacao/requirements-gpu.txt`
(Python 3.12/PyTorch CUDA 11.8). Resultados em
`analises/execucao_gpu_similaridade_semantica.md`; notebook independente:
`Investigacao_Similaridade_GPU.ipynb`. `python -m investigacao.relatorio --gpu`
reconstrói esse notebook a partir dos artefatos GPU nomeados da sessão.

O diagnóstico salva métricas por eixo/método/calibração, previsões por pergunta,
ordenação B3a/B3b, B4 por pares, limiares transferidos B5 e cópia das âncoras com
origem no notebook. O manifesto registra versões, revisão dos modelos, hashes,
tempo, RSS final (não pico), tokens processados e truncamentos.

## Corpus externo

```powershell
python -m investigacao prepare-ustancebr --archive analises/ustancebr_r3.zip --hydrated dados/tweets_hidratados.jsonl --output dados/ustancebr_preparado
python -m investigacao external --corpus dados/corpus.jsonl --metadata dados/corpus.meta.json --output analises/execucoes/externo_novo --seeds 13 42 77
python -m investigacao controlled --corpus dados/corpus.jsonl --output analises/execucoes/recuperacao_nova
```

O adaptador r3 recebe os CSVs oficiais do ZIP e uma hidratação JSONL com
`id`, `text`, `author_id`. Separam-se componentes do treino em desenvolvimento;
colisões globais entre treino e teste interrompem a importação para não esconder
vazamento. Perdas de hidratação ficam registradas. Não é necessário extrair o ZIP.

Uma linha JSON por relação texto-alvo, com campos:

```json
{"id":"exemplo-1","text":"Texto original","target":"Alvo original","label":"favor","split":"train","author_id":"autor-1","family_id":"origem-1","label_source":"corpus_publico"}
```

`label` aceita `favor`/`against`; `split` aceita `train`/`dev`/`test`. Todos os
subconjuntos precisam das duas classes. IDs são strings. A auditoria bloqueia
autores, duplicatas e famílias compartilhados entre partições, inclusive entre
alvos. Para derivados sintéticos, preserve a família/partição de origem.

Metadados do corpus:

```json
{
  "name":"Nome da base", "version":"Versão efetivamente obtida",
  "source":"URL original", "license":"Licença conferida",
  "annotation_unit":"text_target", "label_definition":"Mapeamento documentado",
  "split_policy":"Partições oficiais, com desenvolvimento separado por autor",
  "author_ids_unavailable":false
}
```

O comando compara zero-shot, encoder congelado + regressão logística e ajuste
contrastivo + a mesma cabeça; inclui NLI como comparador. C usa somente dev;
sementes, pares de treino, heads, encoder ajustado, seleção por dev, previsões por
alvo e intervalos agrupados ficam persistidos. Os arquivos joblib são artefatos
locais e só devem ser carregados quando produzidos por uma execução confiável.

O diagnóstico de recuperação salva offsets da passagem inserida, rank, MRR e
recall@1/3/5 **da inserção**. Passagens que não cabem inteiras numa janela recebem
falha de contenção explícita; não se interpreta isso como recall de toda evidência.

## Documentos e Sabiá

O comando documental usa E5 fixo + NLI fixo como aplicação exploratória. As 70
perguntas recebem evidências com offsets, similaridade, probabilidades e estado.
Sem escala validada de intensidade, não se fabricam respostas de cinco níveis:
as respostas ficam ausentes e a pontuação integral permanece não identificada.
Após uma execução externa válida, `--selected-run analises/execucoes/externo_novo`
também aplica o modelo escolhido no desenvolvimento às mesmas evidências, salvando
a transferência separadamente em `transferencia_externa.json`.

Para comparar com Sabiá, acrescente `--sabia arquivo.json`, contendo `items`
(`question_id`, `state`), `document_sha256` (mesmo hash do resultado documental)
e `config` (`model`, `prompt_sha256`, `temperature`).
Não use resultados antigos de outro modelo ou documento como se fossem Sabiá
fixo. A função `nli_ablation` permite comparar proposição específica e âncoras
amplas usando o mesmo modelo e os mesmos textos.

O estado da execução real e os impedimentos de dados estão em
`analises/implementacao_similaridade_semantica.md`.

## BRmoral disponível e baselines em GPU de 3 GB

O corpus original v5.10 foi obtido pelo site do autor, com licença CC BY 4.0
no README do ZIP. O registro atualizado está em `analises/acesso_corpora.json`.
Para repetir em diretórios novos:

```powershell
.venv-gpu/Scripts/python.exe -m investigacao prepare-brmoral --archive analises/brmoral_original.download --output analises/dados/brmoral_novo --seeds 42
.venv-gpu/Scripts/python.exe -m investigacao external --corpus analises/dados/brmoral_novo/corpus.jsonl --metadata analises/dados/brmoral_novo/corpus.meta.json --output analises/execucoes/brmoral_novo --device cuda --batch-size 1 --low-vram --baselines-only
```

Esta comparação parcial executa E5 sem ajuste, E5 congelado com cabeça logística
e NLI. `comparison_complete=false` preserva a pendência do contraste com encoder
ajustado. A cabeça logística roda na CPU; E5/NLI usam CUDA. O ajuste completo
float32/AdamW não cabe na GTX 1060 de 3 GB: ver
`analises/brmoral_training_memory.json`. Não substituímos o método por outro
encoder ou treinamento parcial sem registrar uma mudança de protocolo.

Resultados e comandos da rodada: `analises/resultados_brmoral_gpu_20260917.md`.
