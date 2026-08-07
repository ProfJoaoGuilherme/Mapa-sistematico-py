# -*- coding: utf-8 -*-
"""
PRIORIZAÇÃO DA LISTA DE LEITURA
===============================

Lê tudo de config.py (seção RANKING). Não contém nada específico do tema: os
nomes das colunas de saída, os conceitos de interesse e os campos herdados são
declarados na configuração, de modo que a mesma rotina serve a qualquer área.

    python3 ranquear.py                      # usa corpus_consolidado.csv
    python3 ranquear.py meu_corpus.csv       # outro arquivo de entrada

Ordena os trabalhos por RELEVÂNCIA à pergunta do pesquisador, seguindo a boa
prática de triagem (screening): a máquina PRIORIZA; a INCLUSÃO é decidida por
leitura (O'Mara-Eves et al., 2015). Nada é cortado.

A relevância combina, sem peso arbitrário, nesta ordem lexicográfica:

  1) cobertura de conceitos — quantos dos RANKING['conceitos'] o trabalho
     satisfaz (cada conceito é um OU de padrões sobre título+palavras+resumo);
  2) centralidade do objeto — RANKING['foco_termos'] ponderado por campo
     (título vale mais que palavras-chave, que valem mais que o resumo);
  3) desempate — citação normalizada pela idade (percentil na coorte do ano)
     ou recência, conforme RANKING['desempate'].

Empates em todos os critérios preservam a ordem do corpus de entrada (a
ordenação é estável), de modo que a saída é determinística para uma dada
entrada.

TODA COLUNA DA SAÍDA É PRODUZIDA AQUI OU HERDADA DO CORPUS
----------------------------------------------------------
    cobertura_conceitos    soma dos conceitos satisfeitos
    <conceitos>            uma coluna por chave de RANKING['conceitos']
    <foco_coluna>          centralidade do objeto, ponderada por campo
    <descritivos>          renomeação de rótulos já codificados no LÉXICO
    <grupos>               'declarou algum destes' + quais (ex.: metodo_qual)
    cit_percentil_coorte   percentil da citação na coorte do ano
    cit_por_ano            citações / (ano_referência − ano de publicação)
    <marcadores_tipo>      binários derivados do tipo documental
    <enriquecimento>       herdadas de enriquecer_periodicos.py, se presentes
    <campos_herdados>      campos do corpus, renomeados conforme a configuração

Saída: lista_leitura_priorizada.csv. Leia de cima para baixo, e use as facetas
(tipo documental, via de origem, foco) para varrer por recortes, de modo que
nenhum trabalho forte se perca no desempate.
"""
import csv, re, sys, unicodedata
from collections import defaultdict
from datetime import date

import config

csv.field_size_limit(10 ** 9)


def sem_acento(s):
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def texto(r):
    return sem_acento(" ".join([r.get("titulo", ""), r.get("palavras_chave", ""),
                                r.get("resumo", "")]))


def casa_algum(t, padroes):
    return any(re.search(p, t) for p in padroes)


def centralidade(r, cfg):
    """Termo do objeto ponderado por campo: título > palavras-chave > resumo."""
    pat = cfg["foco_termos"]
    th = 1 if any(re.search(p, sem_acento(r.get("titulo", ""))) for p in pat) else 0
    kh = 1 if any(re.search(p, sem_acento(r.get("palavras_chave", ""))) for p in pat) else 0
    rh = sum(len(re.findall(p, sem_acento(r.get("resumo", "")))) for p in pat)
    return (cfg["foco_peso_titulo"] * th
            + cfg["foco_peso_palavras_chave"] * kh
            + min(rh, cfg["foco_resumo_max"]))


def num_citacoes(r):
    try:
        return int(r.get("citacoes") or "")
    except ValueError:
        return None


def percentil_coorte(valor, coorte):
    """Percentil da citação dentro da coorte do ano (0..100)."""
    if valor is None:
        return ""
    pool = sorted(coorte)
    if len(pool) <= 1:
        return 100.0
    menores = sum(1 for x in pool if x < valor)
    return round(100 * menores / (len(pool) - 1), 1)


def ano_de(r):
    try:
        return int(r.get("ano_de_publicacao") or 0)
    except ValueError:
        return 0


def bin_col(r, rotulo):
    """Lê um rótulo binário já codificado no corpus."""
    return 1 if str(r.get(rotulo, "")).strip() in ("1", "True", "true") else 0


def main(entrada="corpus_consolidado.csv"):
    cfg = config.RANKING
    with open(entrada, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise SystemExit("Entrada vazia: " + entrada)

    presentes = set(rows[0])
    ano_ref = cfg.get("ano_referencia") or date.today().year

    # coortes de citação por ano de publicação
    por_ano = defaultdict(list)
    for r in rows:
        c = num_citacoes(r)
        if c is not None:
            por_ano[r.get("ano_de_publicacao", "")].append(c)

    faltando = set()
    for r in rows:
        t = texto(r)

        # 1) conceitos de interesse: a chave da configuração é o nome da coluna
        cob = 0
        for coluna, padroes in cfg["conceitos"].items():
            v = int(casa_algum(t, padroes))
            r[coluna] = v
            cob += v
        r["cobertura_conceitos"] = cob

        # 2) centralidade do objeto
        r[cfg["foco_coluna"]] = centralidade(r, cfg)

        # 3) descritivos: renomeia rótulos já codificados no LÉXICO
        for coluna, rotulo in cfg.get("descritivos", {}).items():
            if rotulo not in presentes:
                faltando.add(rotulo)
            r[coluna] = bin_col(r, rotulo)

        # 4) grupos: binária de resumo + coluna textual com os membros
        for coluna, spec in cfg.get("grupos", {}).items():
            siglas = []
            for sigla, rotulo in spec["membros"].items():
                if rotulo not in presentes:
                    faltando.add(rotulo)
                if bin_col(r, rotulo):
                    siglas.append(sigla)
            r[coluna] = int(bool(siglas))
            r[spec["coluna_qual"]] = ";".join(siglas)

        # 5) marcadores derivados do tipo documental
        tipo = (r.get("tipo_documental") or "").strip()
        for coluna, tipos in cfg.get("marcadores_tipo", {}).items():
            r[coluna] = int(tipo in tipos)

        # 6) métricas de citação
        c = num_citacoes(r)
        a = ano_de(r)
        r["citacoes"] = "" if c is None else c
        r["cit_percentil_coorte"] = percentil_coorte(
            c, por_ano.get(r.get("ano_de_publicacao", ""), []))
        r["cit_por_ano"] = "" if c is None else round(c / max(ano_ref - a, 1), 1)

        r["_ano"] = a
        r["_pc"] = r["cit_percentil_coorte"] if r["cit_percentil_coorte"] != "" else -1.0
        r.setdefault("decisao_inclusao", "")
        r.setdefault("disrupcao_por_leitura", "")

    if faltando:
        print("AVISO: rótulos declarados em RANKING e ausentes no corpus: "
              + ", ".join(sorted(faltando))
              + "\n       (rode triar_e_codificar.py com o LEXICO atual)")

    if cfg.get("desempate") == "recencia":
        desempate = lambda r: (-r["_ano"], -r["_pc"])
    else:
        desempate = lambda r: (-r["_pc"], -r["_ano"])
    rows.sort(key=lambda r: (-r["cobertura_conceitos"], -r[cfg["foco_coluna"]])
              + desempate(r))
    for i, r in enumerate(rows, 1):
        r["ordem"] = i

    # ------------------------------------------------------ ordem das colunas
    cols = ["ordem", "decisao_inclusao", "disrupcao_por_leitura",
            "cobertura_conceitos"]
    cols += list(cfg["conceitos"])
    cols += [cfg["foco_coluna"]]
    cols += list(cfg.get("descritivos", {}))
    for coluna, spec in cfg.get("grupos", {}).items():
        cols += [coluna, spec["coluna_qual"]]
    cols += ["cit_percentil_coorte", "cit_por_ano", "citacoes"]
    cols += [c for c in cfg.get("colunas_enriquecimento", []) if c in presentes]
    cols += list(cfg.get("marcadores_tipo", {}))

    saida = []
    for r in rows:
        d = {c: r.get(c, "") for c in cols}
        for campo, nome in cfg["campos_herdados"]:
            d[nome] = r.get(campo, "")
        saida.append(d)
    cols += [nome for _, nome in cfg["campos_herdados"]]

    destino = "lista_leitura_priorizada.csv"
    with open(destino, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore", restval="")
        w.writeheader()
        w.writerows(saida)

    print("gerado %s: %d trabalhos, ordenados por relevância." % (destino, len(saida)))
    dist = defaultdict(int)
    for r in rows:
        dist[r["cobertura_conceitos"]] += 1
    print("cobertura de conceitos:", {k: dist[k] for k in sorted(dist, reverse=True)})
    print("Leia de cima para baixo; use as facetas para varrer por recortes.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "corpus_consolidado.csv")
