-- Vade — eventos imutáveis de um mês (um arquivo por mês: eventos-AAAA-MM.sqlite).
--
-- Fatos que só são acrescentados, nunca alterados: revisões FSRS, respostas a questões e
-- lançamentos de XP/moedas. As tabelas de estado em usuarios.sqlite (cartao, dominio, perfil) são
-- projeções desses eventos e podem ser reconstruídas por replay.
--
-- id = UUIDv7 gerado no cliente: a sincronização offline reenviar o mesmo evento não duplica nada
-- (INSERT OR IGNORE). hlc = relógio lógico híbrido, para ordenar o replay entre aparelhos.

PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS revisao (
  id                TEXT PRIMARY KEY,
  usuario_id        TEXT NOT NULL,
  item_chave        TEXT NOT NULL,
  nota              INTEGER NOT NULL CHECK (nota BETWEEN 1 AND 4),
  revisado_em       TEXT NOT NULL,
  dias_decorridos   REAL NOT NULL,
  retencao_prevista REAL,
  estab_antes       REAL NOT NULL,
  estab_depois      REAL NOT NULL,
  dific_depois      REAL NOT NULL,
  duracao_ms        INTEGER,
  versao_algoritmo  TEXT NOT NULL DEFAULT 'fsrs-5',
  hlc               TEXT NOT NULL
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS revisao_usuario ON revisao (usuario_id, revisado_em);

CREATE TABLE IF NOT EXISTS resposta (
  id          TEXT PRIMARY KEY,
  usuario_id  TEXT NOT NULL,
  questao_id  INTEGER NOT NULL,
  sessao_id   TEXT,
  resposta    TEXT NOT NULL,                 -- JSON
  correta     INTEGER,
  nota        REAL,                          -- discursivas
  duracao_ms  INTEGER,
  criado_em   TEXT NOT NULL,
  hlc         TEXT NOT NULL
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS resposta_usuario ON resposta (usuario_id, criado_em);
CREATE INDEX IF NOT EXISTS resposta_questao ON resposta (questao_id);

-- Razão (ledger) de XP e moedas: a soma é o saldo. O servidor recalcula o XP antes de gravar.
CREATE TABLE IF NOT EXISTS lancamento (
  id          TEXT PRIMARY KEY,
  usuario_id  TEXT NOT NULL,
  moeda       TEXT NOT NULL CHECK (moeda IN ('xp','moedas')),
  quantidade  INTEGER NOT NULL,
  motivo      TEXT NOT NULL,                 -- resposta|revisao|missao|conquista|compra|streak…
  ref         TEXT,
  criado_em   TEXT NOT NULL
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS lancamento_usuario ON lancamento (usuario_id, moeda, criado_em);
