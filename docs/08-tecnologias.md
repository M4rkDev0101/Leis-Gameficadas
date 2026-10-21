# 8. Tecnologias (e por quê)

Critério: o melhor para *este* domínio (texto legal + memória + jogo + IA) e para uma equipe
pequena. Tecnologia comum onde não há vantagem em inovar.

## Frontend

| Escolha | Por quê | Alternativa descartada |
| --- | --- | --- |
| **TypeScript + React 19 + Next.js 15 (App Router)** | SSR/SEO para páginas públicas de leis (cada artigo indexável no Google é aquisição gratuita), RSC para o catálogo, maior ecossistema | SvelteKit (ecossistema menor para componentes ricos), SPA pura (sem SEO) |
| **PWA + SQLite WASM (OPFS)** | offline real com o *mesmo* arquivo de pacote gerado pelo importador; consultas SQL/FTS locais | IndexedDB/Dexie (sem FTS nem SQL; duplicaria o modelo) |
| **Expo / React Native** (V1) | reaproveita núcleo TS, tipos e lógica; SQLite nativo | Flutter (outra linguagem, sem reaproveitar o núcleo) |
| **Tailwind CSS v4 + Radix Primitives (via shadcn/ui)** | tokens do design system viram utilitários; Radix dá acessibilidade pronta (diálogos, menus, tabs) | MUI (estética difícil de fugir do "Material") |
| **Motion (Framer Motion)** | microinterações estilo Duolingo (acerto, combo, subir de nível) com springs; respeita `prefers-reduced-motion` | CSS puro (difícil orquestrar sequências) |
| **TanStack Query** | cache, retry e modo offline das chamadas à API | Redux (estado de servidor não é estado global) |
| **Zustand** | estado local pequeno (sessão de estudo, player do desafio) | Redux |
| **Cliente gerado do OpenAPI** (orval/openapi-ts) | tipos ponta a ponta sem acoplar linguagens | tRPC (exige backend TS) |
| **Lexical** (V2) | editor de notas pessoais com backlinks (estilo Obsidian) | Slate (menos mantido) |

## Backend

| Escolha | Por quê | Alternativa descartada |
| --- | --- | --- |
| **Python 3.12 + FastAPI**, monólito modular | o domínio pesado é texto, ML e IA (parser, FSRS-optimizer, TRI, embeddings), nativos em Python; o importador já é Python; FastAPI dá OpenAPI, async e Pydantic | NestJS (dividiria a lógica de IA/ML em duas linguagens); microserviços no dia 1 (custo operacional sem ganho) |
| **SQLAlchemy 2 + Alembic** | migrações versionadas, SQL explícito quando preciso | ORM "mágico" |
| **Fila em tabela SQLite** (MVP) → **Temporal** (V2) | jobs simples numa tabela com status (sem infraestrutura nova); Temporal para pipelines longos e retomáveis (geração IA em lote) | Celery/Redis (infraestrutura extra no MVP) |
| **uv** | gestão de dependências e ambientes rápida e reprodutível | pip + venv manual |

## Dados

| Escolha | Por quê |
| --- | --- |
| **SQLite 3.45+ (WAL)** | um formato só para servidor e cliente offline (o pacote baixado pelo app é o mesmo arquivo); zero servidor de banco para operar; FTS5 sem acento; leitura concorrente com uma escrita por vez, suficiente porque a escrita chega em lotes de eventos; backup e réplica contínuos com **Litestream** |
| **sqlite-vec** | busca semântica no mesmo arquivo, sem outra infraestrutura |
| **MySQL 8** (plano B) | se a escrita precisar de vários servidores; o SQL de `db/sqlite` foi mantido portável para essa migração |
| **Redis** (opcional, V1+) | só se o ranking nacional ao vivo ou o rate limit distribuído pedirem |
| **Busca dedicada** (só se necessário) | Meilisearch/OpenSearch apenas se o FTS5 deixar de atender (latência ou recursos como sinônimos) |
| **DuckDB** | heatmaps, Radar, coortes e funis lendo direto os arquivos SQLite/Parquet, sem servidor |
| **Cloudflare R2 / S3 + CDN** | pacotes SQLite, PDFs originais, mídia; R2 não cobra saída de dados |
| **SQLite** | catálogo de desenvolvimento e pacotes offline (o mesmo esquema) |

## IA

| Escolha | Por quê |
| --- | --- |
| **Claude** (`claude-sonnet-5-5` padrão; `claude-haiku-5-5` em tarefas baratas; `claude-opus-5-5` em questões especialista e correção de discursivas) | ótimo em português jurídico e em seguir instruções de citação; Batches API para geração em massa; prompt caching para textos longos de lei |
| **BGE-M3** self-hosted (ou Voyage AI) | embeddings multilíngues de boa qualidade em PT-BR; self-hosted elimina custo por token |
| **Verificação por um 2º modelo + regras** | a questão só é publicada se outro modelo resolver sem gabarito e acertar, e se a justificativa citar o dispositivo |
| **py-fsrs / fsrs-optimizer** (V1) | otimização dos 19 pesos por usuário a partir do log de revisões |

## Infraestrutura e qualidade

| Escolha | Por quê |
| --- | --- |
| **Docker**; PaaS (Fly.io/Render) no MVP → **Kubernetes (EKS sa-east-1)** na V2 | começar simples; região Brasil (latência e LGPD) quando escalar |
| **GitHub Actions** | CI com testes Python, TS, vetores de paridade, migrações |
| **OpenTelemetry + Grafana (Tempo/Loki/Prometheus) + Sentry** | rastreio ponta a ponta incluindo chamadas de IA (latência, tokens, custo) |
| **Auth:** Better Auth ou Supabase Auth no MVP; **WorkOS/Keycloak** para SSO enterprise | evitar escrever autenticação; SAML/SCIM quando vier B2B |
| **Playwright** (E2E), **Vitest** (TS), **unittest/pytest** (Python), **Hypothesis** (propriedades do sync e do FSRS) | |
| **Monorepo:** pnpm + Turborepo (TS) e uv workspaces (Python) | um repositório, builds incrementais |

## Estrutura do repositório (alvo)

```
apps/
  web/                 Next.js PWA
  mobile/              Expo (V1)
services/
  api/                 FastAPI (monólito modular: catalog, learning, assessment, game, planning, ai, identity)
  ingest/              ✅ importador do acervo
  learning/            ✅ núcleo FSRS, gamificação, dificuldade (referência Python)
  workers/             geração IA, empacotador, jobs
packages/
  core-ts/             FSRS + regras de XP em TS (paridade com services/learning)
  ui/                  design system (tokens + componentes)
  api-client/          gerado do OpenAPI
db/sqlite/             ✅ esquemas (usuários, eventos mensais) e testes
docs/                  ✅ este material
```
