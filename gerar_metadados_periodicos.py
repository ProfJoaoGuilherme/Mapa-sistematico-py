# -*- coding: utf-8 -*-
"""
TABELA DE METADADOS DE PERIÓDICOS
=================================

Gera `metadados_periodicos.csv`, a tabela de consulta que documenta a
procedência dos metadados auxiliares de periódico usados no levantamento.

    python3 gerar_metadados_periodicos.py [lista_leitura_priorizada.csv]

POR QUE ESTA TABELA EXISTE
--------------------------
O estrato Qualis e o CiteScore entram na lista de leitura como metadados de
APOIO À LEITURA: ajudam o pesquisador a decidir a ordem em que abre os textos.
Eles NÃO participam do cálculo de relevância — a ordenação usa apenas cobertura
de conceitos, centralidade do objeto e percentil de citação na coorte do ano
(ver config.RANKING). Publicá-los em separado torna essa fronteira verificável:
qualquer pessoa pode conferir que nenhuma coluna daqui aparece em ranquear.py.

VIGÊNCIA DOS INDICADORES — LEIA ANTES DE REUTILIZAR
--------------------------------------------------
Qualis e CiteScore são indicadores DATADOS, não atributos permanentes do
periódico. O Qualis distribuído aqui é o vigente em julho de 2026; a CAPES
publica nova classificação a cada quadriênio. O CiteScore muda todo ano.

Ao repetir o levantamento em outra data:
  1. baixe a lista Qualis atual em https://sucupira.capes.gov.br
  2. substitua qualis_capes.txt
  3. atualize metricas_periodicos.csv com o CiteScore do ano de referência
  4. rode este programa de novo

Não fazer isso não invalida a ordenação — estes atributos não entram no cálculo
de relevância —, mas desatualiza a informação de apoio à leitura.

PROCEDÊNCIA DE CADA COLUNA
--------------------------
    estrato_qualis  DERIVADO. Lido de `qualis_capes.txt`, a lista Qualis (Novo)
                    da CAPES distribuída com o repositório. O casamento é por
                    título normalizado; quando o título vem truncado da base de
                    origem, tenta-se prefixo unívoco. Verificável por execução.
    citescore       EXTERNO. CiteScore/Scopus, sem via aberta de recuperação.
                    Reproduzido do levantamento e marcado como tal na coluna
                    `fonte_citescore`. Cobertura parcial e declarada.
    area_scopus     EXTERNO, A PREENCHER. Área ASJC, também sem via aberta.
                    Sai marcada 'A VERIFICAR' nos veículos citados nominalmente
                    na seção 4.2 do artigo — os únicos cuja classificação
                    sustenta uma afirmação do texto.

A distinção importa: `estrato_qualis` é auditável por quem baixar o repositório;
as outras duas dependem de base fechada e por isso são declaradas, não afirmadas.
"""
import csv, re, sys, unicodedata
from collections import defaultdict

QUALIS = "qualis_capes.txt"

# Veículos cuja área temática é invocada na seção 4.2 do artigo.
CITADOS_NO_TEXTO = [
    "Remote Sensing",
    "International Journal of Applied Earth Observation and",
    "IEEE Journal of Selected Topics in Applied Earth Observ",
    "Remote Sensing of Environment",
    "Ecological Indicators",
    "The Science of The Total Environment",
    "Water",
]

LINHA_QUALIS = re.compile(
    r"\s*(\d{4}[‐‑-]\d{3}[\dXx])\s+(.+?)\s{2,}([ABC][1-4]?|C)\s*$")


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.upper().replace("&", " AND ")
    s = re.sub(r"\(.*?\)", "", s)
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", s)).strip()


def carregar_qualis(caminho=QUALIS):
    """título normalizado -> conjunto de estratos (um título pode ter vários ISSN)"""
    tabela = defaultdict(set)
    try:
        fh = open(caminho, encoding="utf-8", errors="replace")
    except FileNotFoundError:
        print(f"AVISO: {caminho} ausente; estrato_qualis nao sera derivado.")
        return {}
    with fh:
        for linha in fh:
            m = LINHA_QUALIS.match(linha)
            if m:
                tabela[norm(m.group(2))].add(m.group(3).strip())
    return dict(tabela)


def buscar_estrato(periodico, tabela, chaves):
    """casa por título exato; se falhar, por prefixo unívoco (título truncado)"""
    n = norm(periodico)
    if n in tabela:
        vals = tabela[n]
        if len(vals) == 1:
            return next(iter(vals)), "exato"
        # título compartilhado por mais de um periódico na lista CAPES:
        # não se escolhe arbitrariamente; devolve-se a ambiguidade.
        return "", "ambiguo:" + "/".join(sorted(vals))
    if len(n) > 25:
        pref = [k for k in chaves if k.startswith(n)]
        vals = {v for k in pref for v in tabela[k]}
        if len(vals) == 1:
            return next(iter(vals)), "prefixo"
        if len(vals) > 1:
            return "", "ambiguo:" + "/".join(sorted(vals))
    return "", ""


def main(entrada="lista_leitura_priorizada.csv", saida="metadados_periodicos.csv"):
    with open(entrada, encoding="utf-8") as fh:
        registros = list(csv.DictReader(fh))

    tabela = carregar_qualis()
    chaves = list(tabela)
    print(f"qualis_capes.txt: {len(tabela)} titulos distintos.")

    agregado = defaultdict(lambda: {"n": 0, "qualis": set(), "citescore": set()})
    for r in registros:
        p = (r.get("periodico") or "").strip()
        if not p:
            continue
        a = agregado[p]
        a["n"] += 1
        if (r.get("estrato_qualis") or "").strip():
            a["qualis"].add(r["estrato_qualis"].strip())
        if (r.get("citescore") or "").strip():
            a["citescore"].add(r["citescore"].strip())

    linhas, conferem, divergem, so_corpus, ambiguos = [], 0, 0, 0, 0
    divergencias = []
    for p, a in sorted(agregado.items(), key=lambda kv: (-kv[1]["n"], kv[0])):
        derivado, modo = buscar_estrato(p, tabela, chaves)
        do_corpus = next(iter(a["qualis"])) if a["qualis"] else ""
        if derivado and do_corpus:
            if derivado == do_corpus:
                conferem += 1
            else:
                divergem += 1
                divergencias.append((p, do_corpus, derivado))
        elif do_corpus and modo.startswith("ambiguo"):
            ambiguos += 1
        elif do_corpus and not derivado:
            so_corpus += 1
        if modo.startswith("ambiguo"):
            fonte = "titulo ambiguo na CAPES (%s); valor do corpus" % modo.split(":", 1)[1]
        elif derivado:
            fonte = "qualis_capes.txt (%s)" % modo
        elif do_corpus:
            fonte = "corpus, sem correspondencia"
        else:
            fonte = ""
        linhas.append({
            "periodico": p,
            "trabalhos": a["n"],
            "estrato_qualis": derivado or do_corpus,
            "fonte_qualis": fonte,
            "citescore": next(iter(a["citescore"])) if a["citescore"] else "",
            "fonte_citescore": "Scopus (base fechada)" if a["citescore"] else "",
            "area_scopus": "A VERIFICAR" if p in CITADOS_NO_TEXTO else "",
        })

    with open(saida, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["periodico", "trabalhos",
                                           "estrato_qualis", "fonte_qualis",
                                           "citescore", "fonte_citescore",
                                           "area_scopus"])
        w.writeheader()
        w.writerows(linhas)

    com_q = sum(1 for l in linhas if l["estrato_qualis"])
    com_c = sum(1 for l in linhas if l["citescore"])
    pend = sum(1 for l in linhas if l["area_scopus"])
    print(f"gerado {saida}: {len(linhas)} periodicos, {com_q} com Qualis, "
          f"{com_c} com CiteScore.")
    print(f"conferencia contra o corpus: {conferem} conferem, {divergem} divergem, "
          f"{ambiguos} de titulo ambiguo, {so_corpus} sem correspondencia na CAPES.")
    for p, c, d in divergencias:
        print(f"  DIVERGE  {p[:50]:52} corpus={c:3} CAPES={d}")
    print(f"area_scopus a preencher manualmente: {pend} veiculos.")


if __name__ == "__main__":
    main(*sys.argv[1:3])
