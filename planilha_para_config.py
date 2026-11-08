# -*- coding: utf-8 -*-
"""
PLANILHA -> CONFIGURAÇÃO
========================

Converte a planilha de configuração no `config.py` que os programas do
protocolo leem. Serve a quem não programa: o tema é descrito em palavras
comuns, numa planilha, e este programa escreve as expressões regulares.

    python3 planilha_para_config.py modelo_configuracao.xlsx

A planilha tem uma aba por parte da configuração (ver a aba LEIA-ME do
modelo). Se houver erro, nada é gravado e a lista de problemas é impressa.

COMO UM TERMO VIRA PADRÃO DE BUSCA NO TEXTO
-------------------------------------------
    - acentos e maiúsculas são ignorados:   Várzea  casa com  varzea, VARZEA
    - o termo casa com o COMEÇO da palavra: wetland casa com  wetlands
    - palavra_inteira = sim fecha o fim:    SAR     não casa com  sarampo
    - espaço e hífen se equivalem:          time series casa com time-series
    - asterisco final é aceito e ignorado:  accurac* equivale a accurac
    - prefixo re: passa uma expressão regular pronta, sem conversão

O config.py existente, se não tiver sido gerado por este programa, é guardado
antes como config_referencia.py, para que a configuração do estudo de
referência nunca se perca.
"""
import os, pprint, re, shutil, sys, unicodedata
from datetime import date, datetime

try:
    import openpyxl
except ImportError:
    raise SystemExit("Falta o pacote openpyxl. Instale com: pip install openpyxl")

MARCA = "# GERADO POR planilha_para_config.py"
DESTINO = "config.py"
RESERVA = "config_referencia.py"

IDIOMAS_VALIDOS = ("en", "pt", "es")
BLOCOS_VALIDOS = ("tema", "fonte", "abordagem")

# Registro dos acervos que buscar.py sabe consultar. A planilha só escolhe
# quais ficam ativos; endereços e tecnologia de acesso ficam aqui.
REGISTRO_BASES = {
    "openalex": {
        "tipo": "openalex", "consulta": "boolean",
        "endpoint": "https://api.openalex.org/works",
        "chave_env": None,
        "nota": "Índice aberto; aceita AND/OR/parênteses no parâmetro search.",
    },
    "crossref": {
        "tipo": "crossref", "consulta": "matriz",
        "endpoint": "https://api.crossref.org/works",
        "chave_env": None,
        "nota": "Texto livre ranqueado; resumo frequentemente ausente.",
    },
    "semanticscholar": {
        "tipo": "semanticscholar", "consulta": "matriz",
        "endpoint": "https://api.semanticscholar.org/graph/v1/paper/search",
        "chave_env": "S2_API_KEY",
        "nota": "Busca por texto livre; limite de taxa sem chave.",
    },
    "core": {
        "tipo": "core", "consulta": "boolean",
        "endpoint": "https://api.core.ac.uk/v3/search/works",
        "chave_env": "CORE_API_KEY",
        "nota": "Agrega repositórios abertos. Exige chave gratuita.",
    },
    "oasisbr": {
        "tipo": "vufind", "consulta": "matriz",
        "endpoint": "https://oasisbr.ibict.br/vufind/api/v1/search",
        "chave_env": None,
        "nota": "IBICT. Produção brasileira; consulta lenta.",
    },
    "bdtd": {
        "tipo": "vufind", "consulta": "matriz",
        "endpoint": "https://bdtd.ibict.br/vufind/api/v1/search",
        "chave_env": None,
        "nota": "IBICT. Teses e dissertações; contida na OASISBR.",
    },
}

CAMPOS_HERDADOS = [
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
]


def sem_acento(s):
    s = unicodedata.normalize("NFKD", str(s or ""))
    return "".join(c for c in s if not unicodedata.combining(c))


def chave(s):
    """Nome de coluna ou de parâmetro: sem acento, minúsculo, com _."""
    return re.sub(r"[^a-z0-9]+", "_", sem_acento(s).lower()).strip("_")


def sim(v):
    return chave(v) in ("sim", "s", "x", "yes", "y", "1", "true", "verdadeiro")


def lista(v):
    return [chave(x) for x in re.split(r"[,;\s]+", str(v or "")) if x.strip()]


def padrao(termo, inteira):
    """Termo comum -> expressão regular sobre texto sem acento e minúsculo."""
    t = str(termo).strip()
    if t.lower().startswith("re:"):
        return t[3:].strip()
    t = sem_acento(t).lower().strip().strip('"').rstrip("*").strip()
    if not t:
        return None
    corpo = r"[\s-]*".join(re.escape(p) for p in re.split(r"[\s\-]+", t))
    ini = r"\b" if t[0].isalnum() else ""
    fim = r"\b" if inteira and t[-1].isalnum() else ""
    return ini + corpo + fim


def termo_de_busca(termo):
    """Termo para a equação enviada às bases: compostos vão entre aspas."""
    t = str(termo).strip().rstrip("*").strip()
    if " " in t and not t.startswith('"'):
        t = '"%s"' % t.strip('"')
    return t


class Planilha:
    def __init__(self, caminho):
        self.wb = openpyxl.load_workbook(caminho, data_only=True)
        self.abas = {chave(n): n for n in self.wb.sheetnames}
        self.erros, self.avisos = [], []

    def aba(self, nome, obrigatoria=True):
        """Linhas da aba como dicionários; a 1ª linha é o cabeçalho."""
        if nome not in self.abas:
            if obrigatoria:
                self.erros.append("falta a aba '%s'" % nome)
            return []
        linhas = list(self.wb[self.abas[nome]].iter_rows(values_only=True))
        if not linhas:
            return []
        cab = [chave(c) for c in linhas[0]]
        saida = []
        for n, valores in enumerate(linhas[1:], start=2):
            d = {c: v for c, v in zip(cab, valores) if c}
            if all(v in (None, "") for v in d.values()):
                continue
            d["_linha"] = n
            saida.append(d)
        return saida

    def termos(self, nome_aba, coluna_grupo):
        """Agrupa os termos de uma aba por grupo: {grupo: [padrões]}."""
        grupos = {}
        for d in self.aba(nome_aba, obrigatoria=False):
            g = chave(d.get(coluna_grupo)) if coluna_grupo else "_"
            termo = d.get("termo")
            if not g or termo in (None, ""):
                self.erros.append("aba '%s', linha %d: falta %s"
                                  % (nome_aba, d["_linha"],
                                     "o nome ou o termo" if coluna_grupo else "o termo"))
                continue
            p = padrao(termo, sim(d.get("palavra_inteira")))
            if p is None:
                continue
            try:
                re.compile(p)
            except re.error as e:
                self.erros.append("aba '%s', linha %d: expressão inválida (%s)"
                                  % (nome_aba, d["_linha"], e))
                continue
            grupos.setdefault(g, []).append(p)
        return grupos


def converter(caminho):
    P = Planilha(caminho)

    # ------------------------------------------------------------- geral ---
    geral = {chave(d.get("parametro")): d.get("valor") for d in P.aba("geral")}
    tema = str(geral.get("nome_do_tema") or "tema sem nome").strip()
    try:
        periodo = (int(geral.get("ano_inicial")), int(geral.get("ano_final")))
    except (TypeError, ValueError):
        P.erros.append("aba 'geral': ano_inicial e ano_final devem ser números")
        periodo = (0, 0)
    idiomas = lista(geral.get("idiomas")) or ["en"]
    for i in idiomas:
        if i not in IDIOMAS_VALIDOS:
            P.erros.append("aba 'geral': idioma '%s' desconhecido (use %s)"
                           % (i, ", ".join(IDIOMAS_VALIDOS)))
    bases = lista(geral.get("bases")) or ["openalex"]
    for b in bases:
        if b not in REGISTRO_BASES:
            P.erros.append("aba 'geral': base '%s' desconhecida (use %s)"
                           % (b, ", ".join(REGISTRO_BASES)))
    objeto_curto = chave(geral.get("nome_curto_do_objeto")) or "objeto"
    desempate = "recencia" if chave(geral.get("desempate")).startswith("rec") \
        else "citacao_coorte"
    try:
        limite = int(geral.get("limite_por_consulta") or 2000)
    except ValueError:
        limite = 2000

    # ------------------------------------------------------------- busca ---
    blocos = {i: {b: [] for b in BLOCOS_VALIDOS} for i in idiomas}
    for d in P.aba("busca"):
        i, b, t = chave(d.get("idioma")), chave(d.get("bloco")), d.get("termo")
        if b not in BLOCOS_VALIDOS or t in (None, ""):
            P.erros.append("aba 'busca', linha %d: bloco deve ser tema, fonte "
                           "ou abordagem, e o termo não pode faltar" % d["_linha"])
            continue
        if i not in blocos:
            P.avisos.append("aba 'busca', linha %d: idioma '%s' fora da aba "
                            "'geral', linha ignorada" % (d["_linha"], i))
            continue
        blocos[i][b].append(termo_de_busca(t))
    for i in idiomas:
        for b in BLOCOS_VALIDOS:
            if not blocos[i][b]:
                P.erros.append("aba 'busca': nenhum termo de %s em '%s'" % (b, i))

    # --------------------------------------------------------- critérios ---
    criterios = {}
    for d in P.aba("criterios"):
        nome = chave(d.get("criterio"))
        if not nome:
            continue
        c = criterios.setdefault(nome, {"obrigatorio": None, "descricao": "",
                                        "padroes": []})
        if c["obrigatorio"] is None and d.get("obrigatorio") not in (None, ""):
            c["obrigatorio"] = sim(d.get("obrigatorio"))
        if not c["descricao"] and d.get("descricao"):
            c["descricao"] = str(d["descricao"]).strip()
    for nome, pats in P.termos("criterios", "criterio").items():
        criterios[nome]["padroes"] = pats
    for nome, c in criterios.items():
        c["obrigatorio"] = bool(c["obrigatorio"])
        c["descricao"] = c["descricao"] or nome
        if not c["padroes"]:
            P.erros.append("aba 'criterios': o critério '%s' não tem termos" % nome)
    obrigatorios = [n for n, c in criterios.items() if c["obrigatorio"]]
    if not obrigatorios:
        P.erros.append("aba 'criterios': marque ao menos um critério como "
                       "obrigatorio = sim")
    objeto = chave(geral.get("criterio_do_objeto")) or \
        (obrigatorios[0] if obrigatorios else "")
    if objeto and objeto not in criterios:
        P.erros.append("aba 'geral': criterio_do_objeto '%s' não existe na aba "
                       "'criterios'" % objeto)

    # ---------------------------------------------- exclusão e atributos ---
    exclusao = P.termos("exclusao", None).get("_", [])
    lexico = P.termos("atributos", "atributo")

    # ---------------------------------------------------------- conceitos --
    # "@nome" num conceito reaproveita os termos de um critério ou atributo.
    conceitos = {}
    for d in P.aba("conceitos", obrigatoria=False):
        nome, termo = chave(d.get("conceito")), str(d.get("termo") or "").strip()
        if not nome or not termo:
            continue
        if termo.startswith("@"):
            ref = chave(termo[1:])
            fonte = (criterios.get(ref) or {}).get("padroes") or lexico.get(ref)
            if not fonte:
                P.erros.append("aba 'conceitos', linha %d: '%s' não é critério "
                               "nem atributo" % (d["_linha"], termo))
                continue
            conceitos.setdefault(nome, []).extend(fonte)
        else:
            p = padrao(termo, sim(d.get("palavra_inteira")))
            try:
                re.compile(p)
            except re.error as e:
                P.erros.append("aba 'conceitos', linha %d: expressão inválida "
                               "(%s)" % (d["_linha"], e))
                continue
            conceitos.setdefault(nome, []).append(p)
    if not conceitos:
        P.avisos.append("aba 'conceitos' vazia: a lista será ordenada só pela "
                        "centralidade do objeto e pela citação")

    # --------------------------------------------- subtipos e recorte ------
    subtipos = P.termos("subtipos", "tipo") or None
    recorte_pats = P.termos("recorte", None).get("_", [])
    recorte = None
    if recorte_pats:
        recorte = {
            "rotulo": str(geral.get("nome_do_recorte") or "recorte").strip(),
            "padroes": recorte_pats,
            "atributos": [(a, a) for a in lexico],
        }

    # ------------------------------------------------- nomes de coluna -----
    foco = "foco_" + objeto_curto
    vistos = {}
    for origem, nomes in (("atributos", lexico), ("conceitos", conceitos),
                          ("geral", [foco])):
        for n in nomes:
            if n in vistos and vistos[n] != origem:
                P.erros.append("o nome '%s' aparece em '%s' e em '%s'; use "
                               "nomes distintos" % (n, vistos[n], origem))
            vistos[n] = origem

    if "core" in bases and not os.environ.get("CORE_API_KEY"):
        P.avisos.append("a base core exige a chave CORE_API_KEY (gratuita, em "
                        "core.ac.uk/services/api); sem ela, a busca no CORE falha")

    config = {
        "PERIODO": periodo,
        "IDIOMAS": idiomas,
        "BLOCOS": blocos,
        "BASES": {n: dict(c, automatica=n in bases)
                  for n, c in REGISTRO_BASES.items()},
        "CRITERIOS": criterios,
        "EXCLUSAO": exclusao,
        "TIPOS_DESCARTADOS": ["peer-review", "editorial", "erratum", "paratext"],
        "LEXICO": {a: (pats, a) for a, pats in lexico.items()},
        "DERIVADOS": {},
        "NIVEIS": {},
        "RANKING": {
            "foco_termos": criterios.get(objeto, {}).get("padroes", []),
            "foco_peso_titulo": 3,
            "foco_peso_palavras_chave": 2,
            "foco_resumo_max": 4,
            "foco_coluna": foco,
            "conceitos": conceitos,
            "descritivos": {a: a for a in lexico},
            "grupos": {},
            "marcadores_tipo": {"tese_doutorado": ["doctoralThesis"]},
            "desempate": desempate,
            "ano_referencia": date.today().year,
            "campos_herdados": CAMPOS_HERDADOS,
            "colunas_enriquecimento": [],
        },
        "ENRIQUECIMENTO_PERIODICO": {"ativo": False},
        "TIPOS_OBJETO": subtipos,
        "TRIAGEM_LEITURA": None,
        "RECORTE_COMPARADO": recorte,
        "PAGINA": 50,
        "PAUSA": 1.0,
        "TENTATIVAS": 3,
        "TIMEOUT": 120,
        "MAX_POR_CONSULTA": limite,
    }
    return P, tema, config


def escrever(caminho_planilha, tema, config):
    if os.path.exists(DESTINO):
        with open(DESTINO, encoding="utf-8") as fh:
            gerado = MARCA in fh.read()
        if not gerado:
            reserva = RESERVA if not os.path.exists(RESERVA) else \
                "config_anterior_%s.py" % datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy(DESTINO, reserva)
            print("config.py anterior guardado como %s" % reserva)

    partes = [
        "# -*- coding: utf-8 -*-",
        MARCA,
        "# a partir de %s, em %s." % (os.path.basename(caminho_planilha),
                                      datetime.now().strftime("%d/%m/%Y %H:%M")),
        "# Tema: %s" % tema,
        "# Para mudar a configuração, edite a planilha e rode o conversor de novo.",
        "",
    ]
    for nome, valor in config.items():
        partes.append("%s = %s\n" % (nome, pprint.pformat(
            valor, width=79, sort_dicts=False)))
    with open(DESTINO, "w", encoding="utf-8") as fh:
        fh.write("\n".join(partes))


def resumo(tema, c):
    print("TEMA: %s" % tema)
    print("período: %d a %d | idiomas: %s" % (c["PERIODO"] + (", ".join(c["IDIOMAS"]),)))
    print("bases: %s" % ", ".join(n for n, b in c["BASES"].items() if b["automatica"]))
    print("\nEQUAÇÃO DE BUSCA, por idioma")
    for i, b in c["BLOCOS"].items():
        eq = " AND ".join("(" + " OR ".join(b[k]) + ")" for k in BLOCOS_VALIDOS)
        print("  [%s] %s" % (i, eq if len(eq) < 300 else eq[:297] + "..."))
    print("\nCRITÉRIOS DE ELEGIBILIDADE")
    for n, cr in c["CRITERIOS"].items():
        print("  %-28s %-14s %3d termos" % (n, "obrigatório" if cr["obrigatorio"]
                                            else "alternativo", len(cr["padroes"])))
    print("  exclusão: %d termos" % len(c["EXCLUSAO"]))
    print("\nATRIBUTOS CODIFICADOS: %s" % (", ".join(c["LEXICO"]) or "nenhum"))
    print("CONCEITOS DA ORDENAÇÃO: %s"
          % (", ".join(c["RANKING"]["conceitos"]) or "nenhum"))
    if c["TIPOS_OBJETO"]:
        print("SUBTIPOS DO OBJETO: %s" % ", ".join(c["TIPOS_OBJETO"]))
    if c["RECORTE_COMPARADO"]:
        print("RECORTE COMPARADO: %s" % c["RECORTE_COMPARADO"]["rotulo"])


def main(caminho):
    if not os.path.exists(caminho):
        raise SystemExit("Planilha não encontrada: %s" % caminho)
    P, tema, config = converter(caminho)
    for a in P.avisos:
        print("AVISO: " + a)
    if P.erros:
        print("\nA planilha tem %d problema(s). Nada foi gravado.\n" % len(P.erros))
        for e in P.erros:
            print("  - " + e)
        raise SystemExit(1)
    resumo(tema, config)
    escrever(caminho, tema, config)
    print("\ngravado %s. Os demais programas já podem ser executados." % DESTINO)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "modelo_configuracao.xlsx")
