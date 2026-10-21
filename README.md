# Vade: a lei seca, viva

Plataforma de estudo de legislação brasileira para concursos, OAB e faculdade: leitura
estruturada + revisão espaçada (FSRS) + questões no estilo das bancas + gamificação + professor de
IA ancorado no texto legal. O conteúdo vem do acervo aberto [ctresb/leis](https://github.com/ctresb/leis)
(MIT, ~1,06 milhão de normas em Markdown com cabeçalho YAML).

## Estado atual (Fase 0: fundação)

| Parte | Situação |
| --- | --- |
| [`docs/`](docs) | análise do acervo, arquitetura, funcionalidades, dados, pipeline, roadmap, riscos, tecnologias, design system |
| [`services/ingest`](services/ingest) | ✅ importador (parser estrutural, precedentes, qualidade, classificação, SQLite + FTS) e **painel com o botão "Verificar atualização"** (47 testes) |
| [`services/learning`](services/learning) | ✅ núcleo de aprendizagem: FSRS-5, XP/níveis/streak/ligas/moedas, dificuldade dinâmica (21 testes) |
| [`db/sqlite`](db/sqlite) | ✅ esquema de usuários/progresso/gamificação e eventos mensais em SQLite (4 testes) |
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

## Rodando

Requisitos: Python 3.11+ e git. Sem dependências externas.

```bash
cd services/ingest && PYTHONPATH=src python -m unittest discover -s tests
```

```bash
cd services/learning && PYTHONPATH=src python -m unittest discover -s tests
```

```bash
python -m unittest discover -s db/sqlite
```

### Painel com o botão "Verificar atualização"

O acervo de leis muda a cada poucos minutos. O painel verifica em ~0,5 s se há commits novos, mostra
quantos arquivos mudaram e quantos caem no seu recorte, e atualiza só esses
([detalhes](docs/05-pipeline-importacao.md#58-botão-verificar-atualização-o-acervo-muda-a-cada-poucos-minutos)).

1. Clone parcial do acervo (sem checkout: funciona também no Windows, onde o checkout completo
   falha por nomes de arquivo inválidos):

```bash
git clone --filter=blob:none --no-checkout https://github.com/ctresb/leis.git acervo
```

2. Abra o painel e acesse http://127.0.0.1:8765 (escolha o recorte, clique em **Verificar
   atualização** e depois em **Importar/Atualizar**):

```bash
cd services/ingest && PYTHONPATH=src python -m vade_ingest serve --repo ../../acervo --db catalogo.sqlite
```

Pela linha de comando, sem o painel:

```bash
cd services/ingest && PYTHONPATH=src python -m vade_ingest recorte --repo ../../acervo --db catalogo.sqlite constituicao.md federal/decretos-lei jurisprudencia/stj/sumulas
```

```bash
cd services/ingest && PYTHONPATH=src python -m vade_ingest verificar --repo ../../acervo --db catalogo.sqlite
```

```bash
cd services/ingest && PYTHONPATH=src python -m vade_ingest atualizar --repo ../../acervo --db catalogo.sqlite
```

```bash
cd services/ingest && PYTHONPATH=src python -m vade_ingest search --db catalogo.sqlite "legitima defesa"
```

> Os textos têm caráter informativo e não substituem a publicação oficial. Confira sempre a fonte
> indicada em cada norma.
