"""Gera a base sintética rotulada para medir acionamento do LLM, acerto e latência por tamanho.

Cada texto é montado com frases de posição conhecida (eixo e nível de -2 a 2) e frases
neutras de preenchimento (sobre o próprio documento, sem posição em nenhum eixo). O
gabarito de cada texto vem das frases que o compõem.

O desenho é aninhado: dentro de cada tipo de texto, o texto maior contém as frases de
posição do menor, mais frases do mesmo nível e mais preenchimento. Assim a diferença
entre tamanhos não se confunde com troca de conteúdo. Até "muito_longo" (~600 tokens, o
tamanho do chunk do documento) a proporção de frases com posição fica perto de 1/3;
"extra" (~1.200 tokens) repete o conteúdo de posição de "muito_longo" com o dobro de
preenchimento, para medir o efeito de chunks maiores e mais diluídos.

Tipos de texto (por tamanho):
- simples: 1 eixo, um dos 5 níveis (4 eixos x 5 níveis = 20 textos);
- duplo: 2 eixos com direção (8 combinações fixas);
- misto: 1 eixo com o mesmo número de frases do polo A moderado e do polo B moderado,
  sem predominância (gabarito: nível 0, relevante); 4 textos;
- nenhum: só preenchimento (todos os eixos irrelevantes); 4 textos.

Gabarito por eixo: {"relevante": True | False | None, "nivel": -2..2 | None}.
relevante=None significa que as duas respostas são aceitas: frases de diagnóstico do
tema (nível 0 no tipo simples) tratam do eixo sem conter proposta ou posição.

Uso: python base_sintetica/gerar_base_sintetica.py
Não faz chamadas de API.
"""

import hashlib
import json
import random
from pathlib import Path

import tiktoken

SEMENTE = 42
SAIDA = Path(__file__).with_name("base_sintetica.json")
EIXOS = ("economic", "diplomatic", "state", "society")
NIVEIS = (-2, -1, 0, 1, 2)

# Frases de posição: FRASES[eixo][nível] -> 8 frases. Polos como no notebook:
# economic B=Mercado, A=Igualdade; diplomatic B=Nação, A=Globo;
# state B=Autoridade, A=Liberdade; society B=Tradição, A=Progresso.
# Forte = mudança ampla e estrutural; moderado = medida pontual ou gradual;
# 0 = diagnóstico ou proposta sem escolher polo (ver NOTAS_EIXO no notebook).
# Diferentes da escada de intensidade (seção 9.5) e dos exemplos das âncoras.
FRASES = {
    "economic": {
        -2: [
            "Propomos privatizar todas as empresas estatais, incluindo os bancos públicos, a companhia de petróleo e os Correios, entregando esses setores inteiramente à iniciativa privada.",
            "A carga tributária será reduzida de forma drástica, com a extinção da maioria dos impostos federais e sua substituição por um único imposto de alíquota baixa e uniforme.",
            "Saúde, ensino superior e previdência deixarão de ser oferecidos pelo Estado e passarão a funcionar por meio de contas individuais e de empresas privadas concorrentes.",
            "Vamos eliminar a maior parte das regulações sobre preços, salários e contratos, deixando que o mercado defina livremente as condições da atividade econômica.",
            "O salário mínimo nacional e as regras trabalhistas obrigatórias serão abolidos, e cada contrato de trabalho será negociado livremente entre empregado e empregador.",
            "Os gastos do governo federal serão cortados pela metade, com o fechamento de ministérios, de autarquias e dos programas de transferência de renda.",
            "Todos os subsídios, o crédito público direcionado e os bancos de fomento serão extintos, e o financiamento da economia ficará exclusivamente a cargo do mercado.",
            "Rodovias, portos e redes de saneamento hoje públicos serão vendidos a empresas privadas, que passarão a explorá-los sem controle de tarifas.",
        ],
        -1: [
            "A gestão de três rodovias federais será concedida à iniciativa privada por meio de licitação, mantida a fiscalização da agência reguladora.",
            "Vamos simplificar a cobrança de tributos sobre o consumo, unificando duas contribuições federais e reduzindo a burocracia para pequenas empresas.",
            "O crescimento das despesas correntes do governo ficará limitado à inflação nos próximos quatro anos, sem cortes nos programas existentes.",
            "A contribuição patronal sobre a folha de pagamento será reduzida gradualmente em alguns setores que empregam muita mão de obra.",
            "Parcerias com empresas privadas serão usadas para construir e operar novos hospitais, que continuarão atendendo pelo sistema público.",
            "A abertura de empresas será facilitada com um cadastro único e com o fim de algumas licenças exigidas para atividades de baixo risco.",
            "A participação do governo em duas empresas de economia mista será vendida, preservado o controle estatal nas demais.",
            "O prazo de autorização para novos investimentos privados em energia será encurtado, com regras mais simples para pequenos geradores.",
        ],
        0: [
            "Segundo o instituto oficial de estatística, a renda média do trabalho cresceu 3% no último ano, enquanto a inflação ficou em 4,5%.",
            "A dívida bruta do governo geral corresponde hoje a cerca de 75% do produto interno bruto.",
            "Em 2025, a arrecadação federal somou aproximadamente 2,6 trilhões de reais, com destaque para o imposto de renda e as contribuições sociais.",
            "O setor de serviços responde pela maior parte dos empregos formais criados nos últimos cinco anos.",
            "A taxa de informalidade no mercado de trabalho permaneceu próxima de 39% ao longo de 2025.",
            "A produtividade da indústria de transformação está praticamente estagnada há uma década.",
            "Este capítulo apresenta a evolução do salário mínimo, do desemprego e da inflação desde 2015.",
            "Os gastos com aposentadorias e pensões são hoje a maior despesa primária do orçamento federal.",
        ],
        1: [
            "O valor do benefício pago às famílias em situação de pobreza será ampliado, com um adicional para cada criança de até seis anos.",
            "Será criada uma faixa adicional de imposto de renda para rendimentos mensais acima de cinquenta salários mínimos.",
            "O número de fiscais do trabalho será ampliado para combater a informalidade e o descumprimento de direitos trabalhistas.",
            "Vamos abrir novas unidades básicas de saúde e farmácias populares nos bairros de menor renda das grandes cidades.",
            "O salário mínimo terá reajuste anual acima da inflação, acompanhando o crescimento da economia.",
            "Os dividendos distribuídos a acionistas voltarão a ser tributados, com isenção para pequenos investidores.",
            "O crédito subsidiado para agricultores familiares será ampliado e terá juros menores nas regiões mais pobres.",
            "A tarifa social de energia elétrica será estendida a mais famílias inscritas no cadastro de programas sociais.",
        ],
        2: [
            "Os bancos privados, as mineradoras e as empresas de energia serão estatizados e passarão a operar sob controle público.",
            "Será criado um imposto anual sobre grandes fortunas e um imposto elevado sobre heranças, com o objetivo de redistribuir amplamente a riqueza do país.",
            "A economia passará a ser orientada por um plano nacional que definirá metas de produção, preços e investimentos para os setores estratégicos.",
            "Grandes propriedades rurais improdutivas serão desapropriadas e redistribuídas em larga escala a trabalhadores sem terra.",
            "Todas as empresas com mais de quinhentos empregados terão metade do conselho de administração eleita pelos trabalhadores e participação obrigatória nos lucros.",
            "Saúde, transporte e moradia serão garantidos integralmente pelo Estado, com a reestatização de todos os serviços hoje concedidos a empresas privadas.",
            "Será instituída uma renda básica universal para toda a população, financiada por uma reforma tributária que concentra a cobrança sobre patrimônio e altas rendas.",
            "Os imóveis urbanos ociosos mantidos para especulação serão desapropriados e convertidos em moradia pública em grande escala.",
        ],
    },
    "diplomatic": {
        -2: [
            "O país deixará a Organização Mundial do Comércio e todos os tratados internacionais que limitem suas decisões econômicas e militares.",
            "O orçamento das Forças Armadas será triplicado para garantir que o país possa impor seus interesses na região pela força, se necessário.",
            "Nenhuma decisão de tribunal ou organismo internacional terá efeito no território nacional, e o país denunciará os tratados que o obriguem a cumpri-las.",
            "As fronteiras serão fechadas à imigração, e os estrangeiros sem cidadania perderão o direito de residir no país.",
            "O país desenvolverá armas nucleares próprias para afirmar sua posição de potência diante dos vizinhos.",
            "A política externa terá como princípio a supremacia do interesse nacional, com o rompimento de relações com países e blocos que se oponham às nossas decisões.",
            "O país abandonará os blocos regionais de integração e cancelará os acordos de livre comércio, adotando uma política de autossuficiência nacional.",
            "Tropas serão enviadas às áreas de fronteira disputadas para ocupá-las e afirmar a soberania do país sobre elas.",
        ],
        -1: [
            "O acordo comercial com o bloco asiático será renegociado para proteger setores da indústria nacional considerados estratégicos.",
            "Os equipamentos da Marinha e da Aeronáutica serão modernizados, com aumento moderado do orçamento de defesa.",
            "A compra de terras por estrangeiros em áreas de fronteira passará a depender de autorização prévia do governo nacional.",
            "O país continuará nas organizações internacionais, mas votará contra resoluções que interfiram em decisões internas sobre a Amazônia.",
            "A vigilância das fronteiras terrestres será reforçada com mais efetivos militares e novos radares.",
            "O governo exigirá um índice mínimo de fabricação nacional nas compras de equipamentos de defesa.",
            "A adesão a novos acordos internacionais sobre recursos naturais só ocorrerá com a garantia de que o país manterá o controle sobre sua exploração.",
            "Será criado um programa para reduzir a dependência de fornecedores estrangeiros na produção de equipamentos militares.",
        ],
        0: [
            "O país mantém relações diplomáticas com mais de 190 Estados e embaixadas em cerca de 130 capitais.",
            "Os três principais destinos das exportações nacionais são a China, os Estados Unidos e a Argentina.",
            "O efetivo atual das Forças Armadas é de aproximadamente 360 mil militares da ativa.",
            "O país participa de missões de paz das Nações Unidas desde a década de 1950.",
            "A fronteira terrestre do país tem cerca de 17 mil quilômetros e é compartilhada com dez países.",
            "Este capítulo descreve a história da política externa do país desde a redemocratização.",
            "O número de imigrantes registrados no país dobrou entre 2015 e 2025.",
            "O país é membro fundador de vários blocos regionais e de organismos multilaterais de crédito.",
        ],
        1: [
            "O país aderirá ao acordo multilateral de proteção dos oceanos e cumprirá as metas de conservação assumidas.",
            "Em conflitos entre países vizinhos, o governo dará prioridade à mediação diplomática e à negociação.",
            "A cooperação técnica com os países da região será ampliada nas áreas de saúde e de agricultura.",
            "O país apoiará o envio de mais tropas às missões de paz das Nações Unidas.",
            "Os procedimentos para acolhimento de refugiados serão simplificados, em cooperação com a agência das Nações Unidas para refugiados.",
            "O governo ratificará o tratado internacional de proibição de armas nucleares.",
            "O país terá participação mais ativa nos fóruns multilaterais, com propostas de reforma do Conselho de Segurança.",
            "O país assinará acordos de reconhecimento mútuo de diplomas e de livre circulação de trabalhadores com os países do bloco regional.",
        ],
        2: [
            "Propomos criar uma assembleia regional eleita com poder de aprovar leis que prevaleçam sobre as leis nacionais dos países membros.",
            "O país adotará uma moeda comum com os vizinhos, transferindo a política monetária a um banco central supranacional.",
            "As Forças Armadas serão progressivamente desmobilizadas, e a defesa do país ficará a cargo de um sistema internacional de segurança coletiva.",
            "O país aceitará integralmente a jurisdição de tribunais internacionais e transferirá a organismos supranacionais as decisões sobre comércio, migração e meio ambiente.",
            "Defendemos a criação de um governo mundial democrático, com instituições eleitas acima dos Estados nacionais.",
            "As fronteiras com os países do bloco serão abolidas, com cidadania comum e plena livre circulação de pessoas.",
            "O país renunciará constitucionalmente ao uso da força militar e submeterá qualquer conflito à arbitragem internacional obrigatória.",
            "Propomos uma federação dos países sul-americanos, com constituição, governo e exército comuns.",
        ],
    },
    "state": {
        -2: [
            "O presidente poderá governar por decreto, sem aprovação do Congresso, sempre que considerar a ordem pública ameaçada.",
            "Partidos e movimentos que se opuserem ao governo poderão ser suspensos, e seus dirigentes, presos preventivamente.",
            "Todas as comunicações telefônicas e pela internet serão monitoradas por um órgão central de inteligência, sem necessidade de ordem judicial.",
            "Os veículos de imprensa precisarão de autorização do governo para publicar reportagens sobre segurança e política.",
            "Manifestações públicas ficarão proibidas, salvo quando autorizadas previamente pela polícia.",
            "O mandato presidencial deixará de ter limite de reeleição, e os ministros do Supremo passarão a ser nomeados e destituídos livremente pelo presidente.",
            "As forças de segurança poderão prender suspeitos por até trinta dias sem acusação formal e sem acesso a advogado.",
            "Será criado um sistema de identificação e pontuação de todos os cidadãos, com restrições a quem desobedecer às determinações do governo.",
        ],
        -1: [
            "O efetivo das polícias militares será ampliado em 15%, e as penas para roubo com uso de arma serão aumentadas.",
            "Câmeras de reconhecimento facial serão instaladas em estádios de futebol e em grandes eventos públicos.",
            "A maioridade penal será reduzida para dezesseis anos nos casos de crimes hediondos.",
            "A progressão de regime para condenados por crimes violentos ficará mais restrita.",
            "A polícia poderá acessar dados de localização de celulares em investigações de sequestro, com autorização judicial posterior.",
            "As guardas municipais passarão a usar armas de fogo e terão mais poderes de abordagem.",
            "Será criado um cadastro nacional de condenados por crimes sexuais, com consulta liberada a escolas e empresas de transporte.",
            "A fiscalização sobre o uso de drogas em locais públicos será intensificada, com aumento das multas.",
        ],
        0: [
            "Segundo o anuário de segurança pública, o número de homicídios no país caiu 5% em 2025.",
            "O sistema prisional tem hoje cerca de 850 mil pessoas presas, das quais um terço aguarda julgamento.",
            "Este capítulo descreve a estrutura atual dos tribunais, das polícias e das defensorias públicas.",
            "O país realiza eleições gerais a cada quatro anos, com voto eletrônico desde 1996.",
            "A informatização dos processos judiciais reduziu em média 20% o tempo de tramitação nos tribunais estaduais.",
            "As delegacias passarão a usar um sistema único de registro de ocorrências, para agilizar o atendimento.",
            "O número de servidores públicos federais está praticamente estável há uma década.",
            "A última pesquisa de vitimização indicou que a maioria dos furtos não é registrada na polícia.",
        ],
        1: [
            "Os dados de gastos de todos os órgãos públicos serão publicados em tempo real e em formato aberto.",
            "A Defensoria Pública receberá mais recursos para garantir defesa gratuita a todos os acusados sem advogado.",
            "O acesso de órgãos públicos a dados pessoais dependerá sempre de autorização judicial prévia.",
            "Os conselhos municipais de saúde e de segurança terão mais vagas para representantes eleitos pela população.",
            "As audiências de custódia serão obrigatórias em até vinte e quatro horas após qualquer prisão.",
            "Será aprovada uma lei de proteção a jornalistas e a defensores de direitos humanos ameaçados.",
            "O uso de câmeras corporais pelos policiais será obrigatório, com acesso às imagens garantido à defesa.",
            "Os cidadãos poderão propor leis com menos assinaturas, e os plebiscitos sobre temas locais serão facilitados.",
        ],
        2: [
            "O porte e o consumo de todas as drogas deixarão de ser crime, e os presos por essas condutas serão libertados.",
            "A polícia militar será extinta, e os poderes de vigilância e de abordagem do Estado serão drasticamente reduzidos.",
            "As principais decisões políticas passarão a assembleias populares locais, com o esvaziamento do poder do governo central.",
            "Todos os órgãos estatais de inteligência e de monitoramento de cidadãos serão desmontados.",
            "A maior parte das penas de prisão será substituída por medidas alternativas, com o fechamento progressivo dos presídios.",
            "Nenhuma forma de expressão, inclusive a ofensiva, poderá ser punida pelo Estado, e todas as leis que permitem censura serão revogadas.",
            "Os municípios e as comunidades terão autonomia para recusar leis federais, num modelo de descentralização radical do poder.",
            "O Estado ficará proibido de coletar e armazenar dados pessoais dos cidadãos sem o consentimento expresso de cada um.",
        ],
    },
    "society": {
        -2: [
            "As políticas de educação, saúde e cultura deverão seguir os princípios morais da religião majoritária do país.",
            "A lei passará a reconhecer como família apenas a união entre homem e mulher, revogando as normas que ampliaram esse conceito.",
            "Serão revogadas as leis das últimas décadas que mudaram os costumes, restaurando as normas morais tradicionais.",
            "O ensino religioso confessional será obrigatório em todas as escolas públicas, e conteúdos contrários aos valores tradicionais serão retirados do currículo.",
            "O Estado promoverá ativamente o papel tradicional da mulher no lar, com incentivos às famílias em que apenas o homem trabalha fora.",
            "Os feriados e símbolos religiosos passarão a orientar oficialmente a vida pública, e o Estado deixará de ser laico.",
            "O divórcio voltará a ser restrito, permitido apenas em casos excepcionais definidos em lei.",
            "Toda a legislação sobre família, sexualidade e educação será reescrita para seguir a moral cristã tradicional.",
        ],
        -1: [
            "As festas religiosas e as tradições populares de cada região receberão apoio público para sua preservação.",
            "Mudanças nos conteúdos escolares sobre sexualidade e valores só ocorrerão após consulta às famílias.",
            "Alterações nas regras sobre casamento e adoção serão feitas de forma gradual e após amplo debate na sociedade.",
            "Serão criados programas de fortalecimento dos vínculos familiares, com cursos de preparação para o casamento.",
            "Os patrimônios históricos e religiosos tombados terão mais recursos para restauração e conservação.",
            "As escolas poderão oferecer, em caráter optativo, aulas sobre os valores e a história das religiões do país.",
            "As entidades religiosas que prestam assistência social terão suas parcerias com o poder público mantidas e ampliadas.",
            "A legislação sobre temas morais controversos só será alterada mediante consulta popular.",
        ],
        0: [
            "Os dados do censo mostram que o número médio de moradores por domicílio diminuiu na última década.",
            "A proporção de pessoas que se declaram sem religião passou de 8% para 10% entre os dois últimos censos.",
            "O número de casamentos registrados em cartório caiu cerca de 10% desde 2015.",
            "A idade média das mulheres no nascimento do primeiro filho aumentou nas últimas duas décadas.",
            "Serão construídas 200 escolas técnicas e instalados laboratórios de ciências em escolas públicas.",
            "Este capítulo descreve as transformações demográficas do país desde 1980.",
            "A população com 60 anos ou mais já ultrapassa 15% do total de habitantes.",
            "O investimento em pesquisa científica será ampliado, com novas bolsas para universidades e institutos.",
        ],
        1: [
            "Será criada uma política nacional de combate à discriminação de gênero e de raça no mercado de trabalho.",
            "A licença parental passará a ser compartilhada entre pai e mãe, com período igual para ambos.",
            "O currículo escolar incluirá conteúdos sobre a diversidade de arranjos familiares existentes no país.",
            "Os direitos previdenciários de casais do mesmo sexo serão equiparados aos dos demais casais.",
            "O nome social de pessoas trans será reconhecido em todos os documentos e serviços públicos.",
            "A educação sexual baseada em evidências científicas será oferecida nas escolas a partir do ensino fundamental.",
            "Serão ampliadas as cotas para pessoas negras e indígenas em concursos públicos.",
            "A pesquisa com células-tronco embrionárias terá regras mais flexíveis, definidas com base em critérios científicos.",
        ],
        2: [
            "Todas as instituições públicas serão reorganizadas para abolir a distinção de papéis entre homens e mulheres e afastar qualquer influência religiosa das decisões do Estado.",
            "A família deixará de ser definida em lei, e qualquer forma de convivência afetiva terá os mesmos direitos, sem distinção.",
            "O ensino religioso será retirado das escolas, e os símbolos religiosos serão removidos de todos os espaços públicos, numa separação radical entre religião e Estado.",
            "O aborto será legalizado em qualquer circunstância, e a legislação sobre reprodução será integralmente reescrita com base na autonomia individual.",
            "A escola será profundamente reformada para substituir a transmissão de costumes herdados por uma formação crítica voltada à transformação da sociedade.",
            "As isenções fiscais das instituições religiosas serão extintas, e as igrejas perderão qualquer papel nas políticas públicas.",
            "O casamento civil será substituído por um regime de contratos de convivência livremente definidos entre quaisquer pessoas adultas.",
            "Propomos transformar radicalmente a cultura nacional, superando os valores tradicionais sobre família, sexualidade e religião.",
        ],
    },
}

# Preenchimento: frases sobre o próprio documento, sem tema de nenhum eixo.
PREENCHIMENTO = [
    "Este documento foi organizado em capítulos temáticos, numerados na ordem em que os assuntos foram discutidos.",
    "A versão preliminar do texto circulou entre os membros da equipe durante o mês de março.",
    "Cada capítulo começa com um breve resumo e termina com uma lista das referências consultadas.",
    "As reuniões de redação ocorreram às terças-feiras, numa sala emprestada por uma biblioteca do centro da cidade.",
    "Os termos técnicos usados ao longo do texto estão reunidos num glossário no final do volume.",
    "As tabelas e figuras foram produzidas com a mesma paleta de cores para facilitar a leitura.",
    "Os números de página aparecem no canto inferior direito de cada folha.",
    "O texto final passou por revisão ortográfica e por uma leitura completa antes da impressão.",
    "As citações de outros documentos aparecem entre aspas e com a indicação da fonte.",
    "A capa traz uma fotografia da praça central tirada no início da manhã.",
    "A primeira versão tinha mais de duzentas páginas e foi encurtada para facilitar a consulta.",
    "Os capítulos podem ser lidos de forma independente, sem prejuízo da compreensão.",
    "As siglas são explicadas na primeira vez em que aparecem no texto.",
    "Um resumo de duas páginas acompanha a versão completa para quem tiver menos tempo de leitura.",
    "O documento estará disponível em formato impresso e em versão para leitura em tela.",
    "As datas citadas seguem o formato dia, mês e ano.",
    "A diagramação usa letras maiores do que o habitual para tornar a leitura mais confortável.",
    "Ao longo do texto, os quadros em destaque reúnem exemplos e explicações complementares.",
    "As notas de rodapé foram reduzidas ao mínimo para não interromper a leitura.",
    "A equipe de redação reuniu profissionais de diferentes áreas, que trabalharam juntos durante vários meses.",
    "O sumário, no início do volume, indica a página de cada capítulo e de cada seção.",
    "A numeração dos itens recomeça em cada capítulo, precedida pela letra do tema.",
    "As ilustrações internas foram feitas à mão e depois digitalizadas.",
    "A impressão foi feita em papel de gramatura média, com capa em papel mais resistente.",
    "Os anexos trazem os mapas usados nas reuniões e a lista de documentos consultados.",
    "Cada seção tem um título curto que resume o assunto tratado.",
    "O texto evita repetições e remete, quando necessário, a capítulos anteriores.",
    "A última página traz os contatos da equipe para o envio de correções sobre o texto.",
    "Os gráficos trazem, logo abaixo do título, a fonte dos dados e o período a que se referem.",
    "Os parágrafos foram mantidos curtos, com uma ideia principal em cada um.",
    "A fonte escolhida para o corpo do texto é a mesma usada nos títulos, em tamanho menor.",
    "As margens das páginas foram ampliadas para permitir anotações à mão durante a leitura.",
    "A revisão final foi feita por duas pessoas que não participaram da redação.",
    "Os nomes dos capítulos aparecem no alto de cada página par.",
    "O volume tem cerca de oitenta páginas, contando os anexos e o glossário.",
    "Algumas seções foram reescritas depois da leitura em voz alta numa das reuniões da equipe.",
    "As listas foram organizadas em ordem alfabética sempre que não havia outra ordem mais útil.",
    "A versão para leitura em tela tem links que levam diretamente a cada capítulo.",
    "O texto usa a mesma grafia para os nomes próprios em todas as seções.",
    "Cada anexo começa numa página nova e tem numeração própria.",
    "As imagens foram escolhidas entre fotografias feitas pela própria equipe ao longo do trabalho.",
    "Os títulos das seções foram escritos de forma a indicar logo o assunto de cada uma.",
    "Na abertura do volume, uma página explica como as seções estão numeradas.",
    "A equipe preferiu frases diretas e evitou palavras pouco usadas no dia a dia.",
    "Os rascunhos anteriores foram guardados numa pasta compartilhada pela equipe.",
    "O índice remissivo, no final, lista os principais termos e as páginas em que aparecem.",
    "Cada capítulo tem, em média, seis páginas.",
    "A contracapa traz apenas o título do documento e o ano de publicação.",
]

# Composição por tamanho: número de frases de posição e de preenchimento.
# simples: (posição, preenchimento); duplo: (posição por eixo, preenchimento);
# misto: (frases de cada polo, preenchimento); nenhum: preenchimento.
# Até muito_longo, cerca de 1/3 das frases têm posição. "muito_longo" fica perto do chunk
# de 600 tokens usado no documento; "extra" tem o mesmo conteúdo de posição de
# "muito_longo" diluído em ~2x mais texto: mede o custo e o efeito de chunks maiores.
TAMANHOS = {
    "curto":       {"simples": (1, 0), "duplo": (1, 0), "misto": (1, 0), "nenhum": 2},
    "medio":       {"simples": (2, 2), "duplo": (1, 2), "misto": (1, 2), "nenhum": 4},
    "longo":       {"simples": (4, 6), "duplo": (2, 6), "misto": (2, 6), "nenhum": 10},
    "muito_longo": {"simples": (8, 16), "duplo": (4, 16), "misto": (4, 16), "nenhum": 24},
    "extra":       {"simples": (8, 40), "duplo": (4, 40), "misto": (4, 40), "nenhum": 48},
}

# Pares de eixos com direção, cobrindo cada eixo 4 vezes e cada polo e intensidade.
COMBINACOES_DUPLO = [
    (("economic", 2), ("society", 1)),
    (("economic", -1), ("state", -2)),
    (("diplomatic", -2), ("society", -1)),
    (("diplomatic", 1), ("state", 2)),
    (("state", -1), ("society", -2)),
    (("economic", 1), ("diplomatic", -1)),
    (("state", 1), ("economic", -2)),
    (("society", 2), ("diplomatic", 2)),
]
# Frases de posição usadas por tipo (o banco tem 8 por eixo e nível); os tipos usam
# trechos diferentes do banco quando possível. Os textos de "nenhum" variam o preenchimento.
INICIO_POSICAO = {"simples": 0, "duplo": 4, "misto": 4}
FRASES_POR_PARAGRAFO = 4


def _gabarito_vazio():
    return {eixo: {"relevante": False, "nivel": None} for eixo in EIXOS}


def _montar(id_texto, frases_posicao, n_preenchimento, desloc_preenchimento):
    """Embaralha posição e preenchimento com semente própria do texto e agrupa em parágrafos."""
    preench = [
        {"tipo": "preenchimento", "eixo": None, "nivel": None, "indice": (desloc_preenchimento + i) % len(PREENCHIMENTO),
         "frase": PREENCHIMENTO[(desloc_preenchimento + i) % len(PREENCHIMENTO)]}
        for i in range(n_preenchimento)
    ]
    frases = frases_posicao + preench
    rng = random.Random(f"{SEMENTE}-{id_texto}")
    rng.shuffle(frases)
    paragrafos = [frases[i:i + FRASES_POR_PARAGRAFO] for i in range(0, len(frases), FRASES_POR_PARAGRAFO)]
    texto = "\n\n".join(" ".join(f["frase"] for f in p) for p in paragrafos)
    return texto, frases


def _posicao(eixo, nivel, inicio, n):
    banco = FRASES[eixo][nivel]
    if inicio + n > len(banco):
        raise ValueError(f"Banco insuficiente para {eixo} {nivel}: {inicio}+{n} > {len(banco)}.")
    return [{"tipo": "posicao", "eixo": eixo, "nivel": nivel, "indice": inicio + i, "frase": banco[inicio + i]}
            for i in range(n)]


def gerar():
    enc = tiktoken.get_encoding("cl100k_base")
    itens = []
    for tamanho, comp in TAMANHOS.items():
        n_pos, n_pre = comp["simples"]
        for eixo in EIXOS:
            for nivel in NIVEIS:
                id_texto = f"{tamanho}-simples-{eixo}-{nivel:+d}"
                texto, frases = _montar(id_texto, _posicao(eixo, nivel, INICIO_POSICAO["simples"], n_pos),
                                        n_pre, EIXOS.index(eixo) * 5 + NIVEIS.index(nivel))
                gabarito = _gabarito_vazio()
                # Diagnóstico do tema: relevância aceita nos dois sentidos; nível 0 se relevante.
                gabarito[eixo] = {"relevante": None if nivel == 0 else True, "nivel": nivel}
                itens.append({"id": id_texto, "tamanho": tamanho, "tipo": "simples",
                              "eixos_alvo": [eixo], "texto": texto, "gabarito": gabarito, "frases": frases})

        n_pos, n_pre = comp["duplo"]
        for k, ((e1, n1), (e2, n2)) in enumerate(COMBINACOES_DUPLO):
            id_texto = f"{tamanho}-duplo-{k}-{e1}{n1:+d}-{e2}{n2:+d}"
            posicao = (_posicao(e1, n1, INICIO_POSICAO["duplo"], n_pos)
                       + _posicao(e2, n2, INICIO_POSICAO["duplo"], n_pos))
            texto, frases = _montar(id_texto, posicao, n_pre, 3 * k)
            gabarito = _gabarito_vazio()
            gabarito[e1] = {"relevante": True, "nivel": n1}
            gabarito[e2] = {"relevante": True, "nivel": n2}
            itens.append({"id": id_texto, "tamanho": tamanho, "tipo": "duplo",
                          "eixos_alvo": [e1, e2], "texto": texto, "gabarito": gabarito, "frases": frases})

        n_pos, n_pre = comp["misto"]
        for eixo in EIXOS:
            id_texto = f"{tamanho}-misto-{eixo}"
            posicao = (_posicao(eixo, 1, INICIO_POSICAO["misto"], n_pos)
                       + _posicao(eixo, -1, INICIO_POSICAO["misto"], n_pos))
            texto, frases = _montar(id_texto, posicao, n_pre, 7 * EIXOS.index(eixo) + 2)
            gabarito = _gabarito_vazio()
            gabarito[eixo] = {"relevante": True, "nivel": 0}
            itens.append({"id": id_texto, "tamanho": tamanho, "tipo": "misto",
                          "eixos_alvo": [eixo], "texto": texto, "gabarito": gabarito, "frases": frases})

        for k in range(4):
            id_texto = f"{tamanho}-nenhum-{k}"
            texto, frases = _montar(id_texto, [], comp["nenhum"], 7 * k)
            itens.append({"id": id_texto, "tamanho": tamanho, "tipo": "nenhum", "eixos_alvo": [],
                          "texto": texto, "gabarito": _gabarito_vazio(), "frases": frases})

    for item in itens:
        item["n_tokens"] = len(enc.encode(item["texto"]))
        item["n_palavras"] = len(item["texto"].split())
        item["n_frases"] = len(item["frases"])
        item["n_frases_posicao"] = sum(f["tipo"] == "posicao" for f in item["frases"])
        item["sha256"] = hashlib.sha256(item["texto"].encode("utf-8")).hexdigest()
    assert len({i["id"] for i in itens}) == len(itens)
    assert len({i["sha256"] for i in itens}) == len(itens), "Há textos repetidos."
    return itens


def main():
    itens = gerar()
    base = {
        "descricao": "Base sintética rotulada por eixo e nível, em 5 tamanhos (ver docstring do gerador).",
        "semente": SEMENTE,
        "tamanhos": {k: {t: list(v) if isinstance(v, tuple) else v for t, v in c.items()}
                     for k, c in TAMANHOS.items()},
        "itens": itens,
    }
    SAIDA.write_text(json.dumps(base, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(itens)} textos gravados em {SAIDA}")
    for tamanho in TAMANHOS:
        toks = sorted(i["n_tokens"] for i in itens if i["tamanho"] == tamanho)
        print(f"  {tamanho:<12} n={len(toks):3d}  tokens min={toks[0]:4d}  mediana={toks[len(toks) // 2]:4d}  max={toks[-1]:4d}")


if __name__ == "__main__":
    main()
