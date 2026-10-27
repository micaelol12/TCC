# Punkt em português brasileiro

Parâmetros originais do diretório `portuguese` do pacote `punkt_tab` do NLTK,
copiados sem alterações da instalação local. O carregamento usa apenas tabelas
de texto, sem pickle, treino ou download durante a execução.

- Fonte: https://github.com/nltk/nltk_data/tree/gh-pages/packages/tokenizers
- Pacote: https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/tokenizers/punkt_tab.zip
- Autores do modelo: Jan Strunk / Tibor Kiss.
- Corpus de treinamento: CETENFolha (Linguateca), Folha de São Paulo.
- O `README.original` preserva a descrição e a atribuição distribuídas pelo NLTK.
- Referência: Kiss, Tibor e Strunk, Jan (2006). Unsupervised Multilingual
  Sentence Boundary Detection. Computational Linguistics 32: 485–525.

Os ajustes locais de abreviações e estrutura estão em `tcc_lib/segmentacao.py`,
identificados como `punkt_pt_v1` nos registros. O modelo é heurístico: revisar
amostras, especialmente OCR, listas e abreviações fora do domínio de treinamento.
