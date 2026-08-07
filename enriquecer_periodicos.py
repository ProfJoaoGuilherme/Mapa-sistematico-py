# -*- coding: utf-8 -*-
"""
ENRIQUECIMENTO COM MÉTRICAS DE PERIÓDICO
========================================

Junta ao corpus colunas de avaliação de periódico que não têm via aberta de
recuperação por programa (avaliações nacionais, indicadores de base fechada).

    python3 enriquecer_periodicos.py                     # corpus_consolidado.csv
    python3 enriquecer_periodicos.py meu_corpus.csv

Lê tudo de config.ENRIQUECIMENTO_PERIODICO: o arquivo da tabela, o campo de
casamento e quais colunas trazer. Nada aqui é específico de um tema ou de um
país — para usar outra avaliação, aponte a configuração para outra tabela.

POR QUE ESTA ETAPA EXISTE
-------------------------
Métricas como o estrato Qualis ou o CiteScore não podem ser recuperadas por
consulta aberta: uma depende de planilha oficial, a outra de base assinada.
Distribuí-las como TABELA versionada, e não como valores soltos dentro do
resultado, é o que torna a junção verificável: qualquer pessoa confere linha a
linha de onde veio cada valor, mesmo sem acesso à base de origem.

Estas colunas são METADADOS DE APOIO À LEITURA. Elas não entram no cálculo de
relevância — confira em config.RANKING, que não as menciona. Servem para o
pesquisador decidir a ordem em que abre os textos.

A procedência declarada de cada coluna está em
config.ENRIQUECIMENTO_PERIODICO['procedencia'] e é impressa na execução.
"""
import csv, os, re, sys, unicodedata

import config

csv.field_size_limit(10 ** 9)


def norm(s):
    """Normaliza o título do periódico para o casamento."""
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.upper().replace("&", " AND ")
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", s)).strip()


def carregar_tabela(cfg):
    caminho = cfg["arquivo"]
    if not os.path.exists(caminho):
        raise SystemExit(
            "Tabela de métricas ausente: %s\n"
            "Aponte config.ENRIQUECIMENTO_PERIODICO['arquivo'] para o arquivo "
            "correto, ou desative com 'ativo': False." % caminho)
    with open(caminho, encoding="utf-8") as fh:
        linhas = list(csv.DictReader(fh))
    chave = cfg["chave_tabela"]
    tabela = {}
    for l in linhas:
        k = norm(l.get(chave, ""))
        if k:
            tabela[k] = l
    return tabela, len(linhas)


def main(entrada="corpus_consolidado.csv"):
    cfg = config.ENRIQUECIMENTO_PERIODICO
    if not cfg.get("ativo"):
        print("Enriquecimento desativado em config; nada a fazer.")
        return

    with open(entrada, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise SystemExit("Entrada vazia: " + entrada)

    tabela, n_tab = carregar_tabela(cfg)
    campo = cfg["chave_corpus"]
    colunas = cfg["colunas"]

    if campo not in rows[0]:
        raise SystemExit(
            "O corpus não tem o campo de casamento '%s'.\n"
            "Verifique config.ENRIQUECIMENTO_PERIODICO['chave_corpus']." % campo)

    casados = 0
    preenchidos = {c: 0 for c in colunas}
    for r in rows:
        achado = tabela.get(norm(r.get(campo, "")))
        if achado:
            casados += 1
        for c in colunas:
            valor = (achado or {}).get(c, "") or ""
            r[c] = valor
            if valor:
                preenchidos[c] += 1

    cols = list(rows[0])
    for c in colunas:
        if c not in cols:
            cols.append(c)

    with open(entrada, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore", restval="")
        w.writeheader()
        w.writerows(rows)

    print("tabela %s: %d linhas, %d chaves distintas." % (cfg["arquivo"], n_tab, len(tabela)))
    print("corpus %s: %d registros, %d casaram com a tabela." % (entrada, len(rows), casados))
    for c in colunas:
        proc = cfg.get("procedencia", {}).get(c, "procedência não declarada")
        print("  %-16s %4d preenchidos  | %s" % (c, preenchidos[c], proc))
    print("Estas colunas são de apoio à leitura e não entram na relevância.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "corpus_consolidado.csv")
