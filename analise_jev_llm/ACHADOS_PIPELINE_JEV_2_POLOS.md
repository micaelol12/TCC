# Catálogo de achados — Pipeline_JEV_2_Polos_LLM.ipynb

Anexo de `ANALISE_PIPELINE_JEV_2_POLOS.md`. Cada achado foi produzido por um revisor especializado e conferido por um verificador independente, que tentou refutá-lo relendo o código e as saídas salvas e, quando possível, reproduzindo o comportamento offline. Achados com sufixo `-Vnn` foram acrescentados pelo verificador; os `CMP-*`, pelo crítico de completude, e também foram verificados.

- **Severidade** é a ajustada pela verificação.
- **Parcial**: o achado procede em parte; o texto abaixo usa o enunciado e a recomendação corrigidos.
- Os textos foram resumidos. As referências a células usam o índice JSON do notebook, começando em 0 (`CELL n`).

## Código, robustez e reprodutibilidade (COD)

### COD-01 · Alta · Correção · Confirmado
**As saídas salvas vêm de execuções diferentes: o gráfico e a tabela do documento não batem**

- **Onde:** Metadados execution_count; CELL 39 (tabela de cobertura), CELL 41 (decisões por chunk), CELL 44 (gráfico); CELLs 26–32 (benchmark); CELLs 37 e 43
- **Enunciado corrigido:** As saídas salvas misturam pelo menos duas execuções do documento: o gráfico (CELL 44) e a tabela por chunk (CELL 41) são de uma execução anterior à tabela de cobertura (CELL 39), e a diferença no valor A chega a 5,4 pontos. As CELLs 37 e 43 foram editadas depois de executadas (execution_count None), então não se sabe se o código salvo é o que gerou as saídas. O benchmark (contagens 14–18) também é anterior à reexecução das definições (41–56).
- **Impacto:** Nenhum número do notebook pode ser atribuído com segurança a uma única versão de código e configuração. Juntar valores de células diferentes no texto do TCC (por exemplo, '46 chamadas' com 'economic 93,4') mistura execuções distintas.
- **Recomendação (ajustada):** Manter a recomendação: execução limpa do início ao fim (nbconvert/papermill) antes de citar números, mais a célula final de invariantes. Além disso, gravar os registros brutos de cada execução (COD-04). Assim, uma divergência futura pode ser explicada comparando registros, sem precisar de novas chamadas.

### COD-04 · Alta · Melhoria · Confirmado
**Resultados não são salvos em disco e falta um manifesto da execução (run_id, versões, commit, tokens)**

- **Onde:** CELLs 29, 39, 41 e 44 (resultados só em memória); CELL 22 (usage descartado); repositório git
- **Evidência:** Os objetos `benchmark_jev_llm_2_polos` (CELL 29), `resultado_documento` (CELL 39) e a figura (CELL 44) não são gravados: não há to_csv, json.dump nem savefig no notebook. Não há run_id, data/hora, versão do Python ou dos SDKs, commit git nem hash da configuração. Só o modelo informado pelo JEV fica registrado ('jev-1.13.0'). SystemOneResponse.usage (input/output tokens) e o usage da resposta do LLM são descartados. No git, todos os commits recentes têm a mensagem '.' (497ba73, 44f6824, 7c02a72…), e analise_jev_llm/__pycache__/pipeline_score.cpython-314.pyc está versionado; o .gitignore só contém '.venv/' e '.env'.
- **Impacto:** Sem resultados salvos e sem manifesto, não dá para auditar nem recalcular métricas sem novas chamadas pagas, nem provar qual código e configuração produziram cada número do TCC (ver COD-01). Custo e tamanho em tokens não podem ser reportados.
- **Recomendação (ajustada):** A recomendação é adequada e viável. Priorize gravar `registros` em JSONL, porque o restante pode ser recalculado a partir deles. Inclua no manifesto o hash das rubricas (`pipeline.rubricas`) e do texto do prompt do LLM.

### COD-V01 · Alta · Correção · Acrescentado na verificação
**Com o limiar de confiança 0,70 e o LLM em 0/100, o 'valor A' do documento é quase uma proporção de trechos no polo A, e os rótulos do 8Values são aplicados a essa proporção**

- **Onde:** CELL 5 (confianca_score_minima=0.70), CELL 22 (_motivos; score_8values = nivel*100 no LLM), CELL 37 (média), CELLs 43–44 (rotulo_8values no gráfico)
- **Evidência:** Nas 20 linhas visíveis (CELLs 31 e 41), a confiança do Score é igual a |P(A) − P(B)| com diferença de no máximo 0,01, e o score é P(A) (COD-09). Pela regra de _motivos, um eixo relevante com confiança < 0,70 vai para o LLM. Assim, todo score do JEV que permanece tem P(A) ≥ ~0,85 ou ≤ ~0,15, e o LLM só produz 0 ou 100. Os dados da CELL 39 confirmam essa distribuição quase binária. O desvio-padrão observado é 90%, 95% e 94% do máximo possível para uma variável binária com a mesma média: economic 22,2 de 24,8; diplomatic 42,2 de 44,6; state 38,9 de 41,5. Em society, dp 1,75 com média 98,75 indica que praticamente todos os scores estão perto de 100.
- **Impacto:** O índice mede principalmente a proporção de trechos com posição que se inclinam para o polo A, não uma intensidade comparável à pontuação do quiz 8Values. Qualquer documento consistente numa direção tende a 95–100.
- **Recomendação:** Tratar e nomear o índice como 'proporção de trechos com posição no polo A' e informá-lo com n, cobertura e intervalo bootstrap. Não aplicar rótulos do 8Values ao documento, ou aplicá-los só quando o intervalo inteiro couber numa faixa, marcando-os como ilustrativos. Como análise de sensibilidade, informar também a média de P(A) sem fallback (usar_fallback=False) e a variação dos limiares, mostrando quanto a regra de encaminhamento empurra o índice para os extremos. Para o alinhamento com o usuário, usar o mesmo construto dos dois lados, ou calibrar o índice com dados anotados, antes de comparar. Aplicar o mesmo tratamento a todos os documentos.

### COD-02 · Média · Correção · Confirmado
**O notebook só roda em Python 3.14, embora a CELL 1 afirme '3.10 ou superior'**

- **Onde:** CELL 8 (ler_json_tiptado), CELL 17 (T = TypeVar), CELL 1 (texto), requirements.txt (pandas==3.0.6)
- **Evidência:** CELL 8: `def ler_json_tiptado(caminho: str | Path, tipo: type[T]) -> T:`, mas T só é criado na CELL 17 (`T = TypeVar("T")`). Executei essa definição isolada: Python 3.11.9 → `NameError: name 'T' is not defined`; Python 3.12.10 → mesmo erro. O pyflakes também acusa 'undefined name T'. No kernel salvo (3.14.8) funciona só porque as anotações são avaliadas de forma preguiçosa (PEP 649/749). Além disso, o PyPI informa requires_python '>=3.11' para pandas 3.0.6, a versão fixada em requirements.txt.
- **Impacto:** Em Python 3.10–3.13, executar de cima para baixo para na CELL 8. Em 3.10 nem o pandas instala. Quem seguir a instrução da CELL 1 não consegue reproduzir o notebook.
- **Recomendação (ajustada):** A recomendação está correta: definir T na CELL 3 (ou usar PEP 695) e declarar na CELL 1 'Python ≥ 3.11 (resultados gerados em 3.14.8)'.

### COD-03 · Média · Correção · Confirmado
**Qualquer exceção aborta o benchmark ou o documento e descarta todos os registros já obtidos**

- **Onde:** CELL 27 (executar_benchmark_jev_llm_2_polos), CELL 37 (processar_documento_com_jev_2_polos), CELL 22 (CascataJevLLM2Polos.classificar)
- **Evidência:** Os laços `registros.append(await pipeline.classificar(...))` (CELLs 27 e 37) não têm try/except, gravação incremental nem retomada, e `registros` é uma variável local. Injetei falhas com dublês na 3ª chamada ao LLM, em 12 perguntas: output_parsed=None → `ValidationError` (RespostaLLM2Polos.model_validate(None)); eixo 'econômico' → `ValueError('O LLM deve retornar exatamente os eixos encaminhados.')`; `TimeoutError` → propagado. Nos três casos, as 3 chamadas ao JEV já feitas foram perdidas e a função não retornou nada. Os SDKs só repetem erros HTTP transitórios: o typesafe-sdk RetryPolicy faz 2 novas tentativas para 408/429/5xx, com timeout de 10 s por operação;
- **Impacto:** Uma única resposta malformada no 70º item (ou no 84º chunk) faz perder o benchmark ou o documento inteiro e o custo de API já gasto. Reexecutar gera inferências novas e não idênticas, o que dificulta reproduzir os números já obtidos.
- **Recomendação (ajustada):** A ideia está correta (try/except por item, JSONL incremental, retomada, nenhuma falha vira 'irrelevante'), mas o código sugerido precisa de três ajustes. (1) A nova tentativa refaz `pipeline.classificar` inteiro e, portanto, uma nova inferência do JEV, o que muda a decisão inicial daquele item. Repita só a etapa do LLM, guardando a resposta do JEV já obtida. (2) A chave do benchmark é só `p.id`. Inclua nela o hash da configuração, das rubricas e do modelo para não reaproveitar resultados de uma configuração antiga. (3) A concorrência é opcional e muda o significado das latências medidas (ver COD-14). Comece com concorrência 1.

### COD-05 · Média · Correção · Parcial (corrigido na verificação)
**requirements.txt não instala: arquivo em UTF-16 com pacotes torch +cu132 e sem separar as dependências do notebook**

- **Onde:** requirements.txt; CELL 2 (%pip sem versões); .env.example; CELL 24 (carregar_credenciais)
- **Enunciado corrigido:** `pip install -r requirements.txt` falha porque o freeze inclui torch/torchvision com rótulo local +cu132, que não existe no PyPI. O arquivo também está em UTF-16, o que o pip lê, mas o git trata como binário (sem diffs). Ele mistura 132 pacotes do projeto inteiro, enquanto a CELL 2 instala versões não fixadas.
- **Impacto:** O ambiente não pode ser recriado com um comando. A CELL 2 instala versões mais novas que as usadas nos resultados. Mudanças de dependências não aparecem em diffs nem em revisão.
- **Recomendação (ajustada):** Manter o requirements-pipeline.txt em UTF-8 com as dependências diretas fixadas e usá-lo na CELL 2. Se quiser manter o lock completo, retire torch/torchvision dele ou documente o --index-url do PyTorch.

### COD-06 · Média · Melhoria · Parcial (corrigido na verificação)
**Versões dos modelos não são fixadas e o LLM roda sem parâmetros de amostragem definidos**

- **Onde:** CELL 24 (AsyncTypeSafeClient), CELL 17 (MaritacaClient.generate), CELL 22 (registro de 'modelo')
- **Enunciado corrigido:** O cliente JEV usa o alias padrão 'jev-latest' (o modelo servido é registrado em cada decisão). O LLM é chamado sem temperature, e seu modelo efetivo, id e usage não são registrados. Assim, uma troca de versão entre execuções não é detectada automaticamente.
- **Impacto:** Uma mudança de versão do JEV ou do Sabiá entre execuções altera os resultados sem deixar rastro. A amostragem não determinística do LLM contribui para a variabilidade observada em COD-01.
- **Recomendação (ajustada):** Rodar `await jev_client.models.list()` e, se existir um nome não-alias, fixá-lo em `model=`. Caso contrário, registrar `response.model` por execução e interromper se ele mudar entre execuções comparadas. Testar `temperature=0` numa chamada isolada antes de adotá-lo e registrar `response.model`, `response.id` e `usage` do LLM. A mudança na assinatura de generate exige ajustar classificar(), como já indicado.

### COD-07 · Média · Correção · Confirmado
**A verificação de evidência aceita citações triviais e recusa citações corretas que atravessam marcação Markdown ou escapes do JSON**

- **Onde:** CELL 20 (_score_evidencia_confere, _score_normalizar_citacao); CELL 22 (prompt com json.dumps); CELL 37 e 41 (sem contagem de evidência não verificada)
- **Evidência:** Testei com os 84 chunks reais do md (candidato 'Lula (PT)'). Falsos positivos: as citações 'a', 'de' e 'Brasil' são aceitas ('brasil' aparece em 68 dos 84 chunks). Falsos negativos, todos reprovados: título seguido do início do parágrafo sem a marcação '## **…**' (17 de 17 casos); reticências no início ('...atual gestão, o PPA…') ou no fim ('…'); aspas seguidas de ponto ('"…".'); hífen com espaços inserido; quebra de linha copiada da serialização JSON do prompt (os caracteres literais '\n\n'). A suspeita sobre o negrito se confirma só em parte: no md, '**' envolve linhas inteiras (só 1 linha de prosa tem negrito), então a citação sem asteriscos passa quando não cruza fronteiras de marcação.
- **Impacto:** A salvaguarda descrita na CELL 18 dá falsa garantia: uma palavra solta 'verifica' qualquer decisão. Ao mesmo tempo, decisões corretas do LLM podem virar abstenção quando a citação cruza marcação. Sem a contagem no documento, não se sabe quantos eixos foram afetados.
- **Recomendação (ajustada):** Acrescentar às mudanças sugeridas: (1) alterar o prompt para exigir o mesmo tamanho mínimo (por exemplo, 'uma oração completa, com pelo menos 4 palavras'). Sem isso, a nova regra transforma citações curtas, mas legítimas, em abstenções e altera a cobertura sem aviso. (2) Contar no documento os status por eixo (evidencia_nao_verificada, posicao_indeterminada). (3) Com os registros gravados (COD-04), reavaliar as evidências antigas com a regra nova e informar quantas decisões mudariam.

### COD-09 · Média · Melhoria · Confirmado
**O limiar de margem do Score é redundante e o 'score' é P(polo A); a média do documento mistura essa probabilidade com o 0/100 do LLM**

- **Onde:** CELL 5 (CONFIG_JEV_LLM_2_POLOS), CELL 20 (_normalizar_polaridade_score_2_polos), CELL 22 (_motivos), CELL 37 (média)
- **Evidência:** Em typesafe_sdk/_schemas/models.py, ScoreAnswer.score é descrito como 'Expected score: the probability-weighted average of the rubric levels'. Com os critérios [polo B, polo A] (níveis 0 e 1), score = P(nível 1) = P(polo A), e a margem do Score é |2·score − 1|. Nas 10 linhas visíveis da saída da CELL 41, os pares confiança/margem são: 0,30/0,30; 0,84/0,84; 0,64/0,64; 0,24/0,24; 0,99/0,98 (score 99); 1,00/1,00; 0,97/0,98; 0,97/0,98 (score 1); 0,22/0,22 (score 61); 0,96/0,96 (score 98). Logo `margem_score < 0,20` (P(A) entre 0,40 e 0,60) implica `confidence < 0,70`: o motivo 'baixa_margem_score' nunca é o único gatilho e margem_score_minima não tem efeito.
- **Impacto:** A configuração aparenta ter dois critérios independentes, e a análise de sensibilidade de um deles não mostraria efeito. O nome 'score' sugere intensidade. A média do documento mistura duas escalas sem informar a composição por método.
- **Recomendação (ajustada):** A recomendação é adequada. Acrescentar que, com os limiares atuais, todo score do JEV que permanece está em [0,15] ou [85,100] (ver COD-V01). Por isso, renomear para p_polo_a e informar a composição por método são passos necessários para interpretar o índice.

### COD-13 · Média · Melhoria · Confirmado
**A segmentação herda quebras de página do PDF no meio da frase e inclui capa e sumário como chunks**

- **Onde:** CELL 36 (dividir_texto_em_chunks_tokens), CELL 39 (separar_em_chunks), CELL 37 (cobertura)
- **Evidência:** Reproduzi a segmentação: 84 chunks de 26 a 592 tokens. 6 chunks começam no meio de uma frase, por exemplo chunk 79 → 80: '…o Brasil deve reafirmar sua soberania e preservar sua' | 'capacidade de fazer escolhas políticas e econômicas…'. A causa não é o tamanho: o parágrafo tem 79 tokens. O md traz 'preservar sua \n\n\n\n\n\ncapacidade', uma quebra de página virou separador de parágrafo. Há 43 ocorrências desse padrão. O chunk 1 (26 tokens) é a capa com '# Índice', e o chunk 2 é o sumário em tabela Markdown (54 '|'); ambos entram no denominador da cobertura com o mesmo peso dos outros. Com o pré-processamento abaixo, a segmentação gera 85 chunks e nenhum começa no meio de frase (testado).
- **Impacto:** Proposições divididas entre dois chunks podem ser avaliadas pela metade por eixo. Trechos não substantivos reduzem a cobertura e aumentam o número de chamadas.
- **Recomendação (ajustada):** Corrigir o texto do achado: são 43 quebras no meio de frase, das quais 19 vêm de páginas e 24 são quebras duplas de linha. O filtro `count('|') > 20` só atinge o chunk 2 neste documento. Em outros planos, conferir se alguma tabela substantiva seria excluída. Aplicar as mesmas regras a todos os documentos comparados e registrar o que for descartado.

### COD-20 · Média · Nova ideia · Confirmado
**Teste-reteste: medir a estabilidade do pipeline entre execuções antes de comparar planos ou eixos**

- **Onde:** Nova seção depois da CELL 39 (usa processar_documento_com_jev_2_polos / classificar)
- **Evidência:** As duas execuções do mesmo documento visíveis no notebook (gráfico da CELL 44 × tabela da CELL 39) diferem em até 5,4 pontos no valor A (diplomatic: 32,8 × 27,4; state: 81,7 × 77,9; economic: 91,0 × 93,4). Não há nenhuma medida de estabilidade do pipeline. O arquivo tcc/teste_estabilidade.json tem 133 bytes, JSON inválido e é de outro experimento (gemini_flash_lite).
- **Impacto:** Sem estimar a variabilidade entre execuções, não se sabe se as diferenças entre eixos, ou entre planos se o método for aplicado aos 12 documentos, superam o ruído do próprio instrumento. É uma questão de validade, independente de qual candidato seja analisado.
- **Recomendação (ajustada):** Além do teste-reteste com k = 3 a 5 execuções sem cache, informar um intervalo bootstrap por chunks para cada eixo (incerteza amostral, diferente da variabilidade entre execuções). Aplicar exatamente o mesmo protocolo a todos os documentos comparados.

### COD-08 · Baixa · Correção · Confirmado
**As margens médias da cascata ficam infladas porque os casos encaminhados saem do cálculo, e a margem de polaridade inclui casos não avaliados**

- **Onde:** CELL 27 (recalcula margem_media_* da cascata); CELL 26 (executar_benchmark_8values, 'margem polaridade')
- **Evidência:** CELL 27: `detalhes.loc[detalhes['LLM ativado no eixo'], ['margem relevância','margem polaridade']] = nan`, seguido do recálculo das médias. As linhas não encaminhadas da cascata têm exatamente as margens do JEV, então a média da cascata é a média do JEV sem os casos de margem baixa, que são justamente os encaminhados. Saídas salvas (cascata × JEV) de margem_media_relevancia: 0,9412 × 0,9280 (diplomatic), 0,9424 × 0,9389 (economic), 0,7481 × 0,6517 (society), 0,8656 × 0,7803 (state). A cascata fica sempre maior, por seleção. A sobrescrita é redundante, porque calcular_margem({'A': nan, 'B': nan}) já devolve NaN. Na CELL 26, 'margem polaridade' é calculada para as 70 linhas de cada eixo.
- **Impacto:** As tabelas de resumo sugerem que a cascata aumenta a margem ou certeza, mas isso é um artefato de seleção. A margem de polaridade mistura casos irrelevantes e não é comparável entre eixos.
- **Recomendação (ajustada):** Retirar as colunas de margem do resumo da cascata ou rotulá-las como 'margem JEV dos casos não encaminhados'. Calcular a margem de polaridade só quando a polaridade é avaliada e a classe prevista é A ou B.

### COD-10 · Baixa · Correção · Confirmado
**O Markdown descreve um notebook autocontido que não existe, e os hashes de origem nunca são verificados (o das perguntas depende do fim de linha)**

- **Onde:** CELLs 0, 6 e 33 (texto); CELLs 9, 10 e 34 (leitura de arquivos); metadata.origem
- **Evidência:** CELL 0: 'Todo o código, as 70 perguntas do 8Values e o documento de exemplo estão incorporados. Não é necessário…'. CELL 6: 'As perguntas abaixo foram incorporadas de tcc/questions.json'. CELL 33: 'foi incorporado abaixo… Nenhum carregamento externo é necessário'. Na prática, a CELL 9 lê './tcc/questions.json', a CELL 10 lê './tcc/textos_candidatos.json' (3,5 MB) e a CELL 34 usa plano_lula['md'], sempre com caminhos relativos ao diretório de trabalho. metadata.origem guarda três sha256 que o código nunca confere. Recalculei os três: documento_texto_sha256 = sha256 do md em UTF-8 (confere).
- **Impacto:** O texto induz o leitor a pensar que o notebook roda sozinho. A integridade dos insumos é declarada mas não checada. No Windows com autocrlf, uma verificação ingênua por bytes falharia, e abrir o notebook a partir de outro diretório causa FileNotFoundError.
- **Recomendação (ajustada):** Corrigir os textos e verificar os hashes ao carregar, normalizando o fim de linha, como sugerido.

### COD-11 · Baixa · Melhoria · Confirmado
**O schema de saída do LLM aceita qualquer nome de eixo, e a recusa (output_parsed=None) não é tratada**

- **Onde:** CELL 19 (EixoLLM2Polos.eixo), CELL 17 (MaritacaClient.generate), CELL 22 (checagem do conjunto de eixos)
- **Evidência:** CELL 19 declara `eixo: str` sem restrição, e a CELL 22 levanta ValueError se os nomes não baterem exatamente; reproduzi isso com 'econômico'. `response.output_parsed` (CELL 17) pode ser None em caso de recusa ou sem parse, e vira uma ValidationError genérica em `RespostaLLM2Polos.model_validate(None)`. Se faltar um eixo, a execução inteira é abortada em vez de manter a decisão do JEV.
- **Impacto:** Desvios triviais do modelo abortam toda a execução (ver COD-03), quando poderiam ser impedidos pelo próprio schema da saída estruturada.
- **Recomendação (ajustada):** Usar Literal nos quatro eixos e tratar None. Quando faltar um eixo, escolher e documentar uma política: manter a decisão do JEV com status próprio ou abster-se. Contar esses casos no resumo.

### COD-12 · Baixa · Melhoria · Parcial (corrigido na verificação)
**O fallback substitui também uma relevância que o JEV decidiu com margem alta, mesmo quando o motivo do encaminhamento é só a polaridade**

- **Onde:** CELL 22 (CascataJevLLM2Polos.classificar: prompt e montagem de finais[item.eixo])
- **Enunciado corrigido:** Em eixos encaminhados só por incerteza de polaridade, o LLM também pode alterar a relevância decidida pelo JEV com margem alta, e a cascata não registra quando isso acontece. O tamanho desse efeito nos resultados não é conhecido.
- **Impacto:** O fallback pode alterar decisões que não eram incertas. Assim, os números 'corrigidos/piorados' (11/2) misturam o efeito pretendido do encaminhamento com mudanças fora do seu escopo.
- **Recomendação (ajustada):** Primeiro medir: contar, por motivo de encaminhamento, quantos eixos tiveram a relevância invertida pelo LLM. Se houver casos, rodar a variante 'apenas_nivel' como ablação e comparar, em vez de mudar o desenho principal sem evidência.

### COD-14 · Baixa · Melhoria · Parcial (corrigido na verificação)
**Execução sequencial com pausas fixas, sem cache, e clientes nunca fechados**

- **Onde:** CELL 27 e CELL 37 (laços com asyncio.sleep), CELL 24 (clientes)
- **Enunciado corrigido:** As chamadas são sequenciais e sem cache: cada reexecução repete todas as inferências pagas e gera resultados novos. O custo de tempo atual é modesto (cerca de 2 min no benchmark).
- **Impacto:** Iterações lentas e caras desestimulam a execução limpa completa (COD-01) e o teste-reteste (COD-20). Sem cache, cada reexecução gera inferências novas e muda os números.
- **Recomendação (ajustada):** Priorizar o cache por hash (texto + configuração + rubricas + modelo) para reanálises. Deixar a concorrência como opção desligada por padrão e, se usada, informar que as latências medidas não são comparáveis às da execução sequencial.

### COD-15 · Baixa · Melhoria · Confirmado
**Código morto e duplicado: textos 'a'/'b' de AXIS_SPECS, _score_classe, modo unitário do avaliador e mapas de polos repetidos**

- **Onde:** CELL 13 (AXIS_SPECS, criar_questoes_eixo), CELL 15 (MAPA_SCORE_CASCATA), CELL 20 (_score_classe), CELL 7 (Effect.to_list), CELL 26 (modo unitário), CELLs 29/32, CELL 22 (default de tipo_relevancia)
- **Evidência:** AXIS_SPECS[*]['a'] e ['b'] só alimentam o dicionário `polaridade` de criar_questoes_eixo, que é descartado nas duas chamadas (`relevancia, _ = criar_questoes_eixo(...)` nas CELLs 20 e 22). Os polos realmente enviados vêm de TEXTOS_EIXOS_2. Pela contagem por AST, `_score_classe` e `Effect.to_list` têm 0 usos. O modo unitário de executar_benchmark_8values (`classificar_pergunta`, `time.sleep` bloqueante, `exigir_70_perguntas`, docstring que cita 'Laya') nunca é usado. MAPA_SCORE_CASCATA repete POLOS_EIXOS_2 em ordem invertida (A, B). `registros_pipeline_score` é atribuído nas CELLs 29 e 32 e nunca lido.
- **Impacto:** O leitor (ou a banca) pode supor que as descrições 'a'/'b' de AXIS_SPECS definem os polos avaliados, o que não é verdade. As duplicações podem ficar inconsistentes em edições futuras.
- **Recomendação:** Remover o código morto, derivar MAPA_SCORE_CASCATA de POLOS_EIXOS_2 e alinhar os defaults. O texto de relevância não muda; é o mesmo do bloco original.

### COD-16 · Baixa · Correção · Confirmado
**A coluna de acerto de polaridade tem dtype object, por isso o arredondamento não é aplicado e a média depende de comportamento frágil do pandas**

- **Onde:** CELL 26 (executar_benchmark_8values: 'acerto polaridade avaliada'), CELL 31 (round)
- **Evidência:** `'acerto polaridade avaliada': polaridade_correta if polaridade_avaliada else pd.NA` gera uma coluna object com bool e NA. Reproduzi com pandas 3.0.6: o dtype da coluna em detalhes e o de resumo['acuracia_polaridade'] são object. Por isso o `.round(4)` da CELL 31 não arredonda essa coluna: a saída salva mostra 0.541667 e 0.681818, enquanto as demais têm 4 casas.
- **Impacto:** Médias sobre dtype object podem mudar ou quebrar em versões futuras do pandas, e a apresentação fica inconsistente.
- **Recomendação:** Usar float com NaN, ou o dtype 'boolean'.

### COD-17 · Baixa · Correção · Confirmado
**rotulo_8values devolve 'Laissez-Faire' para NaN em vez de rótulo vazio**

- **Onde:** CELL 43 (rotulo_8values)
- **Evidência:** Os limiares (>90, >75, >60, ≥40, ≥25, ≥10) e a ordem dos arrays coincidem com set_label do TCC.ipynb (célula 25) e com o 8Values. Mas `rotulo_8values(float('nan'), ECON_ARRAY)` retorna 'Laissez-Faire' (testado): toda comparação com NaN é falsa, e a função cai em labels[6]. Na regra original em JavaScript, a última condição é `val >= 0`, também falsa para NaN, e o resultado é string vazia.
- **Impacto:** Hoje o impacto é baixo, porque None é tratado antes. Mas um NaN vindo da agregação produziria um rótulo extremo em vez de vazio.
- **Recomendação:** Rejeitar valores não finitos.

### COD-18 · Baixa · Melhoria · Confirmado
**grafico_scores_documento altera o resultado, usa uma variável global para o título e não mostra cobertura nem n**

- **Onde:** CELL 44 (grafico_scores_documento)
- **Evidência:** A função grava `documento['labels'] = rotulos` dentro da plotagem (efeito colateral). O título usa a global DOCUMENTO_NOME em vez de documento['documento']['nome'], que já existe. Patch é importado dentro da função, as barras recebem label e depois a legenda é sobrescrita, e a figura não é salva. A barra do polo B é sempre 100 − A, uma informação redundante, enquanto a cobertura e o n, que a CELL 35 diz acompanharem o índice, não aparecem (por exemplo, state tem cobertura de 0,29).
- **Impacto:** Ao reutilizar a função, o título pode trazer o nome de outro documento. Quem lê o gráfico não vê que alguns índices se baseiam em poucos chunks.
- **Recomendação (ajustada):** Além das mudanças sugeridas, o gráfico imprime rótulos ideológicos do 8Values sobre um documento real, calculados sobre um índice que é praticamente uma proporção (COD-V01). Por neutralidade e validade, remova esses rótulos ou mostre-os apenas quando o intervalo de confiança do índice ficar dentro de uma única faixa, com nota explícita de que são ilustrativos.

### COD-19 · Baixa · Nova ideia · Confirmado
**Testes automatizados offline com dublês de JEV e LLM, extraindo o pipeline para um módulo**

- **Onde:** CELLs 7–44 (código hoje só dentro do notebook); analise_jev_llm/ (já tem pipeline_score.py e testes do pipeline antigo)
- **Evidência:** Este notebook não tem testes; analise_jev_llm/test_pipeline_score.py cobre o pipeline antigo. Com dublês simples (um FakeJEV que devolve dicionários no formato de SystemOneResponse.answers e um FakeLLM que devolve RespostaLLM2Polos), executei a cascata e o benchmark completos sem rede e reproduzi os defeitos de COD-03, COD-07, COD-08 e COD-16 em segundos.
- **Impacto:** Mudanças de código, como as que provavelmente geraram as execuções divergentes de COD-01, passam sem ser detectadas. Com testes, as correções podem ser validadas sem gastar API.
- **Recomendação (ajustada):** Alinhar os testes à política escolhida para falhas: ou classificar() levanta uma exceção explícita, e o teste usa pytest.raises, ou devolve um status 'llm_falhou' sem usar a decisão. Incluir um teste de invariante: com os limiares atuais, todo score_8values do JEV mantido fica em [0,15] ou [85,100].

## Benchmark 8Values: metodologia e estatística (BEN)

### BEN-01 · Alta · Correção · Confirmado
**'Acurácia de polaridade' mistura erro de relevância com erro de direção e não é a métrica do bloco original**

- **Onde:** CELL 22 (CascataJevLLM2Polos._decisao_jev: classe = posicao['choice'] if relevante else 'C'); CELL 26 (executar_benchmark_8values: 'acerto polaridade avaliada'); CELL 25 (markdown)
- **Evidência:** Em _decisao_jev, um eixo previsto irrelevante recebe classe 'C' mesmo quando o Score nativo é direcional. Em executar_benchmark_8values, C conta como erro sempre que o efeito é diferente de 0. Exemplo na CELL 31, linha 0 (Q1, economic, efeito +10): relevância prevista B (P=0,29), Score {0:0,01, 1:0,99}, ou seja, direção certa, mas 'acerto polaridade avaliada'=False. No bloco original (TCC.ipynb, célula 308) a polaridade vinha do Score sem condicionar na relevância: o mesmo par aparece com acerto True e as acurácias eram dipl 0,875, econ 0,909, society 0,939, state 0,838 (103/116 = 88,8%, IC95% Wilson 81,8–93,3%). Aqui os valores são 0,583/0,591/0,818/0,378.
- **Impacto:** A leitura natural 'polaridade de state abaixo de 50%' atribui à direção um problema que é de detecção de relevância. A comparação com o bloco original fica inválida, e conclusões do TCC sobre a capacidade direcional do JEV ou do LLM ficam distorcidas.
- **Recomendação:** Renomear a coluna atual (ex.: 'acerto_relevancia_e_direcao_nos_relevantes') e reportar quatro métricas separadas. (a) Relevância: matriz 2×2, precisão, revocação, F1, acurácia balanceada, kappa. (b) Direção condicional a relevante esperado E previsto. (c) Direção pelo Score nativo, independente da relevância, que é comparável ao bloco original, mais AUROC de P(A). (d) Taxa de abstenção: relevância C do LLM e classe C entre os detectados. Corrigir a frase da CELL 25.

### BEN-02 · Alta · Melhoria · Confirmado
**A acurácia conjunta é dominada pelos 164 pares de efeito zero e é reportada sem baseline trivial nem métricas balanceadas**

- **Onde:** CELL 26 (resumo: acuracia_conjunta); CELL 32 (print 212/280 e 221/280)
- **Evidência:** Em questions.json, 164 dos 280 pares têm efeito 0 (econ 48, dipl 46, govt 33, scty 37), e um par de efeito 0 'passa' apenas por ser previsto irrelevante. Baseline 'tudo irrelevante': 164/280 = 58,6% no total; por eixo, econ 0,686, dipl 0,657, state 0,471, society 0,529, contra JEV 0,857/0,829/0,629/0,714 e cascata 0,900/0,814/0,671/0,771. Relevância derivada das contagens salvas, JEV: TP=76, FN=40, FP=20, TN=144; precisão 0,792, revocação 0,655, F1 0,717, especificidade 0,878, acurácia balanceada 0,767, kappa 0,547. Cascata: TP=78, FN=38, FP=13, TN=151; 0,857/0,672/0,754/0,921, acurácia balanceada 0,797, kappa 0,612.
- **Impacto:** 75,7%/78,9% parecem altos, mas descontam pouco do baseline de 58,6%. Um sistema que se abstém de declarar relevância é recompensado. O ranking entre eixos muda quando a métrica é balanceada.
- **Recomendação:** Reportar sempre, ao lado da acurácia conjunta: baseline 'tudo irrelevante' (global e por eixo), matriz de confusão de relevância por eixo, acurácia balanceada, kappa e MCC, e a direção condicional (BEN-01). Usar como métrica principal do TCC uma média macro por eixo da acurácia balanceada de relevância e da direção condicional, em vez da média sobre 280 pares.

### BEN-03 · Alta · Correção · Confirmado
**Hipótese confirmada: confidence = margem = |2p−1| e score = P(polo A); margem_score_minima é redundante e o 'score' mede direção, não intensidade**

- **Onde:** CELL 5 (CONFIG_JEV_LLM_2_POLOS); CELL 22 (_motivos); CELL 20 (_normalizar_polaridade_score_2_polos); consequência em CELLs 35/37/43
- **Evidência:** Nas 10 linhas visíveis da CELL 31, |confidence − |pA−pB|| é no máximo 0,01. Exemplos: 0,92 com {0,04; 0,96}; 0,18 com {0,41; 0,59}; 0,26 com {0,63; 0,37}; 0,62 com {0,19; 0,81}. Nas 10 da CELL 41, |confiança − margem| é no máximo 0,01 (0,30/0,30, 0,84/0,84, 0,99/0,98, 0,97/0,98, 0,22/0,22) e |margem − |2·score/100 − 1|| = 0,00 nas 4 linhas com score (99→0,98; 1→0,98; 61→0,22; 98→0,96). O bloco antigo mostra o mesmo (Q1 dipl: score 0,54, confiança 0,08). No SDK (typesafe_sdk/_schemas/models.py, ScoreAnswer.score) o score é descrito como 'the probability-weighted average of the rubric levels'; com níveis 0/1 isso dá exatamente P(nível 1) = P(polo A).
- **Impacto:** Os três parâmetros aparentes valem dois efetivos, e descrever 'confiança ≥ 0,70 e margem ≥ 0,20' como critérios independentes é enganoso. Como score_8values = 100·P(A), a média do documento (ex.: society 98,75, dp 1,75) mede a consistência da direção entre os chunks, não a intensidade.
- **Recomendação:** Documentar a identidade no notebook. Remover margem_score_minima ou declarar que ela só atua se for maior que confianca_score_minima. Parametrizar o roteamento diretamente como faixas de q e de P(A) e escolhê-las por simulação offline (BEN-09). No texto do TCC, chamar o valor de 'probabilidade média de direção A' e não usá-lo como intensidade sem validação própria.

### BEN-06 · Alta · Melhoria · Confirmado
**Sem teste de significância nem IC; os 280 pares não são independentes e o resultado de McNemar está no limite**

- **Onde:** CELL 32 (prints de 212/280, 221/280, 11 corrigidos, 2 piorados); CELL 27 (comparacao)
- **Evidência:** McNemar exato (binomial bicaudal) para b=11 e c=2: p=0,0225 (mid-p 0,0129). Com 13 pares discordantes, b ≥ 11 é o mínimo para p<0,05; com 10 vs 3, p=0,092, ou seja, a conclusão depende de um único par. Os pares estão agrupados por pergunta: a Q70 tem 4 FN, a Q1 tem 2 erros, e os 31 eixos encaminhados saíram de 26 chamadas. Teste do sinal por pergunta: p=0,0225 se as 11 correções estiverem em 11 perguntas distintas, 0,065 se em 9 e 0,109 se em 8. ICs 95% para a acurácia conjunta: JEV 75,7% com Wilson n=280 [70,4; 80,4] e com n efetivo 70 [65,7; 85,8]; cascata 78,9% com [73,8; 83,3] e [69,4; 88,5]. Polaridade de state 14/37: [24,1; 53,9]%.
- **Impacto:** Afirmar que 'a cascata melhora' com base em 221 vs 212 é estatisticamente frágil. Os ICs se sobrepõem amplamente, e diferenças por eixo de 1 a 3 pares são ruído.
- **Recomendação:** Reportar McNemar exato por par E o teste do sinal por pergunta (ganho líquido por pergunta). Calcular os ICs por bootstrap agrupado por pergunta (reamostrar as 70 perguntas com seus 4 eixos), inclusive para a diferença cascata − JEV. Tratar o p-valor como nominal, já que os limiares não foram pré-registrados (BEN-08).

### BEN-09 · Alta · Nova ideia · Confirmado
**Guardar em cache JEV e LLM em TODOS os eixos para simular qualquer limiar offline: Pareto custo × acurácia, LLM sozinho e oráculo**

- **Onde:** CELL 22 (CascataJevLLM2Polos.classificar); CELL 27
- **Evidência:** Hoje o LLM só responde os 31 eixos encaminhados (26 chamadas), então é impossível saber o que ele faria nos outros 249 pares. Sem isso não há baseline 'LLM sozinho' nem limite superior de roteamento, e cada nova combinação de limiares exige novas chamadas (não determinísticas, BEN-12). Custo medido na CELL 31: 70 chamadas JEV em 20,2 s; 26 chamadas LLM em 92,7 s (~3,6 s cada). Rodar o LLM nos 4 eixos das 70 perguntas custa cerca de 250 s.
- **Impacto:** Sem esses dados, não dá para demonstrar a tese central da cascata ('qualidade igual ou maior com menos chamadas que um LLM aplicado a tudo'), nem escolher limiares sem viés.
- **Recomendação:** Rodar uma vez o LLM em todos os eixos, com a mesma rubrica e prompt equivalente, e persistir o resultado (BEN-13). Simular offline a grade de limiares (faixa de q e de P(A)), traçar a fronteira de Pareto 'chamadas LLM × acurácia conjunta/balanceada' e comparar JEV sozinho, LLM sozinho, cascata e oráculo (acerta se JEV OU LLM acerta). Observação: o prompt com 4 eixos difere do prompt só com os eixos encaminhados; registrar isso como limitação.

### BEN-10 · Alta · Melhoria · Confirmado
**A cascata não alcança o erro dominante (falsos negativos de relevância); o ganho de +9 vem quase todo de pares de efeito zero**

- **Onde:** CELL 22 (_motivos: 'relevancia_ambigua' só com margem < 0,20; critérios de Score só se relevante)
- **Evidência:** Orçamento de erros derivado das contagens salvas. JEV: 68 erros = 40 FN de relevância + 20 FP + 8 de direção. Cascata: 59 = 38 FN (inclui abstenções) + 13 FP + 8 de direção. O saldo de +9 decompõe-se em TN 144→151 (+7, pares de efeito 0) e acertos entre relevantes 68→70 (+2). Por eixo: econ TN +1 e direção +2; state TN +2 e +1; society TN +4; dipl −1 na direção. Pela regra efetiva (BEN-03), um eixo previsto irrelevante só é encaminhado se q_rel ∈ (0,40; 0,50). Os FN visíveis têm q_rel 0,29 (Q1 econ) e 0,00/0,03/0,00/0,18 (Q70), e nenhum foi encaminhado.
- **Impacto:** Descrever a cascata como 'corrige a direção' seria incorreto: a direção entre detectados fica em 8 erros nos dois estágios. A cascata melhora principalmente a precisão de relevância (0,792→0,857), enquanto a revocação (0,655→0,672), maior fonte de erro, quase não muda.
- **Recomendação:** Reportar o orçamento de erros (FN, FP, direção) por estágio. Testar, por simulação offline (BEN-09), uma faixa assimétrica para relevância: encaminhar 'irrelevante' com q_rel ∈ [q_min; 0,5) e escolher q_min por validação cruzada. Examinar a distribuição de q_rel entre os FN: se muitos FN tiverem q≈0, o problema é de rubrica ou gabarito (BEN-04/05), não de roteamento.

### BEN-12 · Alta · Melhoria · Parcial (corrigido na verificação)
**Não determinismo do JEV e do LLM não medido; números de execuções diferentes estão sendo comparados**

- **Onde:** CELL 29 (execução única); CELL 17 (MaritacaClient.generate sem temperature/seed); comparação implícita com o TCC.ipynb
- **Enunciado corrigido:** A variabilidade entre execuções não é medida. O mesmo protocolo JEV variou 1 a 3 pares entre execuções (215 contra 212; 204 contra 205; relevância 221 contra 220), na mesma ordem do ganho da cascata (+9) e da folga do McNemar (1 par). Pelo menos uma 'correção' (Q2 economic) é um par que o JEV acertava antes. A comparação JEV contra cascata dentro do notebook é pareada. O risco está em generalizar uma execução única e em citar números do TCC.ipynb como se fossem a mesma medição.
- **Impacto:** A variação entre execuções (±1–3 pares no total) tem a mesma ordem do saldo da cascata (+9) e da diferença McNemar crítica (1 par, BEN-06). Comparar números de execuções diferentes atribui ao método uma variação que é ruído.
- **Recomendação (ajustada):** Repetir o JEV k ≥ 5 vezes (~20 s cada) e reportar média ± dp, pares instáveis e kappa de Fleiss (o código proposto é adequado). Fixar a versão do JEV com o parâmetro model= de system_one, usando o identificador devolvido em response.model, se a API aceitar. No MaritacaClient, passar temperature=0 em responses.parse se o endpoint aceitar e registrar response.model em vez do alias 'sabia-4'. Repetir o LLM nos eixos encaminhados. Ao citar o bloco original, usar 215/280.

### BEN-13 · Alta · Correção · Confirmado
**Registros do benchmark ficam só em memória: sem persistência, não dá para recalcular métricas sem novas chamadas**

- **Onde:** CELL 29 e CELL 32 (registros_pipeline_score); CELL 27 (retorno de executar_benchmark_jev_llm_2_polos)
- **Evidência:** Um grep no dump do notebook por to_csv, to_json, to_parquet, json.dump(, open(...'w'), pickle e savefig não encontrou nada. O retorno de executar_benchmark_jev_llm_2_polos tem registros, config e rubricas, mas nada é gravado. Além disso, a resposta bruta do JEV (response.model_dump()) não entra no registro, só os campos normalizados. Como as execuções não são determinísticas (BEN-12), cada nova análise (BEN-01 a BEN-11) exigiria nova inferência e daria números diferentes.
- **Impacto:** Os números 212/221 não podem ser auditados nem reanalisados. As tabelas do TCC não ficam ligadas a um artefato identificado (run_id).
- **Recomendação:** Ao final da CELL 29, gravar um JSONL por execução com manifesto (run_id, data, hash da config, versões dos modelos, rubricas e os sha256 já presentes na metadata) e uma linha por pergunta com o registro completo e a resposta bruta do JEV. Gerar todas as tabelas e gráficos a partir desse arquivo.

### BEN-16 · Alta · Nova ideia · Parcial (corrigido na verificação)
**Frases de ~16 tokens não validam chunks de ~530 tokens: usar tcc/d0_manual_validation_avaliado.csv como 2º conjunto (relevância)**

- **Onde:** CELLs 25–32 (benchmark só com QUESTIONS); CELLs 36–39 (aplicação a chunks de 600 tokens); arquivo não usado: tcc/d0_manual_validation_avaliado.csv
- **Enunciado corrigido:** O benchmark usa frases de cerca de 16 tokens, mas a aplicação usa chunks de cerca de 530 tokens. O tcc/d0_manual_validation_avaliado.csv (66 chunks com rótulos de relevância) não é usado. Ele vem de um único plano do próprio corpus (2026BR280002552484_01.pdf), segmentado em trechos de cerca de 95 tokens com prefixo de títulos. Serve como segundo conjunto de teste de relevância, mas é de um documento só e com granularidade diferente da aplicação.
- **Impacto:** O desempenho no 8Values (concordância com o instrumento, frases curtas e explícitas) não sustenta conclusões sobre a classificação de planos, que é o objetivo do TCC.
- **Recomendação (ajustada):** Usar o d0 como teste de relevância (código proposto), registrando a origem (arquivo e procedimento de segmentação) e a dependência de um único documento. Para validar na granularidade real e reduzir o viés de documento único, anotar com 2 anotadores (kappa) uma amostra estratificada dos chunks de 600 tokens produzidos pela própria CELL 36, com o mesmo número de chunks de cada um dos 12 planos. Assim a avaliação fica simétrica entre candidatos. Anotar também a direção nos positivos.

### BEN-04 · Média · Correção · Parcial (corrigido na verificação)
**Gabarito pelo sinal do efeito trata efeitos secundários e cargas cruzadas teóricas como posição defendida pelo texto**

- **Onde:** CELL 26 (esperado_pelo_efeito); CELL 6 (markdown); CELL 20 (instrução do Score: 'Considere somente posições efetivamente defendidas')
- **Enunciado corrigido:** O gabarito binário dá o mesmo peso a efeitos secundários (|e| igual a 5 ou 2; 23 de 116 pares relevantes) e a cargas cruzadas do modelo teórico do 8Values. O notebook não estratifica as métricas por esse critério. State concentra secundários (9) e primários empatados (15) entre seus 37 pares relevantes, o que pode explicar parte da baixa revocação. Essa hipótese precisa ser testada com os registros.
- **Impacto:** Parte dos 'erros' é desacordo legítimo entre a rubrica textual e o modelo teórico do 8Values. Isso pune sobretudo state, que concentra secundários e empates. O efeito pode explicar a baixa revocação de state (17/37) sem que exista falha do classificador.
- **Recomendação (ajustada):** Reclassificar como 'melhoria'. Estratificar as métricas (primário único, primário empatado, secundário) e reportar análises de sensibilidade sem secundários e sem Q69/Q70, além da acurácia ponderada por |efeito|, com o código proposto. Levar ao texto do TCC a frase da CELL 6 sobre o estimando ('concordância com a codificação do 8Values'), deixando claro que ela difere de 'posição defendida pelo texto'.

### BEN-05 · Média · Melhoria · Confirmado
**Efeito 0 não equivale a irrelevância semântica pela própria rubrica 'topic' de AXIS_SPECS**

- **Onde:** CELL 26 (esperado_pelo_efeito: efeito 0 → relevância 'B'); CELL 13 (AXIS_SPECS[...]['topic'])
- **Evidência:** Há pares com efeito 0 cujo texto cai num tema que a rubrica lista explicitamente. Q59 ('Se aceitarmos imigrantes...') tem dipl 0, e o topic de diplomatic inclui 'imigração'. Q6 (tarifas no comércio internacional) tem dipl 0, e o topic inclui 'relações entre países'. Q23 ('O gasto militar é um desperdício de dinheiro') tem econ 0, e o topic inclui 'política fiscal'. Q33 (suicídio assistido) tem scty 0, e o topic de society inclui 'moralidade'. Q30 ('valores de nossa nação') tem scty 0, e o topic inclui 'valores sociais e culturais'.
- **Impacto:** Parte dos 20 FP (13 na cascata) pode ser acerto semântico punido pelo gabarito. Como 7 das 11 correções da cascata foram FP→TN (BEN-10), o ganho medido depende dessa convenção.
- **Recomendação:** Adjudicar manualmente, com 2 anotadores, os pares FP e FN (60 no JEV) contra a definição de relevância da rubrica e calcular o kappa entre anotadores. Reportar as métricas contra os dois gabaritos: 8Values e semântico. Alternativa: restringir o topic de society para alinhá-lo ao construto do 8Values, declarando a mudança.

### BEN-07 · Média · Melhoria · Confirmado
**Poder estatístico insuficiente para comparações por eixo e para o ganho observado da cascata**

- **Onde:** CELL 31 (comparacao por eixo); CELL 26 (resumo por eixo)
- **Evidência:** Calculei o poder de McNemar (aproximação de Connor) com o efeito observado (p10=11/280, p01=2/280): 0,24 com n=70, 0,42 com 140 e 0,71 com 280 pares tratados como independentes. Para 80% são necessários 351 pares independentes, o que dá cerca de 88 perguntas com DEFF 1 e 176 com DEFF 2. Diferença mínima detectável entre duas proporções independentes (p≈0,75, α=0,05, poder 0,8): 37 pp com n=22 (econ relevantes), 35 pp com 24 (dipl), 30 pp com 33 (scty), 28 pp com 37 (state) e 20 pp com 70. As variações por eixo reportadas (dipl 0,583→0,542 = 1 par; econ 0,591→0,682 = 2 pares) estão muito abaixo disso.
- **Impacto:** Ordenações e conclusões por eixo ('o LLM piora diplomatic', 'melhora economic') não são sustentáveis com 70 perguntas.
- **Recomendação:** Restringir as conclusões inferenciais ao agregado, com IC por bootstrap. Apresentar os eixos como descritivos, com IC. Aumentar o conjunto de avaliação: itens negados ou invertidos (BEN-17) dobram para 140 perguntas, e o CSV d0 mais novas anotações de trechos (BEN-16) completam. Calcular o tamanho de amostra antes da coleta.

### BEN-08 · Média · Melhoria · Parcial (corrigido na verificação)
**Limiares herdados e avaliados no mesmo conjunto de 70 perguntas após dezenas de variantes (otimismo por seleção)**

- **Onde:** CELL 4 (markdown: 'parâmetros iniciais a selecionar na validação'); CELL 5 (CONFIG_JEV_LLM_2_POLOS); CELL 29
- **Enunciado corrigido:** Não há conjunto de validação separado. O desenho do pipeline foi iterado nas mesmas 70 perguntas que servem de teste, e os limiares que a CELL 4 promete 'selecionar na validação' só podem ser escolhidos nesse mesmo conjunto. A acurácia de 78,9% é, portanto, uma estimativa de desenvolvimento, não fora da amostra. O viés de seleção atual é moderado, porque os limiares 0,70/0,20 foram herdados sem ajuste nestes dados.
- **Impacto:** O 78,9% não é uma estimativa fora da amostra. Com muitas configurações testadas, escolher a melhor infla a acurácia esperada (garden of forking paths).
- **Recomendação (ajustada):** Congelar a configuração atual e registrar o hash dela. Tratar as 70 perguntas como conjunto de desenvolvimento. Avaliar a configuração final num conjunto independente: d0 mais trechos anotados de vários planos (ver BEN-16). Qualquer varredura futura de limiares deve reutilizar respostas em cache (BEN-09/BEN-13), nunca refazer a inferência para cada limiar. A validação cruzada agrupada por pergunta só é possível depois de obter o LLM em todos os eixos (BEN-09).

### BEN-11 · Média · Melhoria · Confirmado
**Desequilíbrio de polos em state misturado com cargas cruzadas; faltam análises que separem viés de polo de erro de relevância**

- **Onde:** CELL 26 (resumo por eixo); CELL 31
- **Evidência:** Em questions.json, state tem 24 pares do polo B (autoridade) e 13 do polo A (liberdade). No polo B: 7 primários únicos, 10 empatados e 7 secundários, ou seja, 17/24 (71%) com carga cruzada. No polo A: 6, 5 e 2 (7/13 = 54%). Os outros eixos: econ 13A/9B, dipl 12/12, scty 18/15. A revocação de relevância em state é 17/37 (46%). A direção nativa de state no bloco original foi 31/37 (83,8%), sem quebra por polo. Assim, a pior revocação em state pode vir do polo, do estrato ou de ambos, e o notebook não permite distinguir.
- **Impacto:** Sem análise por polo, um viés sistemático de um polo (ex.: P(A) alto por padrão) ficaria escondido pela acurácia média, o que é sensível para um TCC com exigência de neutralidade.
- **Recomendação:** Reportar por eixo × polo × estrato: revocação de relevância, acurácia de direção nativa, acurácia de direção balanceada por polo (média das duas) e AUROC de P(A) entre itens A e B. Calcular também o 'viés de P(A)' nos itens irrelevantes (média de P(A) − 0,5). Ajustar uma regressão logística acerto ~ polo + estrato + eixo com erros padrão agrupados por pergunta, ou a versão por bootstrap de BEN-06.

### BEN-14 · Média · Nova ideia · Confirmado
**Calibração das probabilidades de relevância e curvas risco × cobertura não são medidas, embora todos os dados existam**

- **Onde:** CELL 27 (coluna 'probabilidade relevância JEV'); CELL 22 (_motivos usa margens como se fossem confiáveis)
- **Evidência:** O roteamento supõe que margem baixa sinaliza erro, mas há erros com probabilidade extrema: na Q70, os 4 eixos são FN com q_rel 0,00/0,03/0,00/0,18 (CELL 31), e na Q1 econ o FN tem q_rel 0,29. Na CELL 31, margem_media_relevancia vai de 0,65 (society) a 0,94 (economic), mas não há Brier, ECE, diagrama de confiabilidade nem curva risco × cobertura que liguem margem a acerto.
- **Impacto:** Sem calibração, não há justificativa empírica para os limiares, e não dá para saber se 'baixa confiança' concentra os erros (pré-condição para a cascata funcionar).
- **Recomendação:** Calcular Brier e ECE por eixo de P(relevante) contra o gabarito 8Values e, em separado, contra o d0 (BEN-16). Traçar o diagrama de confiabilidade e a curva risco × cobertura (o JEV decide só nos pares de maior margem). Se a calibração for ruim, considerar recalibração isotônica ou de Platt ajustada em validação cruzada agrupada.

### BEN-17 · Média · Nova ideia · Confirmado
**Testes de simetria para neutralidade: inverter a ordem dos critérios e criar versões negadas dos 70 itens**

- **Onde:** CELL 20 (criar_perguntas_jev_2_polos: criteria=[texto_polo_b, texto_polo_a]); CELL 22 (prompt do LLM: nivel=0 → polo B)
- **Evidência:** A ordem é sempre [polo B, polo A] no Score e no prompt do LLM ('nivel=0 corresponde ao primeiro critério (polo B)'). Nada no notebook testa se a posição na lista influencia P(A), um viés de posição conhecido em LLMs. Os polos também têm extensões ligeiramente diferentes em TEXTOS_EIXOS_2 (economic: 8 frases em equality contra 9 em wealth; diplomatic: 8 em might contra 9 em peace). O benchmark mede a direção só contra a distribuição de polos do 8Values (ex.: 24B/13A em state).
- **Impacto:** Sem esses testes, não é possível afirmar que o instrumento é simétrico entre polos, um requisito explícito de neutralidade do TCC.
- **Recomendação:** (i) Inversão de ordem: rodar o JEV com criteria=[A, B] e comparar P(A) com 1 − score invertido; fazer o mesmo no LLM trocando o mapeamento de nivel. Repetir k vezes nas duas ordens para separar o efeito de ordem do não determinismo (BEN-12). (ii) Contrafactual por negação: redigir à mão, com revisão de 2 pessoas, a versão oposta de cada item (ex.: Q3 'Quanto mais livres os mercados, menos livres as pessoas'). Esperado: mesma relevância e direção invertida. Medir a taxa de consistência por eixo e por polo. Isso também dobra o conjunto para 140 itens. (iii) Equalizar o número de frases por polo ou testar a sensibilidade a isso.

### BEN-18 · Média · Melhoria · Confirmado
**Falta a análise condicional dos eixos encaminhados (por motivo) e da cobertura das citações**

- **Onde:** CELL 27 (comparacao); CELL 32 (ativacoes_llm)
- **Evidência:** Só há totais: 31 eixos encaminhados (dipl 2, econ 4, society 16, state 9), 11 corrigidos e 2 piorados. Isso implica 18 sem mudança: taxa de correção 11/31 = 35,5% e de piora 2/31 = 6,5%. Não se sabe a acurácia do JEV e do LLM no subconjunto encaminhado, nem a quebra por motivo (relevancia_ambigua vs baixa_confianca_score) ou por relevância esperada. A evidência do LLM costuma ser a frase inteira (CELL 31, linha 4, Q2), então a verificação literal não discrimina nada no benchmark.
- **Impacto:** Não dá para saber em qual tipo de encaminhamento o LLM agrega valor, nem justificar a manutenção de cada motivo.
- **Recomendação:** Reportar, nos pares encaminhados: acurácia do JEV contra a do LLM (pareada), corrigidos e piorados por motivo e por relevância esperada, taxa de abstenção do LLM e cobertura da citação (tamanho da citação / tamanho do texto). Não generalizar essa acurácia condicional para o LLM em todo o corpus.

### BEN-V01 · Média · Melhoria · Acrescentado na verificação
**Empates exatos P(A)=0,50 com granularidade de 0,01 contam como erro de direção do JEV e entram nos 'pares corrigidos' da cascata**

- **Onde:** CELL 20 (_normalizar_polaridade_score_2_polos: choice='C' se prob_a == prob_b); CELL 22 (_motivos: 'empate_polaridade'); CELL 27/32 (fallback corrigiu)
- **Evidência:** Todas as probabilidades exibidas com round(4) nas CELLs 31 e 41 têm no máximo 2 casas (0,01/0,99; 0,41/0,59; 0,5/0,5; scores 99, 61, 1), o que indica granularidade de 0,01 na API. Por isso, P(A)=0,50 exato é um resultado discreto e frequente, não um evento de medida nula. Das 10 linhas visíveis da CELL 31, 2 são empates exatos. Q1 diplomatic tem {0,5; 0,5}, mas era {0,46; 0,54} no TCC.ipynb, célula 308. Q2 economic tem {0,5; 0,5}, confiança 0,00, motivos 'empate_polaridade; baixa_confianca_score; baixa_margem_score' e 'fallback corrigiu'=True. No TCC.ipynb, célula 308, o mesmo par saiu {0,49; 0,51} → A, com passou=True.
- **Impacto:** A linha de base JEV inicial é penalizada por uma regra de abstenção aplicada a um valor discreto, e parte do ganho da cascata pode ser só resolução de empates. Esse ganho não demonstra capacidade do LLM, e um desempate barato (nova chamada ao JEV) poderia obtê-lo.
- **Recomendação:** Reportar o número de empates exatos por eixo (total e entre previstos relevantes) e quantas correções e pioras da cascata vieram de 'empate_polaridade'. Reportar o JEV inicial de duas formas: com empate como abstenção, informando a cobertura, e numa análise de sensibilidade que desempata com uma segunda chamada ao JEV. Comparar essa linha de base de custo baixo com a cascata nos mesmos pares.

### BEN-15 · Baixa · Correção · Confirmado
**Margens médias da cascata calculadas só nos pares não encaminhados (viés de seleção)**

- **Onde:** CELL 27 (detalhes.loc[LLM ativado, ['margem relevância','margem polaridade']] = NaN e recálculo de margem_media_*)
- **Evidência:** Os eixos encaminhados, que por construção têm margem baixa, viram NaN e saem da média. Em society, margem_media_relevancia é 0,7481 na cascata (54 pares) e 0,6517 no JEV (70 pares); isso implica média de cerca de 0,33 nos 16 encaminhados (0,6517·70 = 0,7481·54 + m·16). O resumo sugere que a cascata está 'mais segura', mas o efeito é só a remoção dos casos difíceis. Também margem_media_polaridade do JEV inclui os pares previstos irrelevantes, cujo Score não é usado.
- **Impacto:** A tabela induz uma interpretação errada de aumento de certeza. Efeito pequeno nas conclusões, mas fácil de citar por engano.
- **Recomendação:** Remover margem_media_* do resumo da cascata ou reportá-las sempre do JEV, sobre o mesmo conjunto de pares e com n explícito. Calcular a margem de polaridade só entre os pares previstos relevantes.

### BEN-19 · Baixa · Melhoria · Confirmado
**Execução piloto com LIMITE_PERGUNTAS pega as N primeiras perguntas, todas de economia**

- **Onde:** CELL 29 (perguntas_benchmark = QUESTIONS[:LIMITE_PERGUNTAS]); CELL 5
- **Evidência:** As perguntas 1–15 têm econ ≠ 0 e quase todas dipl = govt = 0 (questions.json). Com LIMITE_PERGUNTAS=3, o piloto cobre só economia (Q1–Q3) e não exercita os outros eixos, os polos nem o roteamento típico de society e state (16 e 9 dos 31 encaminhamentos).
- **Impacto:** Pilotos pouco representativos podem esconder falhas (ex.: abstenções ou evidência não verificada em outros eixos) antes da execução completa.
- **Recomendação:** Usar amostra estratificada pelo eixo primário, com semente fixa, e registrar os IDs sorteados.

## Aplicação a documentos: segmentação, agregação e incerteza (DOC)

### DOC-01 · Alta · Correção · Parcial (corrigido na verificação)
**Rótulos ideológicos do quiz 8Values aplicados a um índice documental de outra natureza e com incerteza que cobre várias faixas**

- **Onde:** CELL 43 (rotulo_8values), CELL 44 (grafico_scores_documento), CELL 42 (markdown)
- **Enunciado corrigido:** A CELL 44 aplica os rótulos do quiz 8Values a um índice documental de outra natureza: proporção de votos direcionais entre trechos relevantes, sem níveis de intensidade nem respostas neutras. Com IC de Wilson aproximado, o rótulo é indeterminado em 3 dos 4 eixos (economic 2 faixas, diplomatic 3, state 3). A sensibilidade que trata a irrelevância como neutralidade (50+(m−50)·n/84) muda a faixa em 3 eixos. Essa convenção, porém, não é a do quiz: no quiz, perguntas de efeito 0 ficam fora do denominador. O análogo do quiz não muda nada nesta execução, porque não há trechos relevantes sem posição.
- **Impacto:** O rótulo é indeterminado em 3 dos 4 eixos e depende de uma convenção arbitrária. Apresentar 'plano X = rótulo Y' seria uma conclusão inválida e um risco direto à exigência de neutralidade do TCC. O texto da CELL 42 já ressalva que os rótulos 'não substituem validação', mas a figura os mostra como manchete.
- **Recomendação (ajustada):** Manter a recomendação: não exibir rótulos ideológicos para documentos e usar descrição neutra com n e IC. No TCC, justificar a incomparabilidade de escalas por dois motivos: - a ausência de níveis de intensidade e de respostas neutras no documento; - a incerteza amostral. Não usar a convenção 'n/84' como se fosse a do quiz. Se quiser uma sensibilidade, rotulá-la como 'irrelevância tratada como neutralidade'.

### DOC-03 · Alta · Correção · Confirmado
**Saídas salvas das seções 10–11 vêm de execuções diferentes (tabela ≠ gráfico) e a célula de agregação foi editada após rodar**

- **Onde:** CELL 37 (execution_count None), CELL 39 (exec 60), CELL 41 (exec 23), CELL 44 (exec 25); também CELLs 26–32 (exec 14–18) contra definições 2–24 (exec 41–56)
- **Enunciado corrigido:** As saídas salvas das seções 10–11 vêm de execuções diferentes da análise do documento. A CELL 39 (exec 60) mostra 93,4 / 27,4 / 77,9 / 98,75. A CELL 41 (exec 23) e a figura da CELL 44 (exec 25) correspondem a uma execução anterior: 91,0 / 32,8 / 81,7 / 98,7 e 46 chamadas ao LLM. CELL 37 e CELL 43 não têm execution_count, então o código salvo não comprova que gerou essas saídas.
- **Impacto:** Números reportados no TCC podem misturar execuções. Não é possível reproduzir a figura a partir da tabela. Além disso, a variabilidade entre execuções (LLM ou JEV) existe e não está quantificada.
- **Recomendação:** 1. Usar 'Restart & Run All' antes de salvar o .ipynb. 2. Persistir resultado_documento completo (registros por chunk) com sha256 do texto, configuração, timestamp e versões. 3. Gerar a tabela e o gráfico do mesmo objeto salvo, com run_id no título. 4. Quantificar o teste–reteste em pelo menos 3 execuções completas (concordância por trecho e variação do índice). Reportar separadamente da validade.

### DOC-04 · Alta · Melhoria · Confirmado
**Sem intervalo de confiança nem regra de evidência mínima; dp de distribuição bimodal não informa precisão**

- **Onde:** CELL 37 (processar_documento_com_jev_2_polos), CELL 39 (tabela de cobertura)
- **Evidência:** **Precisão real dos eixos com menos trechos.** - Com 30 (diplomatic) e 24 (state) trechos posicionados, cada trecho vale 3,3 e 4,2 pontos. - Wilson 95%: diplomatic [14,7; 45,2], state [58,1; 89,9], com meia-largura de ±15–16. - O dp reportado (42,2; 38,9) está perto do máximo possível para a média e não indica precisão. O erro-padrão da média é ≈7,7 e 7,9. **Dependência entre trechos vizinhos.** Na segmentação reproduzida, as seções têm 4 a 12 trechos e 12 dos 84 cruzam fronteira entre diretrizes. **Já existe código para isso.** O TCC.ipynb tem moving_block_indices e bootstrap_plan_score_intervals (CELL 237: 2000 réplicas, bloco n^(1/3)), e este notebook não reaproveita.
- **Impacto:** Leitores podem tratar diferenças de 5–10 pontos entre eixos ou planos como reais quando estão dentro do erro amostral. Eixos com poucos trechos produzem índices instáveis.
- **Recomendação (ajustada):** Manter a recomendação, com dois ajustes: 1. Definir a regra mínima de forma coerente: por exemplo, n≥16 para ±20 com p≈0,75, ou testar a meia-largura do próprio IC bootstrap em vez de um n fixo. 2. Pré-registrar essa regra antes de processar os outros planos.

### DOC-05 · Alta · Nova ideia · Parcial (corrigido na verificação)
**Alinhamento com o usuário exige estimando comum: score do quiz (comprimido para 50) e índice do documento (sem abstenções) não estão na mesma escala**

- **Onde:** Seções 10–11 (não implementado); TCC.ipynb CELL 25 (Quiz8Values.calc_score/calculate_8values); tcc/lista_total.json, tcc/ideologies.json, docx do TCC
- **Enunciado corrigido:** O score do quiz é comprimido em direção a 50 por respostas neutras e de intensidade parcial (±0,5). O índice documental é uma proporção de votos direcionais. Nos 3 conjuntos de tcc/lista_total.json, a diferença entre as duas escalas chega a 23 pontos, sempre no sentido de afastar o '% pró-A' de 50. Comparar diretamente o score do quiz com o índice do documento viesa o alinhamento.
- **Impacto:** Comparar diretamente o score do quiz do usuário com o índice do documento infla as distâncias de forma sistemática. Usuários com muitas respostas neutras pareceriam distantes de qualquer plano. A conclusão central do TCC (alinhamento) ficaria enviesada pela escala, não pelo conteúdo.
- **Recomendação (ajustada):** Escolher e pré-registrar um estimando comum. Há duas opções: - **(a)** Medir o usuário com o mesmo estimando do documento (% pró-A entre respostas posicionadas, ponderado por |efeito|), sempre com a cobertura. - **(b)** Medir o documento no instrumento do usuário: o modelo responde às 70 perguntas pelo documento, como no 'Teste Perguntas Total' do TCC.ipynb, com validação própria. Reportar a outra opção como robustez. Manter o restante: IC por eixo, eixos 'não comparáveis' sem imputar 50, nenhuma 'ideologia mais próxima' para planos e ranking ordinal como checagem.

### DOC-06 · Alta · Melhoria · Confirmado
**Artefatos de extração e trechos não propositivos (capa, sumário, siglas, quebras de página, diagnósticos) contam como votos, de forma desigual entre planos**

- **Onde:** CELL 34 (proposta_texto = plano_lula['md']), CELL 36 (dividir_texto_em_chunks_tokens), CELL 39
- **Evidência:** **Plano analisado (segmentação reproduzida offline: 84 chunks, 26–592 tokens):** - Chunk 1: capa + '# Índice', com 26 tokens. - Chunk 2: sumário em tabela Markdown. A CELL 41 mostra o JEV marcando economic como relevante (0,95) com score 99, ou seja, um voto A derivado só de títulos que repetem o conteúdo. - Chunk 84: contém comentários '<!-- Start of picture text -->' com o número de página e a lista de siglas da coligação, além de uma frase de campanha com o nome do candidato. - 34 dos 84 chunks têm ≥4 quebras de linha seguidas (quebras de página do PDF). - 7 terminam no meio da frase (ex.: o chunk 45 termina em 'selecionamos outras 59'). - 12 cruzam fronteiras das 13 diretrizes.
- **Impacto:** Votos espúrios entram na média e no denominador da cobertura. Como a contaminação varia muito entre planos, ela pode criar diferenças entre planos que vêm do formato do PDF, não do conteúdo, o que é uma ameaça à comparação neutra.
- **Recomendação (ajustada):** Manter. - Aplicar a mesma limpeza, versionada e com log, a todos os planos antes de qualquer comparação. - Reportar quantos chunks de cada plano foram removidos ou alterados. - Tratar o índice 'sem diagnósticos' como sensibilidade, não como versão principal, a menos que a tipagem das unidades seja validada.

### DOC-09 · Alta · Nova ideia · Confirmado
**Usar tcc/d0_manual_validation_avaliado.csv (66 trechos de 'Clariana Barão (DC)') para validar a relevância por trecho no regime documental**

- **Onde:** Não usado no notebook; seria uma nova seção entre 9 e 10
- **Evidência:** **Origem dos trechos.** As frases 'Proteger Hoje, Transformar o Amanhã', 'Mulheres e crianças em primeiro lugar' e 'Rede nacional de proteção e resposta à violência' só aparecem no md/txt de 'Clariana Barão (DC)'. **Formato do arquivo.** - 66 trechos de 78–150 tokens (mediana 94), com prefixo de caminho de títulos ('PLANO DE GOVERNO > 1. … > 1.1 …'). - Sobreposição de pelo menos 1 frase em 33 de 65 pares vizinhos; 9 seções. - Rótulos binários de relevância: economic 16, diplomatic 4 (todos no cap. 4 Segurança), state 15, society 7. 30 trechos não têm nenhum eixo.
- **Impacto:** Hoje não há nenhuma evidência de que a relevância por trecho (que define cobertura e denominador) concorda com julgamento humano em planos de governo. O d0 permite medir isso já, a baixo custo: 66 chamadas JEV mais o fallback.
- **Recomendação:** 1. Rodar a cascata nos 66 textos. Calcular precisão, recall, F1 e κ por eixo, para o JEV inicial e para a cascata. 2. Calcular IC por bootstrap por seção (clusters), porque os vizinhos se sobrepõem. 3. Não usar o d0 para ajustar limiares e reportar no mesmo conjunto. Se ajustar, separar por seção. 4. Ampliar a anotação: amostra estratificada de trechos dos 12 planos, cegos quanto à origem (DOC-15), com 2 anotadores (κ) e rótulos de polaridade, na mesma unidade usada no pipeline.

### DOC-10 · Alta · Melhoria · Parcial (corrigido na verificação)
**Possível efeito teto em economic e society por sobreposição entre o tópico de relevância e o polo A (baixa discriminabilidade entre planos)**

- **Onde:** CELL 13 (AXIS_SPECS: topic/a/b), CELL 39 (saída)
- **Enunciado corrigido:** Possível efeito teto em society e economic. Em society, os 72 trechos posicionados do plano analisado foram todos classificados como A; isso é dedutível de média 98,75 com dp 1,75. O mecanismo provável é a combinação de três fatores: - um tópico de relevância amplo (AXIS_SPECS['topic'], que inclui ciência, educação, meio ambiente, políticas sociais e serviços públicos); - critérios de polo (TEXTOS_EIXOS_2) em que propostas genéricas de melhoria se encaixam em 'progress'/'equality'; - a ausência de opção 'sem posição'. AXIS_SPECS['a'/'b'] não é usado na polaridade.
- **Impacto:** Se confirmado, os eixos economic e society medem quanto do texto trata de políticas públicas, e não a direção. Os planos ficariam todos perto do teto, com baixo poder de discriminação: um viés de operacionalização, não do texto.
- **Recomendação (ajustada):** 1. Fazer o teste de discriminabilidade nos 12 planos e cruzar com o d0, como proposto. 2. Revisar o 'topic' de relevância e os textos de TEXTOS_EIXOS_2, sem mexer no AXIS_SPECS['a'/'b'] não usado. Uma alternativa é remover esse código morto ou documentar que ele não entra na polaridade. 3. Separar 'trata do tema' de 'defende posição entre os polos' (DOC-V01). 4. Qualquer alteração de rubrica deve ser validada no benchmark e no d0 antes de ser aplicada a todos os planos.

### DOC-V01 · Alta · Melhoria · Acrescentado na verificação
**A abstenção de posição prevista no desenho não ocorre: 201/201 trechos-eixo relevantes receberam um polo**

- **Onde:** CELL 20 (criar_questoes_eixo/criar_perguntas_jev_2_polos), CELL 22 (_decisao_jev), CELL 37, CELL 39 (saída)
- **Evidência:** **Na CELL 39**, 'chunks relevantes' = 'chunks com posição' nos 4 eixos (75/75, 30/30, 24/24, 72/72). Nenhum dos 201 trechos-eixo relevantes ficou sem posição. **Por que isso acontece:** - A pergunta de relevância mede o TEMA, não a presença de posição: 'Há evidência substantiva sobre {topic}' (CELL 13/20). - O Score tem só 2 níveis. Em _normalizar_polaridade_score_2_polos, a classe 'C' só ocorre em empate exato (math.isclose com abs_tol=1e-12). - O LLM pode devolver nivel=null, mas no documento isso nunca resultou em 'relevante sem posição'. - Com isso, o 'C = abstenção' das CELLs 12 e 21 não atua nos dados. **Consequência:** qualquer menção ao tema vira voto direcional.
- **Impacto:** O índice mede, em parte, a frequência temática, e não a posição. Trechos sem direção entre os polos são forçados a um polo, o que infla a cobertura e pode empurrar eixos para o teto ou para o piso de forma que não se compara entre planos.
- **Recomendação:** 1. Separar 'trata do tema' de 'defende uma posição situável entre os polos', com uma pergunta Choice adicional de presença de posição. Só conta voto quando as duas respostas são 'sim'. 2. Reportar por eixo a taxa de 'relevante sem posição'. 3. Validar a nova pergunta no benchmark (efeito ≠ 0) e no d0 ampliado com rótulos de polaridade. 4. Manter a versão atual como sensibilidade.

### DOC-V02 · Alta · Melhoria · Acrescentado na verificação
**Índices de state e diplomatic são reportados sem evidência de validade da direção**

- **Onde:** CELL 31/32 (resumo do benchmark), CELL 39 e CELL 44 (resultado do documento)
- **Evidência:** **O que o benchmark mostra (CELL 31, cascata):** - Acurácia de polaridade: state 0,405405 = 15/37 e diplomatic 0,541667 = 13/24. - Para comparação: economic 15/22 e society 27/33. - A métrica conta como erro os pares com efeito ≠ 0 que o modelo marcou como irrelevantes (polaridade prevista 'C', CELL 26). Ela mistura recall de relevância com acerto de direção. - A acurácia condicional de direção (entre pares com A/B previsto) não é reportada. - As saídas salvas estão truncadas, então não é possível recalculá-la. **O que o documento mostra (CELL 39/44):** state 77,9 e diplomatic 27,4, com rótulos.
- **Impacto:** Dois dos quatro eixos do resultado documental podem refletir ruído de direção. Apresentá-los com a mesma confiança dos outros eixos distorce a conclusão de alinhamento.
- **Recomendação:** 1. Reportar no benchmark a acurácia condicional de direção, com IC, separada do recall de relevância. 2. Definir antes um critério mínimo de validade por eixo (por exemplo, acurácia condicional ≥0,75 com IC inferior >0,5). Nos eixos abaixo dele, exibir no documento 'direção não validada' em vez do índice, ou com aviso explícito. 3. Criar um gabarito de polaridade para documentos: - anotar a direção numa amostra estratificada e cega de trechos dos 12 planos (2 anotadores, κ); - opcionalmente, usar um corpus externo com codificação de especialistas, como os manifestos codificados por quase-sentença do Manifesto Project.

### DOC-02 · Média · Correção · Parcial (corrigido na verificação)
**O 'score' do documento é a proporção de trechos pró-polo A, não intensidade; a cascata extremiza exatamente os trechos ambíguos**

- **Onde:** CELL 20 (_normalizar_polaridade_score_2_polos), CELL 22 (CascataJevLLM2Polos._motivos/classificar), CELL 35 (markdown), CELL 37 (processar_documento_com_jev_2_polos)
- **Enunciado corrigido:** No Score de 2 níveis, o score nativo é P(polo A), segundo a documentação do SDK. Como os trechos com P(A) entre ~0,15 e ~0,85 vão ao LLM, que devolve 0 ou 100, o índice do documento equivale, na prática, a 100 × a fração de trechos posicionados classificados como A. Ele deve ser declarado e nomeado assim, e não como 'score 8values'. O limiar margem_score_minima parece redundante com confianca_score_minima, mas isso só foi verificado nas linhas visíveis. A frase da CELL 35 é ambígua, não falsa.
- **Impacto:** O 'valor A' é, na prática, ≈ 100 × fração de trechos posicionados classificados como A, com ruído pequeno. Interpretá-lo como intensidade ou posição no espaço do 8Values é inválido.
- **Recomendação (ajustada):** 1. Declarar o estimando como '% de trechos com posição cuja direção é o polo A' e renomear score_8values para p_polo_A (JEV) e voto (LLM). 2. Antes de remover margem_score_minima, registrar todas as linhas de (confidence, margem) e verificar a relação nos 336 pares chunk–eixo. 3. Adotar o voto rígido como regra principal e reportar a regra suave como sensibilidade (DOC-11). 4. Reescrever a CELL 35 sem ambiguidade.

### DOC-07 · Média · Melhoria · Confirmado
**Precisão muito desigual entre os 12 planos (8 a 156 trechos): planos curtos ficam com 2–3 trechos por eixo**

- **Onde:** CELL 10/34 (só 'Lula (PT)' é processado), CELL 37
- **Evidência:** **Tamanho dos planos.** Reproduzi a segmentação de 600 tokens cl100k em todos os 12 planos de tcc/textos_candidatos.json: - Tamanhos de 15.646 a 311.775 caracteres. - Clariana Barão (DC) e Rui Costa Pimenta (PCO): 8 chunks cada. - Edmilson Costa 28, Hertz Dias 42, Wilson Grassi 60, Samara Martins 65, Romeu Zema 71, Renan Santos 72, Flávio Bolsonaro 82, Lula 84, Augusto Cury 152, Ronaldo Caiado 156. - Razão de 19,5× entre o maior e o menor. **O que isso significa para os planos curtos.** Com as coberturas observadas (0,29–0,36 em state e diplomatic), um plano de 8 chunks teria 2–3 trechos posicionados, e cada trecho vale 33–50 pontos.
- **Impacto:** Planos curtos terão índices extremos e instáveis por pura granularidade. Uma comparação entre planos por pontos favoreceria artefatos de tamanho.
- **Recomendação (ajustada):** Manter. - Corrigir o comentário do código: ±20 pontos com p≈0,75 exige n≈16. - Usar a prévia offline de n esperado por plano para decidir, antes de chamar a API, quais eixos ou planos terão 'evidência insuficiente'.

### DOC-08 · Média · Nova ideia · Confirmado
**Processar os 12 planos com protocolo idêntico, ordem aleatória, cache e repetições; relatório comparativo neutro**

- **Onde:** CELL 37 (processar_documento_com_jev_2_polos), CELL 39
- **Evidência:** **Escopo atual.** Só 'Lula (PT)' foi processado (CELL 34). **Fragilidade da função.** processar_documento_com_jev_2_polos não tem try/except, retry nem cache: uma falha no chunk k perde os k−1 registros já pagos. **Custo estimado para os 12 planos.** 828 chunks de 600 tokens; com a taxa de encaminhamento observada no documento (46/84), ≈453 chamadas ao LLM. **Registros que faltam.** O modelo é registrado por decisão, mas não há timestamp por chamada, versão do SDK nem ordem de processamento. **Teste de estabilidade anterior.** tcc/teste_estabilidade.json tem 133 bytes e é JSON inválido (truncado em 'estimado_md'), então não existe medida de teste–reteste aproveitável.
- **Impacto:** Sem um protocolo idêntico e registrado, diferenças entre planos podem vir da configuração, da ordem ou da data das chamadas (deriva do modelo), e não do conteúdo. Uma interrupção também encarece e atrasa o experimento.
- **Recomendação:** 1. Congelar CONFIG_JEV_LLM_2_POLOS, CONFIG_CHUNKS, rubricas e limpeza antes de ver os resultados de todos os planos, e registrar o hash da configuração. 2. Embaralhar a ordem dos planos com semente registrada. 3. Usar cache JSONL por sha256(config+chunk), com retry exponencial e retomada após falha. 4. Fazer pelo menos 2–3 repetições completas para teste–reteste. 5. Relatório comparativo neutro: ordem alfabética ou aleatória, mesma escala e mesmo gráfico para todos, IC e n sempre visíveis, sem ranking nem rótulos ideológicos, e a mesma lista de limitações para todos os planos.

### DOC-11 · Média · Nova ideia · Parcial (corrigido na verificação)
**Análise de sensibilidade da agregação com as decisões já obtidas (sem novas chamadas)**

- **Onde:** CELL 37; dados em resultado_documento['chunks'] (eixos e eixos_jev)
- **Enunciado corrigido:** As decisões salvas permitem recalcular o índice offline sob várias regras de agregação. A regra 'irrelevância = neutralidade' não corresponde à convenção do quiz.
- **Impacto:** Sem sensibilidade, não se sabe se uma conclusão depende da regra de agregação escolhida, nem quanto o LLM puxa o índice.
- **Recomendação (ajustada):** Manter as variantes, com dois ajustes no rótulo: - renomear 'abstenção = 50 (escala do quiz)' para 'irrelevância tratada como neutralidade'; - incluir a variante 'análogo do quiz', que soma ao denominador, com valor 50, apenas os trechos com relevante=True e sem posição. Manter também a regra de marcar como 'não robusta' qualquer conclusão que mude de lado em relação a 50.

### DOC-12 · Média · Melhoria · Confirmado
**Peso igual por trecho: tamanho, seção e trechos mistos definem implicitamente o estimando**

- **Onde:** CELL 37 (média simples de scores), CELL 35 (markdown 'Cada chunk tem o mesmo peso')
- **Evidência:** **Pesos implícitos na segmentação reproduzida.** - Trechos de 26 a 592 tokens recebem o mesmo peso. - A apresentação e os compromissos gerais, antes da diretriz 1, somam 12 trechos (14% dos votos; 5.652 tokens). - A diretriz 8 tem 11 trechos; as diretrizes 1, 3, 6, 7 e 12 têm 4 cada; a diretriz 13 (política externa/soberania) tem 5. **Trecho misto.** O chunk 84 junta enunciados descritos pelos dois polos diplomáticos: cooperação multilateral, ODS, governança internacional e compromissos internacionais, de um lado; autonomia e soberania, do outro. Recebeu um único voto extremo (diplomatic P(A)=0,01; CELL 41). **Fronteiras.** 12 dos 84 trechos cruzam a fronteira entre diretrizes.
- **Impacto:** 'Um trecho, um voto' mede ênfase textual: seções mais longas pesam mais. Trechos mistos são forçados a um polo, e o resultado depende de onde caem as fronteiras. É uma escolha legítima, mas precisa ser declarada e testada.
- **Recomendação:** Declarar o estimando principal e reportar como sensibilidade: - (i) ponderação por tokens - (ii) 'uma seção, um voto' (média das médias por diretriz) - (iii) unidade proposicional (parágrafo ou frase com verbo de compromisso: 'faremos', 'ampliaremos'…), que reduz trechos mistos Com o Score de 2 níveis, um trecho misto deveria preferir abstenção ou o nível 'misto' de uma rubrica ordinal.

### DOC-13 · Média · Nova ideia · Confirmado
**Análise de sensibilidade ao tamanho e ao tipo de segmentação (tokens cl100k vs. seção; md vs. txt)**

- **Onde:** CELL 5 (CONFIG_CHUNKS), CELL 36 (dividir_texto_em_chunks_tokens)
- **Evidência:** **Número de trechos varia muito com o tamanho.** No mesmo plano, 300, 600, 1000 e 2000 tokens geram 188, 84, 48 e 24 trechos. Trechos maiores aumentam a cobertura e a mistura de conteúdo; menores aumentam o ruído. **'600 tokens' é uma convenção.** É contado em cl100k (≈3,75 caracteres por token no plano: 166.922 caracteres / 44.550 tokens), e o JEV e o Sabiá tokenizam de outro modo. **md vs. txt muda a contagem.** Wilson Grassi: 60 vs. 64; Flávio Bolsonaro: 82 vs. 86. O TCC.ipynb já comparava md e txt (CELLs 139–154), mas este notebook usa só md.
- **Impacto:** O índice e a cobertura dependem da unidade de análise. Sem sensibilidade, não se sabe se as conclusões sobrevivem a uma escolha razoável diferente.
- **Recomendação:** 1. Pré-registrar uma grade pequena: 300 tokens, 600 tokens, 1000 tokens e híbrido por seção, todas sobre o md limpo (DOC-06). 2. Escolher a configuração principal antes de ver os resultados de todos os planos. 3. Reportar índice, cobertura e IC por configuração. 4. Documentar que 'token' significa cl100k. 5. Custo extra no plano analisado: ~188 + 48 chamadas JEV.

### DOC-14 · Média · Melhoria · Parcial (corrigido na verificação)
**Polissemia de 'soberania' pode transformar o eixo diplomático em contagem lexical**

- **Onde:** CELL 14 (TEXTOS_EIXOS_2['diplomatic']['might']), CELL 13 (AXIS_SPECS['diplomatic']['b']), CELL 39
- **Enunciado corrigido:** 'Soberania' aparece em 25 dos 84 trechos do plano analisado e em 10 dos 12 planos, muitas vezes em sentido setorial. O termo está no tópico de relevância do eixo diplomático (AXIS_SPECS['topic']) e no primeiro critério do polo B (TEXTOS_EIXOS_2['might']). Assim, pode puxar tanto a relevância quanto a direção pela frequência lexical.
- **Impacto:** Usos setoriais (autossuficiência em saúde, alimentos ou tecnologia) podem ser lidos como posição de política externa, puxando o eixo pela frequência do termo e não pela posição. O efeito atinge planos de diferentes orientações e precisa ser medido, não presumido.
- **Recomendação:** 1. Cruzar as decisões do eixo diplomatic com a presença e o tipo de uso do termo, por trecho. 2. Revisar manualmente uma amostra. 3. Explicitar na rubrica que soberania setorial não é, por si só, posição em política externa. 4. Teste metamórfico: trocar 'soberania digital' por 'autonomia tecnológica' e conferir que a decisão não muda.

### DOC-15 · Média · Nova ideia · Confirmado
**Cegamento de identidade (nomes, siglas, coligações) antes da classificação, com teste de sensibilidade**

- **Onde:** CELL 20 (instrução do JevScore), CELL 22 (prompt do LLM), CELL 34
- **Evidência:** **A instrução existe, mas o texto carrega a identidade.** A instrução do JEV pede para não deduzir a posição pela 'identidade do autor, partido, organização' (CELL 20). Mesmo assim, o texto enviado contém a identidade: - O chunk 84 traz a lista de siglas da coligação (num comentário de imagem) e uma frase de campanha com o nome do candidato. - Menções ao nome do próprio candidato no md: Lula 31, Flávio Bolsonaro 23, Augusto Cury 13. - Menções à própria sigla: Renan Santos/Missão 28, Samara Martins/UP 14, Edmilson Costa/PCB 12, Wilson Grassi/Democrata 7. **Por que isso importa.** Os modelos conhecem esses nomes, e uma instrução não garante que não serão usados.
- **Impacto:** Existe o risco de inferência por identidade, e não por conteúdo, para todos os planos. Para um TCC com exigência de neutralidade, o cegamento é o procedimento padrão e torna o resultado defensável.
- **Recomendação (ajustada):** Manter o cegamento e o teste de sensibilidade, com quatro cuidados: 1. Usar uma lista curada de nomes, siglas e coligações, com padrões de contexto (por exemplo, 'Partido X', listas de coligação nos comentários de imagem, assinaturas). 2. Gerar um log de cada substituição e revisá-lo manualmente. 3. Não mascarar palavras comuns ('Rede', 'Novo', 'Missão', 'Avante', 'PL') fora desses contextos. 4. Remover os blocos de imagem com siglas (DOC-06), em vez de mascará-los.

### DOC-16 · Média · Nova ideia · Confirmado
**Apresentação ao usuário com evidências verificáveis dos dois polos (explicabilidade prevista no TCC)**

- **Onde:** CELL 22 ('evidencia': None nas decisões do JEV), CELL 41
- **Evidência:** **O que o TCC prevê.** A metodologia do docx inclui 'geração de explicações interpretáveis, traduzindo os resultados técnicos em justificativas compreensíveis para o usuário'. **O que o pipeline oferece hoje.** - Só os eixos encaminhados ao LLM têm citação. Em _decisao_jev, 'evidencia' e 'evidencia_verificada' são None. - No documento, a maioria dos votos é do JEV sem citação. No benchmark, só 31 de 280 pares passaram pelo LLM. - O resumo (CELL 39) mostra só médias, sem os trechos que as sustentam.
- **Impacto:** O usuário não consegue auditar por que um plano aparece de certo lado. Sem trechos dos dois polos, a apresentação pode parecer opinativa, quando o objetivo é educativo e neutro.
- **Recomendação:** Para cada eixo, mostrar ao usuário: - contagens A, B e sem posição; - IC e cobertura; - 2–3 trechos de cada polo, os de maior |P(A)−0,5| no JEV e as citações verificadas do LLM, com número do trecho. Usar um texto-modelo neutro e um aviso de limitações. Para trechos do JEV sem citação, gerar a citação numa etapa de auditoria (LLM com verificação literal) ou mostrar o trecho inteiro.

### DOC-17 · Média · Melhoria · Parcial (corrigido na verificação)
**Gráfico da CELL 44: barras A/B redundantes, sem incerteza nem n, rótulos ideológicos e título por variável global**

- **Onde:** CELL 44 (grafico_scores_documento)
- **Enunciado corrigido:** O gráfico da CELL 44 tem três problemas: - duplica informação (B = 100 − A); - não mostra incerteza, n nem cobertura; - exibe rótulos ideológicos. Além disso, usa uma variável global no título e altera o objeto recebido. A paleta atual não é um problema de daltonismo.
- **Impacto:** A figura transmite precisão e classificação que os dados não sustentam e não permite comparar planos de forma justa.
- **Recomendação:** Usar barra horizontal divergente no estilo 8values, com polo A à esquerda e B à direita, nomes dos polos nas pontas, ponto com IC95, 'n de N trechos (cobertura)' e 'evidência insuficiente' explícito. Outros ajustes: - Cores Okabe–Ito. - Título padronizado e neutro, a partir de documento['documento']. - Para os 12 planos, small multiples com a mesma escala, em ordem alfabética ou aleatória. - Sem rótulos ideológicos e sem mutar a entrada. O código abaixo foi testado com dados sintéticos.

### DOC-18 · Baixa · Correção · Confirmado
**Documentação diz que o documento está incorporado, mas ele é carregado de arquivo; hash não verificado; segmentador opcional envia o documento inteiro**

- **Onde:** CELL 0 e CELL 33 (markdown), CELL 10/34 (carregamento), CELL 37 (separar_em_chunks=None)
- **Evidência:** **A documentação contradiz o código.** - A CELL 0 diz que 'as 70 perguntas … e o documento de exemplo estão incorporados'. - A CELL 33 diz 'Nenhum carregamento externo é necessário'. - Mas a CELL 9 lê tcc/questions.json e as CELLs 10/34 leem tcc/textos_candidatos.json. **O hash existe, mas não é conferido.** metadata.origem.documento_texto_sha256 = d18c54c0…f096 confere com o sha256 do md de 'Lula (PT)', que calculei, mas nenhuma célula faz essa verificação. **O default é arriscado.** Em processar_documento_com_jev_2_polos, separar_em_chunks=None envia o documento inteiro (44.550 tokens cl100k) numa única chamada JEV.
- **Impacto:** Leitores e avaliadores podem achar que o notebook é autocontido. Uma mudança silenciosa no JSON alteraria os resultados sem aviso, e o default pode gerar uma chamada inválida ou cara.
- **Recomendação (ajustada):** Manter. - Ao adicionar a verificação de questions.json, documentar o que exatamente é hasheado (bytes do arquivo ou serialização canônica) e atualizar a metadata.

## Neutralidade, simetria e validade de construto (VIE)

### VIE-01 · Crítica · Correção · Confirmado
**Rótulos ideológicos do 8Values aplicados a um índice que não está na escala do 8Values (plano de um candidato real)**

- **Onde:** CELL 11 (ECON_ARRAY…SCTY_ARRAY); CELL 37 processar_documento_com_jev_2_polos; CELL 43 rotulo_8values; CELL 44 grafico_scores_documento (figura salva)
- **Evidência:** (1) O 'score' do Score de 2 níveis é P(polo A). No typesafe-sdk 0.7.2 (_schemas/models.py, ScoreAnswer.score), score é a média dos níveis ponderada pela probabilidade; com níveis {0,1}, score = P(nível 1) = P(polo A). As saídas salvas da CELL 41 confirmam a hipótese: score 61 ↔ margem 0,22 (=|2·0,61−1|), 99 ↔ 0,98, 1 ↔ 0,98 e 98 ↔ 0,96. Nas 10 linhas visíveis, confidence ≈ margem: 0,30/0,30; 0,84/0,84; 0,64/0,64; 0,24/0,24; 0,99/0,98; 1,00/1,00; 0,97/0,98; 0,97/0,98; 0,22/0,22; 0,96/0,96. Portanto 'valor A' é a média, entre trechos, de uma probabilidade de direção, e não uma intensidade.
- **Impacto:** O TCC pode acabar associando a um candidato identificado rótulos como 'Comunista' ou 'Revolucionário' que não decorrem da escala do instrumento. É um erro de categoria (probabilidade de direção lida como intensidade ideológica) e uma violação direta da exigência de neutralidade, agravada por apenas 1 dos 12 planos ter sido rotulado.
- **Recomendação (ajustada):** Manter a recomendação e acrescentar: (a) reportar n_A e n_B com IC de Wilson para a proporção A/(A+B), ou a escala logit log((n_A+0,5)/(n_B+0,5)), que é simétrica e tem variância analítica; (b) fazer o bootstrap por blocos de trechos adjacentes, porque trechos vizinhos não são independentes; (c) gerar figura e tabela a partir dos mesmos registros salvos (ver VIE-V03).

### VIE-02 · Alta · Correção · Confirmado
**Assimetria de extremidade e de valência: o polo 'authority' descreve um regime autoritário, enquanto 'liberty' descreve a democracia liberal (tabela de simetria por polo)**

- **Onde:** CELL 14 TEXTOS_EIXOS_2 (todos os eixos, foco em 'state'); CELL 13 AXIS_SPECS['state']['topic']; CELL 20 criar_perguntas_jev_2_polos
- **Evidência:** Tabela por polo. Palavras contadas com regex \w+. 'Itens de grau alto' são os itens que derivam das frases 'Em pontuações mais altas…' ou 'Nos extremos…' da versão longa TEXTOS_EIXOS_1 (TCC.ipynb CELL 159); a codificação é minha, item a item. eixo | polo | itens | palavras | marcadores do tópico presentes | itens de grau alto | ressalva moderadora da v1 economic | wealth (B) | 9 | 80 | privatiz | 1 (it. 8) | mantida (it. 9) economic | equality (A) | 8 | 76 | tribut, redistribu | 1 atenuado (it. 7) | - diplomatic | might (B) | 8 | 60 | soberan | 1 brando (it. 8) | conteúdo militar retirado de propósito diplomatic | peace (A) | 9 | 67 | soberan, supranac, multilater | 1-2 (it.
- **Impacto:** Textos programáticos democráticos, de qualquer orientação, quase nunca se reconhecem em 'restrição do pluralismo' ou 'subordinação'. Propostas comuns de ordem e segurança pública ficam sem contraparte na rubrica, o que gera baixa confiança, encaminhamento ao LLM ou deriva sistemática para 'liberty'.
- **Recomendação:** Reescrever 'authority' como seus defensores o descreveriam, em grau moderado: ordem, segurança, regulação de condutas, poderes de fiscalização e punição. Os traços de regime autoritário ficam como 'Forma forte' explícita, espelhada em 'liberty' (rubrica completa em VIE-08). Incluir instrumentos de segurança pública e de proibição ou liberação de condutas nos dois polos, com exemplos que atravessem campos (drogas, armas, expressão). A codificação de extremidade deve ser feita por 2 juízes, com kappa reportado.

### VIE-03 · Alta · Correção · Parcial (corrigido na verificação)
**Eixo social com efeito-teto: o tópico inclui C&T, educação e ambiente, e só o polo 'progress' tem contrapartida para eles**

- **Onde:** CELL 13 AXIS_SPECS['society']['topic']; CELL 14 TEXTOS_EIXOS_2['society'] (progress it. 3); CELL 39 (saída)
- **Enunciado corrigido:** O tópico de 'society' inclui C&T, educação e ambiente, mas só 'progress' tem contrapartida para esses temas na rubrica. No plano analisado, todos os 72 trechos com posição ficaram ≥ ~84, e o critério humano do projeto marca como irrelevantes 21 dos 26 trechos técnico-científicos. Parte disso vem do próprio 8Values (9 dos 18 itens scty+ são sectoriais), mas o gabarito também tem itens sectoriais no polo Tradição (Q45 educação em valores; Q65 cautela com o progresso), que a rubrica não espelha. A saturação em outros planos é hipótese a testar.
- **Impacto:** Em planos de governo, o eixo social passa a medir o volume de conteúdo setorial de C&T, educação e ambiente, e não posição sobre valores e costumes. É provável que qualquer plano sature perto de 100 (rótulo 'Revolucionário'), e o eixo perde a capacidade de discriminar entre planos. Chen et al.
- **Recomendação (ajustada):** Antes de mudar a rubrica, rodar o diagnóstico proposto e processar ao menos 2 ou 3 outros planos com a mesma configuração, para verificar a saturação. Na opção (b), usar Q45 e Q65 como base para as contrapartes de 'tradition' (ensino de valores; cautela com mudanças tecnológicas e sociais). Nas duas opções, reportar a acurácia do benchmark com e sem os 9 itens scty+ sectoriais.

### VIE-04 · Alta · Correção · Confirmado
**Eixo diplomático: a rubrica mede 'soberania × integração supranacional', mas o gabarito e os rótulos medem 'militarismo/nacionalismo × pacifismo/globalismo'**

- **Onde:** CELL 13 AXIS_SPECS['diplomatic'] ('name', 'topic'); CELL 14 TEXTOS_EIXOS_2['diplomatic']; CELL 11 DIPL_ARRAY; CELL 41 (chunk 84)
- **Evidência:** (1) Contagem exata nos dois polos: 'paz', 'pacíf*', 'milit*', 'guerra', 'força' e 'defesa' aparecem zero vezes. O polo se chama 'peace' e não contém 'paz'. O tópico de relevância, porém, inclui 'defesa nacional, forças armadas, conflitos, guerra, intervenção militar'. (2) O gabarito do 8Values tem itens de força militar no eixo dipl: Q17 (−10), Q21 (+10), Q22 (−10), Q23 (+10), além de Q28 (+5, violência). A definição original (docx do TCC) descreve Nação como política externa agressiva, militar, força e soberania, e DIPL_ARRAY ('Pacífico', 'Chauvinista') herda essa leitura.
- **Impacto:** Vocabulário de soberania setorial, comum em planos de orientações diferentes, é empurrado para 'might' e rotulado 'Patriota/Nacionalista'. Propostas de cooperação multilateral que não proponham partilhar soberania não chegam a 'peace'.
- **Recomendação:** Escolher e declarar o construto. A opção recomendada é dividir o eixo em dois sub-eixos pontuados separadamente: D1, autonomia nacional × integração e multilateralismo; D2, força e dissuasão × diplomacia e contenção militar. Mapear os itens do gabarito para cada um. Nos dois polos, acrescentar uma nota simétrica sobre termos ambíguos ('soberania X', 'cooperação técnica') e passar 'autodeterminação' para essa nota neutra. Trocar o 'name' por um nome bipolar e renomear os rótulos de exibição conforme o construto realmente medido.

### VIE-08 · Alta · Melhoria · Parcial (corrigido na verificação)
**Reescrever os polos com estrutura paralela, mesma extensão e linguagem de autodescrição, e validar a nova rubrica fora do conjunto de teste**

- **Onde:** CELL 14 TEXTOS_EIXOS_2; CELL 13 AXIS_SPECS; CELL 20 criar_perguntas_jev_2_polos
- **Enunciado corrigido:** A rubrica precisa de estrutura paralela (princípio, papel do Estado, instrumentos, custo aceito, forma moderada e forte) e de validação fora do conjunto de teste. A v3 proposta é um bom ponto de partida, mas mistura sub-construtos no eixo diplomático e cria sobreposição lexical entre state e society.
- **Impacto:** Sem uma rubrica simétrica, nenhum teste posterior consegue separar o viés do instrumento da posição do texto.
- **Recomendação (ajustada):** Adotar a estrutura e o protocolo, corrigindo três pontos: (1) definir antes o construto diplomático (só autonomia × integração, ou D1/D2 separados) e não misturar força militar e soberania no mesmo polo; (2) retirar de society os termos de autonomia ou direitos individuais e usar só vocabulário de valores e costumes; (3) reportar a acurácia com e sem os 9 itens scty+ sectoriais. Rodar auditar_simetria (VIE-02) e uma checagem de raízes compartilhadas entre eixos antes de congelar a versão.

### VIE-05 · Média · Correção · Parcial (corrigido na verificação)
**Eixo econômico: 'equality' cobre tributação e políticas sociais; 'wealth' não cobre impostos, gasto nem responsabilidade fiscal**

- **Onde:** CELL 14 TEXTOS_EIXOS_2['economic']; CELL 13 AXIS_SPECS['economic']['topic']
- **Enunciado corrigido:** 'wealth' não nomeia os instrumentos tributários e fiscais do polo Mercados (impostos menores, controle de gasto, orçamento equilibrado, que é o Q4 do gabarito), ao passo que 'equality' nomeia tributação progressiva e redistribuição, e o tópico de relevância econômica abrange qualquer política social. O efeito sobre o índice de 93,4 é hipótese a testar.
- **Impacto:** Trechos que combinam programas sociais com disciplina fiscal tendem para 'equality', porque só um dos polos nomeia seus instrumentos. Isso infla o índice econômico (93,4 no documento, com 75/84 trechos com posição) de qualquer plano que fale em serviços públicos.
- **Recomendação (ajustada):** Formular os instrumentos dos dois polos como trade-offs explícitos, e não como termos de consenso. Exemplo: wealth = 'redução de tributos ou do gasto público mesmo com menor oferta de serviços'; equality = 'aumento de tributos ou do gasto público para ampliar serviços e transferências'. Acrescentar às instructions uma nota simétrica: 'menção a responsabilidade fiscal, a serviço público ou a programa social, sem trade-off, não indica polo'. Validar só no conjunto de desenvolvimento (VIE-19).

### VIE-06 · Média · Correção · Confirmado
**Ordem dos critérios confundida com a identidade do polo: [B, A] fixo no JEV e no LLM, com polo A sempre no mesmo quadrante**

- **Onde:** CELL 20 criar_perguntas_jev_2_polos (criteria=[texto_polo_b, texto_polo_a]); CELL 22 prompt do LLM ('nivel=0 corresponde ao primeiro critério (polo B)'); CELL 14 POLOS_EIXOS_2
- **Evidência:** (1) O SDK trata o Score como rubrica ordenada: a posição de cada descrição define sua pontuação, a partir de zero (ScoreQuestion.criteria em typesafe_sdk/_schemas/models.py). Logo, polo A = nível 1 = 2ª posição nos 4 eixos, e o mesmo vale no LLM. (2) Os quatro polos A (equality, peace, liberty, progress) formam um único quadrante. Sakhawat et al. (2026, tcc/'comparacao politica modelos.pdf') auditaram 26 LLMs com Political Compass, SapplyValues e 8Values: 96,3% caíram no quadrante libertário-esquerda. Na classificação de notícias, encontraram leve deslocamento sistemático do conteúdo neutro (erro direcional médio −0,26) e detecção assimétrica dos extremos.
- **Impacto:** Um desvio constante a favor do 2º critério seria lido como posição ideológica do documento, sempre no mesmo sentido nos quatro eixos. Sem permutação, não dá para afirmar que o instrumento não tem viés.
- **Recomendação:** Rodar o teste de permutação [B,A] → [A,B] nos 70 itens, nos 84 trechos e no banco sintético (VIE-17). Na ordem invertida, converter com P(A) = 1 − score, e alternar qual ordem é chamada primeiro. Critérios de aceite por eixo: |Δ médio| ≤ 0,02; |Δ| médio ≤ 0,05; taxa de inversão de direção ≤ 3%; Wilcoxon pareado sem significância (p > 0,05). Se falhar, adotar como medida final a média das duas ordens (contrabalanceamento). Repetir com o LLM, invertendo os critérios e o mapeamento de 'nivel'.

### VIE-07 · Média · Melhoria · Parcial (corrigido na verificação)
**Só 1 dos 12 planos é processado, identificado pelo nome; falta processar todos de forma cega, idêntica e repetida**

- **Onde:** CELL 10 (seleção de 'Lula (PT)'); CELLs 33–34; CELL 39; CELL 44 (título com DOCUMENTO_NOME)
- **Enunciado corrigido:** O pipeline em cascata só foi aplicado a um plano, identificado pelo nome e usado repetidamente como exemplo no projeto, sem repetições. Para comparar planos é preciso processar os 12 com a configuração congelada, nomes mascarados e repetições que permitam separar a variação entre execuções da variação entre planos.
- **Impacto:** Mesmo com um instrumento neutro, aplicá-lo a um só candidato e apresentar o resultado com nome e rótulo gera assimetria de exposição. Sem repetições, a variação entre execuções (de 2 a 5 pontos) se confunde com diferença real entre planos.
- **Recomendação (ajustada):** Manter o processamento cego dos 12 planos (com 2 a 3 repetições, conforme o custo). Trocar o critério ad hoc por: ICC(2,1) por eixo ≥ 0,75, com a variância entre planos maior que a variância entre repetições, e sinal de alerta se ≥ 10 dos 12 planos caírem na mesma faixa de rótulo. Registrar a versão do modelo em cada execução. O ICC pode ser calculado por componentes de variância, sem acrescentar o pingouin às dependências.

### VIE-10 · Média · Melhoria · Confirmado
**Marcas de identidade (nome, partido, coligação) entram nos trechos, e não há teste contrafactual de invariância**

- **Onde:** CELL 34 proposta_texto; CELL 36 dividir_texto_em_chunks_tokens; CELL 20 (instrução 'Não deduza… identidade'); CELL 22 (prompt do LLM)
- **Evidência:** (1) No plano analisado, 23 de 84 trechos (27%) citam o próprio nome ou a sigla do candidato, e o chunk 84 termina com uma frase de exaltação do candidato e a lista de partidos da coligação. Nos 12 planos, de 0% a 29% dos trechos citam nome ou sigla da própria candidatura (86 de 828 no total). É um limite inferior, porque busquei só o nome como registrado em 'candidato'. A exposição a pistas de identidade varia muito entre planos. (2) A instrução do Score proíbe inferir pela identidade (CELL 20) e é repassada ao LLM via rubricas, mas nada verifica se ela é cumprida. (3) Haroon et al.
- **Impacto:** Se o modelo tiver prior associado a nomes ou partidos, planos com mais autorreferências recebem mais desse prior, e de forma desigual entre candidatos.
- **Recomendação:** (a) Mascarar nomes, siglas, números de urna e listas de coligação em todos os 12 planos antes da segmentação. (b) Teste contrafactual: em cerca de 40 frases neutras ou de política setorial, substituir '[CANDIDATURA]' por cada um dos 12 nomes ou siglas e medir P(polo A). Critérios: |ΔP(A)| médio ≤ 0,03 por eixo e identidade; nenhuma inversão de direção; teste de Friedman entre identidades com p > 0,05. (c) Comparar o índice com e sem máscara no mesmo plano.

### VIE-11 · Média · Nova ideia · Parcial (corrigido na verificação)
**O Score devolve direção confiante até em texto sem conteúdo; é preciso medir o prior de cada eixo**

- **Onde:** CELL 20 _normalizar_polaridade_score_2_polos; CELL 22 _decisao_jev (score_nativo); CELL 41 (chunks 1, 83 e 84)
- **Enunciado corrigido:** O Score de 2 polos produz uma direção para qualquer texto, às vezes confiante mesmo numa capa sem conteúdo (diplomatic com margem 0,84). Como a relevância tem falsos positivos, a direção padrão de cada eixo precisa ser medida.
- **Impacto:** Se o prior de um eixo for assimétrico (por exemplo, 'progress' por padrão), cada falso positivo de relevância soma sempre no mesmo sentido. O viés cresce com o tamanho do plano, que varia de 8 a 156 trechos.
- **Recomendação (ajustada):** Manter os dois testes, mas persistir os registros do benchmark (VIE-V03) para que a medição nos 164 pares não exija reexecução. Os critérios propostos são razoáveis.

### VIE-12 · Média · Melhoria · Parcial (corrigido na verificação)
**O fallback binário do LLM (0 ou 100) dá peso máximo ao prior do LLM justamente nos casos ambíguos**

- **Onde:** CELL 22 CascataJevLLM2Polos.classificar (score_8values = nivel × 100); CELL 37 (média sem distinguir o método); CELL 41
- **Enunciado corrigido:** O fallback transforma casos de baixa confiança do JEV em 0 ou 100 e os mistura ao P(A) contínuo. Assim, qualquer tendência do LLM pesa com valor extremo justamente nos casos de fronteira, e o índice não mostra quanto dele vem do LLM.
- **Impacto:** A cascata leva o LLM justamente aos casos de fronteira, onde o prior pesa mais, e converte a escolha em valor extremo. Um viés modesto do LLM vira deslocamento grande nos eixos mais encaminhados (society e state).
- **Recomendação (ajustada):** Implementar primeiro, sem custo, a tabela 'só JEV × cascata × LLM→A/LLM→B/abstenção' por eixo, incluindo as abstenções (VIE-V02) e importando numpy. A simetrização em duas ordens dobra as chamadas ao LLM; aplicá-la pelo menos no benchmark e numa amostra de trechos.

### VIE-13 · Média · Melhoria · Confirmado
**Trechos mistos são forçados a uma só direção, e a evidência pedida ao LLM é de um polo só**

- **Onde:** CELL 20 (Score com 2 critérios); CELL 19 EixoLLM2Polos (campo único 'evidencia'); CELL 22 (prompt)
- **Evidência:** O chunk 84 (600 tokens) contém proposições alinhadas aos dois polos diplomáticos (ODS, governança internacional e cooperação científica × defesa da soberania) e recebeu 0,01 com margem 0,98. O schema do LLM pede uma única citação, que pode ser escolhida para sustentar um polo só, sem registro de evidência contrária. Com trechos de 600 tokens organizados por seção temática, misturas desse tipo são esperadas.
- **Impacto:** A unidade de análise favorece o polo cuja linguagem é mais saliente no trecho, e assimetrias de saliência lexical (como 'soberania', VIE-04) ficam invisíveis.
- **Recomendação:** (a) Pedir ao LLM evidência para os dois polos e permitir o rótulo 'misto'. (b) Medir no nível da proposição (frase ou parágrafo), contando proposições A e B por eixo. (c) Reportar a fração de trechos mistos por plano e eixo. Critério: nos trechos que os anotadores (VIE-18) marcarem como mistos, o sistema deve indicar 'misto' em ≥ 70% dos casos e, nos demais, não favorecer um polo (|A − B| ≤ 10 p.p.).

### VIE-15 · Média · Nova ideia · Confirmado
**O benchmark não tem métricas por polo (revocação A × B), e o gabarito é desbalanceado entre polos**

- **Onde:** CELL 26 executar_benchmark_8values (agrega só por eixo); CELL 27 executar_benchmark_jev_llm_2_polos
- **Evidência:** (1) O resumo agrega apenas por eixo; não há revocação por polo. (2) A 'acurácia de polaridade' conta como erro a classe 'C' gerada pelo gate de relevância (classe = 'C' se não relevante, CELL 22). Por isso state aparece com 0,405 aqui. No bloco original (TCC.ipynb CELL 308), que avalia a direção sem gate, as acurácias de direção foram: state 0,838 (31/37), diplomatic 0,875 (21/24), economic 0,909 (20/22) e society 0,939 (31/33). A métrica atual mistura relevância com direção e não serve para diagnosticar viés de polo. (3) O gabarito é desbalanceado.
- **Impacto:** Uma revocação menor em Autoridade pode refletir os efeitos secundários do gabarito e não viés do modelo, ou o contrário. Sem estratificação, a assimetria fica invisível ou é atribuída à causa errada.
- **Recomendação:** Calcular, por eixo e por polo, a revocação da direção forçada (score_nativo > 0,5) e a da cascata, estratificadas por efeito primário e secundário, com IC de Wilson e teste exato de Fisher entre polos. Usar acurácia balanceada e salvar os registros em JSON para auditoria. Critério: |revocação A − revocação B| ≤ 10 p.p. nos itens primários de cada eixo, com IC que inclua 0.

### VIE-17 · Média · Nova ideia · Confirmado
**Banco sintético simétrico (pares espelhados por polo, intensidade e registro) para medir revocação e inclinação por polo**

- **Onde:** Nova seção após a CELL 32
- **Evidência:** As 70 perguntas são atitudinais e em 1ª pessoa ('Eu apoio…', 'Minha nação…'), enquanto os documentos são programáticos ('Vamos…', 'Reforçaremos…'). A distribuição por polo é desigual (govt: 13 × 24) e não há controle de intensidade. Hoje não existe nenhum conjunto equilibrado por construção.
- **Impacto:** Sem um banco balanceado, não é possível separar o viés do instrumento de diferenças de dificuldade entre os itens de cada polo.
- **Recomendação (ajustada):** Começar com 4 eixos × 2 intensidades × 2 registros × 5 pares espelhados (80 pares, 160 frases), usando como semente os exemplos de polo da TCC.ipynb CELL 216. Usar o banco só como conjunto de desenvolvimento.

### VIE-18 · Média · Nova ideia · Parcial (corrigido na verificação)
**Anotação humana por pessoas de orientações diversas, com concordância (α de Krippendorff) e comparação modelo × humanos**

- **Onde:** tcc/d0_manual_validation_avaliado.csv (não usado pelo notebook); CELL 37
- **Evidência:** O único rótulo humano disponível (d0_manual_validation_avaliado.csv) cobre só relevância, em 66 trechos de um único plano, sem direção e sem medida de concordância. A divergência com o critério operacional é grande (VIE-03: 21 de 26 trechos de C&T marcados society=0). Benoit et al. (AJPS 2026, tcc/) validam posições estimadas por LLM contra médias de especialistas e usam a correlação especialista × especialista como referência de confiabilidade. Implementei e conferi o α nominal abaixo contra o pacote 'krippendorff' (resultados idênticos em 3 simulações: 0,892; 0,690; 0,628).
- **Impacto:** Sem gabarito humano em documentos, não há como sustentar nem que o índice do plano é válido nem que é neutro.
- **Recomendação (ajustada):** Reduzir para cerca de 10 trechos por plano (cerca de 120), estratificados e mascarados, com 2 a 3 anotadores treinados na rubrica. Diversidade de perspectiva pode ser buscada sem registrar orientação individual; se registrar, fazê-lo com termo de consentimento, de forma anonimizada e só em categorias agregadas. Manter α ≥ 0,667 e a comparação α(modelo+humanos) × α(humanos).

### VIE-19 · Média · Correção · Confirmado
**O benchmark de 70 itens já foi usado para escolher rubrica e limiares e deixou de ser um conjunto de teste independente**

- **Onde:** CELLs 4–5 (limiares 'a selecionar na validação'); TCC.ipynb CELLs 298–328
- **Evidência:** No TCC.ipynb, os mesmos 70 itens serviram para comparar várias rubricas (TEXTOS_EIXOS_1 longa, TEXTOS_EIXOS_2, 5 polos, 2 Nouls independentes) e para varrer limiar_noul de 0,30 a 0,70 (CELL 318: melhor resultado em 0,60, com 209/280). Na CELL 328, os limiares foram ordenados por f1_macro. Os limiares atuais (0,20/0,70/0,20, CELL 5) são descritos na CELL 4 como parâmetros 'a selecionar na validação', mas não existe conjunto de validação separado.
- **Impacto:** Escolhas feitas olhando o teste inflam o desempenho reportado e podem fixar, sem intenção, uma rubrica que acerta o gabarito por razões espúrias (por exemplo, palavras-chave de um polo). Reescrever os polos e reavaliar nos mesmos 70 itens agrava o problema.
- **Recomendação:** Declarar no TCC todas as variantes já testadas. Daqui em diante, ajustar só no conjunto de desenvolvimento (VIE-17 + parte da VIE-18), congelar a versão por hash e avaliar uma única vez no teste (70 itens + trechos anotados de teste). Pré-registrar métricas e critérios de aceite.

### VIE-20 · Média · Melhoria · Parcial (corrigido na verificação)
**É preciso discutir e mitigar os limites do 8Values como referência e sua adequação ao contexto brasileiro**

- **Onde:** CELL 6 (markdown); CELL 9 QUESTIONS; CELL 11 (rótulos)
- **Enunciado corrigido:** O 8Values é uma referência operacional sem validação psicométrica publicada. Tem itens de vários eixos e alguns itens dependentes de contexto (Q18; Q62 diante do SUS; Q25 por tradução). A literatura brasileira debate se textos e votações se ordenam por esquerda–direita ou por governo × oposição. O TCC deve declarar esses limites.
- **Impacto:** Concordar com o 8Values significa concordar com um instrumento não validado e culturalmente situado, não com 'a' ideologia do texto. As conclusões do TCC precisam deixar isso claro.
- **Recomendação (ajustada):** Manter (a)–(d), corrigir a citação (Figueredo et al., 2022) apresentando-a como debate, e trocar Q61 por um exemplo mais claro de dependência de contexto. Fazer a análise com e sem itens dependentes de contexto, com a lista definida por duas pessoas antes de ver os resultados.

### VIE-21 · Média · Nova ideia · Parcial (corrigido na verificação)
**Gerar a pontuação do documento na própria escala do 8Values, com o questionário respondido 'por procuração' e com evidência**

- **Onde:** Nova seção após a CELL 39; reutiliza TCC.ipynb CELL 25 (Quiz8Values) e CELL 8 (AnswerOption)
- **Enunciado corrigido:** Pontuar o documento na própria escala do 8Values, item a item e com citação verificada, torna o escore comparável à fórmula do instrumento e auditável. Porém, tratar 'não trata' como 0 puxa planos de baixa cobertura para ~50, como já mostram os resultados do projeto, então os rótulos só fazem sentido com cobertura suficiente.
- **Impacto:** Os rótulos do 8Values passam a ter o mesmo significado que têm para pessoas, o protocolo pode ser aplicado de forma idêntica aos 12 planos e a auditoria pode ser feita item a item, com citação.
- **Recomendação (ajustada):** (1) Calcular o escore só sobre os itens tratados (máximo = Σ|e| dos itens com evidência verificada) e reportar a cobertura por eixo ao lado. (2) Não aplicar rótulo quando a cobertura de um eixo for menor que um mínimo pré-registrado (por exemplo, 5 itens). (3) Recuperar os trechos relevantes por item antes de perguntar ao LLM, pois planos com mais de 300 mil caracteres não cabem num só prompt. (4) Usar o escore por procuração como teste de validade convergente com o índice da cascata nos 12 planos (correlação de postos por eixo), aproveitando os resultados que já existem.

### VIE-V01 · Média · Melhoria · Acrescentado na verificação
**A 'evidência verificada' do LLM só confere se a citação existe no texto, e não se ela sustenta o eixo e o polo escolhidos**

- **Onde:** CELL 20 _score_evidencia_confere; CELL 22 CascataJevLLM2Polos.classificar; CELL 27 (contagem 'eixos com evidência não verificada'); CELL 41
- **Evidência:** _score_evidencia_confere normaliza o texto e testa 'citacao in original', ou seja, uma substring. Qualquer trecho literal do chunk passa, mesmo que trate de outro eixo ou do polo oposto. Na CELL 41, chunk 84, state: o LLM decidiu 100 (liberty) citando 'Reforçaremos os compromissos internacionais do Brasil em matéria de direitos humanos e igualdade...', com evidência verificada = True. O benchmark registra '0 eixos com evidência não verificada' (CELL 31), o que só mostra que as citações existem. As decisões do LLM entram no índice como 0 ou 100.
- **Impacto:** Nada verifica a coerência entre citação, eixo e polo justamente nas decisões que pesam mais (valores extremos em casos de fronteira). Uma tendência do LLM passaria como 'verificada', e o número '0 não verificadas' pode ser lido erroneamente como validação.
- **Recomendação:** Acrescentar uma checagem independente: para cada decisão do LLM, perguntar ao JEV (Choice), só com a citação e em ordem de critérios alternada, se ela apoia o polo A, o polo B ou não trata do eixo. Reportar a taxa de coerência por eixo e por polo e auditar manualmente uma amostra estratificada. Critério sugerido: coerência ≥ 90% e diferença entre polos ≤ 10 p.p.

### VIE-V02 · Média · Melhoria · Acrescentado na verificação
**Abstenções e exclusões da média não são analisadas por polo, e uma abstenção diferencial pode deslocar o índice**

- **Onde:** CELL 22 classificar (nivel=None; evidência não verificada → relevante=None); CELL 35; CELL 37 processar_documento_com_jev_2_polos
- **Evidência:** A CELL 37 diz que 'Scores disponíveis entram na média; ausências/abstenções não', e a CELL 35 que 'Chunks sem evidência ou com abstenção são excluídos da média'. Na CELL 22, um nivel nulo ou uma evidência não verificada tornam score_8values None. A cobertura varia de 0,29 (state) a 0,89 (economic) (CELL 39), mas não há tabela de abstenções por método nem pela direção inicial do JEV. O LLM é chamado exatamente nos casos de fronteira: 46 dos 84 trechos na execução da CELL 41. As exclusões, portanto, não são aleatórias.
- **Impacto:** Suponha que o LLM se abstenha mais quando o JEV pendia para um polo, por exemplo julgando 'equilibrados' os enunciados moderados desse polo. Nesse caso, o índice se desloca sem que o texto mude, e a cobertura agregada não revela o efeito.
- **Recomendação:** Sem novas chamadas: (1) tabela cruzada por eixo da direção inicial do JEV (P(A) > 0,5 ou < 0,5) com a decisão do LLM (A, B ou abstenção); (2) análise de sensibilidade imputando as abstenções com a direção do JEV ou com 50. Critérios: diferença de taxa de abstenção entre as direções iniciais ≤ 10 p.p. e |Δ índice| ≤ 3 pontos. Reportar as duas tabelas junto com o índice.

### VIE-V03 · Média · Correção · Acrescentado na verificação
**As saídas salvas misturam execuções diferentes, e os registros por trecho não são persistidos, o que impede auditar o viés**

- **Onde:** CELLs 24, 29, 31, 32, 39, 41 e 44 (execution_count); CELL 27 (registros só em memória); CELL 37
- **Evidência:** execution_count no .ipynb: benchmark CELLs 29/31/32 = 16/17/18; inicialização do pipeline CELL 24 = 56; documento CELL 39 (tabela 93,41/27,37/77,88/98,75) = 60; tabela por trecho CELL 41 (46 chamadas ao LLM, exemplos do chunk 84) = 23; figura CELL 44 (91,0/32,8/81,7/98,7) = 25. Assim, a figura e a tabela por trecho vêm de uma execução anterior à tabela-resumo, e o pipeline foi recriado depois do benchmark. Os 'registros' (score_nativo, evidências, motivos) só existem em memória, e as saídas salvas mostram 10 linhas, como confirmei no HTML das CELLs 31 e 41 do notebook e das CELLs 308 e 322 do TCC.ipynb.
- **Impacto:** Os exemplos usados para discutir viés (chunk 84, número de chamadas ao LLM) não correspondem necessariamente aos números da tabela. As auditorias sem custo propostas (VIE-11, VIE-12, VIE-15, VIE-V02) não podem ser refeitas sem novas chamadas pagas, e a versão do modelo não fica ligada aos resultados.
- **Recomendação:** Reiniciar o kernel e executar o notebook de cima a baixo. Salvar em JSON os registros do benchmark e de cada documento, com hash das rubricas, configuração, modelos ('jev-1.13.0', 'sabia-4') e data/hora. Gerar figura e tabelas sempre a partir do arquivo salvo da mesma execução.

### VIE-09 · Baixa · Correção · Parcial (corrigido na verificação)
**AXIS_SPECS['a'/'b'] é código morto, e a documentação (CELL 12 e CELL 13) não descreve o que o modelo de fato recebe**

- **Onde:** CELL 13 criar_questoes_eixo ('polaridade' descartada); CELL 20 criar_perguntas_jev_2_polos ('relevancia, _ = …'); CELL 22 CascataJevLLM2Polos.__init__ ('relevancia, _ = …')
- **Enunciado corrigido:** AXIS_SPECS['a'/'b'] e a 'polaridade' de criar_questoes_eixo nunca chegam ao modelo. A CELL 12 documenta corretamente os critérios usados, mas o código morto e a docstring podem levar a descrever no TCC uma rubrica que não foi usada.
- **Impacto:** Um leitor do código ou do apêndice do TCC pode descrever uma rubrica que não foi usada, com efeito oposto na avaliação de viés (por exemplo, supor que o militarismo está coberto). Isso prejudica a transparência e a reprodutibilidade.
- **Recomendação (ajustada):** Remover 'a'/'b' e a polaridade não usada (ou mantê-los num bloco marcado como 'não utilizado') e publicar no apêndice o conteúdo de pipeline.rubricas com o hash da versão, como sugerido.

### VIE-14 · Baixa · Melhoria · Parcial (corrigido na verificação)
**Sobreposição lexical entre eixos ('autoridade', 'ordem', 'identidade/história', 'participação') causa vazamento e correlação artificial entre eixos**

- **Onde:** CELL 14 TEXTOS_EIXOS_2
- **Enunciado corrigido:** Há vocabulário compartilhado entre polos de eixos diferentes (autoridade/ordem; identidade/instituições históricas), o que pode gerar correlação entre eixos além da prevista pelo próprio 8Values. A magnitude não foi medida.
- **Impacto:** Um trecho sobre ordem pública pode contar como 'authority' e como 'tradition'; um sobre identidade nacional, como 'might' e como 'tradition'. Surgem correlações entre eixos que vêm da rubrica e não do texto, e qualquer viés é contado em dobro.
- **Recomendação (ajustada):** Medir o vazamento só com os 34 itens de um único eixo do gabarito e com o banco sintético (VIE-17), comparando a matriz observada com a matriz de cargas cruzadas do próprio 8Values em vez de exigir zero fora da diagonal. Só depois decidir se vale tornar o vocabulário exclusivo por eixo.

### VIE-16 · Baixa · Nova ideia · Confirmado
**Teste de equivariância: negações e pares mínimos dos 70 itens devem inverter a direção, e paráfrases devem preservá-la**

- **Onde:** CELL 9 QUESTIONS; CELL 27 executar_benchmark_jev_llm_2_polos
- **Evidência:** Nenhuma célula testa sensibilidade à forma do enunciado. Vários itens têm negações ou construções que confundem modelos, como Q46 ('As tradições não têm valor por si só'), Q22 ('As guerras não precisam ser justificadas…') e Q36. Sakhawat et al. (2026) encontraram efeito pequeno de variantes de prompt (η² < 0,02) frente à identidade do modelo; já Röttger et al. (2024), revisados por eles, relatam que paráfrases mínimas podem alterar escores ideológicos de questionários. A robustez, portanto, precisa ser medida, não presumida.
- **Impacto:** Se a direção depender de traços superficiais (presença de 'não', palavras-chave de um polo), o instrumento mede léxico e não posição, possivelmente de forma desigual entre polos.
- **Recomendação (ajustada):** Reaproveitar a suíte da TCC.ipynb CELL 216 (substituindo a função semantic por pipeline.classificar) e acrescentar negações e pares mínimos para uma amostra de cerca de 20 itens, balanceada por polo, revisados por duas pessoas.

### VIE-22 · Baixa · Nova ideia · Parcial (corrigido na verificação)
**Testar se 'progress × tradition' está captando continuidade × mudança (incumbente × desafiante) em vez de valores**

- **Onde:** CELL 14 TEXTOS_EIXOS_2['society']
- **Enunciado corrigido:** Como 'tradition' e 'progress' são definidos em boa parte por continuidade × mudança, o eixo social pode responder à retórica de manter ou consolidar × criar ou transformar, independentemente de valores morais. Vale testar isso com pares mínimos.
- **Impacto:** O eixo social pode estar ordenando os planos pela relação com o governo, e não por valores morais, o que seria uma confusão sistemática entre candidaturas.
- **Recomendação:** Usar pares mínimos que mudam só a forma temporal ou de continuidade ('Vamos criar o programa X' × 'Vamos manter e ampliar o programa X') em temas sem conteúdo moral. Critério: |ΔP(A)| em society ≤ 0,05 e relevância inalterada em ≥ 95% dos pares.

### VIE-23 · Baixa · Correção · Refutado
**tcc/2023.acl-long.530.pdf não é Feng et al. (ACL 2023), e sim Chen, Walker e Saligrama: corrigir a referência**

- **Onde:** tcc/2023.acl-long.530.pdf (bibliografia do TCC)
- **Evidência:** A primeira página extraída com pypdf traz o título 'Ideology Prediction from Scarce and Biased Supervision: Learn to Disregard the What and Focus on the How!', de Chen Chen, Dylan Walker e Venkatesh Saligrama, ACL 2023, pp. 9529–9549. O artigo de Feng et al. sobre vieses políticos que vão do pré-treino aos modelos é outro trabalho da ACL 2023 (salvo engano, 2023.acl-long.656 na ACL Anthology; conferir) e não está em tcc/. O docx do TCC não cita Feng; a associação apareceu apenas no contexto desta análise.
- **Por que foi refutado:** Não há erro a corrigir no material do usuário. O PDF é de fato Chen, Walker e Saligrama (ACL 2023, pp. 9529–9549), conferido com pypdf. O TCC.ipynb cita o arquivo corretamente como 'Chen, Walker e Saligrama (2023)' em pelo menos 9 células. Uma busca no repositório (excluindo PDFs) não encontra 'Feng' em nenhum lugar, nem no docx do TCC. O próprio achado admite que a associação 'apareceu apenas no contexto desta análise'. Além disso, o tema está fora da dimensão de viés do notebook.

## Uso das APIs JEV/TypeSafe e Maritaca/Sabiá (API)

### API-01 · Alta · Correção · Confirmado
**Com 2 níveis, o 'score' do Score é P(polo A), não intensidade. A média por chunks mistura probabilidades do JEV com votos 0/100 do LLM e recebe rótulos de intensidade do 8Values**

- **Onde:** CELL 20 (_normalizar_polaridade_score_2_polos: score_8values = score*100); CELL 22 (CascataJevLLM2Polos.classificar: score_8values = nivel*100 no fallback); CELL 37 (processar_documento_com_jev_2_polos: média); CELLs 43-44 (rotulo_8values, grafico_scores_documento)
- **Evidência:** Pela documentação do Score (https://docs.typesafe.ai/primitives/score) e pelo wire schema do SDK (typesafe_sdk/_schemas/models.py, ScoreAnswer.score), o score é a média dos números dos níveis ponderada pelas probabilidades. Com criteria=[polo B, polo A] os níveis são 0 e 1, logo score = P(nível 1) = P(polo A). As saídas salvas confirmam: CELL 31, Q1/state com probabilidades {0:0.04, 1:0.96} e score 0.96; Q69/society com {0:0.01, 1:0.99} e score 0.99; CELL 41, chunk 84/state com score 61 e margem 0,22 (0,61−0,39).
- **Impacto:** Um documento em que os trechos apenas inclinam de modo consistente para um polo recebe o rótulo do extremo da escala do 8Values. A comparação com o perfil do usuário, objetivo do TCC, passa a confrontar grandezas diferentes: intensidade no quiz e probabilidade de direção no documento.
- **Recomendação:** (1) Declarar na metodologia que, com 2 níveis, score = P(polo A) e confidence = |2P−1|. (2) Renomear 'Score (0–100)' para algo como 'índice de inclinação ao polo A'. (3) Agregar numa escala homogênea: contar chunks A, B e abstenções e calcular a proporção de votos, convertendo também o JEV em classe A/B. Reportar à parte a P média do JEV só nos chunks que não foram encaminhados. (4) Não usar rotulo_8values enquanto não houver validação de que o índice é comparável ao escore do quiz; se mantido, marcar como ilustrativo. (5) Se for preciso intensidade, ver API-15.

### API-04 · Alta · Melhoria · Confirmado
**O LLM roda com a temperatura padrão de 0,7 e o JEV não oferece temperatura nem seed: o ganho da cascata (+9 pares) vem de uma única amostra de um processo estocástico**

- **Onde:** CELL 17 (MaritacaClient.generate sem temperature); CELL 29 (uma única execução); CELL 32 (11 corrigidos e 2 piorados)
- **Evidência:** Na referência da Responses API da Maritaca (https://docs.maritaca.ai/api/pt/responses-api), temperature tem padrão 0,7 (faixa de 0,0 a 2,0) e top_p tem padrão 0,95. O parâmetro seed não aparece na lista do corpo da requisição (não confirmado que exista). No JEV, SystemOneRequest (typesafe_sdk/_schemas/models.py) só tem state, model e questions, sem temperatura nem seed. O cookbook oficial de autoconsistência (https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook) relata que o rótulo modal do TypeSafe se repetiu em cerca de 91% de 15 repetições e que o rótulo mudou em 2 das 8 perguntas, com um campo uid variável no state. Pela CELL 32, a cascata corrigiu 11 pares e piorou 2.
- **Impacto:** Não se sabe se a diferença de 75,7% para 78,9% resiste a uma nova execução, nem quanto do resultado de cada eixo do documento é ruído de amostragem.
- **Recomendação:** Usar temperature=0 no Sabiá. Repetir a execução completa pelo menos 3 vezes (JEV e LLM) e reportar média e desvio-padrão das acurácias, concordância entre execuções (por exemplo, kappa) e o McNemar de cada execução. Guardar todas as execuções (API-05).

### API-05 · Alta · Melhoria · Confirmado
**Sem persistência, cache ou registro de metadados das APIs (usage, request_id, response.id, service_tier): resultados não auditáveis e custo não reportável**

- **Onde:** CELL 22 (classificar descarta os objetos de resposta); CELL 27 (executar_benchmark_jev_llm_2_polos: registros só em memória); CELL 37 (processar_documento_com_jev_2_polos); CELL 17
- **Evidência:** Nenhuma célula grava em disco: só há leituras (ler_json, CELLs 8-10), e os registros vivem em variáveis do kernel. Nada disto é guardado: SystemOneResponse.usage do JEV (typesafe_sdk/_core/response_types.py; só tokens de input são cobrados, US$ 0,042 por milhão, segundo https://docs.typesafe.ai/models); o request_id do cabeçalho x-typesafe-request-id (typesafe_sdk/_core/schemas/base.py, propriedade request_id); e, da Maritaca, response.id, usage (input, output e cached tokens), status e incomplete_details (https://docs.maritaca.ai/api/pt/responses-api-response).
- **Impacto:** Depois de reiniciar o kernel, é impossível reconstituir os números publicados. Somado ao alias móvel e à amostragem estocástica (API-03 e API-04), cada nova execução produz números diferentes. Também não se pode reportar custo nem rastrear uma chamada específica com o suporte do provedor.
- **Recomendação:** Salvar cada resposta bruta em disco com chave sha256 de (modelo, perguntas, state, repetição) para o JEV e de (modelo, instruções, input, schema, temperatura) para o LLM. Gravar no fim de cada execução os registros completos, a configuração, as versões e um resumo de usage e custo.

### API-06 · Alta · Melhoria · Confirmado
**Os critérios do Score descrevem vários conceitos por polo, contra a orientação da TypeSafe. Há sinais de saturação (society: 98,75 com dp 1,75) e de erros confiantes que não são encaminhados**

- **Onde:** CELL 14 (TEXTOS_EIXOS_2); CELL 20 (criar_perguntas_jev_2_polos: JevScore com criteria=[texto_polo_b, texto_polo_a])
- **Evidência:** Em TEXTOS_EIXOS_2 (CELL 14), cada polo é um bloco de 8 ou 9 proposições heterogêneas. 'might' mistura soberania, autodeterminação, identidade cultural e coesão nacional. 'tradition' inclui 'família, religião, autoridade', e autoridade também é polo do eixo state. 'progress' inclui reforma de instituições e uso da ciência e do conhecimento. A documentação do Score (https://docs.typesafe.ai/primitives/score) diz que cada nível é avaliado separadamente, sem ver os vizinhos. Recomenda uma só dimensão por pergunta de Score, com medições múltiplas divididas em perguntas separadas e combinadas em código, e níveis descritos como situações concretas, não graus.
- **Impacto:** O Score pode estar medindo a presença de vocabulário associado a um polo, e não a direção da proposta. A saturação tira do eixo a capacidade de distinguir documentos (validade discriminante), e os erros com confiança alta escapam do fallback.
- **Recomendação (ajustada):** Primeiro o diagnóstico, barato: rodar o pipeline sem fallback nos 12 planos de textos_candidatos.json. Com 600 tokens e sobreposição zero, verifiquei que são 828 chunks no total (de 8 a 156 por plano), com custo do JEV desprezível. Reportar por eixo só o dp entre documentos e a fração de chunks com P(A)>0,9, sem interpretar documentos. Junto, auditar manualmente uma amostra estratificada de cerca de 30 chunks 'society/progress'. Só se a saturação se confirmar, decompor em subdimensões espelhadas, que é o esforço alto proposto pelo revisor. Tirar 'autoridade' do polo tradição é ajuste imediato e de baixo custo.

### API-V01 · Alta · Correção · Acrescentado na verificação
**As saídas salvas vêm de execuções diferentes: o gráfico (91,0/32,8/81,7/98,7) não bate com a tabela (93,4/27,4/77,9/98,75), e o benchmark foi executado antes das definições atuais**

- **Onde:** CELL 39 (tabela de cobertura, execution_count 60); CELLs 41 e 44 (execution_count 23 e 25); CELLs 29-32 (benchmark, 16-18); CELLs 5, 22 e 24 (43, 55 e 56); CELL 37 (execution_count None); markdown das CELLs 0 e 33
- **Evidência:** Extraí do .ipynb a imagem salva da CELL 44. As barras do polo A mostram 91,0 / 32,8 / 81,7 / 98,7, enquanto a tabela da CELL 39 mostra 'valor A' 93,4133 / 27,3667 / 77,8750 / 98,7500. As duas deveriam coincidir, porque grafico_scores_documento lê documento['scores'], que é a mesma 'media' da tabela. Os execution_count mostram a ordem: benchmark 14-18, CELL 41 = 23, CELL 44 = 25 e, depois, reexecução das CELLs 2-24 (41-56), 34 (57), 36 (58) e 39 (60). A CELL 37 está sem execution_count. Portanto, (a) a tabela de chunks da CELL 41 (incluindo chunk 84/state 61→100 e as '46 chamadas LLM') e o gráfico pertencem a uma execução anterior à tabela da CELL 39;
- **Impacto:** O TCC pode citar números do mesmo documento que não concordam entre si (por exemplo, 91,0 no gráfico e 93,4 na tabela) e exemplos por chunk que não pertencem à execução cujos índices são relatados. Não se consegue atribuir os resultados do benchmark a uma versão específica do código e da configuração.
- **Recomendação:** Antes de extrair qualquer número para o TCC, rodar 'Reiniciar e executar tudo' uma única vez. Gerar um RUN_ID e colocá-lo no título do gráfico, nas tabelas e nos arquivos salvos. Persistir juntos tabela, figura, registros e metadados (versões dos pacotes, config, modelos, data). Corrigir o markdown das CELLs 0 e 33 para refletir que os dados são carregados de tcc/*.json.

### API-03 · Média · Melhoria · Confirmado
**Os modelos são chamados por alias que muda com o tempo (jev-latest, sabia-4), e o modelo registrado para o LLM é o solicitado, não o que respondeu**

- **Onde:** CELL 24 (AsyncTypeSafeClient sem model; MODELO_LLM na CELL 5); CELL 17 (MaritacaClient.generate descarta o objeto response); CELL 22 (classificar: 'modelo': getattr(self.llm, 'model', ...))
- **Evidência:** No SDK, typesafe_sdk/constants.py define DEFAULT_MODEL = 'jev-latest'. Como a CELL 24 não passa model, a requisição usa o alias. Segundo https://docs.typesafe.ai/models, um alias passa a apontar para a versão nova a cada lançamento, então as respostas podem mudar sem nenhuma alteração do lado do usuário. A mesma página recomenda fixar o ID versionado quando os limiares foram ajustados para uma versão, e informa que IDs como 'jev-1.13.0' são aceitos. Os cookbooks oficiais registram jev-1.12 em 16/08/2026 (citation_check) e jev-latest já resolvendo para jev-1.13.0 em 11/09/2026 (consistency_choice_cookbook).
- **Impacto:** Os limiares ('a selecionar na validação', CELL 4) e os números do TCC (212/280, 221/280, índices do documento) ficam presos a uma versão que pode mudar sem aviso. Reexecuções futuras podem dar resultados diferentes sem que se saiba por quê.
- **Recomendação (ajustada):** Fixar MODELO_JEV='jev-1.13.0' (passando model= explicitamente, o que neutraliza TYPESAFE_DEFAULT_MODEL) e MODELO_LLM='sabia-4-2026-01-06'. Gravar response.model nos dois clientes, sabendo que o exemplo da própria Maritaca mostra 'model': 'sabia-4' na resposta, isto é, response.model pode só ecoar o nome pedido e não revela o snapshot. Por isso, para o LLM, o que garante a versão é pedir o nome datado. Registrar também typesafe_sdk.__version__ e openai.__version__.

### API-07 · Média · Correção · Confirmado
**Contrato estruturado frágil: 'eixo' livre, regra cruzada fora do JSON schema e nenhum tratamento de output_parsed=None. Qualquer falha aborta a execução inteira**

- **Onde:** CELL 19 (EixoLLM2Polos, RespostaLLM2Polos); CELL 17 (MaritacaClient.generate); CELL 22 (classificar); CELLs 27 e 37 (laços sem try/except)
- **Evidência:** Gerei o schema que o openai 3.24.0 envia, com openai.lib._parsing._responses.type_to_text_format_param(RespostaLLM2Polos). Ele vai com strict=true e usa $defs/$ref. Nele, 'eixo' é string livre, 'relevante' é anyOf [boolean, null] e 'nivel' é anyOf [enum [0,1], null]. A regra 'relevante≠true ⇒ nivel=null' só existe no @model_validator. Testei: {'relevante': false, 'nivel': 0} passa no schema, mas RespostaLLM2Polos.model_validate_json lança ValidationError. Já {'eixo': 'estado', ...} passa no Pydantic e depois a CELL 22 lança ValueError('O LLM deve retornar exatamente os eixos encaminhados').
- **Impacto:** Uma única resposta fora do contrato derruba o benchmark ou a análise do documento e descarta todas as chamadas anteriores, que estão só em memória (API-05).
- **Recomendação:** Usar um schema com uma propriedade obrigatória por eixo encaminhado (create_model), o que torna o conjunto de eixos estrutural, e um único campo enum 'decisao' que só admite estados válidos. Pedir a evidência antes da decisão. Em caso de erro, manter a decisão do JEV com status 'erro_llm' e seguir para o próximo texto.

### API-08 · Média · Melhoria · Parcial (corrigido na verificação)
**O fallback reabre a relevância mesmo quando o eixo foi encaminhado só pela polaridade, e pode descartar uma relevância confiante do JEV**

- **Onde:** CELL 22 (CascataJevLLM2Polos._motivos e classificar: finais[item.eixo] substitui também 'relevante')
- **Enunciado corrigido:** O fallback reabre a relevância também nos eixos encaminhados só por incerteza de polaridade. Isso mistura duas decisões e, sem registro, não se sabe se essa reabertura produziu correções (falsos positivos de relevância do JEV) ou pioras.
- **Impacto:** Mistura duas decisões, relevância e direção, numa só reavaliação. Isso pode reduzir a cobertura e criar pioras não atribuíveis ao motivo do encaminhamento.
- **Recomendação (ajustada):** Não travar a relevância a priori. Registrar 'relevancia_reaberta' (o LLM mudou a relevância de um eixo encaminhado só por polaridade) e tabular corrigidos e piorados por tipo de motivo. Rodar uma ablação com as duas variantes, reabrindo ou não a relevância, sobre as mesmas respostas do JEV (cache de API-05) e escolher pela evidência.

### API-09 · Média · Melhoria · Confirmado
**Prompt do fallback: regras e dados no mesmo 'input', rótulos A/B sobrecarregados, mapeamento posicional invertido (0 = polo B), instrução contraditória herdada e ordem fixa dos polos**

- **Onde:** CELL 22 (classificar: montagem do prompt; __init__: self.rubricas); CELL 13 (criar_questoes_eixo: chaves 'A'/'B' da relevância)
- **Evidência:** A CELL 22 concatena regras e JSON num único 'input', embora a Responses API da Maritaca tenha o parâmetro próprio 'instructions' (https://docs.maritaca.ai/api/pt/responses-api). No modo choice, a rubrica de relevância enviada ao LLM usa as chaves 'A' ('Sim...') e 'B' ('Não...') (CELL 13), enquanto a polaridade usa 'polo A'/'polo B', e o mapeamento é posicional: nivel=0 é o primeiro critério, o polo B. A rubrica 'posicao' herda a instrução do Score do JEV ('Posicione a posição defendida pelo texto entre os dois polos'), mas o mesmo prompt diz 'Não existe um nível intermediário'. A ordem dos polos é sempre B e depois A, então o viés de posição não é controlado.
- **Impacto:** Aumenta o risco de troca de polo, por confusão de rótulos ou índices, e de viés de posição. Também enfraquece a separação entre instrução e dado diante de textos persuasivos.
- **Recomendação:** Mover as regras fixas para 'instructions' e enviar só o JSON em 'input'. Dar rótulos explícitos a cada polo na rubrica (ou usar os nomes dos polos), embaralhar a ordem a cada chamada com semente fixa e remover 'entre os dois polos' da rubrica do LLM. Pedir a evidência antes da decisão (API-07).

### API-10 · Média · Melhoria · Confirmado
**service_tier 'flex': não confirmado na Responses API, fila de até 5 min antes de devolver 429 e timeout padrão de 600 s. A latência relatada mistura fila e inferência**

- **Onde:** CELL 17 (MaritacaClient.__init__ e generate: AsyncOpenAI sem timeout/max_retries; extra_body={'service_tier': 'flex'}); CELLs 31-32 (latências)
- **Evidência:** A página do Flex Tier (https://docs.maritaca.ai/pt/flex-tier) informa 50% de desconto. Sem capacidade imediata, a requisição espera numa fila por até 5 min e depois recebe HTTP 429; com a fila cheia, o 429 é imediato. A página recomenda retry com backoff. O exemplo de lá usa chat.completions, e a referência da Responses API não lista service_tier no corpo nem na resposta (https://docs.maritaca.ai/api/pt/responses-api), logo não está confirmado que o flex se aplique em responses.parse. O AsyncOpenAI é criado sem timeout nem max_retries, então valem os padrões do openai 3.24.0: timeout de 600 s (connect 5 s) e 2 retries (openai/_constants.py, DEFAULT_TIMEOUT e DEFAULT_MAX_RETRIES).
- **Impacto:** A comparação de latência JEV×LLM no TCC pode refletir a fila e não o modelo. O custo e o tier efetivamente aplicado não são verificáveis, e uma chamada pode ficar bloqueada por mais de 10 minutos.
- **Recomendação:** Definir timeout explícito (pelo menos 360 s se usar flex) e max_retries. Registrar response.service_tier (o objeto Response do SDK tem esse campo), usage, id, status e latência. Para comparar latências, rodar uma amostra no tier padrão. Informar o tier na metodologia.

### API-11 · Média · Melhoria · Confirmado
**A faixa de encaminhamento da relevância é estreita (P de 0,40 a 0,60), mas a relevância está em pelo menos 60 das 68 falhas do JEV**

- **Onde:** CELL 5 (margem_relevancia_minima=0.20); CELL 22 (_motivos)
- **Evidência:** Saídas da CELL 31: acurácia de relevância do JEV de 0,8429 (diplomatic), 0,9000 (economic), 0,7286 (society) e 0,6714 (state), ou seja, 11 + 7 + 19 + 23 = 60 erros de relevância. Falhas conjuntas do JEV: 280 − 212 = 68, então pelo menos 60 delas (88%) têm erro de relevância. Na cascata, sobram 51 erros de relevância entre as 59 falhas. A margem < 0,20 só encaminha P(relevante) entre 0,40 e 0,60, enquanto a polaridade encaminha P(A) entre 0,15 e 0,85 (API-02). Exemplo: Q1/economic (efeito +10) teve P(relevante) = 0,29 (margem 0,42), não foi encaminhada e errou.
- **Impacto:** O orçamento do fallback vai para a dimensão que menos erra. Além disso, se os limiares forem ajustados nas mesmas 70 perguntas usadas como teste, a acurácia relatada fica otimista (circularidade).
- **Recomendação (ajustada):** Usar tcc/d0_manual_validation_avaliado.csv (colunas chunk_id, text, economic, diplomatic, state, society; positivos 16/4/15/7) sabendo de duas diferenças. Os chunks do d0 são bem menores: 335 caracteres em média, contra cerca de 1.987 caracteres por chunk de 600 tokens no plano analisado (166.922/84), e vêm de outro documento. Como a prevalência de relevância cresce com o tamanho do chunk, o limiar calibrado no d0 não se transfere diretamente. Convém anotar uma amostra com o mesmo chunking do pipeline, ou reportar o d0 como validação de domínio com tamanho diferente. Com poucos positivos (diplomatic tem 4), juntar os eixos na curva risco × cobertura ou reportar IC por bootstrap.

### API-12 · Média · Melhoria · Parcial (corrigido na verificação)
**Relevância: rótulos 'A'/'B' sem significado, 'Sim' sempre como primeira opção (viés de ordem documentado no jev-1.13) e variante Noul sem critérios, o que confunde a comparação Choice × Noul**

- **Onde:** CELL 13 (criar_questoes_eixo); CELL 20 (criar_perguntas_jev_2_polos: Noul(instructions=...) sem criteria); CELL 22 (__init__: no modo noul, self.rubricas só com instructions; default tipo_relevancia='noul')
- **Enunciado corrigido:** A Choice de relevância sempre apresenta 'Sim' como primeira opção, e o jev-1.13 tem viés documentado para a primeira opção. Como a relevância concentra a maior parte dos erros, falta contrabalançar a ordem. Se o TCC comparar Choice com Noul (bloco do TCC.ipynb), a comparação também deve igualar a informação dada ao modelo, com uma variante Noul com critérios.
- **Impacto:** A comparação Choice × Noul muda ao mesmo tempo a primitiva e a informação dada ao modelo. O viés de ordem pode inflar 'Sim' de forma sistemática.
- **Recomendação:** Usar rótulos semânticos ('relevante'/'irrelevante') e contrabalançar a ordem na mesma chamada, tirando a média das duas probabilidades e registrando |p1−p2| como sensibilidade à ordem. Criar a variante 'noul_criterios', com as mesmas descrições da Choice, para uma comparação justa. Ajustar _decisao_jev aos novos rótulos e alinhar os padrões de tipo_relevancia.

### API-13 · Média · Nova ideia · Confirmado
**Experimento de idioma: o JEV foi treinado sobretudo em inglês, e todo o pipeline (instruções, critérios e state) está em português**

- **Onde:** CELL 13 (criar_questoes_eixo); CELL 14 (TEXTOS_EIXOS_2); CELL 20 (criar_perguntas_jev_2_polos); CELL 9 (questions.json traduzido)
- **Evidência:** https://docs.typesafe.ai/models (seção de idiomas) e https://docs.typesafe.ai/concepts/state informam que o inglês é a principal língua de treino, com a melhor acurácia. Outras línguas são aceitas, porém com acurácia menor, e a recomendação é testar no próprio conteúdo e acompanhar a confiança ao rotear. No notebook, instruções, critérios e state estão em português, e as 70 afirmações são tradução do 8Values, que é originalmente em inglês.
- **Impacto:** Parte dos erros do JEV (por exemplo, a relevância em state e society) pode vir do idioma e não das rubricas. Sem um experimento, o TCC não consegue separar as duas causas.
- **Recomendação:** Fazer um experimento 2×2 no benchmark: instruções e critérios em PT ou EN × state em PT ou EN (afirmações originais do 8Values, disponíveis no repositório público 8values.github.io). Nos planos de governo, variar só instruções e critérios, mantendo o state em PT. Comparar acurácia, confiança média e taxa de encaminhamento, sem fallback, para isolar o efeito do JEV.

### API-15 · Média · Nova ideia · Parcial (corrigido na verificação)
**Testar um Score com 3 a 5 níveis ordenados para estimar intensidade, validável com as magnitudes 2/5/10 do 8Values**

- **Onde:** CELL 12 (decisão de 2 níveis); CELL 20 (criar_perguntas_jev_2_polos, _normalizar_polaridade_score_2_polos)
- **Enunciado corrigido:** Testar um Score com 3 a 5 níveis espelhados para obter uma escala ordinal de posição é viável. As magnitudes 2/5/10 do 8Values, porém, indicam o peso do eixo na afirmação e não a intensidade da posição, e não servem como gabarito de intensidade.
- **Impacto:** Hoje o TCC não tem como medir intensidade e acaba usando P(polo A) no lugar dela (API-01). Uma escala ordinal validada daria sustentação a comparações de intensidade.
- **Recomendação (ajustada):** Validar a escala ordinal com uma amostra de trechos anotados por humanos numa escala de 5 pontos (2 anotadores, kappa ponderado), com Spearman entre o nível previsto (round(score)) e a anotação. No benchmark, usar as magnitudes só como verificação secundária e declarar a limitação. Manter a advertência 'Math using score': tratar o resultado como ordinal, nunca interpolar.

### API-16 · Média · Nova ideia · Parcial (corrigido na verificação)
**Teste contrafactual de autodescrição: o jev-1.13 é sensível a textos que argumentam pela própria classificação, como costumam fazer os planos de governo**

- **Onde:** CELL 20 (instrução do JevScore em criar_perguntas_jev_2_polos); CELL 14 (TEXTOS_EIXOS_2)
- **Enunciado corrigido:** O jev-1.13 pode ser sensível a textos que se autodescrevem com o vocabulário dos critérios. Vale testar essa sensibilidade, mas o mascaramento simples de termos confunde 'rótulo' com 'conteúdo'.
- **Impacto:** O índice pode refletir o vocabulário autodescritivo de cada documento, e não as medidas propostas. Isso afeta a neutralidade se os documentos usarem esse vocabulário de modo desigual.
- **Recomendação (ajustada):** (a) Manter o acréscimo à instrução, como variante comparada no benchmark e não como troca silenciosa. (b) No teste de sensibilidade, mascarar só expressões avaliativas ou autodescritivas (adjetivos e slogans), definidas a priori com o mesmo número de termos por polo e por eixo. Incluir uma condição de controle que mascara o mesmo número de palavras neutras aleatórias e reportar ΔP(A) líquido do controle, só em estatísticas agregadas sobre os 12 planos.

### API-V02 · Média · Melhoria · Acrescentado na verificação
**A polaridade usa um Score de 2 níveis sem opção 'sem posição': a documentação recomenda Choice quando não há intermediário, e a Choice A/B/C já definida na CELL 13 não é usada**

- **Onde:** CELL 13 (criar_questoes_eixo: 'polaridade' com A/B/C, descartada como '_'); CELL 20 (criar_perguntas_jev_2_polos); CELL 22 (__init__: relevancia, _ = ...)
- **Evidência:** A página do Score (https://docs.typesafe.ai/primitives/score, lida e conferida) diz: 'If there is no in-between at all, and the answer is one of a few discrete categories, use a Choice instead, or split the question into several Noul questions.' O notebook declara que não há nível intermediário (CELL 12: 'Não existe um terceiro nível'; prompt da CELL 22: 'Não existe um nível intermediário'). Com 2 níveis, P(A)+P(B)=1 e o modelo é forçado a escolher uma direção mesmo sem posição no texto. A saída da CELL 31 mostra isso: Q1/society tem relevância JEV 0,11 (irrelevante) e mesmo assim Score {0:0,02; 1:0,98}, com confiança 0,96.
- **Impacto:** Em trechos relevantes, mas descritivos ou equilibrados, o JEV é obrigado a atribuir um polo. Isso pode inflar a cobertura e empurrar os índices para os extremos, o que é compatível com a saturação discutida em API-06, e mistura 'ausência de posição' com 'posição'.
- **Recomendação:** Rodar no benchmark (sem fallback) uma variante de polaridade com Choice de 3 opções e rótulos semânticos, {'polo_B', 'polo_A', 'sem_posicao'}, com as mesmas descrições espelhadas e a ordem dos polos contrabalançada (viés de primeira opção do jev-1.13). Comparar com o Score de 2 níveis em acurácia de direção, taxa de abstenção e cobertura no documento. Manter o Score só se o desempenho for igual ou melhor.

### API-02 · Baixa · Correção · Confirmado
**No Score de 2 níveis, confidence = margem = |2·P(A)−1|: confianca_score_minima e margem_score_minima são o mesmo critério e os motivos de fallback se repetem**

- **Onde:** CELL 5 (CONFIG_JEV_LLM_2_POLOS); CELL 22 (CascataJevLLM2Polos._motivos e _decisao_jev); markdown da CELL 21
- **Evidência:** Fórmula oficial do Score (https://docs.typesafe.ai/confidence): conf = max(0, 1 − Σ p_i·|i−m| / MAD_unif), com MAD_unif = (1/n)·Σ|i−(n−1)/2|. Com n=2, MAD_unif = 0,5 e Σ p_i·|i−m| = 1−p_max, portanto conf = 2·p_max−1 = |p1−p0| = margem. Conferi numericamente: P(A) = 0,61 → 0,22; 0,85 → 0,70; 0,96 → 0,92; 0,99 → 0,98, com valores iguais pela fórmula e pela margem. As saídas salvas batem: CELL 41 (0,30/0,30; 0,84/0,84; 0,64/0,64; 0,24/0,24; 0,22/0,22; 0,96/0,96) e CELL 31 (0,92 com {0:0,04; 1:0,96}; 0,98 com {0:0,01; 1:0,99}). As diferenças de 0,01 (0,99/0,98; 0,97/0,98) são compatíveis com valores arredondados a 2 casas, observados nas saídas;
- **Impacto:** A metodologia descreve dois critérios independentes quando existe um só. As contagens por motivo ficam infladas, e numa análise de sensibilidade, variar margem_score_minima abaixo de 0,70 não produz efeito, o que pode levar a conclusões equivocadas.
- **Recomendação:** Usar um único parâmetro de polaridade (limiar sobre |2P−1|, ou diretamente sobre P(A)), tornar os motivos mutuamente exclusivos, documentar o intervalo efetivo de encaminhamento (P(A) entre 0,15 e 0,85) e incluir uma verificação automática de que confiança e margem coincidem.

### API-14 · Baixa · Nova ideia · Parcial (corrigido na verificação)
**Verificar com o próprio JEV se a citação do LLM sustenta o polo escolhido; hoje a checagem é só de substring e fica trivial no benchmark**

- **Onde:** CELL 20 (_score_evidencia_confere); CELL 22 (classificar: evidencia_verificada); CELL 31 (0 evidências não verificadas)
- **Enunciado corrigido:** A verificação de evidência só confere se a citação existe no texto. No benchmark isso é trivial, e uma citação literal que não sustenta o polo escolhido passa. Um verificador baseado no próprio JEV, porém, seria circular para os eixos encaminhados por incerteza do JEV.
- **Impacto:** Uma citação literal que não apoia o polo escolhido (por exemplo, um trecho que critica a posição) é aceita hoje. A métrica de evidência verificada superestima a qualidade do fallback.
- **Recomendação (ajustada):** (1) Usar o JEV apenas como diagnóstico, não como veto, e só com a citação no state ({'citacao': ...}), perguntando se ESSA frase expressa o polo. É uma pergunta mais estreita que a original. Reportar a taxa de discordância. (2) Fazer auditoria manual de uma amostra estratificada das decisões do LLM no documento (por exemplo, 30 casos com dupla anotação e kappa), algo viável num TCC e mais informativo sobre a qualidade do fallback.

### API-17 · Baixa · Melhoria · Parcial (corrigido na verificação)
**Ajustes menores de uso da API: state sem nome e termos inconsistentes, legenda do Score não conferida, laços sequenciais e clientes nunca fechados**

- **Onde:** CELL 22 (classificar: system_one(state=texto)); CELLs 13 e 20 ('o trecho' na relevância e 'o texto' no Score); CELLs 27 e 37 (laços sequenciais com pausa); CELL 24 (clientes)
- **Enunciado corrigido:** Os ajustes menores procedem (termo único nas instruções, fechamento dos clientes, concorrência opcional), mas a checagem de legenda proposta é quase redundante, e a concorrência precisa de limite próprio para o LLM.
- **Impacto:** Pequena perda de clareza para o modelo, risco silencioso de inverter polos se as rubricas mudarem, tempo de execução maior que o necessário e conexões deixadas abertas.
- **Recomendação (ajustada):** Trocar a checagem de legenda por um assert de consistência entre os mapeamentos: for e,(a,b) in MAPA_SCORE_CASCATA.items(): assert (POLOS_EIXOS_2[e]['A'], POLOS_EIXOS_2[e]['B']) == (a, b). Se houver concorrência, usar semáforos separados, até 4 para o JEV e 1 ou 2 para o LLM (ou um limitador de RPM). Fechar os clientes com await jev_client.aclose() e await llm.client.close().

## Objetivo do TCC, literatura e novas ideias (LIT)

### LIT-01 · Alta · Nova ideia · Parcial (corrigido na verificação)
**O notebook não implementa o objetivo declarado do TCC: alinhamento entre o texto e o perfil 8Values do usuário (e as escalas não são comensuráveis)**

- **Onde:** Notebook inteiro (seções 10–11; CELL 37 processar_documento_com_jev_2_polos; CELL 44). Arquivos não usados: tcc/lista_total.json, tcc/lista_individual.json, tcc/ideologies.json. Fórmula do usuário: TCC.ipynb CELL 25 (Quiz8Values.calc_score)
- **Enunciado corrigido:** O repositório não tem o componente de alinhamento usuário–documento, que é o objetivo geral do TCC. O notebook termina no índice do documento, e o TCC.ipynb só calcula a ideologia mais próxima. As escalas não são comensuráveis: o perfil 8Values do usuário é 100·(max+Σ mult·efeito)/(2·max) e vale 75,0 com 'concordo' em todas as afirmações no sentido A. O índice do documento é a média de P(A)×100 (definição do Score no SDK) misturada com valores 0/100 do LLM. Tentativas anteriores de 'questionário por procuração' (results.json) regrediram a 50.
- **Impacto:** Sem o componente de alinhamento, o TCC não responde à sua pergunta central. Uma distância simples entre o perfil do usuário e a média de P(A) compararia grandezas diferentes e produziria alinhamentos artificiais.
- **Recomendação (ajustada):** Antes de implementar, definir um estimando comum aos dois lados. Opção de baixo custo, por eixo: para o usuário, a proporção das respostas não neutras no sentido do polo A, ponderada por |efeito|, com a fração de neutras reportada como cobertura; para o documento, a proporção de trechos com posição no polo A (LIT-02), com cobertura e IC por bootstrap em blocos. Comparar direção e cobertura, nunca as magnitudes 0–100 diretamente. O questionário por procuração com 'não aborda' pode ser um segundo estimador, desde que seja validado contra anotação (LIT-06) e comparado com results.json, para verificar se a abstenção de fato elimina a regressão a 50.

### LIT-02 · Alta · Correção · Confirmado
**O gráfico aplica ao plano nomes de ideologias do 8Values ('Comunista', 'Patriota', 'Libertário', 'Revolucionário') a partir de um índice que não está na escala do questionário**

- **Onde:** CELL 43 (rotulo_8values), CELL 44 (grafico_scores_documento), CELL 11 (ECON_ARRAY…SCTY_ARRAY)
- **Evidência:** Apliquei rotulo_8values aos valores salvos da CELL 39 (economic 93,41; diplomatic 27,37; state 77,88; society 98,75). Resultado: 'Comunista', 'Patriota', 'Libertário' e 'Revolucionário', impressos sobre as barras do plano na CELL 44. Os limiares (>90, >75, >60, ≥40, ≥25, ≥10) são os do 8Values para pessoas que responderam ao questionário. Pela fórmula do 8Values, responder 'concordo' em todas as afirmações econômicas no sentido Igualdade dá 75,0; acima de 90 exige concordância forte com quase todas. Já o 93,4 do documento é a média de P(polo A) em 75 trechos.
- **Impacto:** A figura atribui a uma candidatura real um rótulo ideológico forte sem base de mensuração. Isso contraria a exigência de neutralidade do TCC e pode ser lido como juízo do sistema. O rótulo também esconde a heterogeneidade dos trechos (desvio padrão de 42,2 no eixo diplomático).
- **Recomendação (ajustada):** Remover rotulo_8values e as listas ECON_ARRAY…SCTY_ARRAY da apresentação de documentos. Exibir por eixo a proporção de trechos com posição no polo A, n, cobertura e IC95% por bootstrap em blocos móveis, com Wilson apenas como aproximação declarada. Usar os nomes neutros dos polos.

### LIT-03 · Alta · Correção · Confirmado
**'acuracia_polaridade' mistura falhas de relevância com erros de direção e não é comparável à polaridade do bloco original nem aos baselines**

- **Onde:** CELL 22 (_decisao_jev: classe='C' quando não relevante); CELL 26 (executar_benchmark_8values: 'C' conta como erro); CELL 31/32 (saídas). Comparação: TCC.ipynb CELL 308/311/312
- **Evidência:** Conferi por AST que AXIS_SPECS, TEXTOS_EIXOS_2 e POLOS_EIXOS_2 são idênticos aos de TCC.ipynb (CELL 251/308). NO BLOCO ORIGINAL, a direção do Score era avaliada sem condicionar à relevância: 0,875 (21/24) diplomática, 0,909 (20/22) econômica, 0,939 (31/33) social e 0,838 (31/37) Estado. Total: 103/116 = 88,8% (IC95% 82–93%). NO NOTEBOOK NOVO, o JEV com as mesmas perguntas mostra 0,583 / 0,591 / 0,818 / 0,378, embora a acurácia conjunta seja quase a mesma (212 contra 215/280). A causa está na CELL 22: quando o JEV diz 'irrelevante', classe='C', e a CELL 26 conta isso como erro de polaridade. A métrica mede, portanto, P(relevância detectada E polo correto | esperado relevante). CONSEQUÊNCIA.
- **Impacto:** Afirmações como 'o eixo Estado tem polaridade fraca (0,38–0,41)' ficam erradas. Também ficam inválidas as comparações com o baseline de embeddings (polaridade 72,4%, TCC.ipynb CELL 209) e com a literatura. E fica oculto onde a cascata realmente ajuda: na relevância ou na direção.
- **Recomendação (ajustada):** Como proposto. Observação: os 88,8% de direção bruta vêm da execução antiga (TCC.ipynb). Para a execução atual, recalcular a partir de registros[...]['eixos_jev'][e]['score_nativo'] com decompor().

### LIT-04 · Alta · Melhoria · Confirmado
**Faltam baselines no mesmo protocolo (trivial, polo majoritário, embeddings, NLI); vários já existem no TCC.ipynb e não foram trazidos**

- **Onde:** CELL 26/27/31 (benchmark). TCC.ipynb: CELL 177–180 (NLI), CELL 209 (embeddings), CELL 247 (síntese), CELL 385/390 (Laya)
- **Evidência:** TRIVIAL. Calculei a partir de tcc/questions.json: 164 dos 280 pares têm efeito zero, então a regra 'tudo irrelevante' acerta 58,6% (IC95% 52,7–64,2%) da métrica conjunta. Por eixo: 68,6% econômico, 65,7% diplomático, 47,1% Estado, 52,9% social. O notebook não mostra esses números ao lado de 75,7% e 78,9%. JÁ EXISTENTES NO TCC.ipynb: - o melhor pipeline de embeddings (text-embedding-3-large com múltiplos protótipos, CELL 209) teve relevância 68,9% (BA 66,4%, MCC 0,345) e polaridade 72,4% (BA 72,7%, MCC 0,461) nas mesmas perguntas, com limiar escolhido por validação cruzada; - o NLI mDeBERTa-v3-base-mnli-xnli foi carregado (CELL 177) mas testado em uma única frase (CELL 180);
- **Impacto:** Sem comparadores, 78,9% parece alto, mas está cerca de 20 pontos acima de uma regra constante. Não dá para dizer quanto do resultado vem do JEV, do LLM ou da rubrica.
- **Recomendação (ajustada):** Como proposto, com três ajustes. (1) Nas hipóteses de polaridade do NLI, usar os mesmos textos de polo do JEV e do LLM (TEXTOS_EIXOS_2, resumidos), não AXIS_SPECS['a'/'b']. (2) Escolher limiares por validação cruzada agrupada por pergunta. Note que a CELL 209 usou StratifiedKFold sem agrupamento. (3) Reportar BA e MCC e a decomposição de LIT-03 para todos os comparadores.

### LIT-06 · Alta · Melhoria · Confirmado
**Validar em planos de governo com anotação humana (dois anotadores e concordância); o CSV de validação manual existente não é usado**

- **Onde:** CELL 6 (escopo do benchmark), CELL 35/37/39 (índice sem gabarito); tcc/d0_manual_validation_avaliado.csv; TCC.ipynb CELL 228–247
- **Evidência:** O ÚNICO TESTE quantitativo usa as 70 afirmações do 8Values, curtas e em 1ª pessoa. O documento não tem gabarito. O CSV d0_manual_validation_avaliado.csv tem 66 trechos de cerca de 335 caracteres do plano de Clariana Barão (DC). Os rótulos são só de relevância (positivos: 16 econômico, 4 diplomático, 15 Estado, 7 social; 30 trechos sem nenhum eixo), sem polaridade e sem segundo anotador. Com 4 positivos diplomáticos, um recall de 3/4 teria IC95% de 30% a 95%. O TCC.ipynb já tem infraestrutura de rótulos (152 pares trecho–eixo em 12 candidaturas, a maioria assistida por IA), GroupKFold por candidatura e fila de revisão por incerteza (CELL 241).
- **Impacto:** Sem gabarito em planos, nenhuma afirmação sobre a qualidade dos índices dos documentos se sustenta, e portanto nem sobre o alinhamento com o usuário. O benchmark de afirmações não garante transferência para planos.
- **Recomendação:** (1) Piloto imediato: rodar a cascata nos 66 trechos do CSV (66 chamadas JEV) e reportar recall e especificidade de relevância por eixo, com IC. (2) Protocolo principal: - amostra estratificada de cerca de 120 trechos dos 12 planos, com estratos pela decisão do sistema para garantir positivos de diplomacia e Estado; - nomes de candidatos e partidos mascarados; - manual de codificação derivado de AXIS_SPECS e TEXTOS_EIXOS_2, com a regra 'posição defendida × apenas citada ou criticada'; - rótulos de relevância e de polo (A, B ou indeterminado). (3) Dois anotadores em pelo menos 30% dos trechos; reportar alfa de Krippendorff ou kappa e usar a concordância humana como teto, como em Benoit et al.

### LIT-09 · Alta · Nova ideia · Confirmado
**Testes de simetria e invariância para sustentar a neutralidade: recall por polo, pares espelhados e anonimização da candidatura**

- **Onde:** CELL 20 (instrução do Score), CELL 22 (prompt do LLM), CELL 27/31 (só métricas agregadas); TCC.ipynb CELL 212–217 (suíte CheckList)
- **Evidência:** NO NOTEBOOK. O prompt do JEV proíbe deduzir a posição pela identidade do autor (CELL 20), mas isso não é testado. Contei 23 dos 84 trechos do plano analisado contendo 'Lula', 'PT' ou 'Partido dos Trabalhadores'. O notebook só reporta acurácias agregadas: não há recall por polo nem análise do sentido das correções do LLM. A suíte CheckList de 24 casos do TCC.ipynb (21/24 aprovados com embeddings) não foi aplicada à cascata. LITERATURA LIDA: - Haroon et al.: informar a fonte desloca a classificação do LLM para a ideologia conhecida da fonte, inclusive em conteúdo não político;
- **Impacto:** Um viés direcional do JEV ou do Sabiá, sobretudo nos casos ambíguos encaminhados ao LLM, apareceria como diferença entre candidaturas. Sem esses testes, o TCC não demonstra a neutralidade que exige.
- **Recomendação (ajustada):** Aplicar o mascaramento e a troca de nomes de forma simétrica aos 12 planos, com uma lista de identificadores de todas as candidaturas e partidos (próprios e citados). Reportar a taxa de mudança de decisão por plano em ordem fixa. Recall por polo e pares espelhados como proposto, revisados com o orientador.

### LIT-05 · Média · Nova ideia · Confirmado
**Rodar o LLM sozinho uma vez dá o baseline 'LLM em tudo' e permite simular offline toda a fronteira custo×qualidade do roteamento**

- **Onde:** CELL 4/5 (limiares fixos), CELL 22 (_motivos), CELL 27/31 (desempenho)
- **Evidência:** LIMIARES SEM SELEÇÃO. A CELL 4 descreve os limiares (confiança 0,70; margem do Score 0,20; margem de relevância 0,20) como parâmetros a selecionar na validação, mas nenhuma seleção é feita. RESPOSTAS PARCIAIS DO LLM. Ele só responde nos eixos encaminhados: 31 eixos em 26 chamadas. Não se sabe o que faria nos outros 249 pares. CUSTOS OBSERVADOS. Cerca de 0,29 s por chamada JEV (20,18 s/70) e 3,57 s por chamada ao Sabiá (92,72 s/26). No documento, 46 chamadas ao LLM para 84 trechos. PERGUNTA SEM COMPARADOR. A pergunta sugerida na ANALISE_PIPELINE_JEV_LLM.md (seção 8) é se a cascata mantém a qualidade com menos custo que um LLM aplicado a tudo. Sem o braço 'LLM sozinho', ela não tem resposta.
- **Impacto:** A conclusão 'a cascata melhora com custo controlado' fica sem comparador. Os limiares atuais podem estar longe do ótimo, e escolhê-los olhando o conjunto de teste infla o resultado.
- **Recomendação (ajustada):** Como proposto. Escolher o ponto de operação por validação cruzada agrupada por pergunta e confirmá-lo nos trechos anotados (LIT-06), porque as 70 afirmações já foram muito reutilizadas (LIT-07).

### LIT-07 · Média · Melhoria · Confirmado
**O ganho da cascata (212→221/280) precisa de inferência por pergunta; o mesmo benchmark já foi usado ao menos 24 vezes para escolher configurações**

- **Onde:** CELL 27 (comparacao), CELL 32 (impressão de acertos); TCC.ipynb CELL 279–390
- **Evidência:** INTERVALOS. Calculei IC95% de Wilson: JEV 212/280 = 75,7% [70,4; 80,4]; cascata 221/280 = 78,9% [73,8; 83,3]. McNEMAR. O teste exato sobre os pares (11 corrigidos × 2 piorados) dá p=0,022, mas supõe pares independentes. Isso não vale: os 280 pares vêm de 70 perguntas, e 36 delas têm efeito não nulo em dois ou mais eixos (29 com 2, 4 com 3, 3 com 4). REUSO DO CONJUNTO. Contei 24 resultados '/280' salvos no TCC.ipynb (de 162 a 225), incluindo a varredura de 9 limiares Noul (CELL 318), todos nas mesmas 70 perguntas, além das 2 execuções do notebook novo. LITERATURA. Benoit et al. reportam IC e um teto de concordância; Haroon et al. mostram IC95% nas figuras.
- **Impacto:** O ganho de 3,2 pontos pode estar dentro da variação causada pela escolha de configuração e da variação entre execuções (LIT-08). Relatá-lo como definitivo enfraquece a defesa.
- **Recomendação:** Reportar a diferença pareada com bootstrap por pergunta (reamostrar perguntas, não pares) e um teste de permutação pareado por pergunta. Tratar as 70 perguntas como conjunto de desenvolvimento e declarar quantas configurações foram comparadas. Confirmar o efeito no conjunto anotado de planos (LIT-06), com protocolo definido antes da avaliação (LIT-22).

### LIT-08 · Média · Melhoria · Confirmado
**Resultados variam entre execuções com rubricas idênticas, e faltam controles de reprodutibilidade (temperatura, versão do modelo, cache em disco)**

- **Onde:** CELL 17 (MaritacaClient.generate), CELL 22 (classificar), CELL 29/39; comparação com TCC.ipynb CELL 308/311
- **Evidência:** VARIAÇÃO OBSERVADA. Com rubricas idênticas (conferidas por AST), o JEV sozinho deu 215/280 no TCC.ipynb (CELL 311) e 212/280 no notebook novo. Por eixo: acertos conjuntos econômicos 62→60 e sociais 51→50; relevância social 52→51. Ou há não determinismo, ou a versão do modelo mudou: o notebook novo registra 'jev-1.13.0', a execução antiga não registrava. A variação de 3 pares equivale a um terço do ganho da cascata (+9). AUSÊNCIA DE CONTROLES. A chamada ao Sabiá (CELL 17) não fixa temperatura nem semente, e nada é gravado em disco (não há to_json nem JSONL no notebook). REFERÊNCIA. Benoit et al. usam temperatura zero, top-p 1 e semente quando disponível;
- **Impacto:** Sem repetições não se separa melhoria real de ruído. Sem cache, reexecutar o notebook muda os números do TCC e impede auditoria.
- **Recomendação:** (1) Fixar temperature=0 e semente, se a API da Maritaca aceitar (verificar na documentação), e registrar o modelo devolvido em cada resposta. (2) Repetir o benchmark três vezes (cerca de 210 chamadas JEV) e reportar a concordância entre execuções por eixo e a variação das acurácias. (3) Gravar respostas brutas e decisões em JSONL, com run_id, hash das rubricas e configuração; gerar tabelas e gráficos a partir desses arquivos. (4) Versionar os rótulos e os dados necessários para reproduzir.

### LIT-10 · Média · Melhoria · Parcial (corrigido na verificação)
**O eixo social provavelmente está saturado por temas de valência (educação, ciência, meio ambiente) incluídos no polo Progresso**

- **Onde:** CELL 13 (AXIS_SPECS['society']: 'topic' e polo 'a'), CELL 14 (TEXTOS_EIXOS_2['society']), CELL 39 (resultado)
- **Enunciado corrigido:** O eixo social pode ter pouca capacidade de discriminar planos: 72/84 trechos relevantes com P(A) próximo de 1 (dp 1,75). O principal mecanismo provável é o tópico de relevância, que inclui ciência, tecnologia, educação e meio ambiente, combinado com um Score binário que força uma escolha entre Tradição e Progresso. O próprio 8Values codifica meio ambiente, ciência e educação como Progresso, então a saturação vem em parte do construto do instrumento, não de um erro de rubrica.
- **Impacto:** O eixo pode estar medindo a presença do tema, e não uma posição. Nesse caso, todos os planos tenderiam a ficar perto de 100, e o eixo seria inútil para comparar candidaturas e para o alinhamento com o usuário. É uma hipótese a confirmar rodando os 12 planos.
- **Recomendação (ajustada):** Manter a codificação do 8Values, por comparabilidade com o benchmark e com o perfil do usuário. Marcar cada trecho social como 'tema de valência' ou 'posição contestada' (normas sociais, religião, família, sexualidade) e reportar o índice com e sem os trechos só de valência. Medir a variância entre os 12 planos (LIT-11). Incluir na CheckList casos de 'tema sem posição'. Se a variância for quase nula, declarar o eixo pouco discriminante para planos, em vez de alterar o construto.

### LIT-11 · Média · Nova ideia · Confirmado
**Aplicar o mesmo procedimento aos 12 planos, com persistência e incerteza por bootstrap; uma única candidatura não permite comparar nem validar**

- **Onde:** CELL 10 e CELL 34 (só um plano), CELL 37 (desvio padrão como única medida de dispersão), CELL 39
- **Evidência:** ESCOPO ATUAL. O notebook seleciona apenas 'Lula (PT)'. O arquivo tcc/textos_candidatos.json tem 12 planos. Com o mesmo splitter da CELL 36 (600 tokens, sem sobreposição), contei 828 trechos, de 8 a 156 por plano. Se a taxa de encaminhamento for a do plano analisado (46/84), seriam cerca de 453 chamadas ao LLM. LITERATURA. Benoit et al. e Slapin & Proksch validam posições sempre num conjunto de documentos, por ordenação relativa. INCERTEZA. O TCC.ipynb (CELL 236) já implementa bootstrap em blocos móveis com 2.000 réplicas; o notebook novo só reporta desvio padrão, que ele mesmo diz não ser IC. GÊNERO TEXTUAL.
- **Impacto:** Com um único documento não dá para ver se o método discrimina candidaturas, se há saturação (LIT-10), nem validar ordenações (LIT-17). Além disso, o usuário do sistema precisa comparar vários planos.
- **Recomendação:** Rodar a cascata nos 12 planos com a mesma configuração, gravando cada trecho em JSONL assim que processado, para poder retomar após falhas. Para cada plano e eixo, reportar cobertura, número de trechos com posição e proporção no polo A, com IC por bootstrap em blocos. Apresentar os planos em ordem fixa (alfabética), com o mesmo tratamento visual e sem comentários sobre as candidaturas.

### LIT-13 · Média · Nova ideia · Confirmado
**O 'score' é a probabilidade de direção (P(polo A)), não intensidade: testar uma escala com âncoras em 5–7 níveis e um resumo por eixo, como em Benoit et al.**

- **Onde:** CELL 20 (_normalizar_polaridade_score_2_polos: score_8values = score×100), CELL 22 (LLM: nivel 0/1 → 0/100), CELL 37 (média mista), CELL 41 (saídas)
- **Evidência:** O SCORE É P(A). Nas 10 linhas visíveis da CELL 41, a confiança do Score coincide com a margem: 0,30/0,30; 0,84/0,84; 0,64/0,64; 0,24/0,24; 0,99/0,98; 1,00/1,00; 0,97/0,98; 0,97/0,98; 0,22/0,22; 0,96/0,96. E o score é P(A): 61 corresponde a margem 0,22, ou seja, P(A)=0,61. Nas 10 linhas visíveis de TCC.ipynb CELL 308, 'score jev' é igual a 'probabilidade A' em todas. MISTURA DE ESCALAS. O índice do documento soma esse P(A)×100 com os 0/100 do LLM (CELL 37). LITERATURA. Benoit et al. relatam que um protótipo com a escala CHES de 11 pontos e duas âncoras (uma em cada ponta) deu resultados sistematicamente piores que escalas de 7 pontos com âncora em cada ponto (nota 13).
- **Impacto:** Médias de P(A) acabam lidas como 'quão à esquerda ou à direita' o plano está, o que é uma interpretação inválida. A mistura com 0/100 do LLM também puxa o índice para os extremos.
- **Recomendação (ajustada):** Reaproveitar NIVEIS_SCORE de TCC.ipynb CELL 299 (5 níveis ancorados, já com resultado no benchmark) como rubrica ordinal comum a JEV e LLM, em vez de escrever uma nova. Validar a intensidade com a escada de textos graduados (Spearman), porque o benchmark 8Values mede só relevância e direção.

### LIT-14 · Média · Nova ideia · Confirmado
**Ensemble de LLMs (Sabiá, GPT, Claude, Gemini via OpenRouter) com a discordância usada como incerteza e critério de abstenção**

- **Onde:** CELL 5 (MODELO_LLM = 'sabia-4'), CELL 17 (LLMClient/MaritacaClient), CELL 22; .env.example
- **Evidência:** ESTADO ATUAL. O notebook usa um único LLM. O .env.example já prevê chaves de OpenAI, Claude, Google e OpenRouter. As reuniões de 11/08 e 18/08 registradas no docx pedem testar GPT e Claude e 'modelos mais caros para ver se tem menos variação'. LITERATURA LIDA: - Benoit et al. usam um ensemble 3×3 (três LLMs para resumir × três para pontuar, em zero-shot e few-shot: 18 escores por manifesto e dimensão) e obtêm correlações de 0,87 a 0,92 com especialistas na maioria das dimensões; - no mesmo trabalho, a taxa de 'NA' variou bastante entre modelos (GPT 9% contra Claude 21% em média), ou seja, a escolha do modelo muda a cobertura;
- **Impacto:** Com um único LLM, o resultado herda as particularidades desse modelo (cobertura, viés direcional) e não há como medir a confiabilidade entre modelos.
- **Recomendação:** Usar a abstração LLMClient para rodar 2 ou 3 LLMs nos eixos encaminhados, ou em todos, num subconjunto. Reportar o alfa de Krippendorff entre modelos por eixo. Decidir por consenso e abster-se, ou mandar para revisão humana, quando houver desacordo. Comparar custo e cobertura por modelo. A discordância também pode servir de sinal de roteamento.

### LIT-15 · Média · Nova ideia · Confirmado
**Análise de erros tipificada: magnitude do efeito, afirmações com vários eixos e tipo de falha**

- **Onde:** CELL 26 (esperado_pelo_efeito: sinal define o gabarito, magnitude ignorada), CELL 31 (saídas); tcc/questions.json
- **Evidência:** EFEITOS SECUNDÁRIOS. Pelo tcc/questions.json, entre os pares relevantes há efeitos de magnitude 5: 5 de 22 no eixo econômico, 3 de 24 no diplomático, 10 de 37 no Estado e 6 de 33 no social (mais 1 de magnitude 2). AFIRMAÇÕES COM VÁRIOS EIXOS. 36 das 70 têm efeito em dois ou mais eixos; 3 têm nos quatro. Exemplos nas saídas: - Q70 tem −10 em todos os eixos e foi prevista irrelevante nos quatro (CELL 31, linhas 276–279); - Q1 (opressão por corporações × por governos) tem −5 em 'govt' e foi classificada no polo A (Liberdade), uma leitura semântica plausível que diverge da codificação secundária do instrumento.
- **Impacto:** Sem tipologia de erros, não se sabe se as falhas do eixo Estado são do modelo, da rubrica ou da forma como o instrumento codifica efeitos secundários. O texto do TCC pode atribuir ao modelo erros que são da referência.
- **Recomendação:** Classificar cada erro como: falso relevante, relevante não detectado, direção trocada ou abstenção. Cruzar com eixo, |efeito| e número de eixos da afirmação. Revisar manualmente todos os erros do eixo Estado com um mini-manual ('efeito secundário', 'leitura alternativa plausível', 'erro do modelo'). Reportar uma análise de sensibilidade excluindo |efeito| < 10.

### LIT-16 · Média · Melhoria · Confirmado
**Unidade de análise: janelas de 600 tokens misturam propostas, diagnósticos e balanço de gestão; testar parágrafo ou proposta e marcar o gênero do trecho**

- **Onde:** CELL 5 (CONFIG_CHUNKS), CELL 36 (dividir_texto_em_chunks_tokens), CELL 37 (peso igual por trecho)
- **Evidência:** ESTADO ATUAL. Há uma única configuração (600 tokens). O TCC.ipynb (CELL 370) chegou a rodar 600, 800 e 1000 tokens, mas sem comparação reportada. LITERATURA. Carvalho et al. identificaram propostas por critérios linguísticos (como verbos no infinitivo), classificaram cada uma com justificativa e revisão de especialistas, e normalizaram as contagens pelo número de propostas de cada plano. TESTE DA HEURÍSTICA. Apliquei um detector simples de linhas iniciadas por verbo no infinitivo aos 12 planos: encontrou de 0 a 501 unidades por plano (PCB 0, DC 1, PSD 501, NOVO 269). Os formatos variam demais para essa heurística. Já parágrafos são mais uniformes (99 a 2.222 por plano).
- **Impacto:** Trechos de balanço de gestão podem ser lidos como posições, e janelas longas misturam várias propostas. Isso afeta de forma desigual planos de candidaturas no governo e na oposição, um problema de mensuração, não de conteúdo político.
- **Recomendação:** Segmentar por parágrafo, mantendo o título da seção como contexto e subdividindo parágrafos longos. Acrescentar o campo 'tipo de trecho' (proposta, diagnóstico, balanço de gestão, institucional), atribuído por LLM ou por regras e auditado numa amostra. Reportar o índice só com propostas e com todos os trechos. Fazer análise de sensibilidade com 300, 600 e 1000 tokens e com parágrafo, e ponderar por unidade.

### LIT-21 · Média · Nova ideia · Confirmado
**Interface que mostra as evidências por eixo, a cobertura e o contraste entre planos, como pede o requisito de explicabilidade do TCC**

- **Onde:** CELL 22 (_decisao_jev: evidencia=None), CELL 41 (tabela por trecho), CELL 44 (gráfico)
- **Evidência:** O QUE O TCC PEDE. A metodologia do docx prevê o LLM gerando explicações interpretáveis para o usuário; a reunião de 04/08 pede 'mostrar passo a passo de forma transparente'. O QUE O NOTEBOOK ENTREGA. As decisões do JEV não têm evidência (evidencia=None em _decisao_jev), e elas são a maioria. Só os eixos decididos pelo LLM trazem citação. Exemplo na CELL 41: o trecho 84 recebeu 100 no eixo Estado com base numa citação sobre compromissos internacionais de direitos humanos, um caso de fronteira entre eixos que o usuário só consegue avaliar vendo a evidência. LITERATURA E NOTAS. Patankar et al.
- **Impacto:** Sem evidências visíveis, o usuário não consegue auditar nem contestar o resultado. Mostrar só o plano de uma candidatura, sem contraste, pode reforçar bolhas.
- **Recomendação:** Para cada eixo, exibir: - os trechos com decisão, a citação destacada e o método (JEV ou LLM); - as respostas do próprio usuário às afirmações relacionadas (LIT-01); - 'sem evidência' de forma explícita, com a cobertura; - uma opção 'ver como os outros planos tratam este tema', com trechos dos 12 planos em ordem fixa. Para as decisões do JEV, extrair uma citação apenas sob demanda (custo controlado). Fazer um teste de usabilidade pequeno (5 a 8 participantes; instrumento, como o SUS, a verificar). Manter o questionário 8Values no cliente.

### LIT-22 · Média · Melhoria · Parcial (corrigido na verificação)
**Explicitar perguntas de pesquisa e hipóteses, alinhar o método descrito no TCC ao pipeline atual e pré-registrar a avaliação final**

- **Onde:** Docx do TCC (seções 'Roteiro Apresentação', 'Metodologia', 'Teste GPT', 'Recomendações leituras GPT'); CELL 0/4 do notebook
- **Enunciado corrigido:** O docx não fixa objetivos específicos nem perguntas de pesquisa, e o método descrito (embeddings e cosseno, comparação de LLMs) diverge do pipeline executado (cascata JEV + Sabiá). Os textos dos polos (TEXTOS_EIXOS_2) são condensações das 'Definições ampliadas' redigidas com assistência do ChatGPT a partir de páginas do Dicionário de Política de Bobbio. As 70 afirmações já foram usadas em 24 avaliações distintas (22 no TCC.ipynb e 2 no notebook novo).
- **Impacto:** A banca pode apontar divergência entre o método descrito e o executado. Sem perguntas e hipóteses fixadas antes, qualquer resultado pode ser racionalizado depois.
- **Recomendação (ajustada):** Como proposto: perguntas de pesquisa RQ1 a RQ4, métricas e comparadores definidos antes do teste, versionamento datado e atualização do capítulo de metodologia. Ao declarar a assistência de IA, conferir as páginas de Bobbio indicadas pelo GPT (que usou a numeração do PDF, não a impressa, como ele próprio avisa).

### LIT-V01 · Média · Melhoria · Acrescentado na verificação
**Os polos descritos em AXIS_SPECS ('a'/'b') são código morto e diferem da rubrica efetiva (TEXTOS_EIXOS_2); o eixo diplomático efetivo não tem âncora para paz × força militar**

- **Onde:** CELL 13 (AXIS_SPECS, criar_questoes_eixo), CELL 14 (TEXTOS_EIXOS_2), CELL 20 (criar_perguntas_jev_2_polos: `relevancia, _ = criar_questoes_eixo(...)`), CELL 22 (__init__: rubricas)
- **Evidência:** Em criar_perguntas_jev_2_polos (CELL 20) e em CascataJevLLM2Polos.__init__ (CELL 22), a 'polaridade' devolvida por criar_questoes_eixo é descartada (`relevancia, _ = ...`). Os únicos usos de especificacao['a'] e ['b'] estão nessa saída descartada. JEV Score e LLM usam TEXTOS_EIXOS_2. As duas versões diferem em conteúdo. AXIS_SPECS['diplomatic'] traz 'prioridade à paz em relação à força militar' (a) e 'fortalecimento militar, dissuasão… uso da força' (b). TEXTOS_EIXOS_2['peace'/'might'] falam de cooperação, multilateralismo, soberania e autodeterminação, sem nenhuma menção a paz, guerra ou força militar.
- **Impacto:** Há risco de descrever no texto do TCC uma rubrica diferente da que gerou os resultados, e de construir baselines (NLI, CheckList) sobre outro construto. No eixo diplomático, trechos sobre defesa e guerra são detectados como relevantes, mas o Score não tem âncora de direção para eles.
- **Recomendação:** (1) Eliminar a ambiguidade: transformar criar_questoes_eixo numa função só de relevância e remover 'a'/'b' de AXIS_SPECS, ou movê-los para um dicionário documentado como legado. Gerar a tabela de rubricas do TCC a partir de TEXTOS_EIXOS_2. (2) Decidir explicitamente se o eixo diplomático deve cobrir paz × força militar, como no 8Values e em AXIS_SPECS. Se sim, acrescentar âncoras simétricas aos dois polos e avaliar como ablação. (3) Reportar à parte o desempenho em Q17, Q21, Q22 e Q23.

### LIT-12 · Baixa · Melhoria · Confirmado
**Reconciliação com ANALISE_PIPELINE_JEV_LLM.md: as recomendações P0 de engenharia foram adotadas; validação, baselines, estimando e reprodutibilidade continuam abertos**

- **Onde:** analise_jev_llm/ANALISE_PIPELINE_JEV_LLM.md (seções 2–9) × Pipeline_JEV_2_Polos_LLM.ipynb
- **Evidência:** ADOTADAS: (1) Relevância, posição e status separados, com abstenção; ausência não vira 50 (CELL 22, 35, 37). (2) Ablação sobre as mesmas respostas do JEV, sem troca de função em globals (CELL 27). (3) Rubrica comum entre JEV e LLM, com o LLM avaliando só os eixos encaminhados, numa única chamada (CELL 22). (4) Abstenção após o fallback e evidência literal verificada (CELL 19, 20, 22). (5) Contagem de erro→acerto e acerto→erro (CELL 27). (6) Validação de intervalos, classes e somas (CELL 20). (7) Retorno com decisões por trecho, cobertura, configuração e rubricas (CELL 37); latências separadas de JEV e LLM; chamadas contadas por trecho (CELL 41).
- **Impacto:** Sem esse mapa, o texto do TCC pode apresentar como resolvidas questões que continuam abertas, e o orientador não vê o que mudou desde a análise anterior.
- **Recomendação:** Incluir no notebook, ou num anexo do TCC, uma tabela 'recomendação → status → onde foi tratada'. Para cada item aberto, apontar o achado correspondente: baselines → LIT-04 e LIT-05; anotação → LIT-06; inferência → LIT-07; reprodutibilidade → LIT-08; estimando e escala → LIT-02 e LIT-13; bootstrap do documento → LIT-11; segmentação → LIT-16; efeito zero e tipologia de erros → LIT-15; abstenção → LIT-03; custo → LIT-05.

### LIT-17 · Baixa · Nova ideia · Confirmado
**Validade convergente externa (sem tratá-la como verdade): ordenações de especialistas para partidos brasileiros e o corpus BRmoral**

- **Onde:** Seções 10–11 (nenhuma referência externa); depende de LIT-11
- **Evidência:** LITERATURA LIDA: - Benoit et al. medem validade convergente contra pesquisas com especialistas (CHES, Benoit–Laver) e validade preditiva. Alertam que especialistas usam informação além dos manifestos e que temas de valência e estratégia partidária geram divergências legítimas; - Figueredo et al. usam a classificação de partidos de Power & Zucco Jr. e a checam com Wordfish; - L(u)PIN compara projeções com estimativas de especialistas (Mielka) e confere a semântica com BERTopic;
- **Impacto:** Sem nenhuma referência externa, a validade dos índices dos documentos fica só no plano interno (benchmark de afirmações), o que é insuficiente para a parte aplicada do TCC.
- **Recomendação (ajustada):** Usar o BRmoral, se disponível, apenas como teste de direção por tema mapeado explicitamente a um item do 8Values (escore de posição → polo esperado), sem importar o rótulo esquerda/direita do corpus. A referência de partidos fica como convergência exploratória.

### LIT-18 · Baixa · Nova ideia · Confirmado
**Baseline clássico no nível do documento: Wordfish (e Wordscores) sobre os trechos relevantes de cada eixo**

- **Onde:** Seções 10–11; depende de LIT-11 (12 planos)
- **Evidência:** LITERATURA LIDA: - Slapin & Proksch: o Wordfish estima posições a partir de frequências de palavras (modelo de Poisson), sem textos de referência, e os autores mostram robustez a pressupostos de distribuição e à seleção de documentos. O Wordscores, em contraste, depende de textos de referência com posições conhecidas, e os autores comentam estimativas por dimensão a partir das seções correspondentes do manifesto; - Figueredo et al. aplicaram Wordfish no Senado brasileiro e encontraram sinais de uma dimensão governo × oposição. O docx do TCC lista o Wordfish entre os correlatos. O notebook não tem nenhum baseline baseado em frequência de palavras.
- **Impacto:** Faltaria ao TCC um comparador transparente e tradicional na ciência política para a ordenação dos planos. Ele também serve de diagnóstico de confundidores (estilo, situação × oposição).
- **Recomendação:** Para cada eixo, juntar os trechos que a cascata marcou como relevantes em cada um dos 12 planos e estimar o Wordfish (por exemplo, quanteda.textmodels::textmodel_wordfish no R), com a direção fixada por dois documentos de referência. Comparar a ordenação com a da cascata. Uma divergência sistemática sugere que o Wordfish captou estilo ou governo × oposição. O Wordscores com TEXTOS_EIXOS_2 como referências (0/100) é próximo do que o TCC.ipynb já testou com embeddings e pode ficar como opcional.

### LIT-19 · Baixa · Nova ideia · Confirmado
**Escalonamento por comparações pareadas (Bradley–Terry) entre planos, por eixo**

- **Onde:** CELL 37 (índice absoluto por média); depende de LIT-11
- **Evidência:** L(u)PIN e a revisão de Parschan & Jakob descrevem o LaMP (Wu et al., 2023; original não lido, a verificar): o LLM compara pares de atores e o modelo de Bradley–Terry produz uma escala que, segundo os autores citados, correlaciona fortemente com DW-NOMINATE. Comparações pareadas dispensam a calibração de uma escala absoluta, que é justamente o problema do índice atual (média de P(A), LIT-13). Com 12 planos, são 66 pares × 4 eixos × 2 ordens = 528 chamadas, usando resumos por eixo (como em Benoit et al.) ou conjuntos de trechos relevantes.
- **Impacto:** Oferece uma terceira estimativa, independente, da ordenação relativa dos planos. Ajuda a separar 'sinal' de 'artefato de escala', e as duas ordens de apresentação permitem medir o viés de posição do LLM.
- **Recomendação:** Para cada eixo e par de planos, perguntar qual texto está mais próximo do polo A segundo a mesma rubrica, nas duas ordens. Estimar Bradley–Terry com pseudocontagem. Comparar com a cascata, o Wordfish e a referência externa (LIT-17). Reportar a taxa de inconsistência entre as duas ordens.

### LIT-20 · Baixa · Nova ideia · Confirmado
**Exemplos few-shot balanceados por polo no fallback do LLM (como ablação)**

- **Onde:** CELL 22 (CascataJevLLM2Polos.classificar: prompt zero-shot)
- **Evidência:** O prompt do LLM é zero-shot (CELL 22). LITERATURA LIDA: - Haroon et al.: selecionar demonstrações com balanceamento de classes melhorou o GPT-4o (de 0,64 para 0,69 com k=12 no conjunto do YouTube), e o chain-of-thought não ajudou; - Benoit et al.: o few-shot ficou praticamente igual ao zero-shot, porque havia pouca margem para melhorar.
- **Impacto:** É um ganho possível, de baixo custo, nos casos ambíguos encaminhados ao LLM, e pode reduzir assimetrias entre polos, se exemplos dos dois polos estiverem igualmente representados.
- **Recomendação:** Usar k=2 exemplos por polo e por eixo, tirados dos planos anotados (LIT-06), nunca das 70 afirmações, para evitar vazamento. Avaliar como ablação no conjunto anotado, medindo também a assimetria entre polos (LIT-09).

### LIT-V02 · Baixa · Melhoria · Acrescentado na verificação
**O notebook não cita nenhuma fonte, embora suas decisões de desenho tenham respaldo direto na literatura do próprio repositório**

- **Onde:** CELL 0, 4, 6, 18, 21, 25, 35, 42 (markdown)
- **Evidência:** Uma busca no nb_dump por 'et al', 'Benoit', 'Parschan', 'Chen', 'Bobbio', 'Ribeiro' ou '(20xx)' retorna 0 ocorrências. O TCC.ipynb cita fonte e página em cada bloco, por exemplo na CELL 207 (Parschan & Jakob, p. 16–17; Chen, Walker & Saligrama, p. 9529–9534), na CELL 212 (Ribeiro et al., CheckList) e na CELL 236 (Efron; bootstrap em blocos). Várias decisões do notebook novo têm respaldo direto. (a) A abstenção e o 'sem evidência' correspondem à 'informative missingness' e à instrução de devolver NA em Benoit et al. (seção 'Robustness and reproducibility issues'). (b) A separação entre relevância e posição corresponde ao 'what' × 'how' de Chen, Walker & Saligrama (2023).
- **Impacto:** Num TCC, decisões metodológicas sem fundamentação parecem arbitrárias para a banca, e o notebook novo perde a rastreabilidade bibliográfica que o TCC.ipynb tinha.
- **Recomendação:** Acrescentar a cada seção um bloco curto de 'Fundamentação' (referência, página e decisão sustentada), no formato já usado no TCC.ipynb. Priorizar Benoit et al. (abstenção/NA, temperatura, ensembles), Chen et al. (relevância × posição), Parschan & Jakob (validação) e Bobbio, com as páginas conferidas, para os textos dos polos.

## Crítica de completude (CMP)

### CMP-01 · Média · Melhoria · Confirmado
**O CSV de validação manual não mede o regime de 600 tokens: são unidades de ~95 tokens, reformatadas e de um só plano; projetadas nos chunks do notebook, viram n=8**

- **Onde:** tcc/d0_manual_validation_avaliado.csv (não usado pelo notebook); CELL 36 (dividir_texto_em_chunks_tokens, 600 tokens) e CELL 39 (separar_em_chunks); recomendação comum de BEN-16, DOC-09, LIT-06 e VIE-18
- **Evidência:** Medi com tiktoken cl100k: as 66 unidades do CSV têm de 78 a 150 tokens (mediana 94). As 66 começam com o caminho de seções ('**PLANO DE GOVERNO** > **1. Mulheres e crianças…** > **1.1 …**.') e juntam itens de lista com '. '. Só 4 dos 66 corpos aparecem literalmente no md; após normalizar a pontuação, os 66 são localizáveis. O plano inteiro (2026BR280002552484_01.pdf) tem 4.213 tokens e, com CONFIG_CHUNKS, vira 8 chunks (568, 567, 544, 563, 567, 569, 530 e 297 tokens). Projetei os rótulos nesses 8 chunks (chunk relevante se contém alguma unidade relevante; 1 unidade cai na fronteira entre chunks). Positivos por eixo: economic 4, diplomatic 3, state 5, society 4;
- **Impacto:** Usado como está, o CSV valida o JEV em unidades cerca de 6× menores e com títulos de seção que o notebook não envia. Projetado no regime do notebook, dá n=8 por eixo, o que não basta para estimar precisão ou revocação.
- **Recomendação (ajustada):** Manter (1) e (3). Em (1), tratar as unidades sobrepostas como itens dependentes: deduplicar a frase de fronteira ou fazer bootstrap por seção. Reportar IC de Wilson por eixo e declarar que diplomatic (4 positivos) e society (7) não sustentam estimativas de precisão nem de revocação. Em (2), uma versão mais leve cabe num TCC: amostrar 5 chunks por plano (60 chunks × 4 eixos), estratificados por posição no documento, com rótulo de relevância e de polaridade, e fazer a dupla anotação em cerca de 30% da amostra para calcular o kappa. Incluir obrigatoriamente chunks do documento que o notebook de fato analisa.

### CMP-02 · Média · Correção · Confirmado
**A tradução das 70 perguntas nunca foi validada e tem erros que afetam o gabarito do benchmark e o perfil do usuário**

- **Onde:** CELL 9 (QUESTIONS = ler_json_tiptado('./tcc/questions.json')); CELL 26 (esperado_pelo_efeito); TCC.ipynb CELL 18 (QUESTIONS_PATH: o quiz do usuário usa o mesmo arquivo) e CELL 25 (Quiz8Values)
- **Evidência:** Comparei tcc/questions.json com o original 8values/questions.js (raw do GitHub). Os 70 efeitos são idênticos e estão na mesma ordem, então o gabarito numérico está certo. O texto, porém, tem erros. Q67 'Deberíamos abrir nossas fronteiras à imigração' está em espanhol (dipl +10, govt +10). Q11 'Utilitários básicos como estradas e eletricidade' é falso cognato de 'utilities' (econ +10). Q25 'Minha nação é grande' traduz 'great', mas em português pode ser lido como tamanho (item só de dipl −10). Q36 'A própria existência do estado' e Q39 'Um estado hierárquico' usam minúscula, e 'estado' em PT-BR também é unidade federativa ou condição;
- **Impacto:** Erros de tradução viram 'erros do modelo' no benchmark, porque o jev-1.13 lê literalmente (seção 'Literal reading' da documentação). Eles também mudam a resposta do usuário no quiz. Os dois lados da comparação de alinhamento ficam contaminados. Nenhum achado tratava a fidelidade da tradução; API-13 trata só do idioma do modelo.
- **Recomendação:** Versionar o original em inglês (licença MIT) com hash e conferir os efeitos por assert. Revisar a tradução com duas pessoas e retrotradução (procedimento TRAPD/ITC) e registrar a versão. Rodar o benchmark também com os itens originais em inglês como controle, sem tradução automática. Reportar o desempenho por item nos itens revisados.

### CMP-07 · Média · Nova ideia · Parcial (corrigido na verificação)
**Falta uma ficha do instrumento (model card e datasheet) com uso pretendido, usos fora de escopo e limitações conhecidas, publicada junto com qualquer resultado**

- **Onde:** CELL 0 (descrição do notebook); CELLs 39–44 (saídas por candidatura; título do gráfico com DOCUMENTO_NOME); tcc/textos_candidatos.json (proveniência)
- **Enunciado corrigido:** Falta uma ficha do instrumento voltada ao leitor. A proveniência, porém, está mais registrada do que o achado diz. Os PDFs originais e o leiame.pdf do TSE estão versionados em tcc/proposta_governo_2026_BR/BR/. A CELL 129 do TCC.ipynb registra o extrator (pymupdf4llm.to_markdown e to_text com header=False, footer=False e use_ocr=False), e o requirements.txt fixa pymupdf4llm==1.28.2. Faltam a URL e a data do download, os hashes e a referência a tudo isso no notebook da cascata. '_01' não é versão: segundo o leiame do TSE, é o número sequencial do documento anexado pela candidatura (ver CMP-V01). O risco de comunicação é mais concreto do que o achado descreve.
- **Impacto:** Sem declaração de uso, um índice descritivo e não validado (DOC-V02, DOC-04) pode ser lido como classificação ideológica oficial de uma candidatura, o oposto da neutralidade exigida. Nenhum achado propõe esse documento voltado ao leitor; COD-04 trata do manifesto técnico da execução.
- **Recomendação (ajustada):** Manter a ficha com os campos dados (fonte TSE, leiame, extrator pymupdf4llm 1.28.2 e parâmetros da CELL 129, data e URL do download, sha256 dos PDFs e do JSON), rubricas, modelos, avaliação e limitações. Além disso, enquanto o índice não for validado, tirar dos gráficos de documento os rótulos ideológicos do 8Values (ou trocá-los por 'índice descritivo 0–100, polo A') e usar identificadores cegos no título.

### CMP-V01 · Média · Correção · Acrescentado na verificação
**O corpus considera só o anexo '_01' de cada candidatura; anexos '_02' e seguintes seriam descartados em silêncio**

- **Onde:** TCC.ipynb CELL 127 (dicionário candidatos com chaves '..._01') e CELL 129 (key = filename[:-4]; if key in candidatos); tcc/textos_candidatos.json; tcc/proposta_governo_2026_BR/BR/leiame.pdf; Pipeline CELL 10/34
- **Evidência:** O leiame.pdf do TSE, versionado no repositório, diz que o nome do arquivo é YYYYUFNNNNNNNN_NN.PDF, em que NN é o 'Número sequencial do documento anexado pelo candidato', e que a candidatura 'pode anexar mais de um documento' (_01, _02, _03). No TCC.ipynb, a CELL 127 só tem chaves terminadas em '_01', e a CELL 129 descarta qualquer PDF cuja chave (filename[:-4]) não esteja no dicionário, sem aviso. Um '2026BR..._02.pdf' seria ignorado. A pasta versionada tem só 12 PDFs '_01' e o leiame, e as 12 entradas de textos_candidatos.json também são '_01'. Não consegui verificar se o ZIP original do TSE tem anexos '_02', porque o ZIP não está no repositório e não fiz download.
- **Impacto:** Se alguma candidatura tiver dividido o plano em mais de um PDF, a análise por documento (cobertura, médias por eixo) fica incompleta para ela, e a comparação entre documentos e com o usuário perde a simetria. Nenhum achado tratava a completude do corpus de entrada.
- **Recomendação:** Conferir a lista de arquivos do ZIP do TSE (proposta_governo_2026_BR.zip) e agrupar por SQ_CANDIDATO. Se houver vários anexos, concatená-los na ordem NN e registrar isso. No notebook, validar que cada candidatura analisada tem todos os anexos e registrar a lista no manifesto ou na ficha (CMP-07).

### CMP-V02 · Média · Melhoria · Acrescentado na verificação
**A mesma configuração do JEV deu 215/280 no TCC.ipynb e 212/280 neste notebook: a linha de base varia entre execuções**

- **Onde:** TCC.ipynb CELLs 308, 310, 311 e 312; Pipeline_JEV_2_Polos_LLM.ipynb CELLs 13, 14, 20, 26 e 32
- **Evidência:** Executei as definições dos dois notebooks e comparei. AXIS_SPECS (TCC.ipynb CELL 251 × Pipeline CELL 13), as perguntas de relevância de criar_questoes_eixo e TEXTOS_EIXOS_2 (TCC.ipynb CELL 308 × Pipeline CELL 14) são iguais (==), e as instruções do Score de 2 níveis são textualmente idênticas. Os dois usam o mesmo avaliador, executar_benchmark_8values, e com relevância Choice o critério 'passou' é equivalente nos dois fluxos. Mesmo assim, o TCC.ipynb CELL 311 dá 215/280 e o Pipeline CELL 32 dá 212/280 ('JEV 2 polos inicial'). A relevância correta foi 221/280 (accuracy 0,7893 nas CELLs 303 e 312 do TCC.ipynb) contra 220/280 aqui (soma de acuracia_relevancia × 70 no resumo_jev).
- **Impacto:** As comparações entre desenhos feitas em execuções diferentes (216, 215, 212, 205...; ver CMP-08) não são pareadas, e diferenças de até cerca de 3 pares estão dentro da variação observada entre execuções.
- **Recomendação:** Rodar só o JEV 3 vezes nas 70 perguntas e reportar o intervalo de acertos e o número de pares instáveis. Rodar 3 vezes as chamadas ao LLM dos pares encaminhados e reportar a concordância. Registrar response.model em cada execução. Nas comparações de desenho, reportar diferença e variação entre execuções lado a lado.

### CMP-V03 · Média · Correção · Acrescentado na verificação
**O notebook diz ser autossuficiente e compatível com Python 3.10+, mas depende de dois arquivos externos e a CELL 8 falha antes do Python 3.14**

- **Onde:** CELL 0, CELL 1, CELL 6 e CELL 33 (markdown); CELL 8 (ler_json_tiptado), CELL 9, CELL 10, CELL 17 (T = TypeVar) e CELL 34
- **Evidência:** A CELL 0 afirma: 'Todo o código, as 70 perguntas do 8Values e o documento de exemplo estão incorporados.' A CELL 33 diz que o Markdown 'foi incorporado abaixo' e que 'Nenhum carregamento externo é necessário'. Na prática, a CELL 9 lê ./tcc/questions.json, a CELL 10 lê ./tcc/textos_candidatos.json (3,5 MB, 12 planos) e a CELL 34 usa plano_lula['md']. A CELL 1 pede 'Python 3.10 ou superior', mas a CELL 8 declara def ler_json_tiptado(caminho: str | Path, tipo: type[T]) -> T, e T só é definido na CELL 17. Testei com py -3.11 e a definição gera NameError: name 'T' is not defined.
- **Impacto:** Quem seguir as instruções do próprio notebook, com Python de 3.10 a 3.13 ou sem a pasta tcc/, não consegue passar da seção 3. A documentação de reprodução do TCC fica incorreta.
- **Recomendação:** Mover T = TypeVar('T') para a CELL 3 (ou adicionar from __future__ import annotations). Corrigir os textos das CELLs 0, 1, 6 e 33 para listar os arquivos necessários, com caminho relativo e sha256. Adicionar uma checagem de presença e hash antes da CELL 9.

### CMP-03 · Baixa · Correção · Parcial (corrigido na verificação)
**Dois arquivos de resultados versionados estão truncados (JSON inválido); a persistência que vários achados pedem precisa ser atômica e testada**

- **Onde:** tcc/teste_estabilidade.json e tcc/resultados_total_estimado.json (commit ebf9116); pontos de gravação a criar nas CELLs 29, 39 e 41; TCC.ipynb CELL 245 (padrão atômico já existente)
- **Enunciado corrigido:** Dois arquivos versionados no commit inicial estão truncados: teste_estabilidade.json (133 bytes, termina em '"estimado_md": ') e resultados_total_estimado.json (14 bytes, '[{"estimado": '). A causa não pode ser determinada, porque o código que os gerou não está no repositório. No primeiro arquivo, o corte cai antes de um valor que é texto Markdown. Isso aponta mais para UnicodeEncodeError (open(path, 'w') sem encoding='utf-8' e com ensure_ascii=False no Windows, padrão das CELLs 105, 121 e 130 do TCC.ipynb) do que para um valor não serializável. As armadilhas atribuídas aos registros da cascata estão exageradas.
- **Impacto:** COD-04, BEN-13 e API-05 recomendam salvar os registros. Feito com json.dump direto, uma falha no meio grava um arquivo truncado sem aviso e destrói o resultado anterior, o que já aconteceu duas vezes neste repositório.
- **Recomendação (ajustada):** Remover ou regenerar os dois arquivos truncados. Para os DataFrames (detalhes, comparacao), usar to_parquet ou to_csv, que lidam com NaN e NA. Para os registros, usar JSONL anexado a cada pergunta ou chunk, com encoding='utf-8' explícito e allow_nan=False, mais a gravação atômica proposta para o resumo final. Documentar que, depois da releitura, as chaves de probabilities_score são strings.

### CMP-04 · Baixa · Melhoria · Parcial (corrigido na verificação)
**A resposta do LLM para um eixo depende de quais outros eixos foram encaminhados junto (prompt agrupado e variável)**

- **Onde:** CELL 22 (CascataJevLLM2Polos.classificar: json.dumps({'rubricas': {e: self.rubricas[e] for e in encaminhados}, 'texto': texto})); CELL 19 (RespostaLLM2Polos)
- **Enunciado corrigido:** Na CELL 22, o LLM recebe numa única chamada as rubricas de todos os eixos encaminhados. A decisão de um eixo pode, portanto, depender de quais outros eixos foram junto. É um risco de desenho plausível, mas não medido. No benchmark, o alcance é pequeno: houve 31 ativações de eixo em 26 chamadas (2 + 4 + 16 + 9), então no máximo 5 chamadas agruparam mais de um eixo.
- **Impacto:** A decisão de um eixo deixa de depender só de (texto, eixo). Por isso, guardar em cache a resposta do LLM por eixo e simular limiares offline (BEN-09/LIT-05) passa a ter viés. A comparação JEV × LLM também mistura avaliação independente (JEV) com decisão conjunta (LLM).
- **Recomendação (ajustada):** Primeiro medir: reexecutar os 31 pares (pergunta, eixo) que foram ao LLM no benchmark e uma amostra dos encaminhamentos do documento nas duas formas (agrupada e um eixo por chamada), e reportar a concordância de relevância e de polo. Se houver divergências, adotar uma chamada por eixo com prefixo fixo e texto no fim, como no código sugerido, e ajustar a contagem de chamadas nas CELLs 27, 32 e 41. Caso contrário, documentar que o agrupamento foi testado e mantê-lo.

### CMP-05 · Baixa · Melhoria · Confirmado
**Fronteira de dados do usuário: o perfil 8Values pode ser calculado localmente, mas o desenho no texto do TCC prevê enviar opiniões do usuário a uma API e chamá-las de 'anônimas'**

- **Onde:** Etapa 'comparação com o usuário' (não implementada no notebook); docx do TCC, seção 'LGPD'; TCC.ipynb CELLs 8 e 25 (AnswerOption, Quiz8Values.calc_score); CELL 24 (clientes JEV/Maritaca)
- **Evidência:** O docx do TCC propõe um pop-up dizendo que 'o conteúdo digitado por você será processado ... por meio de uma API de inteligência artificial parceira', com a frase 'autorizo o tratamento das minhas opiniões políticas de forma anônima' e a opção de 'exclusão do seu histórico de análises'. Opinião política é dado pessoal sensível (LGPD, art. 5º, II, e art. 11). Um histórico que o usuário pode excluir está ligado a ele: é pseudonimizado, não anônimo (art. 12 e 13). O perfil já é aritmética local: calc_score = 100·(max+soma)/(2·max), com multiplicadores 1; 0,5; 0; −0,5; −1 (TCC.ipynb CELLs 8 e 25). Testei a versão local abaixo com tcc/lista_total.json; ela roda sem API (ex.: equality 82,05;
- **Impacto:** Se a interface final enviar respostas ou textos livres do usuário às APIs, o sistema passa a tratar dado sensível com possível transferência internacional. Isso exige consentimento específico e base contratual, e a palavra 'anônima' no termo ficaria imprecisa. Nenhum achado tratava a etapa do usuário do ponto de vista de dados.
- **Recomendação:** Arquitetura sugerida: (a) os documentos públicos são classificados offline, com cache (COD-04/BEN-09), e só eles vão para JEV e Sabiá; (b) o perfil do usuário é calculado localmente; (c) a correspondência usuário × documento é feita localmente; (d) se houver texto livre do usuário, filtrar dados pessoais, usar o modelo BR-SP e trocar 'anônima' por 'pseudonimizada' no termo. Se o TCC coletar respostas de outras pessoas, verificar com o orientador se é preciso submeter ao CEP (Res. CNS 510/2016).

### CMP-06 · Baixa · Melhoria · Parcial (corrigido na verificação)
**De ponta a ponta: a extração dos PDFs e a tradução do instrumento não têm nenhuma checagem, e a direção nos documentos e a comparação com o usuário não têm validação**

- **Onde:** CELL 10/34 (entrada md), CELL 36 (segmentação), CELLs 37–44 (agregação e saída); tcc/textos_candidatos.json
- **Enunciado corrigido:** A extração e a segmentação não passam por nenhuma checagem automática no notebook. A auditoria dos 12 planos, porém, mostra que o documento analisado (2026BR280002542548_01.pdf: razão md/txt 0,992 e 0 U+FFFD) não tem problema de extração detectável. Os 15 U+FFFD de 2026BR280002539826_01.pdf estão num título decorativo e também aparecem no txt, então vêm da fonte do PDF e não da conversão para md. A falta de validação da direção nos documentos e da comparação com o usuário é real, mas já está coberta pelos achados citados (DOC-V02, LIT-01, DOC-05). Este achado funciona como resumo deles.
- **Impacto:** O resultado final herda o elo mais fraco da cadeia. Hoje dois elos (extração e tradução) não têm nem um teste automático barato, e dois elos centrais para a pergunta do TCC (direção em documentos e comparação com o usuário) não têm validação alguma.
- **Recomendação (ajustada):** Manter a célula de auditoria só como aviso, sem interromper a execução. Registrar a razão md/txt, os U+FFFD (indicando se também aparecem no txt), os chunks curtos e a fração de chunks que são índice ou sumário, e contar como títulos tanto as linhas com '#' quanto as linhas inteiras em negrito. Inspecionar manualmente os dois md com razão abaixo de 0,95 antes de estender a análise aos 12 planos.

### CMP-08 · Baixa · Correção · Confirmado
**Parte da evidência anterior usada no desenho tem erro: o teste Noul de 5 níveis imprime o resultado do Choice, e o 'teste em inglês' usou retrotradução automática**

- **Onde:** TCC.ipynb CELLs 301–306 (Teste 5 polos) e CELLs 288–295 (variante EN); reflexos nas CELLs 4, 5 e 12 do notebook (escolha de 'choice' e de 2 polos) e nas propostas API-13, API-15 e LIT-13
- **Evidência:** A CELL 305 grava resultado_jev_score_noul, mas a CELL 306 calcula os acertos de resultado_jev_score (o Choice) e imprime de novo 216/280; o Noul de 5 níveis nunca foi medido. A variante em inglês (CELLs 288–295) traduz as perguntas PT→EN com o modelo unicamp-dl/translation-pt-en-t5 (traduzir(q.question)), em vez de usar os itens originais, que têm efeitos idênticos (70/70). Placar salvo das variantes no mesmo benchmark: 216 (Choice, CELL 279), 205 (Noul, 284), 216 (EN retrotraduzido, 295), 216 (Score de 5 níveis, 302), 215 (2 polos, 311), 204 (2 polos Noul, 315), 200 (2 Nouls, 323), 225 (cascata anterior, 334), 221 (cascata Noul, 351), 162 (Laya, 385).
- **Impacto:** As comparações Choice × Noul (5 níveis) e PT × EN não medem o que parecem medir. O desenho de 2 polos também não é o de maior acerto salvo. Isso não é um problema em si, porque as diferenças estão dentro do ruído (BEN-06, BEN-12), mas precisa ficar escrito para não parecer que a escolha foi feita pelo resultado.
- **Recomendação (ajustada):** Corrigir as CELLs 306 e 390 do TCC.ipynb, ou anotar que esses resultados não existem. Na tabela de decisões de desenho, incluir as CELLs 318, 354 e 368, indicar que a variante EN mudou as rubricas e registrar que a mesma configuração do JEV deu 215 e 212 em execuções diferentes (CMP-V02). Diferenças de até cerca de 3 pares entre desenhos não são interpretáveis.

### CMP-09 · Baixa · Melhoria · Parcial (corrigido na verificação)
**Possível contaminação do benchmark: perguntas e efeitos do 8Values são públicos desde 2017 e podem estar no treino do Sabiá-4**

- **Onde:** CELL 9 (QUESTIONS); CELL 22 (fallback LLM); CELLs 27 e 32 (ganho da cascata: 26 chamadas, 11 pares corrigidos)
- **Enunciado corrigido:** Os itens e os efeitos do 8Values estão publicados em inglês, e o Sabiá-4 pode reconhecer o questionário, o que daria uma vantagem ao fallback no benchmark que não existe nos documentos. O benchmark, porém, usa uma tradução própria do projeto, inclusive com erros como a Q67 em espanhol, e não encontrei essa redação na web. A memorização literal é pouco provável; resta a possibilidade de reconhecimento entre idiomas. O risco não foi quantificado.
- **Impacto:** O ganho do LLM no benchmark pode superestimar o ganho nos documentos. É um viés de otimismo diferente da seleção de limiares (BEN-08) e nenhum achado o cita.
- **Recomendação:** Avaliar o LLM também em itens que não estão na internet: paráfrases escritas antes de qualquer execução e pares espelhados (VIE-16 e VIE-17 já propõem esses itens; aqui o objetivo é medir a diferença entre original e paráfrase). Uma queda grande nos eixos decididos pelo LLM, sem queda equivalente no JEV, indica memorização. Citar o risco na seção de limitações.
