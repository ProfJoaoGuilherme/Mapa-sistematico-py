# -*- coding: utf-8 -*-
"""
Aplica os critérios de elegibilidade e codifica os atributos.

Lê tudo de config.py. Não contém nada específico do tema.

    python3 triar_e_codificar.py bruto_vufind.csv

Saídas
------
    incluidos.csv          registros elegíveis, já codificados
    excluidos.csv          registros descartados, com o motivo
    triagem_manual.csv     planilha ordenada por evidência, para leitura humana

A planilha de triagem manual é o produto mais importante. A codificação
automática ordena e prioriza; a decisão de inclusão cabe ao pesquisador,
conforme a recomendação de O'Mara-Eves et al. (2015). A coluna
`decisao_manual` vem vazia para preenchimento com INCLUIR ou EXCLUIR.
"""
import csv, os, re, sys, unicodedata
from collections import Counter

import config

csv.field_size_limit(10 ** 9)


def sem_acento(s):
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c))


def normalizar(s):
    return sem_acento(s).lower()


def casa(texto, padroes):
    return [p for p in padroes if re.search(p, texto)]


# ------------------------------------------------------------ NÍVEIS --------
def avaliar_nivel(texto, spec):
    """Variável em níveis, para termos ambíguos. Ver config.NIVEIS."""
    if casa(texto, spec["nivel1"]):
        return 1
    termo = spec.get("termo_ambiguo")
    if not termo or not re.search(termo, texto):
        return 0
    j = spec.get("janela", 130)
    janelas = [texto[max(0, m.start() - j):m.end() + j]
               for m in re.finditer(termo, texto)]
    valido = any(casa(w, spec["contexto_valido"]) for w in janelas)
    invalido = any(casa(w, spec.get("contexto_invalido", [])) for w in janelas)
    return 2 if (valido and not invalido) else 3


def codificar(texto):
    v = {}
    for chave, (padroes, rotulo) in config.LEXICO.items():
        v[chave] = bool(casa(texto, padroes))
    for chave, (fn, rotulo) in config.DERIVADOS.items():
        v[chave] = bool(fn(v))
    return v


def rotulos():
    r = {k: rot for k, (_, rot) in config.LEXICO.items()}
    r.update({k: rot for k, (_, rot) in config.DERIVADOS.items()})
    return r


def main(entrada="bruto_vufind.csv"):
    with open(entrada, encoding="utf-8") as fh:
        registros = list(csv.DictReader(fh))
    print(f"registros lidos: {len(registros)}")

    ini, fim = config.PERIODO
    ROT = rotulos()
    incluidos, excluidos, triagem = [], [], []
    vistos = set()

    for r in registros:
        texto = normalizar(" ".join([
            r.get("titulo", ""), r.get("titulos_alternativos", ""),
            r.get("palavras_chave", ""), r.get("resumo", "")
        ]))
        foco = normalizar(" ".join([r.get("titulo", ""),
                                    r.get("palavras_chave", "")]))

        # ---- tipo documental descartado
        tipo = (r.get("tipo_documental") or "").strip()
        if tipo in config.TIPOS_DESCARTADOS:
            r["motivo_de_exclusao"] = f"tipo documental descartado ({tipo})"
            excluidos.append(r)
            continue

        # ---- período
        try:
            ano = int(r.get("ano_de_publicacao") or 0)
        except ValueError:
            ano = 0
        if not (ini <= ano <= fim):
            r["motivo_de_exclusao"] = f"fora do periodo ({ano or 'sem ano'})"
            excluidos.append(r)
            continue

        # ---- exclusões explícitas
        if casa(texto, config.EXCLUSAO):
            r["motivo_de_exclusao"] = "criterio de exclusao explicito"
            excluidos.append(r)
            continue

        # ---- duplicata por título
        chave = re.sub(r"[^a-z0-9]", "", normalizar(r.get("titulo", "")))[:80]
        if chave in vistos:
            r["motivo_de_exclusao"] = "duplicado"
            excluidos.append(r)
            continue

        # ---- critérios
        resultado, escore, detalhe = {}, 0, {}
        for nome, spec in config.CRITERIOS.items():
            achados = casa(texto, spec["padroes"])
            resultado[nome] = bool(achados)
            detalhe[nome] = "; ".join(a.replace("\\b", "") for a in achados[:3])
            if achados:
                escore += 2 if spec["obrigatorio"] else 1

        obrig = [n for n, s in config.CRITERIOS.items() if s["obrigatorio"]]
        opc = [n for n, s in config.CRITERIOS.items() if not s["obrigatorio"]]
        ok = all(resultado[n] for n in obrig) and (not opc or any(resultado[n] for n in opc))

        if not ok:
            faltou = [n for n in obrig if not resultado[n]]
            if not faltou:
                faltou = ["nenhum criterio opcional satisfeito"]
            r["motivo_de_exclusao"] = "nao satisfaz: " + ", ".join(faltou)
            excluidos.append(r)
            continue

        vistos.add(chave)
        v = codificar(texto)
        linha = dict(r)
        for k, val in v.items():
            linha[ROT[k]] = int(val)
        for nome, spec in config.NIVEIS.items():
            n = avaliar_nivel(texto, spec)
            linha[spec["rotulo"] + "_nivel"] = n
            linha[spec["rotulo"]] = int(n in (1, 2))
        incluidos.append(linha)

        t = {"decisao_manual": "", "motivo_se_excluir": "",
             "escore_evidencia": escore}
        for nome in config.CRITERIOS:
            t["criterio_" + nome] = detalhe[nome] or ""
        for c in ("ano_de_publicacao", "tipo_documental", "base_de_origem",
                  "primeiro_autor", "titulo", "doi", "url_persistente",
                  "palavras_chave"):
            t[c] = r.get(c, "")
        t["resumo"] = (r.get("resumo") or "")[:1800]
        for k, val in v.items():
            t[ROT[k]] = int(val)
        triagem.append(t)

    triagem.sort(key=lambda x: (-x["escore_evidencia"], x["ano_de_publicacao"]))

    def gravar(nome, linhas):
        if not linhas:
            return
        campos = list(max(linhas, key=len))
        with open(nome, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=campos, restval="")
            w.writeheader()
            w.writerows(linhas)

    # O sufixo da base vem do nome do arquivo de entrada (bruto_openalex.csv ->
    # incluidos_openalex.csv), para que triar uma segunda base não sobrescreva
    # o resultado da primeira e para que consolidar_vias.py as encontre.
    base = re.sub(r"^bruto_|\.csv$", "", os.path.basename(entrada))
    sufixo = "_" + base if base else ""
    gravar("incluidos%s.csv" % sufixo, incluidos)
    gravar("excluidos%s.csv" % sufixo, excluidos)
    gravar("triagem_manual%s.csv" % sufixo, triagem)

    print(f"incluidos: {len(incluidos)} | excluidos: {len(excluidos)}")
    print("\nmotivos de exclusao:")
    for m, n in Counter(x.get("motivo_de_exclusao", "") for x in excluidos).most_common(8):
        print(f"  {n:6d}  {m}")
    print("\ndistribuicao do escore de evidencia na triagem:")
    for e, n in sorted(Counter(x["escore_evidencia"] for x in triagem).items(), reverse=True):
        print(f"  escore {e}: {n}")
    print("\ngerados: incluidos%s.csv, excluidos%s.csv, triagem_manual%s.csv"
          % (sufixo, sufixo, sufixo))
    print("Preencha a coluna decisao_manual em triagem_manual%s.csv "
          "com INCLUIR ou EXCLUIR." % sufixo)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "bruto_vufind.csv")
