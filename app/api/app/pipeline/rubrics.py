# Rubricas extraídas de Pipeline - Passo a Passo.ipynb (pesquisa local).
SITUACAO_SEM_POSICAO = (
    "O trecho trata do tema, mas não defende nenhum dos polos: descreve, diagnostica, "
    "lista ações sem escolher entre os polos ou combina os dois sem predominância."
)
AXIS_SPECS = {
    "economic": {
        "effect": "econ",
        "name": "economia",
        "topic": (
            "distribuição de renda e riqueza, desigualdade econômica, tributação, políticas "
            "sociais, serviços públicos, propriedade dos meios de produção, regulação econômica, "
            "intervenção estatal, privatização, livre mercado, concorrência, relações de trabalho "
            "ou política fiscal"
        ),
        "poles": {
            "A": {
                "id": "equality",
                "label": "Igualdade",
                "description": (
                    "Redução das desigualdades econômicas e sociais.\n"
                    "Distribuição mais equilibrada de renda, riqueza, recursos e oportunidades.\n"
                    "Tributação progressiva e políticas de redistribuição de renda.\n"
                    "Ação do Estado para reduzir desigualdades econômicas e remover obstáculos sociais.\n"
                    "Proteção econômica aos grupos socialmente e economicamente menos favorecidos.\n"
                    "Limitação da concentração de riqueza e de poder econômico.\n"
                    "Maior participação pública, coletiva ou social na propriedade e na organização da economia.\n"
                    "Priorização da igualdade econômica mesmo quando isso exige maior intervenção estatal."
                ),
            },
            "B": {
                "id": "wealth",
                "label": "Mercado",
                "description": (
                    "Livre iniciativa econômica e propriedade privada.\n"
                    "Autonomia dos indivíduos e das empresas para tomar decisões econômicas.\n"
                    "Concorrência como mecanismo de organização da economia.\n"
                    "Liberdade de produção, investimento, contratação e consumo.\n"
                    "Organização descentralizada da atividade econômica por mecanismos de mercado.\n"
                    "Redução da intervenção direta e do planejamento estatal da economia.\n"
                    "Defesa da propriedade particular e da iniciativa econômica individual.\n"
                    "Privatização, desregulamentação e maior liberdade para o funcionamento dos mercados.\n"
                    "Intervenção estatal limitada à garantia de direitos, contratos e regras de concorrência."
                ),
            },
        },
        "note": (
            "Mencionar um serviço público, um programa social ou a responsabilidade fiscal, sem "
            "escolher entre os polos, não indica posição."
        ),
        # Situações concretas por nível; exemplos ainda sujeitos à validação humana.
        "intensity_anchors": {
            "polo_B_forte": {
                "situacao": "Propõe reduzir de forma ampla e estrutural o papel do Estado na economia, transferindo-o ao mercado.",
                "exemplos": ["privatizar a maior parte das empresas e dos serviços estatais",
                             "cortar amplamente tributos e gastos públicos e desregulamentar a economia em geral"],
            },
            "polo_B_moderado": {
                "situacao": "Propõe medidas pontuais ou graduais na direção do mercado, mantendo a estrutura existente.",
                "exemplos": ["conceder à iniciativa privada a gestão de alguns serviços ou obras",
                             "simplificar tributos ou conter o crescimento do gasto público"],
            },
            "sem_posicao": {
                "situacao": SITUACAO_SEM_POSICAO,
                "exemplos": ["apresentar dados ou diagnóstico sobre emprego, renda ou contas públicas",
                             "prometer crescimento ou eficiência sem dizer se o meio é o Estado ou o mercado"],
            },
            "polo_A_moderado": {
                "situacao": "Propõe medidas pontuais ou graduais na direção da igualdade econômica, mantendo a estrutura existente.",
                "exemplos": ["ampliar de forma focalizada um programa social ou serviço público",
                             "tornar um tributo específico mais progressivo"],
            },
            "polo_A_forte": {
                "situacao": "Propõe ampliar de forma ampla e estrutural o papel do Estado para redistribuir renda, riqueza ou propriedade.",
                "exemplos": ["estatizar setores inteiros da economia",
                             "redistribuir amplamente renda, riqueza ou propriedade, ou planejar centralmente a economia"],
            },
        },
    },
    "diplomatic": {
        "effect": "dipl",
        "name": "relações internacionais e soberania",
        "topic": (
            "política externa, diplomacia, relações entre países, cooperação internacional, "
            "organizações internacionais, integração regional ou global, soberania nacional, "
            "nacionalismo, fronteiras, imigração, defesa nacional, forças armadas, conflitos, "
            "guerra, intervenção militar ou projeção de poder"
        ),
        "poles": {
            "A": {
                "id": "peace",
                "label": "Globo",
                "description": (
                    "Cooperação política entre diferentes povos e Estados.\n"
                    "Solidariedade e interdependência internacional.\n"
                    "Soluções multilaterais para problemas que ultrapassam as fronteiras nacionais.\n"
                    "Integração econômica, jurídica e política entre países.\n"
                    "Fortalecimento de instituições internacionais e supranacionais.\n"
                    "Compartilhamento de parcelas da soberania para solucionar problemas comuns.\n"
                    "Construção de estruturas federativas ou supranacionais acima dos Estados.\n"
                    "Valorização de interesses e direitos universais para além da pertença nacional.\n"
                    "Maior integração política da humanidade."
                ),
            },
            "B": {
                "id": "might",
                "label": "Nação",
                "description": (
                    "Soberania e independência do Estado nacional.\n"
                    "Autodeterminação política dos povos.\n"
                    "Prioridade das decisões tomadas pela própria comunidade nacional.\n"
                    "Valorização da identidade, história, cultura e instituições nacionais.\n"
                    "Preservação da autonomia nacional diante de interferências externas.\n"
                    "Prioridade dos interesses nacionais quando entram em conflito com interesses internacionais.\n"
                    "Manutenção da soberania estatal sobre decisões políticas fundamentais.\n"
                    "Valorização da coesão e da unidade nacional."
                ),
            },
        },
        "note": (
            "Mencionar soberania setorial (alimentar, energética, digital, sanitária) ou "
            "cooperação técnica, sem conflito entre autonomia nacional e compromissos "
            "internacionais ou entre força e diplomacia, não indica posição."
        ),
        # Situações concretas por nível; exemplos ainda sujeitos à validação humana.
        "intensity_anchors": {
            "polo_B_forte": {
                "situacao": "Propõe subordinar amplamente compromissos e instituições internacionais ao interesse nacional, ou ampliar fortemente o poder militar e a disposição de usar a força.",
                "exemplos": ["sair de organismos ou tratados internacionais",
                             "ampliar fortemente as forças armadas para impor interesses nacionais"],
            },
            "polo_B_moderado": {
                "situacao": "Propõe priorizar a autonomia nacional ou a defesa em questões específicas, mantendo os compromissos internacionais existentes.",
                "exemplos": ["renegociar um acordo considerado desfavorável ao país",
                             "modernizar a defesa nacional"],
            },
            "sem_posicao": {
                "situacao": SITUACAO_SEM_POSICAO,
                "exemplos": ["descrever relações diplomáticas ou o comércio exterior",
                             "mencionar soberania setorial (alimentar, energética, digital) sem conflito entre autonomia nacional e compromissos internacionais"],
            },
            "polo_A_moderado": {
                "situacao": "Propõe ampliar a cooperação internacional ou a solução negociada de conflitos em questões específicas.",
                "exemplos": ["aderir a um acordo multilateral",
                             "priorizar a mediação diplomática em conflitos"],
            },
            "polo_A_forte": {
                "situacao": "Propõe transferir amplamente competências a instituições supranacionais, integração política profunda entre países ou renúncia ao uso da força.",
                "exemplos": ["criar instituições comuns acima dos Estados nacionais",
                             "reduzir amplamente as forças armadas em favor de mecanismos internacionais"],
            },
        },
    },
    "state": {
        "effect": "govt",
        "name": "liberdade civil e autoridade estatal",
        "topic": (
            "liberdades civis, direitos individuais, democracia, participação política, liberdade "
            "de expressão, privacidade, vigilância, censura, segurança interna, ordem pública, "
            "lei e ordem, polícia, punição, coerção estatal, hierarquia, obediência e disciplina, "
            "autoridade e força da liderança política, intervenção do Estado na vida privada, "
            "concentração de poder ou limites ao poder governamental"
        ),
        "poles": {
            "A": {
                "id": "liberty",
                "label": "Liberdade",
                "description": (
                    "Proteção da autonomia individual diante do poder político.\n"
                    "Garantia das liberdades civis e políticas.\n"
                    "Liberdade de expressão, imprensa, reunião, associação e participação política.\n"
                    "Pluralismo político, social e ideológico.\n"
                    "Limitação jurídica do poder do Estado.\n"
                    "Existência de diferentes grupos, organizações e centros de poder autônomos.\n"
                    "Proteção dos direitos individuais contra interferências e restrições estatais.\n"
                    "Controle dos governantes por instituições representativas e pela participação dos cidadãos.\n"
                    "Resistência à censura, vigilância excessiva e concentração do poder político."
                ),
            },
            "B": {
                "id": "authority",
                "label": "Autoridade",
                "description": (
                    "Concentração e centralização do poder político.\n"
                    "Hierarquia, disciplina e obediência como princípios de organização social.\n"
                    "Prioridade da ordem e da estabilidade sobre a autonomia individual.\n"
                    "Fortalecimento da autoridade do Estado e do poder executivo.\n"
                    "Redução da autonomia de grupos e instituições diante do governo.\n"
                    "Restrição do pluralismo e da oposição política.\n"
                    "Limitação da participação política quando considerada incompatível com a ordem.\n"
                    "Uso de mecanismos coercitivos para assegurar o cumprimento das decisões políticas.\n"
                    "Subordinação dos indivíduos e grupos à autoridade política central."
                ),
            },
        },
        "note": (
            "Melhorias de gestão ou de eficiência em serviços públicos, inclusive de segurança, "
            "sem ampliar ou limitar poderes coercitivos do Estado ou liberdades individuais, não "
            "indicam posição."
        ),
        # Situações concretas por nível; exemplos ainda sujeitos à validação humana.
        "intensity_anchors": {
            "polo_B_forte": {
                "situacao": "Propõe concentrar o poder político ou restringir amplamente liberdades civis e políticas.",
                "exemplos": ["permitir que o governo restrinja a oposição, a imprensa ou manifestações",
                             "ampliar de forma geral a vigilância e a censura"],
            },
            "polo_B_moderado": {
                "situacao": "Propõe ampliar poderes coercitivos, de fiscalização ou de punição do Estado em áreas específicas, mantendo as liberdades civis.",
                "exemplos": ["endurecer penas ou ampliar poderes da polícia",
                             "ampliar a fiscalização estatal sobre condutas individuais numa área"],
            },
            "sem_posicao": {
                "situacao": SITUACAO_SEM_POSICAO,
                "exemplos": ["apresentar estatísticas de segurança ou da administração pública",
                             "melhorar a gestão de serviços, inclusive de segurança, sem ampliar nem limitar poderes coercitivos ou liberdades"],
            },
            "polo_A_moderado": {
                "situacao": "Propõe ampliar garantias individuais, transparência ou participação em áreas específicas, mantendo os poderes do Estado.",
                "exemplos": ["fortalecer o direito de defesa ou a proteção de dados pessoais",
                             "ampliar a transparência ou a participação em conselhos"],
            },
            "polo_A_forte": {
                "situacao": "Propõe reduzir amplamente os poderes coercitivos do Estado ou descentralizar radicalmente o poder político.",
                "exemplos": ["descriminalizar amplamente condutas individuais",
                             "desmontar de forma geral estruturas de vigilância e de polícia"],
            },
        },
    },
    "society": {
        "effect": "scty",
        "name": "progresso e tradição social",
        "topic": (
            "valores sociais e culturais, costumes, religião, secularismo, família, sexualidade, "
            "papéis sociais, moralidade, mudança social, tradição, ciência, tecnologia, educação, "
            "meio ambiente ou transformação cultural"
        ),
        "poles": {
            "A": {
                "id": "progress",
                "label": "Progresso",
                "description": (
                    "Transformação consciente das instituições sociais e políticas.\n"
                    "Confiança na capacidade humana de melhorar a sociedade.\n"
                    "Uso da razão, da ciência, do conhecimento e da crítica para avaliar instituições existentes.\n"
                    "Questionamento de tradições consideradas injustas, irracionais ou ultrapassadas.\n"
                    "Mudança social como possibilidade de aperfeiçoamento das condições humanas.\n"
                    "Reforma de instituições diante de novos conhecimentos e necessidades sociais.\n"
                    "Participação ativa dos indivíduos na transformação histórica da sociedade.\n"
                    "Superação de estruturas sociais consideradas inadequadas.\n"
                    "Valorização do aperfeiçoamento futuro em relação às condições existentes."
                ),
            },
            "B": {
                "id": "tradition",
                "label": "Tradição",
                "description": (
                    "Preservação de instituições, costumes e valores desenvolvidos historicamente.\n"
                    "Valorização da continuidade e da estabilidade social.\n"
                    "Preferência por mudanças graduais em vez de transformações profundas ou abruptas.\n"
                    "Confiança na experiência histórica acumulada pelas instituições sociais.\n"
                    "Cautela diante de projetos de reorganização racional e radical da sociedade.\n"
                    "Preservação de estruturas sociais consideradas fundamentais para a ordem.\n"
                    "Valorização da tradição, da família, da religião, da autoridade e da moral histórica.\n"
                    "Resistência à ruptura com práticas e instituições consolidadas.\n"
                    "Mudança social condicionada à preservação de elementos essenciais da ordem existente."
                ),
            },
        },
        "note": (
            "Mencionar ciência, tecnologia, educação ou meio ambiente, sem posição sobre valores, "
            "costumes, religião, família ou mudança social, não indica posição."
        ),
        # Situações concretas por nível; exemplos ainda sujeitos à validação humana.
        "intensity_anchors": {
            "polo_B_forte": {
                "situacao": "Propõe que o Estado restaure ou imponha amplamente normas morais, religiosas ou familiares tradicionais.",
                "exemplos": ["orientar as políticas públicas por uma moral religiosa",
                             "reverter amplamente, por meio da lei, mudanças recentes nos costumes"],
            },
            "polo_B_moderado": {
                "situacao": "Propõe preservar instituições, costumes ou valores tradicionais em temas específicos, ou só admitir mudanças graduais.",
                "exemplos": ["proteger uma tradição cultural ou religiosa específica",
                             "exigir consulta às famílias antes de mudar conteúdos escolares sobre valores"],
            },
            "sem_posicao": {
                "situacao": SITUACAO_SEM_POSICAO,
                "exemplos": ["descrever mudanças demográficas ou culturais",
                             "propor investimentos em ciência, tecnologia, educação ou meio ambiente sem posição sobre valores e costumes"],
            },
            "polo_A_moderado": {
                "situacao": "Propõe revisar normas, costumes ou papéis sociais em temas específicos.",
                "exemplos": ["ampliar direitos de um grupo historicamente discriminado",
                             "atualizar uma norma social específica"],
            },
            "polo_A_forte": {
                "situacao": "Propõe transformar amplamente instituições sociais, costumes ou papéis tradicionais.",
                "exemplos": ["reformar profundamente instituições como família, escola e religião",
                             "abolir de forma geral costumes e normas morais herdados"],
            },
        },
    },
}
