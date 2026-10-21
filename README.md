# Vade: a lei seca, viva

Plataforma de estudo de legislação brasileira para concursos, OAB e faculdade: leitura
estruturada + revisão espaçada (FSRS) + questões no estilo das bancas + gamificação + professor de
IA ancorado no texto legal. O conteúdo vem do acervo aberto [ctresb/leis](https://github.com/ctresb/leis)
(MIT, ~1,06 milhão de normas em Markdown com cabeçalho YAML).

## Jogar

### Instalador para Windows (recomendado)

Baixe o **[VadeTribunal.exe](https://github.com/M4rkDev0101/Leis-Gameficadas/releases/download/instalador/VadeTribunal.exe)**
e dê dois cliques. Ele faz tudo sozinho:

1. instala em `%LOCALAPPDATA%\VadeTribunal` e cria o atalho **Vade Tribunal** na Área de Trabalho;
2. instala o Git pelo winget, se faltar (pergunta antes);
3. baixa o jogo deste repositório e, nas próximas aberturas, só atualiza;
4. baixa o acervo [ctresb/leis](https://github.com/ctresb/leis) em clone parcial (sem os 2,5 GB);
5. na primeira vez, importa as leis que o jogo usa (Constituição, códigos, leis especiais e súmulas);
6. abre o jogo no navegador e verifica leis novas a cada 30 minutos.

O `.exe` traz o Python embutido e é compilado pelo GitHub Actions a cada mudança em `instalador/`.
Como não é assinado digitalmente, o Windows pode mostrar "editor desconhecido": clique em
*Mais informações → Executar assim mesmo*.

### Pelo código-fonte (Python 3.11+ e git)

```bash
git clone --filter=blob:none --no-checkout https://github.com/ctresb/leis.git acervo
```

```bash
python jogar.py --repo acervo --db catalogo.sqlite
```

Abre http://127.0.0.1:8765. As áreas do jogo:

- **⚖️ Tribunal** (`/tribunal`): simulação de audiência no estilo dos jogos de tribunal, com
  personagens e textos originais. Você é a **defesa**, a **acusação** ou o **juiz**: ouve depoimentos,
  *pressiona* afirmações, abre os **autos do processo** e *apresenta* a prova ou o artigo que
  desmente a testemunha. Tem gritos de **PROTESTO!**, martelo, credibilidade (5 balanças) e veredicto.
  Como juiz, você decide os protestos (deferido/indeferido) pelo CPP art. 212. Bonequinhos animados,
  sons sintetizados e criador de personagem. Todos os julgamentos são validados contra a lei vigente.
  - **Modo Carreira** ([roteiro](docs/10-modo-carreira.md)): de estagiário(a) a juiz(a) em 5 atos, com uma
    trama que atravessa todos os casos. Cada caso tem **investigação** (examine os pontos da cena,
    converse com as pessoas, colete provas obrigatórias) e audiência. O progresso é salvo a cada cena;
    cada caso só libera depois de vencer o anterior. **Ato I — O Estágio** pronto: 6 casos (furto × roubo,
    insignificância, legítima defesa, audiência de custódia, fraude eletrônica e um júri).
  - **Casos avulsos**: julgamentos de promotor(a) e juiz(a) sempre liberados.

- **Simulados**: estrutura de 7 concursos reais (carreiras policiais e INSS/CEBRASPE, tribunais, TRT,
  Fiscal/Receita, OAB 1ª fase/FGV, Magistratura e MP) em quatro dificuldades (🟢 Treino, 🟡 Padrão, 🔴 Difícil,
  ⚫ Elite). Cronômetro, regra de pontuação da banca (no CEBRASPE, cada erro anula um acerto),
  correção comentada com o texto vigente da lei, desempenho por área e XP.
- **Casos**: você é **advogado(a), promotor(a) ou juiz(a)** na Vasconcelos & Duarte Advocacia. Cada
  decisão mexe no seu *Argumento* e na sua *Credibilidade*, cita o artigo que a justifica e leva a
  desfechos diferentes (desclassificação, condenação, sentença mantida, acordo…).
- **Acervo** (`/acervo`): o painel com o botão **Verificar atualização**. Escolha um recorte (o
  atalho "Essencial federal" cobre o que os simulados e casos citam) e importe. Sem catálogo, o jogo
  funciona do mesmo jeito, só mostrando o trecho da lei guardado na questão.

Nível, título (de Estagiário(a) a Ministro(a)), XP e sequência de dias ficam em `jogador.sqlite`.

> As questões e os casos são **originais**: reproduzem o formato e a regra de cada banca, mas não
> copiam provas, que são protegidas por direito autoral. Cada questão cita o dispositivo que a
> fundamenta, e `python jogar.py validar --db catalogo.sqlite` confere se o trecho citado ainda está
> no texto vigente (pega questão desatualizada quando a lei muda).

## Banco de questões

| Origem | Quantidade | Como o gabarito é garantido |
| --- | ---: | --- |
| Escritas à mão (`content/questoes.json`) | 70 | comentário, pegadinha e jurisprudência; fundamento conferido contra o texto vigente |
| Letra da lei, geradas (`content/geradas.json`) | 771 | por construção: item **literal** (Certo) ou com **uma troca controlada** (prazo, fração, reclusão↔detenção, poderá↔deverá, órgão, negação de súmula) mostrada na explicação; múltipla escolha de completar o número, assinalar a correta/incorreta, pena cominada, artigo do crime e tipo pela conduta |

Cobre CF, CP, CPP, CC, CPC, CLT, CTN, CDC, ECA, Leis 8.112, 9.784, 8.429, 12.527, 12.016, LGPD, Maria da
Penha, Drogas, LEP, Juizados, Hediondos, Tortura, Desarmamento, Organizações Criminosas, Abuso de
Autoridade, CTB, Crimes Ambientais, Código Eleitoral, Lei 8.213, Estatuto da Pessoa Idosa, LRF e
súmulas do STJ e vinculantes do STF. Para regenerar depois que a lei mudar:

```bash
python services/arena/tools/gerar_questoes.py --db catalogo.sqlite
```

```bash
python jogar.py validar --db catalogo.sqlite
```

## Estado atual

| Parte | Situação |
| --- | --- |
| [`docs/`](docs) | análise do acervo, arquitetura, funcionalidades, dados, pipeline, roadmap, riscos, tecnologias, design system |
| [`instalador`](instalador) | ✅ `VadeTribunal.exe`: instala, baixa jogo e leis, abre o jogo e mantém tudo atualizado |
| [`services/arena`](services/arena) | ✅ jogo: modo Tribunal com Modo Carreira (Ato I: 6 casos com investigação) e 2 casos avulsos, 7 modelos de concurso × 4 dificuldades, **841 questões** em 20 áreas (70 comentadas à mão + 771 de letra da lei geradas do texto vigente), 4 casos (advogado, promotor, juiz), perfil do jogador e avatar (36 testes) |
| [`services/ingest`](services/ingest) | ✅ importador (parser estrutural, precedentes, qualidade, classificação, SQLite + FTS) e painel com o botão "Verificar atualização" (49 testes) |
| [`services/learning`](services/learning) | ✅ núcleo de aprendizagem: FSRS-5, XP/níveis/streak/ligas/moedas, dificuldade dinâmica (21 testes) |
| [`db/sqlite`](db/sqlite) | ✅ esquema multiusuário de progresso/gamificação e eventos mensais (4 testes) |
| `services/api`, `apps/web`, `packages/*` | próximos (ver [roadmap](docs/06-roadmap.md)) |

## Documentação

1. [Análise do repositório](docs/01-analise-repositorio.md): números medidos e 12 achados que mudam a arquitetura
2. [Arquitetura](docs/02-arquitetura.md): monólito modular, IA ancorada, offline-first com event sourcing
3. [Funcionalidades](docs/03-funcionalidades.md): por módulo e por fase
4. [Modelo de dados](docs/04-modelo-de-dados.md): chave natural de dispositivo, escala para bilhões de eventos
5. [Pipeline de importação](docs/05-pipeline-importacao.md): do `git diff` ao catálogo
6. [Roadmap](docs/06-roadmap.md): MVP → V1 → V2 → Enterprise
7. [Riscos](docs/07-riscos.md): 16 riscos com mitigação
8. [Tecnologias](docs/08-tecnologias.md): escolhas justificadas
9. [Design system](docs/09-design-system.md): identidade, tokens, componentes, movimento

## Testes

Requisitos: Python 3.11+ e git. Sem dependências externas.

```bash
cd services/arena && PYTHONPATH="src;../ingest/src;../learning/src" python -m unittest discover -s tests
```

```bash
cd services/ingest && PYTHONPATH=src python -m unittest discover -s tests
```

```bash
cd services/learning && PYTHONPATH=src python -m unittest discover -s tests
```

```bash
python -m unittest discover -s db/sqlite
```

No Linux e no macOS, o separador do `PYTHONPATH` é `:` em vez de `;`.

## Painel do acervo pela linha de comando

O acervo de leis muda a cada poucos minutos. A verificação leva ~0,5 s, mostra quantos arquivos
mudaram e quantos caem no seu recorte, e a atualização baixa só esses
([detalhes](docs/05-pipeline-importacao.md#58-botão-verificar-atualização-o-acervo-muda-a-cada-poucos-minutos)).

```bash
cd services/ingest && PYTHONPATH=src python -m vade_ingest recorte --repo ../../acervo --db ../../catalogo.sqlite constituicao.md federal/decretos-lei jurisprudencia/stj/sumulas
```

```bash
cd services/ingest && PYTHONPATH=src python -m vade_ingest verificar --repo ../../acervo --db ../../catalogo.sqlite
```

```bash
cd services/ingest && PYTHONPATH=src python -m vade_ingest atualizar --repo ../../acervo --db ../../catalogo.sqlite
```

```bash
cd services/ingest && PYTHONPATH=src python -m vade_ingest search --db ../../catalogo.sqlite "legitima defesa"
```

> Os textos têm caráter informativo e não substituem a publicação oficial. Confira sempre a fonte
> indicada em cada norma.
