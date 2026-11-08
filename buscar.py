# -*- coding: utf-8 -*-
"""
BUSCA UNIFICADA EM MÚLTIPLAS BASES E TRÊS IDIOMAS
=================================================

Lê tudo de config.py. Não contém nada específico do tema.

    python3 buscar.py                 # todas as bases automáticas, 3 idiomas
    python3 buscar.py openalex        # apenas uma base
    python3 buscar.py openalex core --idiomas en pt

Para cada base marcada `automatica=True` em config.BASES, dispara a equação
em cada idioma de config.IDIOMAS e grava:

    bruto_<base>.csv     registros recuperados (colunas padronizadas)
    log_busca.csv        uma linha por requisição, para auditoria

As colunas de saída são idênticas em todas as bases, de modo que
triar_e_codificar.py e consolidar_vias.py operam sobre qualquer uma delas.

ADAPTADORES
-----------
Cada tecnologia de acesso tem um adaptador. Bases que aceitam booleano
(OpenAlex, CORE) recebem a equação inteira; bases de texto livre (Crossref,
Semantic Scholar) e VuFind recebem os termos expandidos, e a triagem posterior
aplica os critérios. Bases não automatizáveis (SciELO, Redalyc, BASE,
LA Referencia) ficam registradas em config.BASES com automatica=False e são
ignoradas aqui — sua inclusão é manual e documentada no README.
"""
import csv, json, os, re, sys, time, unicodedata
import urllib.parse, urllib.request
from datetime import date

import config

csv.field_size_limit(10 ** 9)
UA = {"User-Agent": "protocolo-revisao/2.0 (mailto:pesquisa@exemplo.org)"}

COLUNAS = ["base_de_origem", "identificador_nativo", "doi", "url_persistente",
           "consulta_que_recuperou", "idioma_da_consulta", "data_da_consulta",
           "ano_de_publicacao", "tipo_documental", "idioma", "instituicao",
           "primeiro_autor", "periodico", "titulo", "palavras_chave", "resumo",
           "citacoes"]

HOJE = date.today().isoformat()
LOG = []


# --------------------------------------------------------------- utilidades --
def get_json(url, headers=None, tentativas=None):
    tentativas = tentativas or config.TENTATIVAS
    h = dict(UA)
    if headers:
        h.update(headers)
    for t in range(1, tentativas + 1):
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=config.TIMEOUT) as r:
                return json.loads(r.read().decode("utf-8")), ""
        except Exception as e:
            err = str(e)[:120]
            if t < tentativas:
                time.sleep(config.PAUSA * t)
    return None, err


def registro_vazio(base, idioma, consulta):
    d = {c: "" for c in COLUNAS}
    d.update(base_de_origem=base, idioma_da_consulta=idioma,
             consulta_que_recuperou=consulta, data_da_consulta=HOJE)
    return d


def equacao(idioma):
    """(tema) AND (fonte) AND (abordagem) para o idioma."""
    b = config.BLOCOS[idioma]
    return " AND ".join("(" + " OR ".join(b[k]) + ")"
                        for k in ("tema", "fonte", "abordagem"))


def pares_tema_fonte(idioma):
    """Pares para bases sem booleano; a abordagem fica para a triagem."""
    b = config.BLOCOS[idioma]
    return [(t, f) for t in b["tema"] for f in b["fonte"]]


# --------------------------------------------------------------- OpenAlex ----
def busca_openalex(base, cfg, idioma, colhidos):
    a0, a1 = config.PERIODO
    eq = equacao(idioma)
    mailto = os.environ.get("OPENALEX_MAILTO", "")
    cursor, obtidos = "*", 0
    while cursor and obtidos < config.MAX_POR_CONSULTA:
        params = {
            "search": eq,
            "filter": f"from_publication_date:{a0}-01-01,"
                      f"to_publication_date:{a1}-12-31",
            "per-page": "200", "cursor": cursor,
        }
        if mailto:
            params["mailto"] = mailto
        url = cfg["endpoint"] + "?" + urllib.parse.urlencode(params)
        dados, err = get_json(url)
        if dados is None:
            LOG.append([base, idioma, "cursor", "ERRO", err, HOJE]); break
        cursor = (dados.get("meta") or {}).get("next_cursor")
        recs = dados.get("results") or []
        for w in recs:
            ident = w.get("id", "")
            if ident in colhidos:
                continue
            colhidos[ident] = _openalex_rec(base, idioma, eq, w)
            obtidos += 1
        LOG.append([base, idioma, "pagina", "OK",
                    (dados.get("meta") or {}).get("count", ""), HOJE])
        if not recs:
            break
        time.sleep(config.PAUSA)


def _openalex_abstract(inv):
    if not inv:
        return ""
    pos = {}
    for termo, idxs in inv.items():
        for i in idxs:
            pos[i] = termo
    return " ".join(pos[i] for i in sorted(pos))


def _openalex_rec(base, idioma, eq, w):
    d = registro_vazio(base, idioma, eq)
    auth = w.get("authorships") or []
    inst = ""
    if auth and auth[0].get("institutions"):
        inst = (auth[0]["institutions"][0] or {}).get("display_name", "")
    d.update(
        identificador_nativo=w.get("id", ""),
        doi=(w.get("doi") or "").replace("https://doi.org/", ""),
        url_persistente=w.get("id", ""),
        ano_de_publicacao=w.get("publication_year", ""),
        tipo_documental=w.get("type", ""),
        idioma=w.get("language", ""),
        instituicao=inst,
        primeiro_autor=(auth[0]["author"]["display_name"] if auth else ""),
        periodico=(((w.get("primary_location") or {}).get("source") or {})
                   .get("display_name", "") or ""),
        titulo=w.get("title") or w.get("display_name") or "",
        palavras_chave="; ".join(k.get("display_name", "")
                                 for k in (w.get("keywords") or [])),
        resumo=_openalex_abstract(w.get("abstract_inverted_index")),
        citacoes=w.get("cited_by_count", ""),
    )
    return d


# --------------------------------------------------------------- Crossref ----
def busca_crossref(base, cfg, idioma, colhidos):
    a0, a1 = config.PERIODO
    mailto = os.environ.get("CROSSREF_MAILTO", "")
    for tema in config.BLOCOS[idioma]["tema"]:
        termo = tema.strip('"')
        cursor, obtidos = "*", 0
        while cursor and obtidos < config.MAX_POR_CONSULTA // 4:
            params = {
                "query.bibliographic": termo + " remote sensing",
                "filter": f"from-pub-date:{a0}-01-01,until-pub-date:{a1}-12-31,"
                          "type:journal-article",
                "rows": "100", "cursor": cursor,
            }
            if mailto:
                params["mailto"] = mailto
            url = cfg["endpoint"] + "?" + urllib.parse.urlencode(params)
            dados, err = get_json(url)
            if dados is None:
                LOG.append([base, idioma, termo, "ERRO", err, HOJE]); break
            msg = dados.get("message") or {}
            cursor = msg.get("next-cursor")
            items = msg.get("items") or []
            for it in items:
                ident = it.get("DOI", "")
                if not ident or ident in colhidos:
                    continue
                colhidos[ident] = _crossref_rec(base, idioma, termo, it)
                obtidos += 1
            LOG.append([base, idioma, termo, "OK", msg.get("total-results", ""), HOJE])
            if not items:
                break
            time.sleep(config.PAUSA)


def _crossref_rec(base, idioma, termo, it):
    d = registro_vazio(base, idioma, termo)
    ano = ""
    for k in ("published", "issued", "created"):
        parts = ((it.get(k) or {}).get("date-parts") or [[None]])[0]
        if parts and parts[0]:
            ano = parts[0]; break
    aut = it.get("author") or []
    resumo = re.sub(r"<[^>]+>", " ", it.get("abstract", "") or "").strip()
    d.update(
        identificador_nativo=it.get("DOI", ""),
        doi=it.get("DOI", ""),
        url_persistente="https://doi.org/" + it.get("DOI", ""),
        ano_de_publicacao=ano,
        tipo_documental=it.get("type", ""),
        instituicao="",
        primeiro_autor=(f"{aut[0].get('family','')}, {aut[0].get('given','')}"
                        if aut else ""),
        periodico=(it.get("container-title") or [""])[0],
        titulo=" ".join(it.get("title") or []),
        palavras_chave="; ".join(it.get("subject") or []),
        resumo=resumo,
        citacoes=it.get("is-referenced-by-count", ""),
    )
    return d


# ------------------------------------------------------- Semantic Scholar ----
def busca_semanticscholar(base, cfg, idioma, colhidos):
    a0, a1 = config.PERIODO
    chave = os.environ.get(cfg.get("chave_env") or "", "")
    headers = {"x-api-key": chave} if chave else None
    campos = "title,abstract,year,externalIds,publicationTypes,fieldsOfStudy,citationCount,authors"
    for tema in config.BLOCOS[idioma]["tema"]:
        termo = tema.strip('"')
        offset, obtidos = 0, 0
        while obtidos < config.MAX_POR_CONSULTA // 4:
            params = {"query": termo + " remote sensing",
                      "year": f"{a0}-{a1}", "offset": str(offset),
                      "limit": "100", "fields": campos}
            url = cfg["endpoint"] + "?" + urllib.parse.urlencode(params)
            dados, err = get_json(url, headers=headers)
            if dados is None:
                LOG.append([base, idioma, termo, "ERRO", err, HOJE]); break
            items = dados.get("data") or []
            for it in items:
                ident = (it.get("externalIds") or {}).get("DOI") or it.get("paperId", "")
                if not ident or ident in colhidos:
                    continue
                colhidos[ident] = _s2_rec(base, idioma, termo, it)
                obtidos += 1
            LOG.append([base, idioma, termo, "OK", dados.get("total", ""), HOJE])
            if dados.get("next") is None or not items:
                break
            offset = dados["next"]
            time.sleep(config.PAUSA * 2)   # limite de taxa mais rígido


def _s2_rec(base, idioma, termo, it):
    d = registro_vazio(base, idioma, termo)
    aut = it.get("authors") or []
    d.update(
        identificador_nativo=it.get("paperId", ""),
        doi=(it.get("externalIds") or {}).get("DOI", "") or "",
        url_persistente="https://www.semanticscholar.org/paper/" + it.get("paperId", ""),
        ano_de_publicacao=it.get("year", "") or "",
        tipo_documental=";".join(it.get("publicationTypes") or []),
        primeiro_autor=(aut[0].get("name", "") if aut else ""),
        periodico=it.get("venue", "") or "",
        titulo=it.get("title", "") or "",
        palavras_chave="; ".join(it.get("fieldsOfStudy") or []),
        resumo=it.get("abstract", "") or "",
        citacoes=it.get("citationCount", ""),
    )
    return d


# ------------------------------------------------------------------- CORE ----
def busca_core(base, cfg, idioma, colhidos):
    chave = os.environ.get(cfg.get("chave_env") or "", "")
    if not chave:
        print(f"  [core] pulada: defina {cfg['chave_env']} (chave gratuita).")
        LOG.append([base, idioma, "-", "PULADA_SEM_CHAVE", "", HOJE]); return
    a0, a1 = config.PERIODO
    eq = equacao(idioma) + f" AND yearPublished>={a0} AND yearPublished<={a1}"
    headers = {"Authorization": "Bearer " + chave}
    obtidos, scroll = 0, None
    while obtidos < config.MAX_POR_CONSULTA:
        params = {"q": eq, "limit": "100"}
        if scroll:
            params["scrollId"] = scroll
        else:
            params["scroll"] = "true"
        url = cfg["endpoint"] + "?" + urllib.parse.urlencode(params)
        dados, err = get_json(url, headers=headers)
        if dados is None:
            LOG.append([base, idioma, "scroll", "ERRO", err, HOJE]); break
        scroll = dados.get("scrollId")
        results = dados.get("results") or []
        for it in results:
            ident = it.get("doi") or str(it.get("id", ""))
            if not ident or ident in colhidos:
                continue
            colhidos[ident] = _core_rec(base, idioma, eq, it)
            obtidos += 1
        LOG.append([base, idioma, "pagina", "OK", dados.get("totalHits", ""), HOJE])
        if not results:
            break
        time.sleep(config.PAUSA)


def _core_rec(base, idioma, eq, it):
    d = registro_vazio(base, idioma, eq)
    aut = it.get("authors") or []
    d.update(
        identificador_nativo=str(it.get("id", "")),
        doi=it.get("doi", "") or "",
        url_persistente=it.get("downloadUrl", "") or "",
        ano_de_publicacao=it.get("yearPublished", "") or "",
        tipo_documental=it.get("documentType", "") or "",
        primeiro_autor=(aut[0].get("name", "") if aut and isinstance(aut[0], dict) else ""),
        periodico=(it.get("publisher", "") or ""),
        titulo=it.get("title", "") or "",
        palavras_chave="; ".join(it.get("subjects") or []),
        resumo=it.get("abstract", "") or "",
        citacoes=it.get("citationCount", "") or "",
    )
    return d


# ----------------------------------------------------------------- VuFind ----
def busca_vufind(base, cfg, idioma, colhidos):
    for tema, fonte in pares_tema_fonte(idioma):
        lookfor = f"{tema} AND {fonte}"
        pagina = 1
        while True:
            params = [("lookfor", lookfor), ("type", "AllFields"),
                      ("limit", str(config.PAGINA)), ("page", str(pagina)),
                      ("field[]", "rawData")]
            url = cfg["endpoint"] + "?" + urllib.parse.urlencode(params)
            dados, err = get_json(url)
            if dados is None:
                LOG.append([base, idioma, lookfor, "ERRO", err, HOJE]); break
            total = dados.get("resultCount", 0)
            recs = dados.get("records") or []
            for rec in recs:
                rd = rec.get("rawData") or {}
                ident = rd.get("id")
                if not rd or ident in colhidos:
                    continue
                colhidos[ident] = _vufind_rec(base, idioma, lookfor, rd)
            LOG.append([base, idioma, lookfor, "OK", total, HOJE])
            if pagina * config.PAGINA >= (total or 0) or not recs:
                break
            pagina += 1
            time.sleep(config.PAUSA)
        time.sleep(config.PAUSA)


def _lista(v):
    if v is None:
        return []
    return [str(x) for x in v] if isinstance(v, list) else [str(v)]


def _vufind_rec(base, idioma, lookfor, rd):
    d = registro_vazio(base, idioma, lookfor)
    ano = ""
    for cand in _lista(rd.get("publishDate")) + _lista(rd.get("publicationDates")):
        m = re.search(r"(19|20)\d{2}", cand)
        if m:
            ano = int(m.group(0)); break
    doi = ""
    for cand in _lista(rd.get("identifier_str_mv")) + _lista(rd.get("url")):
        m = re.search(r"10\.\d{4,9}/\S+", cand)
        if m:
            doi = m.group(0); break
    urls = _lista(rd.get("url"))
    aut = _lista(rd.get("author"))
    d.update(
        identificador_nativo=rd.get("id", ""),
        doi=doi,
        url_persistente=urls[0] if urls else "",
        ano_de_publicacao=ano,
        tipo_documental=";".join(_lista(rd.get("format"))),
        idioma=";".join(_lista(rd.get("language"))),
        instituicao=";".join(_lista(rd.get("institution"))),
        primeiro_autor=aut[0] if aut else "",
        periodico=(_lista(rd.get("publisher")) or [""])[0],
        titulo=(_lista(rd.get("title")) or [""])[0],
        palavras_chave="; ".join(dict.fromkeys(_lista(rd.get("topic")))),
        resumo=" ".join(_lista(rd.get("description"))),
    )
    return d


ADAPTADORES = {
    "openalex": busca_openalex, "crossref": busca_crossref,
    "semanticscholar": busca_semanticscholar, "core": busca_core,
    "vufind": busca_vufind,
}


# -------------------------------------------------------------------- main ---
def main(bases_pedidas, idiomas):
    autos = {n: c for n, c in config.BASES.items() if c.get("automatica")}
    if bases_pedidas:
        autos = {n: autos[n] for n in bases_pedidas if n in autos}
        faltam = [n for n in bases_pedidas if n not in autos]
        if faltam:
            print(f"ignoradas (não automáticas ou inexistentes): {faltam}")
    if not autos:
        raise SystemExit("Nenhuma base automática selecionada.")

    print(f"bases: {list(autos)} | idiomas: {idiomas}\n")
    for nome, cfg in autos.items():
        adapt = ADAPTADORES.get(cfg["tipo"])
        if not adapt:
            print(f"[{nome}] sem adaptador para tipo {cfg['tipo']} — pulada.")
            continue
        colhidos = {}
        for idioma in idiomas:
            print(f"[{nome}] idioma={idioma} ...", flush=True)
            adapt(nome, cfg, idioma, colhidos)
            print(f"[{nome}] idioma={idioma}: acumulado {len(colhidos)}",
                  flush=True)
        saida = f"bruto_{nome}.csv"
        with open(saida, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=COLUNAS, extrasaction="ignore")
            w.writeheader()
            w.writerows(colhidos.values())
        print(f"[{nome}] gravado {saida}: {len(colhidos)} registros\n")

    with open("log_busca.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["base", "idioma", "consulta", "situacao", "total", "data"])
        w.writerows(LOG)
    erros = sum(1 for l in LOG if l[3] == "ERRO")
    print(f"requisições: {len(LOG)} | com erro: {erros} | log_busca.csv")


if __name__ == "__main__":
    args = sys.argv[1:]
    idiomas = list(config.IDIOMAS)
    if "--idiomas" in args:
        i = args.index("--idiomas")
        idiomas = args[i + 1:]
        args = args[:i]
    main(args, idiomas)
