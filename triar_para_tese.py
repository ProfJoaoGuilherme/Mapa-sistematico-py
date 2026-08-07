# -*- coding: utf-8 -*-
"""
TRIAGEM DE LEITURA — MONTAGEM DA LISTA DE REFERÊNCIAS
=====================================================

Reparte a lista priorizada nos estratos de leitura definidos em
config.TRIAGEM_LEITURA, do mais próximo da pergunta de pesquisa ao mais
periférico. Não contém nada específico do tema.

    python3 triar_para_tese.py lista_leitura_priorizada.csv

Saída: referencias_tese.xlsx, uma aba por estrato mais um resumo.

PRINCÍPIO
---------
O eixo é CONCEITUAL, não geográfico. O que ordena a leitura é o que o trabalho
faz — se classifica, se tipifica, se valida, se diz com que método —, não onde
foi feito. A área de estudo entra como marcador descritivo e ganha uma aba
transversal própria, mas nunca corta ninguém dos estratos conceituais: a
literatura que responde "o que funciona melhor" quase nunca é da sua região.

Cada trabalho cai no PRIMEIRO estrato cujas condições satisfaz, de modo que as
abas conceituais são mutuamente exclusivas e podem ser lidas em sequência.

AVISO
-----
A codificação é por declaração. Um trabalho pode relatar acurácia sem dizê-lo
no resumo, e cairá num estrato mais baixo do que merece. A triagem ordena a
leitura; não a substitui.
"""
import re, sys, unicodedata
import pandas as pd

import config

cfg = getattr(config, "TRIAGEM_LEITURA", None)
if not cfg:
    raise SystemExit("config.TRIAGEM_LEITURA nao definido.")

MARCADORES = {k: "|".join(v) for k, v in cfg.get("marcadores", {}).items()}
ATRIBUTOS = {k: "|".join(v) for k, v in cfg.get("atributos", {}).items()}

COLS = ["estrato", "ordem", "ano", "autor", "titulo", "periodico", "tipo",
        "metodo_qual", "acuracia", "multitemporal", "atributos",
        "via", "citacoes", "doi", "url_persistente"]


def norm(s):
    s = unicodedata.normalize("NFKD", str(s) if pd.notna(s) else "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def condicao(d, nome):
    """Resolve o nome de uma condição para uma série booleana."""
    if nome in MARCADORES:
        return d["_" + nome]
    if nome == "metodo":
        return d["metodo_qual"].notna()
    if nome in d.columns:
        return d[nome] == 1
    raise SystemExit("condicao desconhecida em TRIAGEM_LEITURA: %r" % nome)


def main(entrada="lista_leitura_priorizada.csv", saida="referencias_tese.xlsx"):
    d = pd.read_csv(entrada)
    d["txt"] = (d["titulo"].fillna("") + " " + d["palavras_chave"].fillna("")
                + " " + d["resumo"].fillna("")).map(norm)

    for rotulo, padrao in MARCADORES.items():
        d["_" + rotulo] = d["txt"].str.contains(padrao, regex=True, na=False)
        d[rotulo] = d["_" + rotulo].map({True: "sim", False: ""})

    d["atributos"] = [
        "; ".join(k for k, p in ATRIBUTOS.items() if re.search(p, t)) or "—"
        for t in d["txt"]
    ]

    extras = list(MARCADORES)
    livre = pd.Series(True, index=d.index)      # ainda não alocado
    abas, resumo = [], []

    for e in cfg["estratos"]:
        m = livre.copy()
        for c in e.get("exige", []):
            m &= condicao(d, c)
        for c in e.get("exclui", []):
            m &= ~condicao(d, c)
        s = d[m].copy()
        s["estrato"] = e["nome"]
        abas.append((e["nome"], s.sort_values("ordem")))
        resumo.append({"estrato": e["nome"], "trabalhos": int(m.sum()),
                       "com metodo nomeado": int((m & d["metodo_qual"].notna()).sum()),
                       "o que e": e.get("nota", "")})
        livre &= ~m                              # exclusivo entre estratos

    tv = cfg.get("recorte_transversal")
    if tv:
        m = condicao(d, tv["marcador"])
        s = d[m].copy()
        s["estrato"] = tv["nome"]
        abas.append((tv["nome"], s.sort_values("ordem")))
        resumo.append({"estrato": tv["nome"], "trabalhos": int(m.sum()),
                       "com metodo nomeado": int((m & d["metodo_qual"].notna()).sum()),
                       "o que e": tv.get("nota", "") + " (transversal: repete trabalhos das abas acima)"})

    with pd.ExcelWriter(saida, engine="openpyxl") as xw:
        pd.DataFrame(resumo).to_excel(xw, sheet_name="resumo", index=False)
        for nome, s in abas:
            s[COLS + extras].to_excel(xw, sheet_name=nome[:31], index=False)

    # ---------------------------------------------------------- formatação
    from openpyxl import load_workbook
    from openpyxl.styles import Font, Alignment
    from openpyxl.utils import get_column_letter
    wb = load_workbook(saida)
    larg = {"titulo": 70, "autor": 24, "periodico": 28, "atributos": 22,
            "metodo_qual": 12, "doi": 26, "url_persistente": 30,
            "estrato": 30, "o que e": 52, "tipificacao": 11,
            "area_de_estudo": 14}
    for ws in wb:
        ws.freeze_panes = "A2"
        for c in ws[1]:
            c.font = Font(name="Arial", bold=True)
            c.alignment = Alignment(vertical="center", wrap_text=True)
        cab = [c.value for c in ws[1]]
        for i, nome in enumerate(cab, start=1):
            ws.column_dimensions[get_column_letter(i)].width = larg.get(nome, 12)
        for row in ws.iter_rows(min_row=2):
            for c in row:
                c.font = Font(name="Arial")
                c.alignment = Alignment(
                    vertical="top",
                    wrap_text=(cab[c.column - 1] in ("titulo", "o que e")))
    wb.save(saida)

    print("gerado %s" % saida)
    for r in resumo:
        print("  %-34s %4d trabalhos (%d com metodo nomeado)"
              % (r["estrato"], r["trabalhos"], r["com metodo nomeado"]))


if __name__ == "__main__":
    main(*sys.argv[1:3])
