# 6. Roadmap: do MVP ao Enterprise

Equipe de referência: 2 full-stack, 1 front/design, 1 dados/IA, 1 editor jurídico (meio período no
MVP). As durações são estimativas para essa equipe.

## Fase 0: Fundação (semanas 1–4) ✅ em andamento

- [x] Análise do acervo e decisões de arquitetura (este diretório `docs/`)
- [x] Importador com parser estrutural, precedentes, qualidade, classificação, sync incremental (37 testes)
- [x] Núcleo de aprendizagem: FSRS-5, XP, níveis, streak, ligas, moedas, dificuldade (21 testes)
- [x] Esquemas SQLite (catálogo, usuários, eventos mensais)
- [x] Botão "Verificar atualização" + painel local + atualização incremental testada contra o GitHub real
- [ ] Monorepo, CI (lint, testes, vetores de paridade), ambientes dev/staging
- [ ] API de catálogo e de estudo (FastAPI) sobre os arquivos SQLite
- [ ] Design system (tokens + componentes base) e protótipo navegável

## Fase 1: MVP (meses 2–4): "estudar a lei seca com memória"

Escopo de conteúdo: CF, CP, CPP, CC, CPC, CLT, CTN, CDC, ECA, Lei 8.112, Licitações, Improbidade,
LGPD, Maria da Penha, Drogas, Penal especial (≈ 25 normas, ~8 mil artigos) + súmulas vinculantes
e súmulas do STF/STJ.

- Web PWA responsiva, dark mode, offline com pacotes SQLite
- Leitura estruturada, busca (sigla, citação "art 157 cp", texto), página do dispositivo
- Flashcards gerados + FSRS; lições de 5 min; fila de revisão
- Questões geradas (CEBRASPE, FGV, FCC), com verificação automática + revisão humana por amostragem
- Explicação IA em 3 níveis, resumo, "comparar conceitos", chat ancorado com citações
- XP, níveis, streak com protetores, meta diária, home completa, mapa de progresso, estatísticas básicas
- Plano de estudo por regras para ~20 concursos curados
- Conta, sincronização entre aparelhos, LGPD (exportar/excluir)
- **Meta de sucesso:** retenção D30 ≥ 25%; ≥ 4 sessões/semana nos ativos; erro factual reportado < 1/1.000 itens

## Fase 2: V1 (meses 5–8): "jogo e concurso"

- Ligas semanais, rankings (amigos, nacional, por concurso), missões, conquistas, moedas e loja
- Modo Desafio (tempo, vidas, combo, multiplicador)
- Banco de questões históricas + **Radar de Concurso** (incidência, tendência, prioridade)
- Simulado real com regras de banca e análise pós-prova
- Correção de discursivas; pegadinhas; jurisprudência por artigo; linha do tempo das alterações; mapa mental
- Busca semântica; FSRS otimizado por usuário; previsão de desempenho
- Edital → plano automático (extração por IA + revisão)
- Alertas "a lei mudou"
- App mobile (Expo) com o mesmo núcleo
- Monetização: freemium (limite diário de IA e de simulados) + Premium

## Fase 3: V2 (meses 9–14): "todo o ordenamento"

- Todo o acervo pesquisável (1 M+ normas), pacotes por concurso estadual/municipal
- Boss Fight, temporadas e eventos, duelos 1x1
- Casos práticos, comentários da comunidade com moderação, notas pessoais com backlinks
- Tutor proativo (monta a sessão do dia sozinho)
- Calibração TRI das questões; DuckDB para analytics; busca semântica com sqlite-vec
- Leis estaduais do PR e RJ (ingestão própria) e re-OCR dos textos ruins

## Fase 4: Enterprise (mês 15+)

- Organizações: cursinhos, órgãos públicos (capacitação), faculdades
- Painel do professor, turmas, trilhas e simulados customizados, relatórios
- SSO (SAML/OIDC), SCIM, auditoria, SLA, região de dados no Brasil
- API pública e white-label; conteúdo próprio do cliente com o mesmo pipeline
- Extração de serviços do monólito conforme a carga: aprendizagem/eventos e IA primeiro

## Marcos de arquitetura por fase

| Fase | Banco | Busca | IA | Deploy |
| --- | --- | --- | --- | --- |
| MVP | SQLite (WAL) num servidor + Litestream (réplica contínua no S3/R2) | FTS5 | Claude (batch + online), cache | contêiner em PaaS com disco persistente, CDN R2 |
| V1 | eventos em arquivos mensais; Redis opcional para ranking nacional | + sqlite-vec | + embeddings BGE-M3 | + workers dedicados |
| V2 | usuários fatiados em N arquivos (por hash do id) ou migração para MySQL se a escrita passar de um servidor | idem | + otimização FSRS por usuário, TRI | vários nós |
| ENT | multi-tenant por org, isolamento opcional | idem | modelos por cliente | multi-AZ, DR |
