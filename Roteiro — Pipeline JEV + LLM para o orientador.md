# Roteiro — Pipeline JEV + LLM para o orientador

Oct 6, 2026 · @Micael

Roteiro para uma conversa de cerca de 25 minutos: o que o notebook faz, por que a polaridade passou a ser ordinal, como os resultados são avaliados e quais decisões dependem do orientador.

## 1. Abertura (2 min)

O TCC quer dizer a um usuário quais planos de governo estão mais próximos das posições dele, eixo por eixo, de forma neutra e explicável.

**O que dizer:**

- O usuário responde ao quiz do 8Values (70 afirmações) e recebe um perfil em 4 eixos: econômico, diplomático, civil e social.
- O notebook faz o lado do documento: lê um plano de governo e estima, nos mesmos 4 eixos, a direção e a intensidade das posições que ele defende.
- Pergunta de pesquisa proposta: *uma cascata JEV + LLM consegue medir a posição de planos de governo nos eixos do 8Values com qualidade igual ou maior que um LLM sozinho, a custo menor e de forma auditável?*

**Frase de transição:** "Vou mostrar o fluxo, a decisão de projeto mais importante que tomei e como pretendo validar."

## 2. Visão geral (3 min)

&#91;embedded content: fluxo do pipeline · 7 etapas, 1 decisão\]

O JEV classifica relevância e nível dos 4 eixos de cada trecho numa chamada; só os eixos incertos vão ao Sabiá, que responde na mesma escala e precisa citar o texto.

**O que dizer:**

- "Eixo incerto" tem três motivos: relevância ambígua, confiança baixa do JEV no nível ou direção ambígua entre os polos.
- O LLM é a etapa cara e lenta: na execução anterior do benchmark, 26 das 70 perguntas precisaram dele, com \~3,6 s por chamada contra \~0,3 s do JEV.
- A caixa tracejada ainda não existe no notebook; é a próxima etapa.

## 3. Passo a passo no notebook (8 min)

Percorra o notebook na ordem das seções; para cada uma, mostre a célula indicada e diga uma frase.

| Seção | O que mostrar | O que dizer |
| --- | --- | --- |
| 2. Configuração | `CONFIG_JEV_LLM_2_POLOS`, `TEMPERATURA_LLM` | Todos os parâmetros do experimento ficam num lugar: limiares de encaminhamento, primitiva de polaridade (Score ou Choice) e temperatura 0 no LLM para reduzir variação. |
| 3. Perguntas do 8Values | `QUESTIONS` | As 70 afirmações e seus efeitos por eixo servem de gabarito do benchmark. |
| 4. Polos e escala | Tabela da seção 4 e célula 4.1 (`ANCORAS_INTENSIDADE`, `NOTAS_EIXO`) | Cada eixo tem dois polos; a intensidade tem 5 níveis descritos por situações concretas, espelhadas entre os polos. |
| 5–6. LLM e contrato | `MaritacaClient`, `EixoLLM2Polos` | O Sabiá responde em JSON validado: relevância, nível de −2 a 2 e uma citação literal do texto. |
| 7. Cascata | `CascataJevLLM2Polos.classificar` e `_motivos` | O JEV avalia os 4 eixos numa chamada; só os eixos incertos vão ao LLM, numa única chamada agrupada. Original e final ficam registrados. |
| 9. Benchmark | Tabelas `resumo`, `comparacao`, `desempenho` | Mede relevância e direção nas 70 afirmações e compara JEV sozinho com a cascata nas mesmas respostas. |
| 9.5. Escada | `ESCADA_INTENSIDADE`, `resumo_escada` | 40 frases de intensidade conhecida testam se a escala ordena corretamente antes de olhar planos reais. |
| 10. Documento | `processar_documento_com_jev_2_polos`, tabela de cobertura | O plano é dividido em trechos de 600 tokens; cada trecho relevante vale 0, 25, 50, 75 ou 100; o índice é a média, com IC e cobertura. |
| 11. Inspeção e gráfico | Tabela por trecho e gráfico do índice | Cada número é rastreável até o trecho, o motivo de encaminhamento e a citação. O gráfico mostra índice, IC e n, sem rótulos ideológicos. |

**Dica:** se o orientador quiser ver um caso concreto, abra a tabela da seção 11.1 e filtre um trecho com `LLM ativado no eixo = True`: mostra a decisão do JEV, o motivo do encaminhamento e a citação do LLM.

## 4. A decisão central (4 min)

A polaridade passou a ser uma escala ordinal de 5 níveis porque a versão anterior media certeza da direção, não intensidade.

**O que dizer, em três passos:**

1. **O problema.** Na versão com 2 níveis, o "score" do JEV é P(polo A), a probabilidade de o trecho estar do lado A (é a definição do SDK). Uma proposta moderada e clara recebia \~99; uma radical e ambígua, \~60. Depois, os casos incertos iam ao LLM, que devolvia 0 ou 100. O índice virava, na prática, a proporção de trechos pró-A, e era rotulado com nomes do 8Values ("Comunista", "Revolucionário") como se fosse pontuação do quiz.
2. **A correção.** Agora a pergunta é explícita: qual situação descreve a posição do trecho, entre polo B forte, B moderado, sem posição, A moderado e A forte. Usa-se só o nível mais provável (a documentação do jev-1.13 desaconselha interpolar entre níveis). O LLM responde na mesma escala.
3. **A consequência.** Cada trecho vale 0, 25, 50, 75 ou 100, e o índice do eixo é `50 × (1 + média(nível/2))`: a mesma forma da fórmula do quiz, em que "concordo fortemente" vale +1, "concordo" +0,5 e "neutro" 0.

**Também aproveitei para corrigir assimetrias das rubricas:**

- "Autoridade moderada" agora inclui endurecer penas e ampliar poderes de polícia; antes o polo só descrevia autoritarismo extremo.
- O eixo diplomático ganhou âncoras sobre força militar e diplomacia, que estavam no gabarito mas não na rubrica.
- Cada eixo tem uma nota do que não indica posição sozinho ("soberania" setorial, investir em ciência ou educação, citar um serviço público).
- Existe a opção "sem posição"; antes todo trecho relevante era forçado a um polo.

**Frase-chave:** "O índice deixou de ser uma probabilidade e passou a ser uma medida de intensidade, mas ela ainda precisa ser validada."

## 5. Avaliação (4 min)

Há três níveis de evidência: o benchmark do 8Values (já rodado na versão anterior), a escada de intensidade (nova, ainda não rodada) e a validação humana (planejada).

**Benchmark nas 70 afirmações, versão anterior de 2 níveis:**

| Medida | JEV sozinho | JEV + LLM |
| --- | --- | --- |
| Acerto conjunto (280 pares pergunta × eixo) | 212/280 (75,7%) | 221/280 (78,9%) |
| Referência: classificar tudo como irrelevante | 164/280 (58,6%) | 164/280 (58,6%) |
| Direção correta, entre eixos detectados como relevantes | 68/76 (89,5%) | 70/78 (89,7%) |
| Erros: falsos negativos de relevância / falsos positivos / direção | 40 / 20 / 8 | 38 / 13 / 8 |

**Como ler, em voz alta:**

- A direção já é boa (\~90%); o erro dominante é **detectar relevância**: 40 dos 68 erros do JEV.
- A cascata ganhou 9 pares, quase todos por evitar falsos positivos. O McNemar dá p ≈ 0,02, mas o resultado depende de um único par e de uma execução. Trato como resultado de desenvolvimento, não como conclusão.
- Esses números são da versão de 2 níveis: a versão ordinal precisa ser rodada de novo.

**Escada de intensidade (seção 9.5):** 40 frases sintéticas, 2 por nível em cada eixo, espelhadas entre os polos e sem nomes de partidos. Critérios a pré-registrar: Spearman ≥ 0,8 por eixo, direção correta ≥ 90% e diferença de acerto entre os polos ≤ 10 p.p.

**Validação humana (planejada):** anotar uma amostra de trechos dos 12 planos (relevância e nível), com dois anotadores em parte da amostra para medir concordância (κ). O arquivo `d0_manual_validation_avaliado.csv` já tem rótulos de relevância de um plano e pode servir de piloto.

## 6. Neutralidade (2 min)

A neutralidade é tratada como propriedade a ser medida, não presumida: algumas proteções já estão no código e uma bateria de testes está planejada.

**Já no notebook:**

- Âncoras espelhadas entre os polos, no mesmo formato e com o mesmo número de exemplos.
- Instrução para não deduzir a posição pela identidade do autor ou do partido.
- Evidência literal obrigatória para as decisões do LLM; citação não encontrada vira abstenção.
- Gráfico com identificador cego ("Documento 1") e sem rótulos ideológicos por padrão.
- Mesmo protocolo para qualquer documento; o código não tem nenhuma regra específica de partido.

**Testes planejados, cada um com critério de aceite definido antes:**

| Teste | O que isola |
| --- | --- |
| Inverter a ordem dos níveis na pergunta | Viés de posição (o jev-1.13 tende à primeira opção) |
| Negar as 70 afirmações | Se a direção inverte quando o sentido inverte |
| Mascarar ou trocar nomes de partidos e candidatos | Se a identidade de quem fala muda o resultado |
| Escada espelhada por polo | Se um polo é reconhecido mais que o outro |
| Processar os 12 planos com a mesma configuração, de forma cega | Se o instrumento distingue documentos ou satura num polo |

## 7. Comparação com o usuário (2 min)

A escala do documento agora tem a mesma forma da escala do quiz, o que permite comparar, mas ainda não garante que os números signifiquem a mesma coisa.

**O que dá para afirmar:** em cada eixo, se usuário e plano estão do mesmo lado de 50, e qual dos 12 planos fica mais perto do usuário (ordenação), sempre com o IC do documento e omitindo eixos com evidência insuficiente.

**O que ainda não dá para afirmar:**

- "O plano X é Socialista": rótulos do 8Values para documentos só depois de validar a escala, e mesmo assim como ilustração.
- Distâncias numéricas exatas: o quiz cobre os mesmos 70 temas para todos, enquanto o plano fala só do que escolhe; e planos raramente propõem rupturas amplas, então o índice tende a ficar mais perto de 25 e 75 que as respostas de pessoas.

**Validação proposta:** pessoas leem um plano e respondem o quiz "como se fossem o plano", com a opção "não aborda". Se o índice do pipeline acompanhar esse quiz por procuração nos 12 planos × 4 eixos, a comparação com o usuário fica justificada.

## 8. Limitações e decisões para o orientador

Declarar as limitações antes que sejam perguntadas, e sair da reunião com quatro decisões.

**Limitações a declarar:**

- A versão ordinal ainda não foi executada com as APIs; as âncoras de intensidade são um rascunho.
- O benchmark do 8Values usa frases curtas, não trechos de planos, e já foi usado para ajustar o desenho; serve de desenvolvimento, não de teste final.
- JEV e Sabiá não são determinísticos: a mesma configuração do JEV deu 215/280 numa execução e 212/280 em outra. É preciso repetir execuções.
- Só um plano foi processado até agora; planos curtos têm 8 trechos e os longos, mais de 150, o que muda a precisão do índice.
- O 8Values é um instrumento anglo-americano; a tradução das perguntas tem erros a revisar (uma delas está em espanhol).

**Decisões a pedir:**

- [x] Aprovar a escala ordinal de 5 níveis como medida principal, com a proporção de trechos por direção como medida secundária.
- [ ] Definir o conjunto de teste final: anotar trechos dos 12 planos (quantos, quantos anotadores) e congelar a configuração antes.
- [ ] Escolher o escopo da comparação com o usuário: direção e ordenação por eixo, ou também distância numérica.
- [ ] Decidir se a análise inclui um baseline de LLM sozinho e outros modelos, ou fica em JEV × cascata.

## 9. Perguntas prováveis e respostas curtas

| Pergunta | Resposta curta |
| --- | --- |
| Por que não usar só um LLM? | Custo e auditabilidade. O JEV resolve a maioria dos eixos em \~0,3 s por texto, com probabilidades; o LLM só entra nos casos incertos. Falta medir o LLM sozinho como comparação (está nas decisões). |
| O que é o JEV? | Um modelo da TypeSafe que responde perguntas estruturadas (Choice, Noul, Score) devolvendo probabilidades e confiança, em vez de texto livre. |
| Como você sabe que o LLM não inventa? | Ele precisa citar um trecho literal do texto; se a citação não existe, o eixo vira abstenção. Isso garante existência da evidência, não que ela sustente o polo; há um teste planejado para isso. |
| Por que 600 tokens por trecho? | É a configuração herdada; está registrada e será comparada com outros tamanhos e com segmentação por seção como análise de sensibilidade. |
| 78,9% é bom? | Só em comparação: a referência trivial faz 58,6%, e a direção entre os relevantes detectados fica perto de 90%. O ponto fraco é detectar relevância. |
| O resultado depende do partido do plano? | O protocolo é idêntico para todos e o gráfico é cego; os testes de identidade e de ordem vão medir isso. Ainda não processei os 12 planos. |
| Por que 5 níveis e não 7 ou 10? | Coincide com as 5 respostas do quiz e mantém níveis distinguíveis por situações concretas; mais níveis pedem precisão que o jev-1.13 não promete. |
| O que acontece se a escada falhar? | Ajusto as âncoras usando só a escada (desenvolvimento), sem tocar no benchmark; se mesmo assim falhar, a medida principal volta a ser a proporção de trechos por direção. |
