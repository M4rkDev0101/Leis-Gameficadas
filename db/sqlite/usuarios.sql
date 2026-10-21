-- Vade — dados de usuários, aprendizagem, avaliação, gamificação e planejamento (SQLite 3.45+).
-- Ver docs/04-modelo-de-dados.md.
--
-- Três arquivos de banco, cada um com um papel:
--   catalogo.sqlite        conteúdo jurídico (services/ingest/src/vade_ingest/schema.sql); só leitura para a API,
--                          o mesmo arquivo vira pacote offline para o cliente
--   usuarios.sqlite        este arquivo: contas, estado atual (cartões, perfil, ligas), questões, planos
--   eventos-AAAA-MM.sqlite fatos imutáveis do mês (eventos.sql): revisões, respostas, XP.
--                          Um arquivo por mês faz o papel do particionamento: consulta recente só abre o
--                          mês atual (ATTACH), e meses antigos são compactados/arquivados sem tocar no resto.
--
-- Conteúdo é referenciado pela CHAVE NATURAL do dispositivo ("<norma_id>#<caminho>"), nunca por id
-- numérico: o catálogo pode ser reimportado sem quebrar o progresso de ninguém.
-- SQL mantido portável (sem recursos exclusivos do SQLite) para permitir migrar para MySQL se um dia
-- for preciso escalar escrita horizontalmente.

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- ===================================================================== identidade
CREATE TABLE IF NOT EXISTS usuario (
  id              TEXT PRIMARY KEY,               -- UUIDv7
  email           TEXT UNIQUE,
  nome            TEXT,
  apelido         TEXT UNIQUE,
  criado_em       TEXT NOT NULL,
  ranking_publico INTEGER NOT NULL DEFAULT 0,
  consentimentos  TEXT NOT NULL DEFAULT '{}',     -- JSON (LGPD)
  fuso            TEXT NOT NULL DEFAULT 'America/Sao_Paulo',
  excluido_em     TEXT
);
CREATE TABLE IF NOT EXISTS amizade (
  usuario_id TEXT NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
  amigo_id   TEXT NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
  status     TEXT NOT NULL CHECK (status IN ('pendente','aceita','bloqueada')),
  criado_em  TEXT NOT NULL,
  PRIMARY KEY (usuario_id, amigo_id)
);
CREATE TABLE IF NOT EXISTS organizacao (id TEXT PRIMARY KEY, nome TEXT NOT NULL, plano TEXT NOT NULL, sso TEXT);
CREATE TABLE IF NOT EXISTS membro_org (
  org_id TEXT NOT NULL REFERENCES organizacao(id) ON DELETE CASCADE,
  usuario_id TEXT NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
  papel TEXT NOT NULL, PRIMARY KEY (org_id, usuario_id)
);

-- ===================================================================== avaliação
CREATE TABLE IF NOT EXISTS banca (id INTEGER PRIMARY KEY, sigla TEXT UNIQUE NOT NULL, nome TEXT NOT NULL, estilo TEXT NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS orgao (id INTEGER PRIMARY KEY, sigla TEXT, nome TEXT NOT NULL, uf TEXT);
CREATE TABLE IF NOT EXISTS cargo (
  id INTEGER PRIMARY KEY, nome TEXT NOT NULL, carreira TEXT,
  nivel_alvo TEXT CHECK (nivel_alvo IN ('basico','intermediario','avancado','especialista'))
);
CREATE TABLE IF NOT EXISTS prova (
  id INTEGER PRIMARY KEY, banca_id INTEGER REFERENCES banca(id), orgao_id INTEGER REFERENCES orgao(id),
  cargo_id INTEGER REFERENCES cargo(id), ano INTEGER, aplicada_em TEXT, n_questoes INTEGER, duracao_min INTEGER,
  regra_pontuacao TEXT, nota_corte TEXT, fonte_url TEXT
);
CREATE TABLE IF NOT EXISTS questao (
  id              INTEGER PRIMARY KEY,
  formato         TEXT NOT NULL CHECK (formato IN ('multipla','certo_errado','vf','lacuna','ordenacao','colunas','arrastar','discursiva')),
  origem          TEXT NOT NULL CHECK (origem IN ('historica','gerada','editorial','usuario')),
  prova_id        INTEGER REFERENCES prova(id),
  estilo_banca_id INTEGER REFERENCES banca(id),
  enunciado       TEXT NOT NULL,
  corpo           TEXT NOT NULL,                  -- JSON: alternativas, pares, ordem, rubrica
  gabarito        TEXT NOT NULL,                  -- JSON
  comentario      TEXT,                           -- JSON por alternativa, com citações
  nivel           TEXT CHECK (nivel IN ('basico','intermediario','avancado','especialista')),
  nivel_calibrado REAL, discriminacao REAL,       -- TRI (b, a)
  status          TEXT NOT NULL DEFAULT 'gerado' CHECK (status IN ('gerado','verificado','revisado','revisar','rejeitado')),
  texto_hash_base TEXT,                           -- texto do dispositivo quando gerada; mudou → 'revisar'
  modelo TEXT, prompt_versao TEXT,
  criado_em       TEXT NOT NULL,
  respostas       INTEGER NOT NULL DEFAULT 0,     -- atualizados em lote por job, nunca por gatilho
  acertos         INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS questao_pub ON questao (nivel, estilo_banca_id) WHERE status IN ('verificado','revisado');
CREATE TABLE IF NOT EXISTS questao_dispositivo (
  questao_id        INTEGER NOT NULL REFERENCES questao(id) ON DELETE CASCADE,
  dispositivo_chave TEXT NOT NULL,
  papel             TEXT NOT NULL DEFAULT 'principal',
  PRIMARY KEY (questao_id, dispositivo_chave)
);
CREATE INDEX IF NOT EXISTS qd_disp ON questao_dispositivo (dispositivo_chave);
CREATE TABLE IF NOT EXISTS simulado (
  id TEXT PRIMARY KEY, usuario_id TEXT NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
  prova_modelo_id INTEGER REFERENCES prova(id), tipo TEXT NOT NULL CHECK (tipo IN ('simulado','desafio','boss')),
  config TEXT NOT NULL, iniciado_em TEXT NOT NULL, concluido_em TEXT, resultado TEXT
);

-- Conteúdo derivado (IA/editorial) ancorado no dispositivo.
CREATE TABLE IF NOT EXISTS material (
  id INTEGER PRIMARY KEY, dispositivo_chave TEXT NOT NULL,
  tipo TEXT NOT NULL,                             -- resumo|explicacao|analogia|exemplo|mapa_mental|caso_pratico|pegadinha|comentario
  nivel TEXT, corpo TEXT NOT NULL,                -- JSON: markdown + citações
  status TEXT NOT NULL DEFAULT 'gerado', texto_hash_base TEXT NOT NULL,
  modelo TEXT, prompt_versao TEXT, criado_em TEXT NOT NULL, revisado_por TEXT
);
CREATE INDEX IF NOT EXISTS material_disp ON material (dispositivo_chave, tipo, nivel);

-- ===================================================================== aprendizagem (estado atual)
CREATE TABLE IF NOT EXISTS flashcard (
  id INTEGER PRIMARY KEY, dispositivo_chave TEXT NOT NULL, autor_id TEXT REFERENCES usuario(id) ON DELETE CASCADE,
  frente TEXT NOT NULL, verso TEXT NOT NULL, tipo TEXT NOT NULL DEFAULT 'basico',
  status TEXT NOT NULL DEFAULT 'gerado'
);
CREATE INDEX IF NOT EXISTS flashcard_disp ON flashcard (dispositivo_chave);

-- Projeção dos eventos de revisão (reconstruível por replay; ver docs/02-arquitetura.md §2.6).
CREATE TABLE IF NOT EXISTS cartao (
  usuario_id TEXT NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
  item_chave TEXT NOT NULL,                       -- "fc:<id>" | "q:<id>" | chave de dispositivo
  dispositivo_chave TEXT NOT NULL,
  estado INTEGER NOT NULL CHECK (estado BETWEEN 0 AND 3),
  dificuldade REAL NOT NULL, estabilidade REAL NOT NULL,
  vence_em TEXT, ultima_rev TEXT, reps INTEGER NOT NULL DEFAULT 0, lapsos INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (usuario_id, item_chave)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS cartao_fila ON cartao (usuario_id, vence_em);
CREATE INDEX IF NOT EXISTS cartao_disp ON cartao (usuario_id, dispositivo_chave);

CREATE TABLE IF NOT EXISTS parametros_fsrs (
  usuario_id TEXT PRIMARY KEY REFERENCES usuario(id) ON DELETE CASCADE,
  pesos TEXT NOT NULL,                            -- JSON com 19 números
  retencao_desejada REAL NOT NULL DEFAULT 0.9 CHECK (retencao_desejada BETWEEN 0.7 AND 0.97),
  otimizado_em TEXT, n_revisoes INTEGER
);
CREATE TABLE IF NOT EXISTS dominio (
  usuario_id TEXT NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
  dispositivo_chave TEXT NOT NULL, norma_id TEXT NOT NULL,
  retencao REAL NOT NULL, acerto REAL, dominado INTEGER NOT NULL DEFAULT 0, atualizado_em TEXT NOT NULL,
  PRIMARY KEY (usuario_id, dispositivo_chave)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS dominio_norma ON dominio (usuario_id, norma_id);
CREATE TABLE IF NOT EXISTS sessao (
  id TEXT PRIMARY KEY, usuario_id TEXT NOT NULL REFERENCES usuario(id) ON DELETE CASCADE, modo TEXT NOT NULL,
  iniciado_em TEXT NOT NULL, duracao_s INTEGER, itens INTEGER, acertos INTEGER
);
CREATE INDEX IF NOT EXISTS sessao_usuario ON sessao (usuario_id, iniciado_em);

-- ===================================================================== gamificação
CREATE TABLE IF NOT EXISTS perfil (
  usuario_id TEXT PRIMARY KEY REFERENCES usuario(id) ON DELETE CASCADE,
  xp_total INTEGER NOT NULL DEFAULT 0, nivel INTEGER NOT NULL DEFAULT 1, moedas INTEGER NOT NULL DEFAULT 0,
  streak_atual INTEGER NOT NULL DEFAULT 0, streak_maximo INTEGER NOT NULL DEFAULT 0, streak_ultimo_dia TEXT,
  protetores INTEGER NOT NULL DEFAULT 0,
  liga TEXT NOT NULL DEFAULT 'bronze' CHECK (liga IN ('bronze','prata','ouro','platina','diamante','mestre','grao-mestre')),
  titulo_ativo TEXT, avatar TEXT, meta_diaria_xp INTEGER NOT NULL DEFAULT 50
);
CREATE TABLE IF NOT EXISTS liga_semana (
  id INTEGER PRIMARY KEY, liga TEXT NOT NULL, semana TEXT NOT NULL, grupo INTEGER NOT NULL,
  UNIQUE (liga, semana, grupo)
);
CREATE TABLE IF NOT EXISTS liga_membro (
  liga_semana_id INTEGER NOT NULL REFERENCES liga_semana(id) ON DELETE CASCADE,
  usuario_id TEXT NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
  xp_semana INTEGER NOT NULL DEFAULT 0, posicao_final INTEGER,
  resultado TEXT CHECK (resultado IN ('subiu','ficou','desceu')),
  PRIMARY KEY (liga_semana_id, usuario_id)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS liga_ranking ON liga_membro (liga_semana_id, xp_semana DESC);

CREATE TABLE IF NOT EXISTS conquista (id TEXT PRIMARY KEY, nome TEXT NOT NULL, descricao TEXT NOT NULL, regra TEXT NOT NULL, raridade TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS usuario_conquista (
  usuario_id TEXT NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
  conquista_id TEXT NOT NULL REFERENCES conquista(id), obtida_em TEXT NOT NULL,
  PRIMARY KEY (usuario_id, conquista_id)
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS missao (
  id TEXT PRIMARY KEY, periodo TEXT NOT NULL CHECK (periodo IN ('diaria','semanal','evento')),
  regra TEXT NOT NULL, recompensa TEXT NOT NULL, ativa_de TEXT, ativa_ate TEXT
);
CREATE TABLE IF NOT EXISTS usuario_missao (
  usuario_id TEXT NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
  missao_id TEXT NOT NULL REFERENCES missao(id), ciclo TEXT NOT NULL,
  progresso INTEGER NOT NULL DEFAULT 0, concluida_em TEXT,
  PRIMARY KEY (usuario_id, missao_id, ciclo)
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS item_loja (id TEXT PRIMARY KEY, tipo TEXT NOT NULL, nome TEXT NOT NULL, preco INTEGER NOT NULL CHECK (preco >= 0), dados TEXT NOT NULL, temporada TEXT);
CREATE TABLE IF NOT EXISTS inventario (
  usuario_id TEXT NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
  item_id TEXT NOT NULL REFERENCES item_loja(id), adquirido_em TEXT NOT NULL,
  PRIMARY KEY (usuario_id, item_id)
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS temporada (id TEXT PRIMARY KEY, nome TEXT NOT NULL, inicio TEXT NOT NULL, fim TEXT NOT NULL, tema TEXT);

-- ===================================================================== planejamento
CREATE TABLE IF NOT EXISTS concurso (
  id INTEGER PRIMARY KEY, slug TEXT UNIQUE NOT NULL, nome TEXT NOT NULL,
  orgao_id INTEGER REFERENCES orgao(id), banca_id INTEGER REFERENCES banca(id), cargo_id INTEGER REFERENCES cargo(id),
  data_prova TEXT, situacao TEXT NOT NULL DEFAULT 'previsto', edital_url TEXT
);
CREATE TABLE IF NOT EXISTS edital_topico (
  id INTEGER PRIMARY KEY, concurso_id INTEGER NOT NULL REFERENCES concurso(id) ON DELETE CASCADE,
  disciplina TEXT NOT NULL, texto TEXT NOT NULL, peso REAL, n_questoes INTEGER, revisado INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS edital_topico_dispositivo (
  edital_topico_id INTEGER NOT NULL REFERENCES edital_topico(id) ON DELETE CASCADE,
  dispositivo_chave TEXT NOT NULL, PRIMARY KEY (edital_topico_id, dispositivo_chave)
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS plano (
  id TEXT PRIMARY KEY, usuario_id TEXT NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
  concurso_id INTEGER REFERENCES concurso(id), horas_semana REAL NOT NULL, data_prova TEXT,
  nivel_inicial TEXT, criado_em TEXT NOT NULL, config TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS plano_item (
  plano_id TEXT NOT NULL REFERENCES plano(id) ON DELETE CASCADE, dia TEXT NOT NULL, ordem INTEGER NOT NULL,
  tipo TEXT NOT NULL, alvo TEXT NOT NULL, minutos INTEGER NOT NULL, concluido INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (plano_id, dia, ordem)
) WITHOUT ROWID;

-- Radar: incidência por dispositivo × banca × ano. No SQLite é tabela recalculada por job
-- (não há materialized view); a consulta de origem está em docs/04-modelo-de-dados.md.
CREATE TABLE IF NOT EXISTS radar_incidencia (
  dispositivo_chave TEXT NOT NULL, banca_id INTEGER, ano INTEGER, questoes INTEGER NOT NULL,
  PRIMARY KEY (dispositivo_chave, banca_id, ano)
);

-- ===================================================================== IA (auditoria e custo)
CREATE TABLE IF NOT EXISTS conversa (id TEXT PRIMARY KEY, usuario_id TEXT NOT NULL REFERENCES usuario(id) ON DELETE CASCADE, criado_em TEXT NOT NULL, contexto TEXT);
CREATE TABLE IF NOT EXISTS mensagem (
  id TEXT PRIMARY KEY, conversa_id TEXT NOT NULL REFERENCES conversa(id) ON DELETE CASCADE, papel TEXT NOT NULL,
  conteudo TEXT NOT NULL, citacoes TEXT, modelo TEXT, tokens_in INTEGER, tokens_out INTEGER, criado_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS uso_ia_diario (
  usuario_id TEXT NOT NULL REFERENCES usuario(id) ON DELETE CASCADE, dia TEXT NOT NULL,
  tokens INTEGER NOT NULL DEFAULT 0, custo_centavos INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (usuario_id, dia)
) WITHOUT ROWID;
