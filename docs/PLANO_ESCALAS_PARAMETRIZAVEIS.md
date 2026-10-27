# Plano: escalas ordinais parametrizáveis

Data: 22/10/2026. Estado: implementado e validado localmente com provedores simulados. Uso, compatibilidade e protocolo em [ESCALAS_PARAMETRIZAVEIS.md](ESCALAS_PARAMETRIZAVEIS.md). Experimentos reais permanecem uma etapa explícita.

## Objetivo e fonte de verdade

Permitir que o pipeline receba um objeto de escala, inicialmente com configurações de cinco e nove níveis, e que outras escalas possam ser experimentadas sem duplicar o algoritmo.

O [Pipeline - Passo a Passo.ipynb](<C:/Users/User/Desktop/TCC/Pipeline - Passo a Passo.ipynb>) será a fonte de verdade. Todas as definições próprias necessárias à execução do pipeline e à avaliação das escalas estarão nele: contrato, validação, escalas, rubricas, normalização, integração JEV/LLM, agregação, evidências e apresentação dos resultados. Bibliotecas externas e arquivos de dados continuam sendo dependências normais.

A ordem de implementação será **notebook → experimentos no TCC → API → app**. O notebook não importará regras, rubricas ou funções de domínio da API. A aplicação receberá posteriormente uma réplica da implementação validada; seu runtime não executará notebooks.

## 1. Situação atual

- O notebook passo a passo usa cinco níveis, com constantes, contrato do LLM e conversões numéricas fixos em várias células.
- A API da branch `codex/jev-granularidade-9-niveis` usa nove níveis fixos. A escala está em `app/api/app/polarity.py`, com pontos dependentes dela no domínio, agregação, validação, auditoria e frontend.
- Os experimentos recentes no [TCC.ipynb](C:/Users/User/Desktop/TCC/TCC.ipynb) usam nove níveis, mas ainda consultam arquivos de rubricas e domínio da API. Essa dependência precisa ser substituída pelas definições do notebook autoritativo.
- O projeto já possui `executar_benchmark_8values` e o fluxo de avaliação individual dos textos de `pesquisa_exemplos/textos_teste.json`. Ambos serão preservados como caminhos de avaliação.

O resultado desta mudança será uma implementação genérica por ambiente, acompanhada de definições de escalas. Não haverá um pipeline completo para cinco níveis e outro para nove.

## 2. Contrato proposto para o objeto de escala

O objeto precisa definir significado e pontuação, além da quantidade de alternativas. Exemplo ilustrativo:

```python
ESCALA_5_NIVEIS = {
    "id": "ordinal_5_v1",
    "versao": 1,
    "niveis": [
        {"chave": "polo_B_forte", "codigo": -2,
         "rotulo": "Polo B forte", "polo": "B", "valor": 0.00},
        {"chave": "polo_B_moderado", "codigo": -1,
         "rotulo": "Polo B moderado", "polo": "B", "valor": 0.25},
        {"chave": "sem_posicao", "codigo": 0,
         "rotulo": "Sem posição entre os polos", "polo": None, "valor": 0.50},
        {"chave": "polo_A_moderado", "codigo": 1,
         "rotulo": "Polo A moderado", "polo": "A", "valor": 0.75},
        {"chave": "polo_A_forte", "codigo": 2,
         "rotulo": "Polo A forte", "polo": "A", "valor": 1.00},
    ],
    "rubricas_por_eixo": RUBRICAS_5_NIVEIS,
}
```

`RUBRICAS_5_NIVEIS` também será definido integralmente no notebook. Cada eixo terá uma entrada por chave de nível, contendo situação e exemplos concretos. A definição de nove níveis seguirá o mesmo contrato, com seus próprios códigos, rótulos, valores e âncoras.

Decisões do contrato:

- A ordem de `niveis` determina a ordem das alternativas enviadas ao JEV.
- `chave` identifica a alternativa; `codigo` mantém a representação numérica usada nas tabelas. O índice retornado pelo JEV Score será mapeado pela ordem, nunca confundido com o código.
- `polo` determina direção e agrupamento das probabilidades. A lógica não inferirá polo a partir de uma posição fixa da lista nem de um código numérico específico.
- `valor` é a pontuação normalizada explícita. A conversão será `100 * valor`; desaparecerão as fórmulas fixas `50 + 25 * nivel` e `50 + 12.5 * nivel`.
- O nível central é uma alternativa de um eixo relevante. Irrelevância e abstenção continuam sendo estados separados, sem pontuação imputada.
- A quantidade de níveis será derivada da lista. Não haverá dois parâmetros independentes, como `usar_9_niveis` e `numero_niveis`, que possam divergir do objeto recebido.
- Cada resultado registrará o identificador, a versão e o hash do conteúdo normalizado da escala. O snapshot completo permitirá reproduzir rubricas e interpretar resultados antigos.

### Validação

A validação ocorrerá ao construir o pipeline, antes de qualquer chamada a provedores:

1. Campos e tipos válidos; chaves e códigos únicos; rótulos preenchidos.
2. Para a primeira versão, escala bipolar com quantidade ímpar de níveis, pelo menos três alternativas e um único centro.
3. Valores finitos, estritamente crescentes entre 0 e 1, com extremos 0 e 1 e centro 0,5.
4. Polos B antes do centro e A depois dele; pelo menos um nível de cada polo.
5. Rubricas completas para os quatro eixos, com correspondência exata às chaves da escala e situações não vazias.
6. Cópia validada da escala por instância, protegida contra alterações posteriores no dicionário original.

Valores explicitamente informados permitem testar espaçamentos diferentes. Isso deverá ficar registrado como parte da convenção do índice; não implica validação científica desse espaçamento.

## 3. Etapa A — implementar no notebook passo a passo

### A1. Definir e validar escalas

- Acrescentar células didáticas para o contrato, validador e funções auxiliares.
- Definir `ESCALA_5_NIVEIS` preservando a escala histórica e suas rubricas.
- Definir `ESCALA_9_NIVEIS` com as âncoras completas hoje usadas no experimento de nove níveis, incorporadas ao próprio notebook.
- Mostrar uma tabela derivada do objeto com chave, código, polo, rótulo e valores 0–1/0–100.

### A2. Parametrizar a classificação

```python
pipeline = CascataJevLLM2Polos(
    # clientes e demais parâmetros existentes
    escala=ESCALA_5_NIVEIS,
)
```

- O construtor valida e congela uma cópia da escala.
- Perguntas de relevância permanecem independentes da granularidade.
- JEV Score e Choice usam alternativas geradas pelo objeto.
- O contrato Pydantic do LLM é construído para a escala da instância. Uma resposta pertencente a outra escala é rejeitada, mesmo se seu código for aceito em algum outro experimento.
- Instruções do LLM, seleção ordinal, massas dos polos, margens e estados usam os mesmos mapas da escala.
- JEV e fallback LLM usam a mesma escala durante toda a análise.
- O nível continua sendo a alternativa mais provável. Não substituir a decisão ordinal pela expectativa das probabilidades nem pela confiança do modelo.
- Retirar importações de código próprio da API, inclusive no fluxo de evidências usado pelo notebook.

### A3. Parametrizar cálculo e apresentação

- Agregação consulta o valor da alternativa selecionada; mantém os critérios atuais de inclusão dos trechos.
- Contagens, gráficos, tabelas, legendas e fluxogramas são derivados da escala, sem listas fixas de cinco ou nove códigos.
- Manifestos, registros de chunks e exportações incluem a escala efetivamente utilizada.
- Resumos de resultados salvos usam o snapshot da execução, mesmo quando a configuração atual do notebook já mudou.
- Atualizar exemplos simulados e documentação das células afetadas. Preservar saídas não relacionadas; saídas invalidadas pela mudança serão limpas ou regeneradas com simulações identificadas.

**Condição para avançar:** o notebook executa suas demonstrações locais com cinco e nove níveis sem buscar definições na API e sem precisar executar o `TCC.ipynb`.

## 4. Etapa B — avaliar no TCC

- Adaptar os experimentos recentes do `TCC.ipynb` para carregar explicitamente as definições do notebook autoritativo em um contexto isolado, sem executar células de chamadas reais durante esse carregamento.
- Substituir consultas às rubricas/domínio de `app/api` e a lógica fixa em nove níveis.
- Permitir selecionar o objeto de escala nos testes de um texto, no 8Values e na avaliação dos textos do JSON.
- Preservar `executar_benchmark_8values` como responsável pelas métricas padronizadas. O adaptador continuará convertendo as decisões para o contrato comum, acrescentando os níveis à tabela sem repetir inferências.
- Preservar a preparação, segmentação, avaliação separada por documento, continuidade após falhas e exportações do bloco **Executar avaliações**.
- Separar pastas/identificadores das rodadas e registrar a escala para evitar misturar resultados.

### Comparação metodológica

Comparar cinco e nove níveis nos mesmos textos, com os mesmos chunks, modelos e demais parâmetros:

- Frequência de cada nível e concentração em 25/75.
- Resultados separados para documentos com um único trecho e com vários trechos.
- Relevância, direção, abstenções e acionamento do fallback.
- Tempo e chamadas efetivamente realizados.
- Exemplos de mudanças de intensidade para revisão humana.

O 8Values fornece referência de relevância/direção, não um gabarito para os nove graus de intensidade. Os textos do JSON não receberão acurácia sem anotação de referência. A escada sintética poderá acompanhar cada escala, identificada como diagnóstico construído a partir das próprias rubricas.

**Condição para avançar:** cinco e nove níveis percorrem os mesmos caminhos de avaliação e cada resultado permite identificar a escala usada. Uma escala experimental de sete níveis exercita o contrato sem acrescentar ramificações específicas para sete.

## 5. Etapa C — replicar a implementação na API

Somente após a implementação e os testes do notebook:

- Replicar contrato, escalas e funções de domínio validadas nos módulos Python da API.
- Incluir `escala` na configuração da análise e no snapshot de configuração efetiva, com validação Pydantic e hash canônico.
- Instanciar perguntas, contratos do LLM e mapas de conversão a partir da escala daquela requisição.
- Substituir constantes globais de escala. Duas requisições simultâneas devem poder usar cinco e nove níveis sem compartilhar estado mutável ou caches incompatíveis.
- Se houver cache de perguntas/esquemas, identificá-lo pelo conteúdo da escala, e não apenas pela quantidade de níveis.
- Replicar as contagens e a auditoria de evidências de forma dinâmica.
- Versionar a resposta para transportar a definição dos níveis e suas contagens sem campos fixos `minus2`/`plus4` como único contrato possível.

Arquivos principais afetados:

| Área | Arquivos atuais |
|---|---|
| Escala e rubricas | `app/api/app/polarity.py`, `pipeline/rubrics.py`, `pipeline/domain.py` |
| Configuração | `experiment_config.py`, `settings.py` |
| Provedores e cascata | `pipeline/clients.py`, `pipeline/strategies.py`, `pipeline/validation.py` |
| Resultados e evidências | `pipeline/aggregation.py`, `pipeline/evidence.py`, `schemas.py`, `report_schemas.py` |
| Verificação | `app/api/tests/` |

### Compatibilidade

- Ler os resultados históricos de cinco e nove níveis com seus significados originais. Por exemplo, o código `1` de uma escala antiga não poderá ser reinterpretado usando a escala atual.
- Preservar a validação dos hashes de configurações antigas quando o novo campo estiver ausente.
- Aplicar a mesma migração a reports, execuções Lab e exportações.
- A escala padrão ficará explícita por versão. Introduzir o campo não mudará silenciosamente o padrão de um consumidor existente.

**Condição para avançar:** para as mesmas respostas simuladas, escala e configuração, notebook e API concordam em alternativas, estados, valores, contagens e índices. Os testes não compararão decisões obtidas por duas chamadas independentes a provedores como se fossem determinísticas.

## 6. Etapa D — adaptar site e extensão

- Atualizar os tipos e validadores do contrato compartilhado.
- Permitir selecionar as escalas de cinco e nove níveis no Lab e transportar o objeto validado na configuração.
- Usar o mesmo contrato para futuros presets experimentais de outras escalas, sem exigir uma tela de edição de rubricas nesta entrega.
- Derivar a distribuição apresentada dos níveis devolvidos na análise.
- Exibir a escala usada junto do resultado; histórico e comparação usam os snapshots originais.
- Migrar presets antigos e preservar seu comportamento.
- Aplicar a alteração aos componentes compartilhados entre site e extensão.

## 7. Verificação e critérios de aceite

| Verificação | Evidência esperada |
|---|---|
| Fonte de verdade | Código próprio do pipeline completo no notebook; nenhuma dependência de domínio da API |
| Escala de cinco níveis | Correspondência com os resultados simulados históricos e passos de 25 pontos |
| Escala de nove níveis | Nove alternativas, conversões corretas e passos de 12,5 pontos |
| Outra escala | Sete níveis funcionam sem condicionais específicos no algoritmo |
| Objetos inválidos | Rejeição local antes de chamadas a provedores |
| Score e Choice | Mapeamento consistente entre índice, chave e código |
| LLM e fallback | Enum e instruções correspondem à escala da instância |
| Ausência e empates | Centro, irrelevância e abstenção permanecem distintos |
| Probabilidades | Massas dos polos somam todas as alternativas corretas; não são confundidas com intensidade |
| Agregação | Consulta valores do objeto; nenhum preenchimento artificial de eixos ausentes |
| Apresentação | Todos os níveis aparecem corretamente em tabelas, gráficos, fluxogramas e HTML |
| Registros | Escala completa e identificação de conteúdo permitem interpretar a execução posteriormente |
| Concorrência | Requisições com escalas diferentes não interferem entre si |
| Compatibilidade | Análises, reports, hashes e presets anteriores continuam interpretáveis |
| Paridade | Mesmas respostas simuladas produzem decisões e índices equivalentes no notebook e na API |

A verificação de paridade terá fixtures com configurações e respostas brutas conhecidas. Eventuais diferenças já existentes entre os métodos de bootstrap do notebook e da API serão documentadas separadamente; não serão confundidas com diferenças de escala nem ocultadas por tolerâncias amplas.

Testes locais usarão provedores simulados. A execução real dos experimentos será uma etapa explícita, com contagem de textos/perguntas/chunks antes do envio. Não será necessário rodar todas as células de APIs ou reexecutar todos os estudos históricos para validar o contrato.

## 8. Entregas e ordem de trabalho

- [x] **A:** notebook autoritativo parametrizado, com objetos completos de cinco e nove níveis e demonstrações locais.
- [x] **B:** experimentos do TCC usando o notebook, benchmark padrão e avaliações por texto com identificação de escala.
- [x] **C:** API replicada, configuração por requisição e compatibilidade com resultados anteriores.
- [x] **D:** site e extensão com seleção, apresentação dinâmica e migração dos presets.
- [x] **E:** testes de equivalência, documentação de uso e protocolo de comparação das escalas.

Não fazem parte desta mudança: substituir os modelos, alterar a tarefa de relevância, trocar o critério de decisão ordinal por uma média de probabilidades, mudar automaticamente os limiares de fallback ou afirmar que uma escala mais detalhada é mais precisa. Essas hipóteses podem ser avaliadas depois, com as escalas já parametrizadas.
