# Guia: aplicar o protocolo a outro tema sem programar

[![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ProfJoaoGuilherme/Mapa-sistematico-py/blob/main/protocolo_no_colab.ipynb)

Este guia é para quem quer usar o protocolo no seu próprio tema e não programa.
Você descreve o tema numa **planilha**, em palavras comuns, e executa tudo no
**Google Colab**, pelo navegador. Não é preciso instalar nada nem abrir nenhum
arquivo de código.

O resultado é o mesmo da versão em linha de comando: uma lista de leitura
ordenada por relevância, o relatório do funil de seleção e as planilhas de
triagem manual.

---

## Sumário

1. [O que você vai precisar](#1-o-que-você-vai-precisar)
2. [Como as peças se encaixam](#2-como-as-peças-se-encaixam)
3. [Passo 1 — Obter a planilha](#3-passo-1--obter-a-planilha)
4. [Passo 2 — Pensar a pergunta em três blocos](#4-passo-2--pensar-a-pergunta-em-três-blocos)
5. [Passo 3 — Preencher a planilha, aba por aba](#5-passo-3--preencher-a-planilha-aba-por-aba)
6. [Passo 4 — Executar no Colab](#6-passo-4--executar-no-colab)
7. [Passo 5 — Calibrar os termos](#7-passo-5--calibrar-os-termos)
8. [Passo 6 — Ler a lista](#8-passo-6--ler-a-lista)
9. [O que a planilha não cobre](#9-o-que-a-planilha-não-cobre)
10. [Executar no próprio computador](#10-executar-no-próprio-computador)
11. [Problemas comuns](#11-problemas-comuns)

---

## 1. O que você vai precisar

- Uma **conta Google**, para o Colab e, se quiser, o Google Planilhas.
- A **planilha-modelo**, que vem deste repositório.
- Cerca de **uma hora** para preencher a planilha pela primeira vez. É aqui que
  mora o trabalho intelectual, e nenhum programa faz essa parte por você.
- Tempo de busca. O OpenAlex responde em minutos. A OASISBR, que alcança a
  produção brasileira, pode levar horas.
- Opcional: uma **chave gratuita do CORE**, se quiser incluir essa base.
  Cadastro em <https://core.ac.uk/services/api>.

---

## 2. Como as peças se encaixam

```
 planilha (.xlsx)          você escreve o tema em palavras comuns
       │
       ▼
 planilha_para_config.py   traduz a planilha em config.py e aponta erros
       │
       ▼
 buscar.py                 consulta as bases          → bruto_<base>.csv
 triar_e_codificar.py      aplica os critérios        → incluidos_<base>.csv
 consolidar_vias.py        remove repetições          → corpus_consolidado.csv
 ranquear.py               ordena por relevância      → lista_leitura_priorizada.csv
 relatorio_funil.py        reconta cada etapa         → relatorio_funil.txt
```

O caderno do Colab (`protocolo_no_colab.ipynb`) executa essa sequência por
você, uma célula para cada etapa. Os programas são os mesmos do estudo de
referência. A única coisa que muda de um tema para outro é a planilha.

---

## 3. Passo 1 — Obter a planilha

Há dois arquivos:

| Arquivo | Quando usar |
|---|---|
| [`modelo_configuracao.xlsx`](https://github.com/ProfJoaoGuilherme/Mapa-sistematico-py/raw/main/modelo_configuracao.xlsx) | **Comece por este.** Vem preenchido com o exemplo de áreas úmidas, para você ver como cada aba é usada, e basta substituir os termos. |
| [`modelo_configuracao_em_branco.xlsx`](https://github.com/ProfJoaoGuilherme/Mapa-sistematico-py/raw/main/modelo_configuracao_em_branco.xlsx) | Só os cabeçalhos e as explicações, para quem já conhece o formato. |

Clique no link para baixar. Depois escolha onde editar:

- **Google Planilhas** (recomendado, porque o Colab lê direto do link). Envie o
  arquivo ao seu Google Drive, clique nele com o botão direito e escolha
  *Abrir com* → *Planilhas Google*. Na hora de rodar, compartilhe a planilha em
  *Compartilhar* → *Qualquer pessoa com o link* → *Leitor*.
- **Excel ou LibreOffice Calc**. Edite e salve em `.xlsx`. No Colab, você vai
  enviar o arquivo do seu computador.

A primeira aba, **LEIA-ME**, resume as regras deste guia.

> **Regras que valem para todas as abas**
> - Não altere a primeira linha (o cabeçalho). O programa localiza as colunas
>   pelo nome.
> - Uma linha por termo. Repita o nome do grupo em cada linha.
> - Linhas vazias são ignoradas. Abas opcionais podem ficar vazias.
> - Não renomeie as abas.

---

## 4. Passo 2 — Pensar a pergunta em três blocos

Antes de digitar qualquer coisa, escreva a sua pergunta e quebre-a em três
partes. A busca exige as três ao mesmo tempo:

```
   (tema)  E  (fonte)  E  (abordagem)
```

| Bloco | Pergunta que ele responde | Estudo de referência |
|---|---|---|
| **tema** | Qual é o objeto? | áreas úmidas, manguezal, várzea |
| **fonte** | Com que material ou meio o objeto é estudado? | Landsat, Sentinel, radar |
| **abordagem** | Como o objeto é examinado? | série temporal, classificação |

Dentro de cada bloco, os termos se unem por **OU**: basta o trabalho citar um
deles. Entre blocos, vale o **E**: o trabalho precisa citar algo dos três.

A palavra "fonte" vem da geociência, mas o papel do bloco é genérico. Veja como
ficariam outros temas:

| Bloco | Pecuária e território | Atenção plena e ansiedade |
|---|---|---|
| tema | pecuária bovina, cattle ranching | ansiedade, estresse, sofrimento psíquico |
| fonte | estrutura fundiária, uso e cobertura da terra | mindfulness, meditação, MBSR |
| abordagem | dinâmica espacial, análise temporal | ensaio randomizado, estudo longitudinal |

O exemplo da pecuária foi testado de fato com estes mesmos programas. Dele
saíram três lições, que valem para qualquer tema:

1. **Restrinja o bloco do tema.** `livestock` sozinho trouxe suinocultura,
   avicultura e aquicultura, e `livestock` mais `cattle` sem qualificação
   devolveram 49 mil registros só em inglês.
2. **Use a aba de exclusão quando o termo do objeto tiver outro uso.** Sem ela,
   entrariam trabalhos de reprodução animal e sanidade.
3. **Escolha conceitos que variam no conjunto.** Um conceito presente em 90%
   dos trabalhos não ajuda a ordenar a lista. Veja a aba *conceitos* abaixo.

---

## 5. Passo 3 — Preencher a planilha, aba por aba

### Como os termos são lidos

Nas abas *criterios*, *exclusao*, *atributos*, *conceitos*, *subtipos* e
*recorte*, cada termo é procurado no **título, no resumo e nas palavras-chave**
de cada trabalho. O programa aplica estas regras:

| Regra | Exemplo |
|---|---|
| Acentos e maiúsculas não importam | `Várzea` encontra *varzea* e *VÁRZEA* |
| O termo casa com o **começo** da palavra | `wetland` encontra *wetlands* |
| Espaço e hífen se equivalem | `time series` encontra *time-series* |
| `palavra_inteira = sim` exige a palavra exata | `SAR` com a marca não encontra *sarampo* |
| Asterisco no fim é aceito e ignorado | `accurac*` equivale a `accurac` |

Três cuidados decorrem dessas regras:

- **O plural de termos compostos precisa ser escrito.** `área úmida` não
  encontra *áreas úmidas*, porque o "s" fica no meio da expressão. Escreva as
  duas formas.
- **Siglas curtas pedem `palavra_inteira = sim`.** Sem a marca, `SAR`
  encontraria *sarampo* e `fen` encontraria *fenologia*.
- **Use o radical para pegar variações.** `accurac` encontra *accuracy* e
  *accurate*. `validat` encontra *validation* e *validated*, mas não
  *validação*. Para o português e o espanhol, escreva `validação` e
  `validación` à parte.

A aba *busca* segue outra lógica, explicada a seguir.

### Aba `geral`

Preencha só a coluna **valor**. A coluna *explicacao* está ali para consulta.

| parâmetro | O que é | Exemplo |
|---|---|---|
| `nome_do_tema` | Nome livre, só para identificação | Pecuária e estrutura fundiária |
| `ano_inicial` / `ano_final` | Recorte temporal, com os dois anos incluídos | 2020 / 2026 |
| `idiomas` | Idiomas da busca, separados por vírgula: `en`, `pt`, `es` | `en, pt, es` |
| `bases` | Bases a consultar, separadas por vírgula (ver abaixo) | `openalex, oasisbr` |
| `nome_curto_do_objeto` | Nome da coluna de centralidade, sem espaços | `pecuaria` (vira `foco_pecuaria`) |
| `criterio_do_objeto` | Qual critério descreve o objeto. Se ficar vazio, vale o primeiro obrigatório | `objeto` |
| `desempate` | `citacao` (citações comparadas no mesmo ano) ou `recencia` (mais novo primeiro) | `citacao` |
| `limite_por_consulta` | Teto de registros baixados por consulta. Use 200 para testar | 2000 |
| `nome_do_recorte` | Nome do recorte comparado, só se a aba *recorte* for usada | Amazônia |

As bases disponíveis são estas:

| Base | Cobertura | Observação |
|---|---|---|
| `openalex` | internacional, multidisciplinar | rápida; **use sempre** |
| `oasisbr` | produção brasileira: teses, dissertações e periódicos nacionais | lenta, mas indispensável para temas com produção nacional |
| `core` | repositórios de acesso aberto do mundo todo | exige chave gratuita |
| `bdtd` | teses e dissertações brasileiras | no estudo de referência, já estava toda contida na OASISBR |
| `crossref`, `semanticscholar` | internacionais | buscam por texto livre e trazem muitos registros sem resumo |

### Aba `busca`

Três colunas: **idioma**, **bloco** (`tema`, `fonte` ou `abordagem`) e
**termo**. Cada idioma da aba *geral* precisa dos três blocos preenchidos.

| idioma | bloco | termo |
|---|---|---|
| en | tema | cattle ranching |
| en | tema | beef cattle |
| en | fonte | land tenure |
| en | fonte | land use |
| en | abordagem | spatial dynamics |
| pt | tema | pecuária bovina |
| … | … | … |

Aqui os termos vão **para as bases**, e não para o texto dos trabalhos. Por
isso as regras são outras:

- Termos com espaço viram expressão exata (`"land use"`), sem você precisar
  das aspas.
- Escreva os termos com acento, como aparecem nos trabalhos. As bases cuidam do
  resto.
- **Os termos de busca não precisam repetir os critérios.** A busca deve ser
  ampla, porque o ruído é eliminado depois, na triagem. Os critérios podem ter
  mais sinônimos que a busca.

> A OASISBR não aceita a equação inteira. Ela consulta cada par tema × fonte
> separadamente, e por isso fica lenta quando os blocos têm muitos termos. Dez
> termos de tema e oito de fonte já são 80 consultas por idioma.

### Aba `criterios`

Define o que torna um trabalho **elegível**. Colunas: **criterio** (o nome),
**obrigatorio** (`sim` ou `não`), **descricao** (preencha só na primeira
linha de cada critério), **termo** e **palavra_inteira**.

A regra de elegibilidade é esta:

- o trabalho precisa satisfazer **todos** os critérios marcados `sim`;
- se houver critérios marcados `não`, precisa satisfazer **ao menos um**
  deles.

No estudo de referência, `objeto` e `fonte_de_dados` são obrigatórios. Já
`abordagem_temporal` e `abordagem_classificatoria` são alternativos: o
trabalho precisa ter um ou outro.

| criterio | obrigatorio | descricao | termo | palavra_inteira |
|---|---|---|---|---|
| objeto | sim | o objeto é uma área úmida | área úmida | |
| objeto | sim | | áreas úmidas | |
| objeto | sim | | wetland | |
| objeto | sim | | bog | sim |
| fonte_de_dados | sim | emprega imagem orbital | landsat | |
| abordagem_temporal | não | componente temporal | time series | |
| abordagem_classificatoria | não | esforço de classificação | mapping | |

> **Prefira poucos critérios obrigatórios, com muitos sinônimos.** A triagem
> por texto erra muito mais por rigor excessivo do que por tolerância. Um
> trabalho bom que fica de fora não volta mais. Um trabalho ruim que entra cai
> para o fim da lista e sai na leitura.

### Aba `exclusao` (opcional)

Termos que eliminam o trabalho **mesmo que ele seja elegível**. Use quando o
termo do objeto tiver outros sentidos. O estudo de referência exclui as
*constructed wetlands*, que são estações de tratamento de esgoto e não áreas
úmidas naturais. Use com parcimônia, porque cada termo aqui elimina sem
apelação.

### Aba `atributos` (opcional, mas é onde está a caracterização)

Cada atributo é **uma pergunta feita a todos os trabalhos de uma vez**. Na lista
final, ele vira uma coluna com 1 (o trabalho menciona) ou 0 (não menciona). O
relatório do funil diz quantos trabalhos mencionam cada atributo.

| atributo | termo | palavra_inteira |
|---|---|---|
| sensor_landsat | landsat | |
| sensor_sar | sar | sim |
| sensor_sar | synthetic aperture radar | |
| validacao | accurac | |
| validacao | validação | |
| validacao | exatidão | |

O nome do atributo vira o nome da coluna. Use letras minúsculas e `_` no lugar
de espaços.

### Aba `conceitos` (recomendada)

Define a **ordem da lista**. Escolha os **dois ou três conceitos** cuja presença
simultânea define, para você, um trabalho de primeira ordem. A lista é ordenada
primeiro por quantos conceitos cada trabalho cobre, depois pela centralidade do
objeto e, por fim, pela citação ou pela data.

Para não digitar tudo de novo, escreva `@nome` no termo. Isso reaproveita todos
os termos de um critério ou de um atributo:

| conceito | termo |
|---|---|
| classif_tipif | @abordagem_classificatoria |
| multitemporal | @abordagem_temporal |
| acuracia | @validacao |

> **Escolha conceitos que variam.** No teste com pecuária, `uso_cobertura` e
> `analise_temporal` estavam em quase 90% dos trabalhos e não ajudaram a
> ordenar nada. Quem fez a diferença foi `estrutura_fundiaria`, presente em
> 4,5%. Critério de elegibilidade não serve como critério de mérito.

### Aba `subtipos` (opcional)

Divide o objeto em tipos, só para **descrever** o conjunto no relatório. Um
trabalho pode cair em mais de um tipo. Exemplo: manguezal, turfeira, planície
de inundação.

### Aba `recorte` (opcional)

Termos que delimitam um recorte, em geral um lugar, para compará-lo com
**todo o restante** do conjunto. O relatório mostra, para cada atributo, o
percentual dentro do recorte, o de fora e a diferença em pontos percentuais. Dê
o nome do recorte em `nome_do_recorte`, na aba *geral*.

### Usuários avançados

Um termo que começa com `re:` é passado sem conversão, como expressão regular.
Por exemplo, `re:\bs-?1\b` encontra *S1* e *S-1*.

---

## 6. Passo 4 — Executar no Colab

Clique no botão **Abrir no Colab**, no topo deste guia. O caderno abre no seu
navegador. Para salvar alterações, vá em *Arquivo* → *Salvar uma cópia no
Drive*.

Cada etapa é uma célula. Clique nela e aperte ▶, à esquerda, ou `Ctrl+Enter`.
Espere uma terminar antes de rodar a próxima. Os campos que aparecem à direita
das células são os únicos lugares onde você escreve. Na primeira execução, o
Colab avisa que o caderno não foi criado pelo Google. Clique em *Executar
assim mesmo*.

| Célula | O que fazer | O que observar |
|---|---|---|
| **1. Preparar** | Deixe `salvar_no_drive` marcado e dê um nome à pasta (um por tema). Autorize o acesso ao Drive. | "Pronto. Pasta do tema: …" |
| **2. Chaves** | Seu e-mail (opcional) e a chave do CORE, se usar essa base. | — |
| **3. Planilha** | Cole o link da planilha Google **ou** deixe vazio e envie o `.xlsx`. Para conhecer o processo, marque `usar_modelo_de_exemplo`. | "Planilha carregada" |
| **4. Conferir** | Só rode. | A lista de problemas, se houver, ou a **equação de busca** de cada idioma. Leia-a. |
| **5. Estimar** | Só rode. | Quantos registros o OpenAlex tem para a sua equação (ver o Passo 5). |
| **6. Buscar** | Deixe `bases_desta_vez` vazio para todas, ou escreva uma só, como `openalex`. | O acumulado por base e idioma, e o número de requisições com erro. |
| **7. Triar** | Só rode. | Incluídos, excluídos e os **motivos de exclusão**. |
| **8. Consolidar** | Só rode. | Quantos trabalhos se repetiram entre bases. |
| **9. Ordenar** | Só rode. | O relatório do funil, com o percentual de cada atributo. |
| **10. Ver** | Escolha quantos trabalhos mostrar. | Os primeiros da lista. Fazem sentido? |
| **11. Baixar** | Só rode. | Baixa `resultados.zip`. |

**Sobre o tempo da busca.** O Colab gratuito desconecta depois de cerca de 90
minutos sem interação, ou de 12 horas de uso. Mantenha a aba aberta. Se a busca
for longa, rode primeiro só `openalex` e depois só `oasisbr`. Cada base grava o
seu próprio arquivo, e com a pasta no Drive nada se perde: ao reconectar, rode
de novo as células 1 a 4 com o **mesmo nome de pasta** e continue da etapa em
que parou.

**Um tema por pasta.** Os programas leem todos os `bruto_*.csv` da pasta. Para
um tema novo, ou para uma versão muito diferente da planilha, use outro nome de
pasta na célula 1.

---

## 7. Passo 5 — Calibrar os termos

Ninguém acerta a planilha na primeira tentativa. O ciclo é este:

```
  editar a planilha → célula 3 → célula 4 → célula 5 → (voltar, até o volume fazer sentido)
                                                   ↓
                                         célula 6 com limite_por_consulta = 200
                                                   ↓
                                   células 7 a 10: os primeiros fazem sentido?
                                                   ↓
                                  limite de volta a 2000 e execução completa
```

**Na célula 5 (volume):**

| Resultado por idioma | Diagnóstico | O que fazer |
|---|---|---|
| dezenas de milhares | equação ampla demais | restrinja o bloco do tema ou o da fonte |
| poucas dezenas | equação estreita demais | acrescente sinônimos e variações |
| acima de `limite_por_consulta` | só os mais relevantes serão baixados, até o teto | aumente o teto ou restrinja a equação |

**Na célula 7 (motivos de exclusão):**

- *"não satisfaz: objeto"* em grande número, em base internacional, é normal: a
  busca ampla traz ruído, e a triagem o retira.
- Se um critério elimina quase tudo, abra o arquivo `excluidos_<base>.csv`,
  procure trabalhos que deveriam ter entrado e veja que palavra eles usam. Ela
  está faltando na aba *criterios*.
- *"fora do período"* na OASISBR é esperado, porque essa base não filtra por
  ano na consulta.

**Na célula 10 (primeiros da lista):** se os primeiros não são o que você
procura, revise a aba *conceitos*.

**Confira por amostragem.** Abra `triagem_manual_<base>.csv` e leia uns vinte
trabalhos incluídos e uns vinte excluídos. Essa é a única forma de saber se os
critérios estão bem calibrados, e vale relatar o resultado no seu texto.

---

## 8. Passo 6 — Ler a lista

O `resultados.zip` traz:

| Arquivo | Para quê |
|---|---|
| `lista_leitura_priorizada.xlsx` | a lista, para abrir no Excel ou no Google Planilhas |
| `lista_leitura_priorizada.csv` | a mesma lista, para o visualizador |
| `visualizador.html` | interface de leitura |
| `relatorio_funil.txt` | os números do funil e da caracterização, para o texto |
| `triagem_manual_<base>.csv` | conferência humana da triagem |
| `config.py` e `configuracao.xlsx` | **guarde os dois**: são o registro exato do que foi feito |
| `log_busca.csv` | cada consulta enviada, com a data |

Descompacte o arquivo, abra o `visualizador.html` no navegador e carregue o
`lista_leitura_priorizada.csv`. As colunas do seu tema (conceitos, foco e
atributos) aparecem na tabela e nos filtros. Clique numa linha para ler o
resumo, marque *Incluir* ou *Excluir* e exporte os incluídos em RIS para o
Zotero.

**A máquina ordena e a leitura decide.** Nenhum trabalho é cortado na
ordenação. Leia de cima para baixo e use os filtros para varrer recortes, de
modo que nenhum trabalho forte se perca no desempate.

**Ao relatar os números**, lembre que a codificação descreve o que os trabalhos
**declaram** no título, no resumo e nas palavras-chave, e não o que executam.
*"X% dos trabalhos declaram o método"* é uma afirmação defensável. *"X% usam o
método"* não é.

**Ao relatar a busca**, informe a data. Uma nova execução não devolve os mesmos
registros, porque as bases indexam trabalhos novos todo dia. O que se reproduz é
o procedimento, e por isso a planilha e o `config.py` devem acompanhar o
trabalho.

---

## 9. O que a planilha não cobre

A planilha dá conta do protocolo completo, mas alguns recursos do estudo de
referência só existem em `config.py`, editado à mão:

- **atributos derivados**, como "fusão radar + óptico", que combinam outros
  atributos;
- **variáveis em níveis**, para termos ambíguos que dependem do contexto, como
  *seasonal*;
- **grupos de atributos** com uma coluna "qual", como `metodo_qual`;
- **enriquecimento com Qualis e CiteScore**;
- **estratos de leitura** para a tese (`triar_para_tese.py`).

Quem precisar desses recursos pode gerar o `config.py` pela planilha e depois
editá-lo. O arquivo gerado é legível e marcado no topo. Atenção: rodar o
conversor de novo sobrescreve as edições.

---

## 10. Executar no próprio computador

Com Python 3.10 ou mais recente instalado:

```bash
git clone https://github.com/ProfJoaoGuilherme/Mapa-sistematico-py.git
cd Mapa-sistematico-py
pip install openpyxl
```

Copie os programas para uma pasta nova, para não misturar com os artefatos do
estudo de referência. Coloque nela a sua planilha:

```bash
mkdir ../meu_tema
cp *.py visualizador.html ../meu_tema/
cp minha_planilha.xlsx ../meu_tema/
cd ../meu_tema
```

Depois rode a sequência:

```bash
python3 planilha_para_config.py minha_planilha.xlsx
python3 buscar.py
python3 triar_e_codificar.py bruto_openalex.csv
python3 triar_e_codificar.py bruto_oasisbr.csv
python3 consolidar_vias.py incluidos_openalex.csv incluidos_oasisbr.csv
python3 ranquear.py
python3 relatorio_funil.py
```

O conversor guarda o `config.py` que encontrar na pasta como
`config_referencia.py` antes de escrever o novo, a não ser que o existente já
tenha sido gerado por ele. A configuração do estudo de referência nunca se
perde.

---

## 11. Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| A célula 4 lista problemas | linha ou aba incompleta | Corrija as linhas indicadas e rode de novo as células 3 e 4. |
| "O Google não entregou a planilha" | a planilha não está compartilhada | *Compartilhar* → *Qualquer pessoa com o link* → *Leitor*. |
| "nenhum termo de tema em 'pt'" | idioma na aba *geral* sem termos na aba *busca* | Preencha os três blocos do idioma ou retire-o de `idiomas`. |
| `HTTP 429` ou erro 5xx na busca | base sobrecarregada | Espere alguns minutos e rode a célula 6 só com essa base. |
| A busca no CORE falha | falta a chave | Preencha `chave_core` na célula 2 e rode as células 4 e 6. |
| O Colab desconectou | inatividade ou limite de uso | Rode as células 1 a 4 com o mesmo nome de pasta e continue. |
| Nenhum trabalho incluído | critérios estreitos demais | Veja os motivos de exclusão na célula 7. |
| Muito ruído na lista | termos curtos casando com outras palavras | Marque `palavra_inteira` nas siglas e use a aba *exclusao*. |
| Volume bruto muito acima do esperado na OASISBR | a base reduz as palavras ao radical (`mangue` traz *manga*) | É esperado. O ruído sai na triagem. |

---

Dúvidas e sugestões: abra uma *issue* no
[repositório](https://github.com/ProfJoaoGuilherme/Mapa-sistematico-py/issues).
Para citar o protocolo, ver [`CITATION.cff`](CITATION.cff).
