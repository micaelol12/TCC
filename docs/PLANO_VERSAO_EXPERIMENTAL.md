# Plano da versão de teste — extensão e site

Data: 13/10/2026. Status: implementado para uso local. Instruções e validação em [app/LAB.md](app/LAB.md).

Atualização de escopo: o Lab agora permite cadastrar chaves Maritaca/Gemini por sessão, selecionar os modelos pedidos e registrar automaticamente todas as execuções no banco. As recomendações originais abaixo sobre credenciais apenas por ambiente e persistência apenas por report foram substituídas por esse fluxo, documentado em `app/LAB.md`.

Criar uma edição **8values Lab** para experimentar parâmetros do algoritmo pelo site e pela extensão, escolher modelos e definir as credenciais dos provedores na API. Reutilizar o pipeline e os componentes existentes, com identificação clara das análises experimentais.

A proposta assume uso inicial local ou interno, com a API administrada por quem conduz os testes. Credenciais próprias de cada usuário em um serviço público exigiriam outro escopo: autenticação, armazenamento de segredos e isolamento por usuário.

## 1. O que já existe

- `app/api/app/settings.py` já recebe `TYPESAFE_API_KEY`, `MARITACA_API_KEY`, `JEV_MODEL`, `LLM_MODEL` e limites operacionais por ambiente.
- `app/api/app/environment.py` carrega as variáveis com prioridade: processo > `app/api/.env` > `.env` da raiz. Mudanças exigem reiniciar a API.
- `app/api/app/pipeline/strategies.py` mantém três limiares JEV fixos em `JEV_CONFIG`.
- A segmentação usa cerca de 600 tokens por trecho. A agregação usa 16 trechos válidos como corte de evidência suficiente, 2.000 reamostragens e semente 42.
- `POST /api/analyze` aceita somente texto e modo. Campos adicionais são rejeitados.
- Site e extensão compartilham cliente HTTP, componentes e contratos em `app/shared`.
- A extensão já tem builds local e produção, com endereço da API, permissões e CSP gerados juntos.

## 2. Decisão de arquitetura

Usar **variáveis de ambiente para configuração da API e credenciais**, e **um painel compartilhado para parâmetros de cada análise**. Variáveis de ambiente, sozinhas, não atendem à troca de parâmetros pela interface sem reinício.

| Camada | Responsabilidade | Quando muda |
|---|---|---|
| Ambiente da API | Chaves, modelos permitidos, padrões do algoritmo, limites de consumo e habilitação do Lab | Ao reiniciar a API |
| Build do site/extensão | Identidade Lab, inclusão do painel experimental e endereços | Ao recompilar |
| Painel de experimentos | Modelos permitidos e parâmetros da próxima análise | Imediatamente, sem recompilar |
| Resultado | Cópia da configuração efetivamente usada | Fixa para aquela análise |

Cada requisição resolve uma configuração imutável: **valores escolhidos no painel > padrões da API > padrões do código**. Os limites operacionais da API continuam obrigatórios. Uma análise não altera os padrões globais nem a configuração de outra análise em andamento.

O painel só fica disponível quando o build é Lab e a API anuncia suporte experimental. A API precisa rejeitar parâmetros experimentais quando esse suporte estiver desligado, independentemente do que a interface mostrar.

## 3. Parâmetros do primeiro escopo

Os nomes abaixo são propostos. Os valores iniciais preservam o comportamento atual.

| Parâmetro no painel | Variável para o padrão na API | Inicial | Validação proposta |
|---|---|---|---|
| Tokens por trecho | `CHUNK_TOKENS` | 600 | Inteiro entre 100 e 2.000, limitado por `MAX_TOKENS` |
| Margem mínima de relevância | `JEV_RELEVANCE_MARGIN_MIN` | 0.60 | Número finito entre 0 e 1 |
| Confiança mínima do nível | `JEV_LEVEL_CONFIDENCE_MIN` | 0.50 | Número finito entre 0 e 1 |
| Margem mínima de direção | `JEV_DIRECTION_MARGIN_MIN` | 0.20 | Número finito entre 0 e 1 |
| Trechos válidos para evidência suficiente | `MIN_VALID_CHUNKS` | 16 | Inteiro positivo, até `MAX_CHUNKS` |
| Reamostragens do intervalo de confiança | `BOOTSTRAP_SAMPLES` | 2000 | Inteiro entre 200 e 10.000 |
| Semente da reamostragem | `BOOTSTRAP_SEED` | 42 | Inteiro de 0 a 2³² − 1 |
| Modelo JEV | `JEV_MODEL` | `jev-1.13.0` | Lista permitida pela API |
| Modelo LLM | `LLM_MODEL` | `sabia-4` | Lista permitida pela API |

As faixas são limites iniciais de engenharia, não parâmetros cientificamente validados. Alterações metodológicas precisam ficar identificadas no resultado.

Os limiares JEV determinam motivos de incerteza e, no modo médio, o encaminhamento ao LLM. Eles não devem ser apresentados como controles diretos da pontuação. No modo alto, desabilitar os controles exclusivos do JEV e explicar que não se aplicam. O corte de evidência suficiente altera a indicação de suficiência, não a média dos eixos.

Ao permitir variar `BOOTSTRAP_SAMPLES`, substituir os índices fixos atuais do intervalo por índices calculados para os percentis de 2,5% e 97,5%, com uma convenção que preserve os índices atuais no padrão de 2.000 amostras. Manter o intervalo ausente quando houver menos de dois valores válidos.

O tamanho do trecho permanece aproximado devido à preservação de caracteres UTF-8. Validar a quantidade real de trechos após segmentar; uma configuração menor pode ultrapassar `MAX_CHUNKS` e deve produzir uma mensagem específica.

Concorrência, prazo, limite horário, orçamento diário, retentativas e limites totais de entrada ficam sob administração da API. Edição livre de prompts, rubricas, provedores e URLs não faz parte deste primeiro escopo.

## 4. Chaves e modelos

Manter as credenciais exclusivamente na API. O painel mostra apenas **configurado/ausente**, o provedor e os modelos permitidos; a presença de uma chave não prova que ela seja válida.

Exemplo proposto para `app/api/.env`:

```dotenv
APP_ENV=lab
EXPERIMENTAL_CONFIG_ENABLED=true

TYPESAFE_API_KEY=
MARITACA_API_KEY=
JEV_MODEL=jev-1.13.0
LLM_MODEL=sabia-4
ALLOWED_JEV_MODELS=jev-1.13.0
ALLOWED_LLM_MODELS=sabia-4

CHUNK_TOKENS=600
JEV_RELEVANCE_MARGIN_MIN=0.60
JEV_LEVEL_CONFIDENCE_MIN=0.50
JEV_DIRECTION_MARGIN_MIN=0.20
MIN_VALID_CHUNKS=16
BOOTSTRAP_SAMPLES=2000
BOOTSTRAP_SEED=42
```

`APP_ENV`, a habilitação experimental, as listas de modelos e os parâmetros do algoritmo acima são adições propostas. Validar os tipos, faixas e combinações na inicialização, com mensagens que identifiquem a variável inválida sem revelar seu conteúdo secreto. Em produção, recusar a habilitação experimental.

Definir ou trocar as chaves significa editar o `.env` da API e reiniciar o serviço. Na interface, **Atualizar conexão e modelos** consulta novamente as capacidades. Um teste de credenciais com chamada real deve ser uma ação explícita, pois pode consumir créditos.

Chaves não recebem prefixo `VITE_`, não entram no ZIP, em configurações exportadas, no histórico ou nos reports. Usar `VITE_APP_VARIANT=lab` apenas como indicador público do build. Ampliar o `.gitignore` para os novos arquivos locais de ambiente, preservando os arquivos `.env.example` versionados.

O primeiro escopo mantém TypeSafe e Maritaca. A existência de outras chaves no exemplo da raiz não significa suporte desses provedores no aplicativo. Acrescentá-los depois requer adaptadores e validação do contrato de saída estruturada.

Caso seja necessário cadastrar chaves pela interface futuramente, tratar isso como uma tela administrativa autenticada com envio de segredo sem leitura posterior. Não adicionar campos de chave ao formulário comum de análise.

## 5. Experiência no site e na extensão

1. Exibir **Versão de teste** e uma seção **Configuração da análise** ao lado da escolha de modo.
2. Carregar os padrões, faixas e modelos permitidos da API; mostrar os provedores disponíveis.
3. Permitir editar números e selecionar modelos, com ajuda curta sobre o efeito de cada parâmetro.
4. Disponibilizar **Restaurar padrões**, **Salvar configuração**, **Importar** e **Exportar JSON**. Importações passam pela mesma validação e nunca transportam credenciais.
5. Mostrar um resumo das alterações antes de analisar. A configuração é capturada junto com o texto no momento do envio.
6. Guardar o snapshot efetivo no resultado e no histórico. Alterar o painel não muda análises anteriores nem dispara reanálise automaticamente.
7. Permitir selecionar dois resultados do mesmo texto e comparar pontuações, cobertura, chamadas lógicas e parâmetros utilizados. Informar quando os modelos ou modos forem diferentes.

Usar um componente em `app/shared` para manter a mesma experiência nas duas interfaces. Persistir apenas preferências e presets sem segredos, com versão de formato e identificação do ambiente. Revalidar os presets quando a API mudar. A semente controla o bootstrap; ela não garante respostas idênticas dos provedores.

## 6. API e rastreabilidade

- Ampliar `GET /api/capabilities` com habilitação Lab, versão do formato de configuração, padrões, faixas, modelos permitidos e estado dos provedores, sem segredos. Preservar os campos existentes.
- Adicionar `experiment_config` opcional ao pedido de análise. Ausência mantém os padrões; presença é validada estritamente e só é aceita no Lab. Rejeitar campos desconhecidos e valores inválidos antes de chamar provedores.
- Resolver a configuração uma única vez e passá-la explicitamente à segmentação, classificação, criação dos clientes e agregação. Evitar modificar `settings` ou `JEV_CONFIG` globalmente.
- Incluir nos resultados `effective_config`, `config_version`, `config_hash` e identificação do ambiente. Calcular o hash a partir de JSON canônico de parâmetros não secretos, modelos solicitados e versão do pipeline; conservar também os modelos efetivamente retornados pelos provedores.
- Atualizar juntos os schemas Python, tipos e validadores TypeScript, histórico, exportação e reports. O validador de reports atual rejeita campos novos, portanto precisa acompanhar a mudança.
- Introduzir metadados opcionais compatíveis com resultados antigos. Resultados sem snapshot são exibidos como configuração não registrada, sem inventar valores históricos. Se houver mudança incompatível, versionar o contrato e suportar a leitura das duas versões.
- Manter reports do Lab em banco separado. Eles continuam sendo snapshots enviados pelo cliente; o hash da configuração não prova autenticidade nem substitui os mecanismos de consentimento existentes.

## 7. Empacotamento e isolamento

Criar scripts explícitos `build:lab` e `package:lab`, com diretórios separados dos artefatos comuns e nome **8values Lab** no manifesto. Adaptar o empacotador, que atualmente lê sempre `extension/dist` e escolhe o sufixo do ZIP apenas pelo host da API.

O modo de build `lab` precisa de tratamento explícito em `buildConfig.ts`, pois hoje qualquer modo diferente de `production` segue as regras locais. No primeiro incremento, manter a API Lab em loopback e gerar permissões/CSP a partir da origem configurada, como já ocorre hoje.

Para executar as duas edições simultaneamente, usar portas/origens, saídas de build e banco de reports separados. Ajustar o proxy do site e a pasta de frontend servida pela API, hoje fixos em porta 8000 e `web/dist`. Usar prefixos de armazenamento distintos e verificar a transferência de perfil entre o site e a extensão correspondentes.

Se o Lab for hospedado remotamente, incluir autenticação de testadores, HTTPS e autorização na API antes de disponibilizá-lo. O nome do build, CORS e a ocultação do painel não são controle de acesso; não embutir um segredo compartilhado na extensão.

## 8. Ordem de implementação

| Etapa | Entrega | Critério de conclusão |
|---|---|---|
| 1. Configuração da API | Settings validados, chaves documentadas e extração das constantes | `.env` define padrões; os valores atuais preservam o comportamento existente |
| 2. Parâmetros por análise | Contratos, resolução imutável, modelos permitidos e metadados | Duas análises concorrentes usam configurações diferentes sem interferência |
| 3. Painel compartilhado | Edição, presets, importação/exportação e estado dos provedores | Site e extensão alteram a próxima análise sem reinício ou recompilação |
| 4. Resultados e reports | Snapshot, comparação de duas análises e compatibilidade histórica | Histórico e reports preservam a configuração aplicada, sem chaves |
| 5. Pacote Lab | Scripts, identificação, saídas e armazenamento isolados | Lab e edição comum podem ser executados sem sobrescrever artefatos |
| 6. Validação | Testes automatizados e verificação nos navegadores | Critérios abaixo atendidos e instruções de instalação atualizadas |

## 9. Validação necessária

- Regressão com provedores simulados: configuração padrão preserva segmentação, decisões, fallback e agregação atuais.
- Cenários nas fronteiras dos três limiares demonstram a alteração esperada no encaminhamento ao LLM; modo alto ignora parâmetros JEV.
- Segmentação e bootstrap respeitam os novos parâmetros, inclusive UTF-8, poucos trechos e limites incompatíveis.
- Requisições concorrentes não compartilham overrides. Presets inválidos, modelos não permitidos e campos extras são rejeitados antes de consumir chamadas.
- API comum recusa configurações experimentais mesmo quando enviadas manualmente. Limites operacionais continuam ativos no Lab.
- Chaves ausentes produzem estados coerentes; falhas de autenticação do provedor têm mensagens adequadas sem expor a chave.
- Testes com chaves fictícias identificáveis verificam sua ausência nos bundles, ZIPs, respostas, exportações, reports e erros.
- Resultados antigos continuam legíveis; resultados novos mantêm metadados ao salvar, recarregar e reportar.
- Exercitar site e extensão em Chrome e Edge, incluindo importação/exportação de presets, comparação e transferência de perfil para a edição correta.
- Fazer uma análise real curta por modo com as credenciais configuradas para validar integração e disponibilidade dos modelos; testes simulados não comprovam esses pontos.

Entrega implementada: site Lab, extensão Lab instalável, API configurável, exemplos de ambiente sem segredos, presets, comparação e guia de uso. Este documento preserva a proposta original como referência; o contrato final e os comandos estão em `app/LAB.md`. A configuração do banco Lab usa `LAB_REPORTS_DB_PATH` para evitar herdar o caminho do banco comum.
