# -*- coding: utf-8 -*-
"""
Consolida as vias de recuperação em tabela única, removendo repetições.

Cada via de busca — base internacional, repositório sem interface de
programação e repositórios nacionais — produz sua própria tabela. Este
programa as reúne, identifica os trabalhos que aparecem em mais de uma via e
grava um único arquivo, no qual cada linha corresponde a um trabalho distinto.

    python3 consolidar_vias.py via1.csv via2.csv via3.csv

Sem argumentos, procura os nomes padrão gerados pelos demais programas.

CRITÉRIO DE REPETIÇÃO
---------------------
Dois registros são o mesmo trabalho quando têm o mesmo identificador digital
de objeto ou, na ausência dele, o mesmo título normalizado — reduzido a
minúsculas, sem acentos, sem pontuação e limitado aos primeiros oitenta
caracteres. O limite evita que subtítulos divergentes separem o que é um só
trabalho.

Quando um trabalho aparece em mais de uma via, prevalece o registro da via
listada primeiro, e as demais ocorrências ficam anotadas na coluna
`tambem_encontrado_em`, preservando o rastro.

SAÍDAS
------
    corpus_consolidado.csv     um trabalho por linha, com a via de origem
    repeticoes_entre_vias.csv  os pares identificados como o mesmo trabalho
"""
import csv, glob, os, re, sys, unicodedata
from collections import defaultdict

csv.field_size_limit(10 ** 9)

# Sem argumentos, consolida os incluidos_<base>.csv — isto é, o que JÁ PASSOU
# pela triagem — mais os arquivos manuais (ex.: via_scielo.csv exportado do
# RIS). A ordem define a prioridade quando o mesmo trabalho aparece em mais de
# uma via. Consolidar os bruto_<base>.csv seria um erro: eles não passaram pelos
# critérios de elegibilidade.
PADRAO = (["via_scielo.csv", "via_nacional.csv"]
          + sorted(glob.glob("incluidos_*.csv"))
          + ["incluidos.csv"])


def sem_acento(s):
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c))


def chave_titulo(t):
    return re.sub(r"[^a-z0-9]", "", sem_acento(t).lower())[:80]


def chave_doi(d):
    d = (d or "").strip().lower()
    for p in ("https://doi.org/", "http://dx.doi.org/", "https://dx.doi.org/",
              "http://doi.org/", "doi:"):
        if d.startswith(p):
            d = d[len(p):]
    return d if d.startswith("10.") else ""


def campo(r, *nomes):
    for n in nomes:
        if r.get(n):
            return r[n]
    return ""


def main(arquivos):
    if not arquivos:
        arquivos = [a for a in PADRAO if os.path.exists(a)]
    if not arquivos:
        raise SystemExit("Nenhuma tabela encontrada. Informe os arquivos como "
                         "argumentos: python3 consolidar_vias.py a.csv b.csv")

    print("vias a consolidar, em ordem de prioridade:")
    for a in arquivos:
        print(f"   {a}")
    print()

    consolidado = {}          # chave -> registro
    por_chave = defaultdict(list)
    repeticoes = []
    total_lido = 0

    for arquivo in arquivos:
        # A via é o nome da base, não o do arquivo: incluidos_openalex.csv ->
        # 'openalex'. Mantém o corpus comparável entre execuções e alinhado ao
        # que relatorio_funil.py espera.
        via = re.sub(r"^(incluidos|bruto|via)_|\.csv$", "",
                     os.path.basename(arquivo))
        via = os.path.splitext(via)[0]
        with open(arquivo, encoding="utf-8") as fh:
            registros = list(csv.DictReader(fh))
        total_lido += len(registros)
        novos = repetidos = 0

        for r in registros:
            titulo = campo(r, "titulo", "title")
            doi = chave_doi(campo(r, "doi", "DOI"))
            k_doi = "doi:" + doi if doi else None
            k_tit = "tit:" + chave_titulo(titulo)

            achou = None
            for k in (k_doi, k_tit):
                if k and k in consolidado:
                    achou = k
                    break

            if achou:
                repetidos += 1
                anterior = consolidado[achou]
                vias = anterior.get("tambem_encontrado_em", "")
                anterior["tambem_encontrado_em"] = (
                    vias + "; " + via if vias else via)
                repeticoes.append({
                    "chave": achou,
                    "via_que_prevalece": anterior.get("via_de_origem", ""),
                    "via_repetida": via,
                    "titulo": titulo[:150],
                    "doi": doi,
                })
                continue

            r["via_de_origem"] = via
            r["tambem_encontrado_em"] = ""
            r["titulo"] = titulo
            r["doi"] = doi
            if k_doi:
                consolidado[k_doi] = r
                por_chave[k_tit].append(k_doi)
            consolidado[k_tit] = r
            novos += 1

        print(f"{via}: {len(registros)} lidos | {novos} novos | "
              f"{repetidos} repetidos de via anterior")

    # remove as entradas duplicadas de índice (mesmo objeto sob duas chaves)
    unicos, vistos = [], set()
    for r in consolidado.values():
        marca = id(r)
        if marca in vistos:
            continue
        vistos.add(marca)
        unicos.append(r)

    campos = []
    for r in unicos:
        for c in r:
            if c not in campos:
                campos.append(c)
    for c in ("via_de_origem", "tambem_encontrado_em"):
        if c in campos:
            campos.remove(c)
    campos = ["via_de_origem", "tambem_encontrado_em"] + campos

    with open("corpus_consolidado.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, restval="", extrasaction="ignore")
        w.writeheader()
        w.writerows(unicos)

    if repeticoes:
        with open("repeticoes_entre_vias.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(repeticoes[0]))
            w.writeheader()
            w.writerows(repeticoes)

    print(f"\nregistros lidos no total: {total_lido}")
    print(f"trabalhos distintos após consolidação: {len(unicos)}")
    print(f"repetições entre vias: {len(repeticoes)}")
    print("gerados: corpus_consolidado.csv, repeticoes_entre_vias.csv")
    print("\nEste é o arquivo a ser usado nas etapas seguintes de análise: "
          "cada linha corresponde a um trabalho distinto, com a via de origem "
          "registrada e as repetições anotadas.")


if __name__ == "__main__":
    main(sys.argv[1:])
