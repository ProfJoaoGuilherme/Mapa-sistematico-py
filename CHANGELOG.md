# Registro de alterações

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).
As versões seguem [Versionamento Semântico](https://semver.org/lang/pt-BR/).

Cada versão publicada recebe um DOI próprio no Zenodo. **Cite sempre o DOI da
versão que você usou**, não o conceitual — este resolve para a mais recente, e
quem seguir sua citação precisa chegar exatamente ao que você utilizou.

---

## [Não publicado]

### Adicionado

- Caminho sem programação: `modelo_configuracao.xlsx` (exemplo preenchido),
  `modelo_configuracao_em_branco.xlsx`, `planilha_para_config.py`, que traduz
  a planilha em `config.py`, e `protocolo_no_colab.ipynb`, que executa o
  protocolo inteiro no Google Colab.
- `GUIA_SEM_PROGRAMACAO.md`, com o preenchimento aba por aba, a execução no
  Colab e a calibração dos termos.
- `visualizador.html` passa a exibir, como colunas e filtros, os conceitos e
  atributos de qualquer tema. A lista de referência aparece como antes.

### Configuração

- BDTD desativada em `config.BASES` (`automatica=False`), como declara o
  artigo. Os 121 elegíveis dela na execução de referência já vinham pela
  OASISBR. O corpus e a lista de leitura não mudam.
- Crossref e Semantic Scholar desativadas em `config.BASES`
  (`automatica=False`). Não fizeram parte da execução de referência, e
  `buscar.py` sem argumentos passa a consultar só os acervos do artigo:
  OpenAlex, OASISBR e CORE.
- Restaurado `config.RECORTE_COMPARADO` (Pantanal frente ao restante), que
  faltava na versão 1.0.0. Sem ele, `relatorio_funil.py` omitia a tabela do
  recorte e não reproduzia o `relatorio_funil.txt` distribuído.

### Documentação

- Retirado do `README.md` o aviso de repositório privado.
- Registrada no `README.md` a sobreposição entre BDTD e OASISBR.
- Registrada no `README.md` a lacuna do léxico de acurácia (`exatidao`,
  `validacao`), com o efeito medido sobre a lista de referência. Os números do
  artigo não mudam.

---

## [1.0.0] — 2026-08-07

Primeira versão publicada, correspondente ao artigo submetido ao Simpósio de
Geotecnologias no Pantanal.

### O protocolo

- Busca automatizada em quatro acervos de acesso aberto — OpenAlex, OASISBR,
  BDTD e CORE — com equações por blocos (tema × fonte × abordagem) em três
  idiomas.
- Triagem por critérios declarados e codificação de atributos, ambos definidos
  em `config.py`.
- Consolidação entre vias com deduplicação por DOI e, na falta dele, por título
  normalizado.
- Ordenação por relevância em quatro níveis: cobertura de conceitos,
  centralidade do objeto, percentil de citação na coorte do ano e recência.
  Nenhum trabalho é cortado — a máquina ordena, a leitura decide.
- Enriquecimento opcional com Qualis e CiteScore, que **não entram** no cálculo
  de relevância.
- Interface de leitura em `visualizador.html`, sem instalação, com exportação
  em RIS para o Zotero.
- Relatório do funil que reconta todos os números a partir dos artefatos.

### Artefatos da execução de referência

Consulta em 23 de julho de 2026: 19.496 registros recuperados, 1.414 elegíveis
por base, 1.208 trabalhos distintos.

### Notas desta versão

- O núcleo do protocolo não tem dependências externas: usa apenas a biblioteca
  padrão do Python 3.10+. Os programas auxiliares pedem `pandas` e `openpyxl`.
- A lista Qualis distribuída é a vigente em julho de 2026. A CAPES reclassifica
  a cada quadriênio; ver a seção correspondente no `README.md`.
- A codificação descreve o que os trabalhos **declaram** em título, resumo e
  palavras-chave, não o que executam. É instrumento de curadoria, não de
  medição de prevalência de práticas.
