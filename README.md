# Protocolo reprodutível de recuperação e curadoria de literatura

[![Licença: MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-blue.svg)](LICENSE) [![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/) [![Cite este repositório](https://img.shields.io/badge/citar-CITATION.cff-green.svg)](CITATION.cff)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21840050.svg)](https://doi.org/10.5281/zenodo.21840050)

Converte uma busca automatizada ampla em acervos de acesso aberto numa **lista
de leitura ordenada por relevância**, com cada passo registrado e repetível.
Tudo o que é específico do tema está reunido em **um único arquivo de
configuração**: aplicar o protocolo a outro objeto, de qualquer área da ciência,
exige apenas editá-lo.

O núcleo do protocolo não tem dependências externas: usa apenas a biblioteca
padrão do Python 3.10+. Os programas auxiliares pedem `pandas` e `openpyxl`.

Este repositório acompanha o artigo *Mapa sistemático da literatura sobre
sensoriamento remoto de áreas úmidas: um protocolo reprodutível de recuperação e
curadoria (2020–2026)*, e contém os programas e os artefatos que tornam os
números do texto verificáveis.

> **Estado:** repositório privado até a publicação do artigo.
>
> **Escopo:** este repositório traz o **protocolo** e os artefatos que ele gera.
> Ficam de fora apenas o que é específico deste estudo de caso — a inferência
> geográfica e os programas que desenham as figuras do artigo — além do texto do
> artigo e das próprias figuras.

---

## Início rápido

```bash
git clone https://github.com/ProfJoaoGuilherme/Mapa-sistematico-py.git
cd Mapa-sistematico-py
pip install -r requirements.txt   # só para os auxiliares

# reproduz a lista de leitura a partir do corpus da execução de referência
python3 ranquear.py corpus_consolidado.csv

# reconta todos os números do artigo a partir dos artefatos
python3 relatorio_funil.py
```

O segundo comando imprime o funil de seleção e a caracterização do corpus. É a
forma mais rápida de conferir qualquer número do artigo.

Para ler a lista sem instalar nada, abra `visualizador.html` no navegador e
carregue `lista_leitura_priorizada.csv`: busca por texto, filtros por faceta,
exportação em RIS para o Zotero e um campo para registrar a decisão de inclusão.

---

## O que faz cada programa

Executados nesta ordem, formam o protocolo completo.

| Programa | O que faz | Saída |
|---|---|---|
| `buscar.py` | consulta os acervos, nos idiomas declarados | `bruto_<base>.csv`, `log_busca.csv` |
| `triar_e_codificar.py` | aplica a elegibilidade e codifica os atributos | `incluidos_<base>.csv` |
| `consolidar_vias.py` | reúne as vias e remove repetições | `corpus_consolidado.csv` |
| `enriquecer_periodicos.py` | acrescenta Qualis e CiteScore ao corpus | corpus enriquecido |
| `ranquear.py` | ordena por relevância | `lista_leitura_priorizada.csv` |
| `relatorio_funil.py` | reconta tudo, para o texto | `relatorio_funil.txt` |

Auxiliares, independentes entre si:

| Programa | O que faz | Saída |
|---|---|---|
| `gerar_metadados_periodicos.py` | monta a tabela de procedência dos metadados de periódico | `metadados_periodicos.csv` |
| `triar_para_tese.py` | reparte a lista nos estratos de leitura definidos em `config.TRIAGEM_LEITURA` | `referencias_tese.xlsx` |

---

## Artefatos da execução de referência

Consulta realizada em **23 de julho de 2026**.

| Arquivo | O que é |
|---|---|
| `corpus_consolidado.csv` | 1.208 trabalhos distintos, já codificados |
| `lista_leitura_priorizada.csv` | a lista ordenada — resultado principal |
| `relatorio_funil.txt` | funil de seleção e caracterização, recontados do corpus |
| `funil_execucao.csv` | totais por base da execução distribuída |
| `auditoria_flips_temporais.csv` | trabalhos cuja marcação temporal mudou ao ampliar o léxico |
| `metadados_periodicos.csv` | procedência do Qualis e do CiteScore, por periódico |
| `metricas_periodicos.csv` | tabela de consulta usada no enriquecimento |
| `qualis_capes.txt` | lista Qualis (Novo) da CAPES — fonte primária do estrato |

**Uma busca não se reproduz idêntica.** As bases indexam trabalhos todo dia e
revisam metadados antigos; uma nova execução de `buscar.py` não devolverá 19.496
registros. O que se reproduz é o **procedimento**. O que é exatamente
reproduzível é a etapa do corpus em diante: dado o mesmo `corpus_consolidado.csv`,
`ranquear.py` devolve o mesmo `lista_leitura_priorizada.csv`, coluna por coluna
e linha por linha.

---

## Exemplo executável

`exemplo/` traz um corpus de **24 registros fictícios** que percorre a cadeia
inteira em segundos, para testar a instalação ou experimentar mudanças na
configuração sem tocar nos dados reais:

> **Atenção:** `consolidar_vias.py` e `ranquear.py` gravam sempre em
> `corpus_consolidado.csv` e `lista_leitura_priorizada.csv`, na raiz. Rodar o
> exemplo **sobrescreve os artefatos da execução de referência**. Faça isso numa
> cópia da pasta, ou restaure os dois arquivos com `git checkout` depois.

```bash
cp -r . /tmp/teste && cd /tmp/teste      # cópia descartável

python3 triar_e_codificar.py exemplo/bruto_exemplo.csv
python3 consolidar_vias.py incluidos_exemplo.csv
python3 ranquear.py corpus_consolidado.csv
```

As saídas esperadas estão em `exemplo/lista_exemplo.csv` e
`exemplo/referencias_exemplo.xlsx`.

---

## Qualis e CiteScore: indicadores datados

O repositório distribui a lista Qualis (Novo) da CAPES vigente em **julho de
2026** e o CiteScore do ano de referência então publicado. **São indicadores
datados, não atributos permanentes do periódico:** a CAPES reclassifica a cada
quadriênio e o CiteScore muda todo ano.

Ao repetir o levantamento em outra data:

1. baixe a lista Qualis atual em <https://sucupira.capes.gov.br> e substitua
   `qualis_capes.txt`;
2. atualize `metricas_periodicos.csv` com o CiteScore do ano corrente;
3. rode `gerar_metadados_periodicos.py` e `enriquecer_periodicos.py` de novo.

Não atualizar **não invalida a ordenação da lista** — nenhum desses atributos
entra no cálculo de relevância, e isso é verificável em `ranquear.py`. Apenas
desatualiza a informação de apoio à leitura.

---

## Adaptar a outro tema

Só `config.py` muda. Os cinco programas do núcleo não contêm uma única palavra
do domínio — verificável com:

```bash
grep -ciE "wetland|umida|landsat|sentinel" buscar.py triar_e_codificar.py \
                                            consolidar_vias.py ranquear.py
```

Roteiro:

1. **`PERIODO` e `IDIOMAS`** — se o seu campo publica sobretudo em inglês, use
   `["en"]` e poupe dois terços das requisições.
2. **`BLOCOS`** — três blocos unidos por E: `tema` × `fonte` × `abordagem`. A
   palavra "fonte" é da geociência, mas o papel é genérico: é o bloco que
   restringe o material com que se estudou o objeto. Em ensaios clínicos seria a
   intervenção; em ciências sociais, o corpus ou a técnica de coleta.
3. **`BASES`** — OpenAlex e CORE são multidisciplinares e servem a qualquer
   campo. OASISBR e BDTD só interessam se houver produção brasileira relevante.
4. **`CRITERIOS`** — o que torna um trabalho elegível. Mantenha poucos
   obrigatórios e generosos: a triagem por texto erra por excesso de rigor com
   muito mais frequência do que por excesso de tolerância.
5. **`LEXICO`** — os atributos a codificar, um por coluna. É aqui que mora o
   trabalho intelectual: cada chave é uma pergunta feita a todos os trabalhos de
   uma vez.
6. **`RANKING['conceitos']`** — os dois ou três conceitos cuja presença
   simultânea define um trabalho de primeira ordem para você.
7. **Seções opcionais** — `TIPOS_OBJETO` subdivide o objeto em tipos, para a
   caracterização temática; `TRIAGEM_LEITURA` define os estratos em que a lista
   é repartida para leitura; `ENRIQUECIMENTO_PERIODICO` aponta a tabela de
   métricas de periódico. Deixe em `None` o que não usar.

### Exemplo de outra área

Uma revisão sobre **intervenções de atenção plena e ansiedade em estudantes
universitários** mapearia assim:

| Papel | Neste repositório | No exemplo |
|---|---|---|
| `tema` | áreas úmidas, manguezal, várzea | ansiedade, estresse, sofrimento psíquico |
| `fonte` | Landsat, Sentinel, SAR | mindfulness, meditação, MBSR, MBCT |
| `abordagem` | série temporal, classificação | ensaio randomizado, estudo longitudinal |
| `LEXICO` | sensores, algoritmos, validação | duração, escala usada, grupo-controle |
| `RANKING['conceitos']` | classificação, temporal, acurácia | desenho, medida validada, seguimento |

O que não muda: a busca em blocos, a triagem por critérios declarados, a
deduplicação por DOI e título, a ordenação lexicográfica, e a regra de que a
máquina ordena e a **leitura decide**.

---

## Duas armadilhas conhecidas

São específicas das interfaces VuFind, não do método. As rotinas já as
contornam, mas quem repetir a busca deve esperá-las.

**Radicalização do índice.** A busca reduz cada palavra ao radical antes de
comparar. Em português, `mangue` recupera *manga* e *Manguebeat*; `modis`
recupera *moda* e *modernidade*. Isso não invalida a busca — amplia a
recuperação, e o ruído sai na triagem —, mas explica volumes brutos muito acima
do esperado.

**Erro 500 em páginas específicas.** A interface retorna erro interno em páginas
que contenham registros cujo metadado bruto quebra a serialização. As rotinas
saltam a página e registram a ocorrência no log.

---

## Limitação a declarar

A codificação incide sobre título, resumo e palavras-chave. Descreve o que os
trabalhos **declaram** nesses campos, não o que executam. Verificação por leitura
de texto completo encontrou trabalhos que empregam procedimentos não mencionados
no resumo e outros que citam o radar sem o utilizar.

O protocolo é, portanto, instrumento de **curadoria**, adequado para ordenar e
selecionar. Não é instrumento de medição de prevalência de práticas. Quem
precisar dessa medição terá de ler os textos completos.

Consequência prática ao reportar números: *"X% dos trabalhos que declararam
método"* é uma afirmação defensável; *"X% dos trabalhos usam o método"* não é.

---

## Histórico de versões

Ver [CHANGELOG.md](CHANGELOG.md). Cada versão publicada recebe um DOI próprio
no Zenodo; cite o da versão que você usou.

---

## Licença e citação

Código sob licença MIT (ver `LICENSE`). Os arquivos de dados têm procedências
distintas, declaradas no mesmo arquivo.

Para citar, ver `CITATION.cff`.

---

## Referências do método

GRANT, M. J.; BOOTH, A. A typology of reviews: an analysis of 14 review types
and associated methodologies. *Health Information & Libraries Journal*, v. 26,
n. 2, p. 91-108, 2009.

O'MARA-EVES, A. et al. Using text mining for study identification in systematic
reviews: a systematic review of current approaches. *Systematic Reviews*, v. 4,
n. 5, 2015.

OUZZANI, M. et al. Rayyan: a web and mobile app for systematic reviews.
*Systematic Reviews*, v. 5, n. 210, 2016.

PAGE, M. J. et al. The PRISMA 2020 statement: an updated guideline for reporting
systematic reviews. *BMJ*, v. 372, n. 71, 2021.
