# -*- coding: utf-8 -*-
"""
RELATÓRIO DO FUNIL E DA CARACTERIZAÇÃO
======================================

Gera `relatorio_funil.txt` a partir dos artefatos existentes, para que os
números relatados no texto nunca sejam digitados à mão.

    python3 relatorio_funil.py

DE ONDE VEM CADA NÚMERO
-----------------------
    recuperados / elegíveis por base
        Recontados de `bruto_<base>.csv` e `incluidos_<base>.csv` quando esses
        arquivos estiverem presentes (execução nova). Na ausência deles, lidos
        de `funil_execucao.csv`, que registra os totais da execução distribuída
        com o trabalho — uma busca é um instantâneo datado e não se reproduz
        idêntica em outra data, por isso seus totais ficam materializados.

    distintos por via, e todo o resto
        Recontados sempre de `corpus_consolidado.csv` e de
        `lista_leitura_priorizada.csv`. Nada aqui é fixo.

Se uma execução nova alterar os totais de busca, este programa reescreve
`funil_execucao.csv`, de modo que o registro acompanhe o resultado.
"""
import csv, glob, os, re, statistics, sys
from collections import Counter, defaultdict

import re
import unicodedata
import config

csv.field_size_limit(10 ** 9)

CORPUS = "corpus_consolidado.csv"
LISTA = "lista_leitura_priorizada.csv"
EXECUCAO = "funil_execucao.csv"
SAIDA = "relatorio_funil.txt"


def _texto(r):
    """titulo + palavras-chave + resumo, sem acento, minusculo"""
    s = " ".join([str(r.get("titulo", "")), str(r.get("palavras_chave", "")),
                  str(r.get("resumo", ""))])
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def conta_csv(caminho):
    with open(caminho, encoding="utf-8") as fh:
        return sum(1 for _ in csv.DictReader(fh))


def etapas_de_busca():
    """Reconta de bruto_*/incluidos_* se houver; senão lê o registro."""
    achados = {}
    for bruto in sorted(glob.glob("bruto_*.csv")):
        base = re.sub(r"^bruto_|\.csv$", "", bruto)
        inc = "incluidos_%s.csv" % base
        achados[base] = {
            "recuperados": conta_csv(bruto),
            "elegiveis": conta_csv(inc) if os.path.exists(inc) else "",
        }
    if achados:
        with open(EXECUCAO, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["base", "recuperados", "elegiveis"])
            w.writeheader()
            for base, d in achados.items():
                w.writerow({"base": base, **d})
        return achados, "recontado dos arquivos brutos desta execução"

    if not os.path.exists(EXECUCAO):
        return {}, "sem registro de busca disponível"
    with open(EXECUCAO, encoding="utf-8") as fh:
        for l in csv.DictReader(fh):
            achados[l["base"]] = {"recuperados": int(l["recuperados"]),
                                  "elegiveis": int(l["elegiveis"])}
    return achados, "lido de %s (execução distribuída)" % EXECUCAO


def main():
    if not os.path.exists(CORPUS):
        raise SystemExit("Ausente: %s. Rode consolidar_vias.py antes." % CORPUS)

    with open(CORPUS, encoding="utf-8") as fh:
        corpus = list(csv.DictReader(fh))
    lista = []
    if os.path.exists(LISTA):
        with open(LISTA, encoding="utf-8") as fh:
            lista = list(csv.DictReader(fh))

    etapas, proveniencia = etapas_de_busca()
    distintos = Counter(r.get("via_de_origem", "") for r in corpus)

    L = []
    add = L.append
    add("FUNIL DE SELECAO")
    add("gerado por relatorio_funil.py a partir dos artefatos do repositorio")
    add("etapa de busca: " + proveniencia)
    add("")
    add("%-12s %12s %10s %10s" % ("base", "recuperados", "elegiveis", "distintos"))
    tot_rec = tot_ele = 0
    for base in sorted(set(list(etapas) + list(distintos))):
        rec = etapas.get(base, {}).get("recuperados", "")
        ele = etapas.get(base, {}).get("elegiveis", "")
        dis = distintos.get(base, 0)
        tot_rec += rec if isinstance(rec, int) else 0
        tot_ele += ele if isinstance(ele, int) else 0
        add("%-12s %12s %10s %10d" % (base, rec, ele, dis))
    add("%-12s %12d %10d %10d" % ("TOTAL", tot_rec, tot_ele, len(corpus)))
    add("")

    # ------------------------------------------------ caracterizacao do corpus
    add("CARACTERIZACAO (N = %d)" % len(corpus))
    add("codificacao = PISO: descreve o que os trabalhos DECLARAM em titulo,")
    add("resumo e palavras-chave, nao o que executam.")
    add("")
    rotulos = []
    for chave, (_, rot) in config.LEXICO.items():
        rotulos.append(rot)
    for chave, (_, rot) in config.DERIVADOS.items():
        rotulos.append(rot)
    for rot in rotulos:
        if rot in corpus[0]:
            n = sum(1 for r in corpus if str(r.get(rot, "")).strip() == "1")
            add("   %-38s %5d (%.1f%%)" % (rot, n, 100 * n / len(corpus)))
    add("")

    tipos_obj = getattr(config, "TIPOS_OBJETO", None)
    if tipos_obj:
        add("TIPOS DO OBJETO (categorias nao exclusivas)")
        for rotulo, padroes in tipos_obj.items():
            rx = re.compile("|".join(padroes))
            n = sum(1 for r in corpus if rx.search(_texto(r)))
            add("   %-30s %5d (%.1f%%)" % (rotulo, n, 100 * n / len(corpus)))
        add("")

    rec = getattr(config, "RECORTE_COMPARADO", None)
    if rec:
        rx = re.compile("|".join(rec["padroes"]))
        dentro = [r for r in corpus if rx.search(_texto(r))]
        fora = [r for r in corpus if not rx.search(_texto(r))]
        add("RECORTE '%s' (N = %d) FRENTE AO RESTANTE (N = %d)"
            % (rec["rotulo"], len(dentro), len(fora)))
        add("os dois grupos se excluem: o recorte NAO entra na base de comparacao")
        add("")
        add("   %-24s %14s %14s %10s" % ("atributo", rec["rotulo"], "restante", "dif. p.p."))
        for rotulo, coluna in rec["atributos"]:
            if coluna not in corpus[0]:
                continue
            a = sum(1 for r in dentro if str(r.get(coluna, "")).strip() == "1")
            b = sum(1 for r in fora if str(r.get(coluna, "")).strip() == "1")
            pa = 100 * a / len(dentro) if dentro else 0
            pb = 100 * b / len(fora) if fora else 0
            add("   %-24s %6d %6.1f%% %6d %6.1f%% %9.1f"
                % (rotulo, a, pa, b, pb, pa - pb))
        add("")

    tipos = Counter(r.get("tipo_documental", "") for r in corpus)
    add("TIPO DOCUMENTAL")
    for t, n in tipos.most_common():
        add("   %-30s %5d" % (t or "(sem tipo)", n))
    add("")

    cit = [int(r["citacoes"]) for r in corpus
           if str(r.get("citacoes", "")).strip().isdigit()]
    if cit:
        add("CITACOES")
        add("   com contagem: %d | sem contagem: %d" % (len(cit), len(corpus) - len(cit)))
        add("   mediana %g | media %.1f | maximo %d"
            % (statistics.median(cit), statistics.mean(cit), max(cit)))
        add("")

    if lista:
        cob = Counter(r.get("cobertura_conceitos", "") for r in lista)
        add("LISTA DE LEITURA (N = %d)" % len(lista))
        add("   cobertura de conceitos: "
            + ", ".join("%s=%d" % (k, cob[k]) for k in sorted(cob, reverse=True)))
        for coluna in config.RANKING["conceitos"]:
            n = sum(1 for r in lista if str(r.get(coluna, "")).strip() == "1")
            add("   %-38s %5d (%.1f%%)" % (coluna, n, 100 * n / len(lista)))

    with open(SAIDA, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))
    print("\ngravado: %s" % SAIDA)


if __name__ == "__main__":
    main()
