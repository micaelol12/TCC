### Leitura da rodada piloto — 16/10/2026

Rodada: `20261016T203411Z-0ec92e`. **8/8 experimentos concluídos**, 107 chamadas
registradas (sem erros), modelos efetivos `jev-1.13.0`, `sabiazinho-4` e `sabia-4`.
Uma chamada preliminar de conectividade ficou fora desta rodada. Oito testes locais
adicionais validaram cache, orçamento, retomada, métricas e tratamento de erros.

| Experimento | Resultado observado | O que permite concluir |
|---|---|---|
| Citações | 4/4 expectativas sintéticas atendidas; a negação foi detectada mesmo com citação literal presente. | Vale avaliar em evidências reais anotadas; quatro casos não estimam acurácia geral. |
| Estabilidade | 23 dos 24 pares texto/eixo mantiveram o mesmo rótulo nas três execuções. Houve oscilação no eixo social do texto sobre direitos civis. | A variação existe; só três repetições e seis textos não estabelecem estabilidade geral. |
| Busca | Encontrou a frase de redistribuição e recusou a consulta internacional sem resposta. | O teste de existência impediu que o primeiro do ranking virasse evidência indevida. |
| Estrutura | 5/5 decisões de junção corresponderam ao esperado, preservando todas as palavras. | Funcionou na quebra sintética; falta avaliar extração e segmentação de PDFs reais. |
| Confiança | Limiares 0,5/0,7: 18 níveis completos, 45 ausências e 9 incertezas. Em 0,9: 9 níveis completos e 9 direções sem intensidade. | A saída menos específica preservou direção em casos que perderam o nível completo; ainda falta validar o acerto. |
| Lote | Mesmos rótulos nas 24 comparações; diferenças de probabilidade de até 0,07. Média de tempo 6.67× menor e 29.2% menos tokens de entrada. | Mantém a escolha de agrupar perguntas; latências são desta rede/rodada e não um ganho garantido. |
| Cascata | A frase de soberania foi classificada como polo A pelos dois LLMs; JEV direto escolheu B. O verificador atribuiu 0,38 de risco de erro. | Em limiares 0,5/0,7 o erro passou. Em 0,3 houve encaminhamento, mas o maior repetiu o erro. Trocar de modelo não garante correção. |
| Atributos | Primeira rodada escolhida no desenvolvimento. Balanced accuracy no teste: 0,583 para atributos JEV e 0,500 para os dois baselines; apenas 5 perguntas no teste. | Amostra insuficiente para afirmar ganho. A segunda rodada piorou no desenvolvimento; mais perguntas não significaram melhora. |

**Limitações adicionais dos atributos:** o LLM propôs uma pergunta disjuntiva
("revertido integralmente aos acionistas ou compartilhado com os trabalhadores"),
que não define bem uma resposta binária. Foi mantida e registrada como saiu,
sem corrigir a rubrica depois de olhar o teste. Uma próxima avaliação deve prever
revisão das perguntas antes de congelar o protocolo e usar um novo teste independente.

**Prioridade após o piloto:** avaliar sustentação semântica das evidências e busca
por IDs em uma amostra humana de propostas reais; manter perguntas em lote;
medir estabilidade em documentos maiores. Cascata invertida e atributos ficam como
alternativas experimentais, pois esta rodada não demonstrou vantagem consistente.

As tabelas completas e respostas originais estão em `runs/cookbooks/20261016T203411Z-0ec92e`.
Nenhum experimento desta seção altera o aplicativo ou os resultados históricos.
