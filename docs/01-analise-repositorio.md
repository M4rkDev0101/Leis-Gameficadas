# 1. Análise do repositório `ctresb/leis`

Medições feitas em 21/10/2026 sobre o commit `bde0c6a` (clone parcial, `--filter=blob:none`),
mais amostras de 3.737 normas importadas e verificadas manualmente.

## 1.1 Tamanho e ritmo

| Métrica | Valor medido |
| --- | ---: |
| Arquivos na árvore | 1.116.044 |
| Arquivos `.md` de normas | **~1.058.000** |
| Tamanho (API do GitHub) | ~2,5 GB (+27 GB de fontes fora do versionamento) |
| Licença | MIT |
| Ritmo de commits | vários por hora, com milhares de arquivos cada (ex.: "Acrescenta 3758 decretos…") |

O README fala em 323.849 normas, mas esse número é só a **base inicial**. O acervo hoje é ~3x maior.

| Área (`.md`) | Arquivos | Observação |
| --- | ---: | --- |
| `estaduais/` | 709.510 | 27 UFs (PR e RJ ainda zerados em `COBERTURA.md`) |
| `federal/` | 166.984 | 78.988 decretos, 21.359 decretos legislativos, 16.784 leis ordinárias, 12.376 decretos-lei, 7.499 MPs, 172 ECs, 239 LCs |
| `reguladores/` | 154.732 | RFB (55 mil), ANVISA, MEC, ANAC, CONTRAN/SENATRAN, SUSEP… |
| `municipais/` | 15.523 | cobertura inicial, via SAPL das câmaras |
| `jurisprudencia/` | 11.700 | STF (controle concentrado 5.198, RG 1.494, súmulas 736, SV 62), STJ (repetitivos 1.474, súmulas 649), TST (OJs 694, súmulas 463), TNU, TRF4, TCU, STM |
| `tratados/` | 161 | |
| `constituicao.md` | 1 | sem cabeçalho YAML; inclui ADCT |

Há **milhares de arquivos internos** (prefixo `_`: `_lotes`, `_candidatos_*`, `_receipts_*.jsonl.gz`,
`_falhas.jsonl`). O importador os ignora (`sources.is_norm_path`).

## 1.2 Formato

Cabeçalho YAML plano + corpo Markdown. Campos sempre presentes: `titulo`, `tipo`, `numero`,
`data`, `versao_texto`, `fonte`, `baixado_em`. Campos por origem:

| Origem | Campos extras |
| --- | --- |
| Federal | `urn` (LexML), `publicacao`, `data_publicacao`, `revogada`, `arquivo` |
| Estadual | `uf`, `situacao`, `ano` (PA, PE: só o ano) |
| Municipal | `municipio`, `codigo_ibge`, `tipo_na_fonte`, `sha256_*`; **`data` entre aspas** |
| Reguladores | `orgao`, `edicao`, `sha256_html_fonte`; `revogada: null` |
| Jurisprudência | `tribunal`, `id_bnp`, `atualizacao_fonte`; `data` pode vir vazia |

`tipo` segue um vocabulário canônico (`CANONICO` em `scripts/comum.py`), o que permite usar
`(tipo, numero, ano)` como identidade das normas federais.

## 1.3 Achados que mudam a arquitetura

1. **A hierarquia não está no número de `#`.** TÍTULO é `##` na CF, `###` no Código Civil e
   CAPÍTULO é `####` na LGPD. A posição vem da palavra-chave (PARTE > LIVRO > TÍTULO > SUBTÍTULO >
   CAPÍTULO > SEÇÃO > SUBSEÇÃO).
2. **A numeração repete dentro da CF.** O ADCT recomeça do art. 1º, então é um escopo próprio (`adct/art-1`).
3. **Leis alteradoras citam artigos entre aspas** (`“Art. 1º-A …”`). Tratá-los como artigos da norma
   criaria artigos fantasmas.
4. **Variações reais de dispositivos** (todas cobertas por testes):
   `**Art. 157.**`, `**Art. 1º**`, `**Art**. 1º`, `ARTIGO 1º -`, `Art. 1.000.`, `Art. 359-M-A`,
   `§ 1º-A.`, `I-A o Conselho…` (sem travessão), `V os conflitos…` (CF art. 114, sem travessão),
   `e) *(VETADA…)*`.
5. **"Hífen com espaço" é separador, não sufixo.** `I - Incapacidade` não é o inciso "I-I" e
   `Art. 242 - A lei` não é o "Art. 242-A". Um parser ingênuo erra isso (o nosso errou na 1ª versão).
6. **Rubricas (epígrafes)** como "Roubo" e "Legítima defesa" aparecem numa linha antes do artigo.
   O CP tem 374. São ótimas para busca e para títulos de cartões.
7. **Notas editoriais estruturáveis:** `*(Redação dada pela Lei nº 13.654, de 23/4/2018)*`,
   `(Incluído pela EC nº 45, de 2004)`, `(Vide…)`, `(Revogado…)`, `(VETADA…)`. Delas sai uma linha do
   tempo por dispositivo ("Mostrar alterações históricas") e a pegadinha "isso ainda vale?".
8. **A qualidade é muito desigual.** Compilados federais estão impecáveis; parte dos estaduais veio por
   OCR ilegível (`"Ar t. lQ - Fic a rec onh eci da"`). `COBERTURA.md` registra milhares "via OCR"
   (PB 5.051, RO 4.034, PI 3.281, PA 3.191). **Não se gera questão de texto ruim.**
9. **A maioria das leis estaduais é ato de efeito concreto.** Na amostra (MG 2019, SP 2015, PB 1995),
   **~68%** declaram utilidade pública, dão nome a rua, concedem título etc. Ficam pesquisáveis, mas
   fora das trilhas de estudo.
10. **Súmulas do STJ trazem ramo, tema e referências legislativas estruturadas:**
    `DIREITO PENAL - LEI MARIA DA PENHA` e `LEG:FED LEI:011340 ANO:2006 / ART:00005 ART:00007`.
    Disso sai o **grafo súmula → artigo**, sem IA. Na amostra, **99%** das referências a dispositivos
    de normas presentes acharam o dispositivo exato.
11. **O checkout quebra no Windows:** há nomes com `"` (`lei-4941-2003-id".md`). O importador lê
    direto do object store do git (`git cat-file --batch`), sem checkout, e busca blobs em lote pelo
    OID (2.134 arquivos em 3 s).
12. **O OID do blob identifica o conteúdo**, então a importação incremental é um `git diff --raw`
    entre o último commit importado e o atual.

## 1.4 Resultado do parser sobre os grandes códigos

| Norma | Artigos | Parágrafos | Incisos | Alíneas | Penas | Rubricas | Avisos |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Constituição (com ADCT) | 424 | 1.074 | 1.434 | 359 | – | 1 | 0 |
| Código Penal | 433 | 471 | 376 | 80 | 334 | 374 | 0 |
| Código Civil | 2.077 | 931 | 857 | 14 | – | 9 | 0 |
| LGPD | 80 | 126 | 224 | 25 | – | – | 0 |

Desempenho: ~150 normas/s numa thread, incluindo o download dos blobs. O acervo completo leva
~2 h numa máquina e é paralelizável por prefixo.

## 1.5 Lacunas do acervo (e o que fazemos)

| Lacuna | Impacto | Estratégia |
| --- | --- | --- |
| PR e RJ sem normas estaduais | concursos estaduais desses estados | marcar no catálogo; ingestão própria futura (ALEP/ALERJ) |
| Sem questões de concurso | núcleo do produto | banco próprio (gerado + curado) e ingestão de provas públicas (ver riscos) |
| Sem editais | plano de estudos | módulo de editais com extração por IA e revisão humana |
| Sem doutrina/comentários | "Comentários" | conteúdo IA ancorado + curadoria + comunidade moderada |
| OCR ruim | geração de conteúdo | faixa de qualidade; reprocessar OCR a partir de `arquivo:` (PDF original) |
