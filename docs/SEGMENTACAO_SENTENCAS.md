# Segmentação do notebook passo a passo

O padrão em `Pipeline - Passo a Passo.ipynb` é identificar sentenças completas em
português e agrupá-las com referência de 600 tokens `cl100k_base`, sem sobreposição.
A implementação fica em `tcc_lib/segmentacao.py`, usada pelas funções exportadas
do notebook. As entradas de documento, PDFs, playground e JSON usam o mesmo caminho.

```python
CONFIG_CHUNKS = {
    "estrategia": "sentencas",
    "tokens_alvo": 600,
    "overlap_tokens": 0,
    "encoding_name": "cl100k_base",
    "limite_tokens_entrada": None,
}
```

`limpar_markdown` mantém a limpeza anterior e une linhas de prosa quebradas pela
extração, sem remover as divisões reconhecidas de títulos, listas, tabelas e
parágrafos. Se a limpeza estiver desligada, as linhas originais são preservadas;
uma quebra de linha, sozinha, não encerra uma sentença no segmentador.

Punkt usa parâmetros locais de português brasileiro e ajustes de abreviações
jurídicas. Títulos e marcadores de listas delimitam blocos; prefixos como `1.` ou
`Art. 1º` não viram fragmentos isolados. Parágrafos que cabem no alvo são mantidos
inteiros. Parágrafos maiores são divididos entre sentenças. Títulos são agrupados
com o texto seguinte quando possível. Nada é truncado ou repetido.

Uma sentença que sozinha exceda o alvo permanece inteira e sozinha. A prévia mostra
`tokens`, `sentencas`, `acima_alvo` e `sentencas_longas` por chunk. Títulos e linhas
de tabela são unidades estruturais, não entram na contagem de sentenças; unidades
estruturais longas também podem aparecer acima do alvo.

O orçamento opcional `limite_tokens_entrada` rejeita uma preparação que gere algum
chunk maior que esse valor, antes de qualquer classificação. Ele deve ser um
inteiro maior ou igual ao alvo, em tokens da codificação configurada e já com uma
reserva para os prompts. `cl100k_base` não mede necessariamente os tokens reais
dos provedores. Sem orçamento definido, o alvo não funciona como limite rígido:
inspecione as exceções antes de executar as APIs.

A preparação congela a configuração resolvida, `segmentador_versao` e
`diagnostico_segmentacao` sem duplicar o texto em cada linha do diagnóstico. O
playground leva esses dados ao fluxograma; os testes de textos os salvam no JSON
de entrada e resultado e em `segmentacao.csv`. O manifesto do documento usa o
snapshot da preparação, em vez de reler uma configuração possivelmente alterada.

Para comparar com o algoritmo anterior, mantenha o mesmo texto limpo e ajuste a
configuração da seção antes de reexecutar sua prévia:

```python
CONFIG_PLAYGROUND["chunks"] = {
    **CONFIG_CHUNKS,
    "estrategia": "tokens",
}
```

O modo `tokens` conserva os separadores `['\n\n', '\n', '. ', ' ', '']` do
`RecursiveCharacterTextSplitter`. `max_tokens` continua aceito como alias para
configurações antigas, mas não deve coexistir com `tokens_alvo`. Sem uma estratégia
explícita, o padrão agora é `sentencas`; o alias sozinho não seleciona o algoritmo
antigo. O modo por sentenças rejeita sobreposição diferente de zero.

600 é uma convenção experimental, não um tamanho ótimo demonstrado. Compare os
cortes mantendo 600; depois avalie outros alvos. JEV, fallback, auditoria de
evidências e agregação não foram alterados. Cada chunk elegível continua com peso
igual; mudar a segmentação pode mudar a classificação, a cobertura e o índice.

Punkt e as regras de estrutura são heurísticos. Revise OCR, abreviações incomuns,
listas e títulos sem marcação. O modelo de português está incluído em
`tcc_lib/resources/punkt_portuguese`; não se executa `nltk.download` nem treino. A
primeira contagem com tiktoken continua dependendo do seu vocabulário em cache.

Referência do algoritmo: https://www.nltk.org/api/nltk.tokenize.punkt.html

Reinicie o kernel e reexecute as células de configuração e preparação antes de
classificar. As saídas que dependiam da segmentação anterior foram limpas do
notebook; arquivos de execuções anteriores em disco foram preservados.
