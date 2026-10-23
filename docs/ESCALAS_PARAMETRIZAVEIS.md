# Escalas ordinais parametrizáveis

Implementação validada localmente em 22/10/2026. A fonte de verdade é `Pipeline - Passo a Passo.ipynb`: contrato, rubricas completas, classificação, evidências, agregação, comparação e apresentação estão no próprio notebook. Não há importação de regras da API. Saídas afetadas pela alteração foram limpas; demonstrações são identificadas como simulações.

## Uso no notebook

Execute primeiro a célula de imports. Ela inicializa também as definições locais exportadas do notebook no namespace do kernel, incluindo os helpers privados, sem executar demonstrações, ler dados/credenciais ou consultar provedores. Assim, as seções podem ser retomadas sem depender de helpers definidos apenas em células intermediárias.

Selecione `ESCALA_ATUAL = ESCALA_5_NIVEIS` ou `ESCALA_9_NIVEIS` na célula de contrato, ou passe o objeto explicitamente:

```python
pipeline = CascataJevLLM2Polos(
    jev_client=cliente, llm=llm, axis_specs=AXIS_SPECS,
    escala=ESCALA_9_NIVEIS,
)
registro = await pipeline.classificar(texto)
resumo = resumir_documento([registro])
```

O padrão histórico do notebook é cinco níveis. O padrão da API permanece nove níveis, como antes desta mudança. O construtor valida e copia a escala antes de construir perguntas ou consultar provedores. As cópias são imutáveis, inclusive as rubricas. Índice Score é posição na lista; código é identidade ordinal; `polo` define direção; `valor` define a pontuação. Não há requisito de códigos consecutivos, positivos no polo A ou centro com código zero.

Cada registro inclui `escala` completa e `escala_hash`. O hash SHA-256 usa JSON canônico, incluindo situações e exemplos, com chaves ordenadas, separadores compactos e `ensure_ascii=True`. Espaçamentos diferentes de `valor` alteram o hash e a convenção do índice; não representam validação científica. `resumir_documento` usa o snapshot salvo e recusa misturar escalas.

## Experimentos do TCC

As três últimas células experimentais de `TCC.ipynb` carregam somente as definições explicitamente exportadas do notebook autoritativo por `tcc_lib/notebook_pipeline.py`, em um namespace novo. O carregamento não executa demonstrações, lê credenciais ou chama provedores. Os nomes antigos com sufixo `9_niveis` foram mantidos para preservar referências, mas as funções recebem qualquer objeto validado.

Selecione `ESCALA_EXPERIMENTO` para o teste individual e o benchmark. Para o JSON, selecione `CONFIG_TEXTOS_9_NIVEIS['escala']`. Os controles `EXECUTAR_*` dessas células começam em `False`. A prévia informa textos, trechos e perguntas antes do envio. O benchmark continua delegando suas métricas a `executar_benchmark_8values`, usando as previsões já coletadas. As avaliações do JSON mantêm limpeza, segmentação, separação por documento, continuidade após falhas, JSONL, CSV, gráficos, fluxogramas e relatório HTML.

Rodadas novas ficam sob `runs/benchmark_escalas/<hash>/<rodada>` e `runs/testes_textos_escalas/<hash>/<rodada>`. Manifestos e registros guardam o snapshot completo. Não misture resultados só porque as escalas têm a mesma quantidade de níveis.

Para comparar rodadas já obtidas:

```python
comparacao = comparar_rodadas_escalas({
    'cinco': {'documento_1': registros_cinco},
    'nove': {'documento_1': registros_nove},
})
display(comparacao['frequencias'])
display(comparacao['documentos'])
display(comparacao['mudancas_para_revisao'])
```

A função exige os mesmos documentos, chunks, modelos e parâmetros. Inclui níveis com contagem zero, concentração em 25/75, relevância/direção/abstenção, fallback, tempo e tentativas observadas; separa documentos com trecho único e múltiplos trechos. Retentativas internas do SDK não são observáveis. O 8Values é referência de relevância/direção; os textos JSON não têm acurácia sem anotações; a escada derivada das rubricas é somente um diagnóstico sintético.

## API, site e extensão

`experiment_config.escala` recebe o objeto completo. A resposta `schema_version: "3"`, pipeline `jev-escalas-ordinal-4`, inclui `escala`, `escala_hash` e `axes[].level_counts_by_key`. Os campos legados de `level_counts` são mantidos para transição; a distribuição autoritativa da versão 3 é a contagem por chave do snapshot. Perguntas, enum do LLM, instruções, auditoria e cálculo são da requisição, sem cache global dependente de escala.

O Lab oferece os presets de cinco/nove níveis publicados por `/api/capabilities`. Site e extensão compartilham o seletor e a apresentação dinâmica; histórico, comparação e reports usam os snapshots originais. Presets v2 transportam a escala completa e aceitam objetos experimentais validados sem editor de rubricas. Presets v1 sem escala migram para nove níveis, o padrão da versão imediatamente anterior desta branch; esses arquivos não contêm informação para distinguir versões anteriores de cinco níveis. Para um preset antigo conhecido de cinco níveis, selecione cinco níveis antes de exportá-lo novamente.

Resultados históricos de schema 1 continuam usando cinco níveis; schema 2, nove. Eles não recebem uma escala atual por inferência. Hashes dos pipelines anteriores continuam excluindo o campo ausente de escala; o pipeline MVP também continua excluindo os campos opcionais de evidências. Reports e exportações mantêm esses contratos.

Após alterar regras/rubricas no notebook e validá-las, execute `scripts/replicate_notebook_scales.py` para atualizar a réplica Python da API e as fixtures TypeScript. O runtime da aplicação não executa notebooks.

## Verificação local

Na raiz, com as dependências de pesquisa instaladas:

```powershell
.venv/Scripts/python.exe scripts/check_local_notebook_demos.py
.venv/Scripts/python.exe scripts/validate_notebook_scales.py
.venv/Scripts/python.exe analise_jev_llm/test_evidencias_pipeline.py
```

Em `app/api`: `python -m unittest discover -s tests -v`. Os testes de paridade carregam o notebook e, portanto, usam também as dependências de pesquisa da raiz. Em `app`: `npm test`, `npm run build`, `npm run build:lab` e `npm run test:lab`.

As fixtures verificam paridade exata de alternativas, valores, estados, rubricas e contagens para cinco, nove e sete níveis, inclusive códigos fora da sequência usual e espaçamento não uniforme. Há testes de respostas inválidas, LLM/fallback, concorrência, hashes históricos, snapshots e caminhos de avaliação. As verificações usam provedores simulados.

Diferença preexistente preservada: o notebook calcula IC por bootstrap de blocos móveis e percentis NumPy; a API usa reamostragem independente com nearest rank. Os índices e contagens coincidem; os intervalos de múltiplos trechos não são comparados como se fossem o mesmo método.

Nenhum experimento novo com provedores reais foi executado nesta implementação. Os checks validam o software, não demonstram que nove níveis são mais precisos.
