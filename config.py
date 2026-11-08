# -*- coding: utf-8 -*-
"""
CONFIGURAÇÃO DA REVISÃO
=======================

Único arquivo que precisa ser editado para aplicar o protocolo a outro tema.
Os demais arquivos são a máquina de busca, triagem e codificação, e não
conhecem nada sobre o objeto de estudo.

O que editar para adaptar a outro objeto:

  1. PERIODO      — recorte temporal
  2. IDIOMAS      — línguas em que a busca será disparada
  3. BLOCOS       — os blocos conceituais da equação, por idioma
  4. BASES        — os acervos a consultar e sua tecnologia de acesso
  5. CRITERIOS    — o que torna um trabalho elegível
  6. EXCLUSAO     — o que exclui um trabalho mesmo elegível
  7. LEXICO       — os atributos a codificar em cada trabalho incluído

A configuração abaixo é a do estudo de referência (mapeamento de áreas úmidas
por sensoriamento remoto orbital), servindo de exemplo comentado.

PRINCÍPIO DAS TRÊS LÍNGUAS
--------------------------
A busca é disparada em inglês, português e espanhol. Cada idioma tem seu
próprio bloco de termos, porque bases multilíngues (OpenAlex, Crossref)
indexam produção nas três línguas e uma busca só em inglês subestima a
produção ibero-americana. As equações por idioma são unidas na consolidação.
"""

# ---------------------------------------------------------------- RECORTE ---
PERIODO = (2020, 2026)          # (ano inicial, ano final), inclusive

# ---------------------------------------------------------------- IDIOMAS ---
IDIOMAS = ["en", "pt", "es"]

# ------------------------------------------------------ BLOCOS DA EQUAÇÃO ---
# Três blocos conceituais por idioma: tema (objeto) x fonte (sensor) x
# abordagem (componente temporal OU esforço de classificação).
#
# A equação é  (tema) AND (fonte) AND (abordagem).  O terceiro bloco reúne
# série temporal e classificação porque a elegibilidade (CRITERIOS) exige um
# OU outro — ver 'abordagem_*' abaixo, marcados obrigatorio=False.
#
# Termos compostos vão entre aspas: '"área úmida"'.
BLOCOS = {
    "en": {
        "tema": ["wetland", "wetlands", "floodplain", "mangrove", "marsh",
                 "swamp", "bog", "fen", "peatland", '"tidal flat"'],
        "fonte": ["Sentinel-1", "Sentinel-2", "SAR",
                  '"synthetic aperture radar"', "Landsat", "MODIS", "MSI",
                  '"remote sensing"', "CBERS", "PlanetScope"],
        "abordagem": ['"time series"', "multitemporal", '"change detection"',
                      '"temporal analysis"', '"long-term monitoring"',
                      '"inter-annual"', '"intra-annual"', "classification",
                      "mapping", "OBIA"],
    },
    "pt": {
        "tema": ['"área úmida"', '"áreas úmidas"', '"zona úmida"', "pantanal",
                 "várzea", "manguezal", "mangue", "banhado", "brejo",
                 "turfeira", '"planície de inundação"', "igapó", "vereda",
                 '"campo alagado"'],
        "fonte": ["Sentinel", "Landsat", "MODIS", "SAR", "radar",
                  '"radar de abertura sintética"', '"sensoriamento remoto"',
                  "CBERS"],
        "abordagem": ['"série temporal"', "multitemporal",
                      '"detecção de mudança"', '"análise temporal"',
                      '"espaço-temporal"', "interanual", "classificação",
                      "mapeamento", "tipologia"],
    },
    "es": {
        "tema": ["humedal", "humedales", '"zona húmeda"', "manglar",
                 "marisma", "ciénaga", "pantano", "turbera",
                 '"llanura de inundación"', "bañado", "estero"],
        "fonte": ["Sentinel", "Landsat", "MODIS", "SAR", "radar",
                  '"radar de apertura sintética"', "teledetección",
                  '"percepción remota"', "CBERS"],
        "abordagem": ['"serie temporal"', "multitemporal",
                      '"detección de cambios"', '"análisis temporal"',
                      "interanual", "clasificación", "cartografía", "mapeo"],
    },
}

# --------------------------------------------------------------- ACERVOS ----
# Registro das bases. Cada uma declara:
#   tipo        — adaptador em buscar.py que sabe consultá-la
#   endpoint    — URL da interface de programação
#   automatica  — True se pode ser consultada sem intervenção manual
#   chave_env   — nome da variável de ambiente com a chave, se exigir
#   consulta    — 'boolean' (aceita a equação inteira) ou 'matriz'
#                 (não aceita parênteses; termos expandidos em pares)
#   nota        — observação de reprodutibilidade
#
# Para incluir outro acervo, acrescente uma entrada com o tipo correspondente.
BASES = {
    # ---- Bases internacionais com interface aberta e busca booleana --------
    "openalex": {
        "tipo": "openalex", "automatica": True, "consulta": "boolean",
        "endpoint": "https://api.openalex.org/works",
        "chave_env": None,   # opcional: OPENALEX_MAILTO para o 'polite pool'
        "nota": "Índice aberto; aceita AND/OR/parênteses no parâmetro search.",
    },
    # Crossref e Semantic Scholar ficaram fora da execução de referência, que
    # consultou quatro acervos. Os adaptadores seguem prontos em buscar.py:
    # para usá-los, ponha automatica=True.
    "crossref": {
        "tipo": "crossref", "automatica": False, "consulta": "matriz",
        "endpoint": "https://api.crossref.org/works",
        "chave_env": None,   # opcional: CROSSREF_MAILTO para o 'polite pool'
        "nota": "query.bibliographic é texto livre ranqueado; sem booleano. "
                "Resumo frequentemente ausente — limita a triagem.",
    },
    "semanticscholar": {
        "tipo": "semanticscholar", "automatica": False, "consulta": "matriz",
        "endpoint": "https://api.semanticscholar.org/graph/v1/paper/search",
        "chave_env": "S2_API_KEY",   # opcional; sem chave há limite de taxa
        "nota": "Busca por texto livre; limite de taxa sem chave.",
    },
    "core": {
        "tipo": "core", "automatica": True, "consulta": "boolean",
        "endpoint": "https://api.core.ac.uk/v3/search/works",
        "chave_env": "CORE_API_KEY",   # OBRIGATÓRIA; grátis mediante cadastro
        "nota": "Agrega repositórios abertos. Exige chave gratuita.",
    },
    # ---- Repositórios nacionais sobre VuFind (matriz de consultas) ---------
    "oasisbr": {
        "tipo": "vufind", "automatica": True, "consulta": "matriz",
        "endpoint": "https://oasisbr.ibict.br/vufind/api/v1/search",
        "chave_env": None,
        "nota": "IBICT. Ver notas de HTTP 500 e field[]=rawData em buscar.py.",
    },
    # BDTD desativada na versão final: seus 121 elegíveis na execução de
    # referência já tinham vindo pela OASISBR, que colhe teses do mesmo
    # repositório do IBICT. Para reativá-la, ponha automatica=True.
    "bdtd": {
        "tipo": "vufind", "automatica": False, "consulta": "matriz",
        "endpoint": "https://bdtd.ibict.br/vufind/api/v1/search",
        "chave_env": None,
        "nota": "IBICT. Teses e dissertações brasileiras. Contida na OASISBR "
                "na execução de referência.",
    },
    # ---- Bases NÃO automatizáveis (documentadas para transparência) --------
    # Mantidas aqui com automatica=False para que a escolha fique explícita.
    # SciELO removida do registro: sem API pública de recuperação, sua via
    # dependeria de exportação manual em RIS, incompatível com a execução
    # reprodutível deste levantamento (decisão registrada em jul/2026).
    "redalyc": {
        "tipo": "manual", "automatica": False, "consulta": None,
        "endpoint": "https://www.redalyc.org",
        "chave_env": None,
        "nota": "Sem API pública. Viés temático para ciências sociais.",
    },
    "lareferencia": {
        "tipo": "oai", "automatica": False, "consulta": None,
        "endpoint": "http://www.lareferencia.info/vufind/OAI/Server",
        "chave_env": None,
        "nota": "Agregador OAI-PMH ibero-americano: coleta por harvesting, "
                "não por busca de termos. Exige estratégia distinta.",
    },
    "base": {
        "tipo": "manual", "automatica": False, "consulta": None,
        "endpoint": "https://www.base-search.net",
        "chave_env": None,
        "nota": "BASE (Bielefeld). Interface de programação restrita a IPs "
                "cadastrados; não abertamente automatizável.",
    },
}

# -------------------------------------------------------------- CRITÉRIOS ---
# Elegível = satisfaz TODOS os obrigatorio=True e ao menos um obrigatorio=False.
# Padrões são expressões regulares sobre o texto sem acento, minúsculo,
# formado por título + resumo + palavras-chave. Cobrem as três línguas.
CRITERIOS = {
    "objeto": {
        "obrigatorio": True,
        "descricao": "o objeto de estudo é uma área úmida",
        "padroes": [
            r"area[s]? umida", r"zona[s]? umida", r"wetland", r"pantanal",
            r"varzea", r"manguezal", r"mangue\b", r"mangrove", r"manglar",
            r"banhado", r"bañado", r"brejo", r"turfeira", r"turbera",
            r"planicie de inundacao", r"llanura de inundacion", r"floodplain",
            r"marsh", r"marisma", r"swamp", r"pantano", r"cienaga",
            r"\bbog\b", r"\bfen\b", r"peatland", r"palustre", r"vereda",
            r"igapo", r"estero", r"tidal flat",
        ],
    },
    "fonte_de_dados": {
        "obrigatorio": True,
        "descricao": "emprega imagem orbital óptica ou de radar",
        "padroes": [
            r"sentinel", r"landsat", r"modis", r"\bsar\b", r"radar",
            r"\bcbers\b", r"planetscope", r"rapideye", r"worldview",
            r"sensoriamento remoto", r"remote sensing", r"teledeteccion",
            r"percepcion remota", r"teledetec", r"satelit", r"orbital",
            r"\bndvi\b", r"\bndwi\b", r"mndwi",
        ],
    },
    "abordagem_temporal": {
        "obrigatorio": False,
        "descricao": "apresenta componente temporal explícito",
        "padroes": [
            r"serie[s]? temporal", r"multitemporal", r"multi-temporal",
            r"time series", r"espaco-?temporal", r"deteccao de mudanca",
            r"deteccion de cambios", r"change detection", r"analise temporal",
            r"analisis temporal", r"interanual", r"inter-annual",
            r"monitoramento", r"monitoreo", r"\d{4}\s*[-a–]{1,3}\s*\d{4}",
            # vocabulário conceitual temporal da produção ibero-americana
            r"sazonal", r"sazonalidade", r"estacional",
            r"evolucao da paisagem", r"evolucao temporal",
            r"pulso de inundac", r"hidroperiodo", r"multi[- ]?ano",
            r"decada", r"decadal",
        ],
    },
    "abordagem_classificatoria": {
        "obrigatorio": False,
        "descricao": "apresenta esforço de classificação ou tipificação",
        "padroes": [
            r"classificacao", r"classification", r"clasificacion",
            r"tipologia", r"tipificacao", r"mapeamento", r"mapping", r"mapeo",
            r"cartografia", r"delimitacao", r"identificacao", r"\bobia\b",
        ],
    },
}

# Exclusões: se qualquer padrão casar, o trabalho é excluído mesmo elegível.
EXCLUSAO = [
    r"tratamento de efluente", r"wetland construid", r"constructed wetland",
    r"humedal construid", r"aguas residuai", r"zona de raizes",
]

# Tipos documentais a descartar (ex.: pareceres de avaliação na OpenAlex).
TIPOS_DESCARTADOS = ["peer-review", "editorial", "erratum", "paratext"]

# ----------------------------------------------------------------- LÉXICO ---
# Atributos a codificar em cada trabalho incluído. Cada chave vira coluna
# binária. Cobrem as três línguas.
LEXICO = {
    "sensor_sentinel1":  ([r"sentinel[- ]?1", r"\bs1\b"], "sensor_sentinel1_sar"),
    "sensor_sentinel2":  ([r"sentinel[- ]?2", r"\bmsi\b"], "sensor_sentinel2_optico"),
    "sensor_landsat":    ([r"landsat", r"\boli\b", r"\betm\+?\b"], "sensor_landsat"),
    "sensor_modis":      ([r"modis"], "sensor_modis"),
    "sensor_sar":        ([r"sentinel[- ]?1", r"\bsar\b", r"synthetic aperture radar",
                           r"radar de abertura", r"radar de apertura",
                           r"radarsat", r"palsar", r"backscatter"], "sensor_sar_qualquer"),
    "sensor_optico":     ([r"landsat", r"sentinel[- ]?2", r"modis", r"optical",
                           r"optico", r"multispectral", r"multiespectral",
                           r"planetscope"], "sensor_optico_qualquer"),
    "metodo_rf":         ([r"random forest", r"floresta[s]? aleatoria",
                           r"bosque[s]? aleatorio"], "metodo_random_forest"),
    "metodo_svm":        ([r"support vector", r"\bsvm\b",
                           r"maquina[s]? de vetor"], "metodo_support_vector_machine"),
    "metodo_dl":         ([r"deep learning", r"aprendizado profundo",
                           r"aprendizaje profundo", r"convolutional", r"\bcnn\b",
                           r"u-net", r"rede[s]? neura", r"red[es]? neuronal"],
                          "metodo_aprendizado_profundo"),
    "metodo_obia":       ([r"object-?based", r"\bobia\b", r"orientada a objeto",
                           r"basada en objeto"], "metodo_analise_orientada_a_objeto"),
    # Léxico temporal ampliado: além dos termos diretos de série temporal,
    # inclui o vocabulário conceitual que a produção ibero-americana usa para
    # dizer 'temporal' sem nomeá-lo (sazonal, estacional, evolução da paisagem,
    # décadas, pulso/hidroperíodo) e o intervalo explícito de anos (ex.:
    # '2000-2020'), que caracteriza estudo multitemporal. A ampliação corrige
    # uma subcodificação observada por leitura de texto completo em teses.
    "temporal_serie":    ([r"time[- ]series", r"multi[- ]?temporal",
                           r"serie[s]? temporal", r"serie[s]? temporais",
                           r"analise temporal", r"analisis temporal",
                           r"interanual", r"inter-annual", r"monitoramento",
                           r"monitoreo", r"sazonal", r"sazonalidade",
                           r"estacional", r"evolucao da paisagem",
                           r"evolucao temporal", r"pulso de inundac",
                           r"hidroperiodo", r"multi[- ]?ano", r"decada",
                           r"decadal", r"(?:19|20)\d{2}\s*[-a–]{1,3}\s*(?:19|20)\d{2}"],
                          "temporal_serie_temporal"),
    "temporal_mudanca":  ([r"change detection", r"deteccao de mudanca",
                           r"deteccion de cambios", r"espaco-?temporal"], "temporal_deteccao_de_mudanca"),
    "infra_nuvem":       ([r"google earth engine", r"\bgee\b", r"cloud comput",
                           r"planetary computer", r"openeo"], "infraestrutura_nuvem"),
    "infra_cubo":        ([r"data ?cube", r"analysis[- ]ready data",
                           r"cubo de dados", r"cubo de datos"], "infraestrutura_cubo_de_dados"),
    "validacao":         ([r"accurac", r"validat", r"\bkappa\b", r"acuracia",
                           r"exactitud", r"matriz de confusao",
                           r"matriz de confusion"], "validacao_relatada"),
}

# Atributos derivados de combinações dos anteriores.
DERIVADOS = {
    "derivado_fusao": (lambda v: v["sensor_sar"] and v["sensor_optico"],
                       "derivado_fusao_sar_optico"),
}

# --------------------------------------------- VARIÁVEL EM NÍVEIS (opcional)
# Trata termos ambíguos por contexto — ex.: 'seasonal', hidrológico vs.
# decomposição estatística de série temporal.
NIVEIS = {
    "fenologia": {
        "rotulo": "fenologia_hidroperiodo",
        "nivel1": [r"phenolog", r"fenolog", r"hydroperiod", r"hidroperiodo",
                   r"flood pulse", r"pulso de inundacao", r"pulso de inundacion",
                   r"inundation frequenc", r"flooding regime"],
        "termo_ambiguo": r"seasonal|estacional|sazonal",
        "contexto_valido": [r"water", r"agua", r"inundat", r"flood", r"hydrolog",
                            r"hidrolog", r"wetland", r"vegetation", r"vegetacao",
                            r"ndvi", r"marsh", r"mangrove"],
        "contexto_invalido": [r"additive seasonal", r"seasonal and trend",
                              r"\bbfast\b", r"\bbeast\b", r"seasonal decomposition",
                              r"harmonic"],
        "janela": 130,
    },
}

# -------------------------------------------------------------- RANKING ----
# Priorização da lista de leitura (ranquear.py). Segue a boa prática de
# screening (Rayyan/Covidence/ASReview): a máquina ORDENA por relevância; a
# INCLUSÃO é decidida por leitura (O'Mara-Eves et al., 2015). Nada é cortado.
#
# A relevância combina, sem peso arbitrário e nesta ordem lexicográfica:
#   1) cobertura de conceitos — quantos dos conceitos de interesse o trabalho
#      cobre (cada conceito é um OU de colunas já codificadas no LÉXICO);
#   2) centralidade do objeto — o termo do objeto ponderado por campo
#      (título vale mais que palavras-chave, que valem mais que o resumo);
#   3) desempate — citação normalizada pela idade (percentil na coorte do ano),
#      que não pune o trabalho recente nem o clássico.
#
# Para adaptar a outro tema, um pesquisador edita apenas o que está abaixo.
RANKING = {
    # Termos do objeto para a CENTRALIDADE. Por padrão reusa o critério de
    # objeto; troque por uma lista própria se quiser medir centralidade de
    # outra coisa que não o objeto de elegibilidade.
    "foco_termos": [p for p in CRITERIOS["objeto"]["padroes"]],
    # Pesos de campo da centralidade e teto de densidade no resumo.
    "foco_peso_titulo": 3,
    "foco_peso_palavras_chave": 2,
    "foco_resumo_max": 4,
    # Nome da coluna de centralidade na saída.
    "foco_coluna": "foco_area_umida",

    # Conceitos de interesse do pesquisador. A CHAVE é o nome da coluna na
    # saída; o valor é um conjunto de padrões (regex, sobre texto sem acento)
    # aplicado a título+palavras-chave+resumo. O trabalho satisfaz o conceito
    # se QUALQUER padrão casar, e a cobertura é quantos conceitos ele satisfaz.
    "conceitos": {
        "classif_tipif": CRITERIOS["abordagem_classificatoria"]["padroes"],
        "multitemporal": CRITERIOS["abordagem_temporal"]["padroes"],
        "acuracia": [r"accurac", r"validat", r"\bkappa\b", r"acuracia",
                     r"exactitud", r"matriz de confusao", r"matriz de confusion"],
    },

    # Colunas binárias apenas descritivas (não entram na relevância).
    # Formato: nome_na_saida -> rótulo do LEXICO/DERIVADOS.
    "descritivos": {
        "fusao": "derivado_fusao_sar_optico",
        "nuvem": "infraestrutura_nuvem",
    },

    # Grupos: uma coluna binária que resume "declarou algum destes" e uma
    # coluna textual que diz QUAIS. Evita pesar várias vezes o mesmo eixo e
    # garante que nenhum membro do LÉXICO fique definido mas não exportado.
    "grupos": {
        "metodo": {
            "coluna_qual": "metodo_qual",
            "membros": {                       # sigla -> rótulo do LEXICO
                "RF":   "metodo_random_forest",
                "DL":   "metodo_aprendizado_profundo",
                "OBIA": "metodo_analise_orientada_a_objeto",
                "SVM":  "metodo_support_vector_machine",
            },
        },
    },

    # Marcadores binários derivados do tipo documental.
    # Formato: nome_na_saida -> lista de tipos que valem 1.
    "marcadores_tipo": {
        "tese_doutorado": ["doctoralThesis"],
    },

    # Desempate: "citacao_coorte" (percentil na coorte do ano) ou "recencia".
    "desempate": "citacao_coorte",

    # Ano de referência da razão citações/ano. None usa o ano corrente.
    # Fixe-o para que a coluna seja estável entre execuções.
    "ano_referencia": 2026,

    # Campos herdados do corpus que saem na lista, na ordem, com o nome final.
    # Formato: (campo_no_corpus, nome_na_saida).
    "campos_herdados": [
        ("tipo_documental",      "tipo"),
        ("via_de_origem",        "via"),
        ("ano_de_publicacao",    "ano"),
        ("primeiro_autor",       "autor"),
        ("periodico",            "periodico"),
        ("titulo",               "titulo"),
        ("palavras_chave",       "palavras_chave"),
        ("resumo",               "resumo"),
        ("doi",                  "doi"),
        ("url_persistente",      "url_persistente"),
        ("identificador_nativo", "wid"),
    ],

    # Colunas vindas do enriquecimento externo (enriquecer_periodicos.py).
    # Saem na lista se existirem no corpus; ausentes, são simplesmente omitidas.
    "colunas_enriquecimento": ["estrato_qualis", "citescore"],
}

# ------------------------------------------------- ENRIQUECIMENTO EXTERNO ---
# Junta ao corpus métricas de periódico que NÃO têm via aberta de recuperação
# (avaliações nacionais, indicadores de base fechada). O casamento é por título
# de periódico, e a tabela acompanha o repositório, de modo que a junção é
# verificável mesmo por quem não tem acesso à base de origem.
#
# Estas colunas são METADADOS DE APOIO À LEITURA: não participam do cálculo de
# relevância (confira em RANKING). Para dispensá-las, ponha "ativo": False.
ENRIQUECIMENTO_PERIODICO = {
    "ativo": True,
    "arquivo": "metricas_periodicos.csv",
    "chave_corpus": "periodico",       # campo do corpus usado no casamento
    "chave_tabela": "periodico",       # campo correspondente na tabela
    "colunas": ["estrato_qualis", "citescore"],
    # Procedência declarada de cada coluna, para o relato do método.
    "procedencia": {
        "estrato_qualis": "Qualis (CAPES); derivável de qualis_capes.txt "
                          "por gerar_metadados_periodicos.py",
        "citescore": "CiteScore (Scopus); base fechada, sem via aberta de "
                     "recuperação — reproduzido do levantamento",
    },
}

# ------------------------------------------------- TIPOS DO OBJETO ----------
# Subdivisão do objeto de estudo em tipos, para a caracterização temática.
# Diferente de CRITERIOS['objeto'], que decide ELEGIBILIDADE, isto apenas
# DESCREVE de que subtipo cada trabalho fala. Categorias não exclusivas: um
# trabalho pode mencionar mais de um tipo, e o genérico convive com o específico.
#
# Deixe TIPOS_OBJETO = None se o seu objeto não se subdivide.
TIPOS_OBJETO = {
    "generico": [r"area[s]? umida", r"zona[s]? umida", r"wetland", r"humedal"],
    "manguezal": [r"manguezal", r"mangue\b", r"mangrove", r"manglar"],
    "costeira_mare": [r"tidal flat", r"coastal wetland", r"planicie de mare",
                      r"salt marsh", r"marisma costeir"],
    "brejo_pantano": [r"\bmarsh\b", r"marshes", r"brejo", r"pantano\b",
                      r"swamp", r"cienaga"],
    "planicie_inundacao": [r"floodplain", r"planicie de inundacao", r"varzea",
                           r"llanura de inundacion"],
    "pantanal": [r"pantanal", r"alto paraguai", r"upper paraguay"],
    "turfeira": [r"peatland", r"turfeira", r"turbera", r"\bbog\b", r"\bfen\b",
                 r"\bmire\b"],
    "igapo_vereda": [r"igapo", r"vereda", r"buritizal"],
}

# ------------------------------------------------- TRIAGEM DE LEITURA -------
# Usado por triar_para_tese.py. Reparte a lista priorizada em estratos de
# leitura, do mais próximo da sua pergunta ao mais periférico.
#
# O eixo dos estratos é CONCEITUAL, não geográfico: o que define a ordem de
# leitura é o que o trabalho FAZ, não onde ele foi feito. A área de estudo
# entra como marcador descritivo — útil para filtrar depois, péssimo como
# critério de corte, porque descarta a literatura metodológica que responde à
# pergunta.
#
#   marcadores  rótulo -> regex aplicada a título+palavras-chave+resumo
#   atributos   rótulo -> regex; viram uma coluna descritiva única
#   estratos    lista ordenada; cada um exige e/ou exclui condições
#
# Uma condição é o nome de um marcador ou de uma coluna binária da lista
# (`acuracia`, `multitemporal`, `classif_tipif`) ou a palavra `metodo`, que
# significa "declarou algum algoritmo". Cada trabalho cai no PRIMEIRO estrato
# cujas condições satisfaz.
TRIAGEM_LEITURA = {
    "marcadores": {
        "tipificacao": [r"tipologia", r"tipificacao", r"typolog",
                        r"wetland type", r"classification system",
                        r"sistema de classificacao", r"classification scheme",
                        r"wetland classes"],
        "area_de_estudo": [r"pantanal", r"alto paraguai", r"upper paraguay"],
    },
    "atributos": {
        "SAR": [r"\bsar\b", r"sentinel[- ]?1", r"synthetic aperture",
                r"radar de abertura", r"palsar", r"radarsat"],
        "Sentinel-2": [r"sentinel[- ]?2", r"\bmsi\b"],
        "Landsat": [r"landsat", r"\boli\b", r"\betm\+?\b"],
        "MODIS": [r"modis"],
    },
    "estratos": [
        {"nome": "T1 tipificacao+acuracia+metodo",
         "exige": ["tipificacao", "acuracia", "metodo"], "exclui": [],
         "nota": "nucleo da pergunta: tipifica, valida e diz como"},
        {"nome": "T2 classificacao+acuracia+metodo",
         "exige": ["classif_tipif", "acuracia", "metodo"], "exclui": [],
         "nota": "nucleo comparavel: sustenta 'o que funciona melhor'"},
        {"nome": "T3 tipificacao+acuracia",
         "exige": ["tipificacao", "acuracia"], "exclui": [],
         "nota": "tipifica e valida; metodo a extrair na leitura"},
        {"nome": "T4 classificacao+acuracia",
         "exige": ["classif_tipif", "acuracia"], "exclui": [],
         "nota": "valida; metodo a extrair na leitura"},
        {"nome": "T5 tipificacao sem acuracia",
         "exige": ["tipificacao"], "exclui": [],
         "nota": "sistemas de classes e propostas conceituais"},
    ],
    # Estrato transversal: sai em aba propria, sem retirar ninguem dos demais.
    "recorte_transversal": {
        "nome": "T6 area de estudo",
        "marcador": "area_de_estudo",
        "nota": "sua area de estudo, qualquer que seja o estrato conceitual",
    },
}

# -------------------------------------------------- RECORTE COMPARADO ------
# Compara um recorte do conjunto com TODO O RESTANTE, e não com o conjunto
# inteiro. A distinção importa: se o recorte permanecer dentro da base de
# comparação, os mesmos trabalhos entram dos dois lados, e a sobreposição
# sempre atenua a diferença que se quer mostrar. Aqui os dois grupos se
# excluem e, somados, dão o total.
#
# Deixe RECORTE_COMPARADO = None se não houver recorte de interesse.
RECORTE_COMPARADO = {
    "rotulo": "Pantanal",
    "padroes": TIPOS_OBJETO["pantanal"],
    # Formato: (rótulo na saída, rótulo da coluna já codificada no corpus).
    "atributos": [
        ("Landsat",                 "sensor_landsat"),
        ("Sentinel-2",              "sensor_sentinel2_optico"),
        ("MODIS",                   "sensor_modis"),
        ("Radar / SAR",             "sensor_sar_qualquer"),
        ("Fusão radar + óptico",    "derivado_fusao_sar_optico"),
        ("Processamento em nuvem",  "infraestrutura_nuvem"),
        ("Análise de acurácia",     "validacao_relatada"),
    ],
}

# ------------------------------------------------------------ OPERACIONAL ---
PAGINA = 50          # registros por requisição (VuFind); ver nota no README
PAUSA = 1.0          # segundos entre requisições
TENTATIVAS = 3       # tentativas por página antes de desistir
TIMEOUT = 120
MAX_POR_CONSULTA = 2000   # teto de registros por consulta em bases enormes
