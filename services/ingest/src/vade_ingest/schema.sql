-- Esquema do catálogo jurídico (SQLite). É o mesmo modelo lógico do PostgreSQL de produção
-- (docs/04-modelo-de-dados.md), reduzido ao conteúdo. É usado em desenvolvimento e
-- como pacote offline distribuído aos clientes (subconjuntos por concurso).
--
-- Regra de ouro: dados do usuário referenciam dispositivos pela CHAVE NATURAL
-- (dispositivo.chave = "<norma_id>#<caminho>", ex.: "federal/decretos-lei/1940/del-2848-1940-12-07#art-157/par-2/inc-ii"),
-- nunca pelo id numérico, que muda a cada reimportação.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS kv (
  chave TEXT PRIMARY KEY,
  valor TEXT
);

CREATE TABLE IF NOT EXISTS norma (
  id            TEXT PRIMARY KEY,          -- caminho no acervo sem ".md"
  content_hash  TEXT NOT NULL,             -- OID do blob: detecta mudança
  esfera        TEXT NOT NULL,             -- constituicao|federal|estadual|municipal|regulador|jurisprudencia|tratado
  tipo          TEXT NOT NULL,
  titulo        TEXT NOT NULL,
  numero        TEXT,
  data          TEXT,                      -- ISO-8601
  ano           INTEGER,
  ementa        TEXT,
  uf            TEXT,
  municipio     TEXT,
  orgao         TEXT,
  tribunal      TEXT,
  situacao      TEXT,
  revogada      INTEGER,
  versao_texto  TEXT,
  urn           TEXT,
  fonte         TEXT,
  nome_popular  TEXT,
  sigla         TEXT,
  areas         TEXT NOT NULL DEFAULT '[]', -- JSON
  relevancia    TEXT NOT NULL DEFAULT 'normal',
  qualidade     REAL NOT NULL,
  faixa_qualidade TEXT NOT NULL,
  n_artigos     INTEGER NOT NULL DEFAULT 0,
  meta          TEXT NOT NULL DEFAULT '{}', -- cabeçalho YAML original (JSON)
  importado_em  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS norma_esfera_tipo ON norma (esfera, tipo, ano);
CREATE INDEX IF NOT EXISTS norma_uf ON norma (uf, ano) WHERE uf IS NOT NULL;
CREATE INDEX IF NOT EXISTS norma_urn ON norma (urn) WHERE urn IS NOT NULL;
CREATE INDEX IF NOT EXISTS norma_sigla ON norma (sigla) WHERE sigla IS NOT NULL;

CREATE TABLE IF NOT EXISTS dispositivo (
  id         INTEGER PRIMARY KEY,
  norma_id   TEXT NOT NULL REFERENCES norma(id) ON DELETE CASCADE,
  chave      TEXT NOT NULL UNIQUE,         -- "<norma_id>#<caminho>"
  caminho    TEXT NOT NULL,                -- "art-157/par-2/inc-ii"
  pai_id     INTEGER REFERENCES dispositivo(id) ON DELETE CASCADE,
  tipo       TEXT NOT NULL,                -- divisao|artigo|paragrafo|inciso|alinea|item|pena
  tipo_divisao TEXT,
  rotulo     TEXT NOT NULL,
  rubrica    TEXT,
  texto      TEXT NOT NULL,
  contexto   TEXT NOT NULL DEFAULT '',     -- "CP Código Penal Roubo": norma + rubrica do artigo (busca)
  revogado   INTEGER NOT NULL DEFAULT 0,
  vetado     INTEGER NOT NULL DEFAULT 0,
  ordem      INTEGER NOT NULL,             -- ordem de leitura dentro da norma
  linha      INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS dispositivo_norma ON dispositivo (norma_id, ordem);
CREATE INDEX IF NOT EXISTS dispositivo_pai ON dispositivo (pai_id);

CREATE TABLE IF NOT EXISTS nota_alteracao (
  dispositivo_id INTEGER NOT NULL REFERENCES dispositivo(id) ON DELETE CASCADE,
  tipo  TEXT NOT NULL,                     -- redacao|inclusao|revogacao|veto|vide|vigencia|renumeracao|redacao_anterior|outro
  texto TEXT NOT NULL,
  norma_ref TEXT                           -- texto da norma alteradora, resolvido depois para norma.id
);
CREATE INDEX IF NOT EXISTS nota_dispositivo ON nota_alteracao (dispositivo_id);
CREATE INDEX IF NOT EXISTS nota_ref ON nota_alteracao (norma_ref) WHERE norma_ref IS NOT NULL;

-- Precedente → dispositivo que ele interpreta (ex.: Súmula 600 STJ → Lei 11.340, art-5).
-- Base de "Relacionar leis", "jurisprudência do artigo" e do Radar de Concurso.
CREATE TABLE IF NOT EXISTS referencia_legal (
  origem_id     TEXT NOT NULL REFERENCES norma(id) ON DELETE CASCADE,
  alvo_tipo     TEXT NOT NULL,
  alvo_numero   TEXT,
  alvo_ano      INTEGER NOT NULL,
  alvo_caminho  TEXT,                       -- "art-226/par-8"; NULL = norma inteira
  alvo_norma_id TEXT                        -- resolvido após a carga; NULL se a norma não está no catálogo
);
CREATE INDEX IF NOT EXISTS ref_origem ON referencia_legal (origem_id);
CREATE INDEX IF NOT EXISTS ref_alvo ON referencia_legal (alvo_norma_id, alvo_caminho);

-- Uma linha por sincronização (botão "Atualizar", agendamento ou CLI).
CREATE TABLE IF NOT EXISTS historico_sync (
  id           INTEGER PRIMARY KEY,
  de_commit    TEXT,
  para_commit  TEXT,
  iniciado_em  TEXT NOT NULL,
  concluido_em TEXT NOT NULL,
  inseridas    INTEGER NOT NULL,
  atualizadas  INTEGER NOT NULL,
  removidas    INTEGER NOT NULL,
  falhas       INTEGER NOT NULL,
  mudancas     TEXT NOT NULL DEFAULT '[]'   -- JSON [{id, titulo, acao}] (até 200)
);

CREATE TABLE IF NOT EXISTS falha_importacao (
  caminho TEXT PRIMARY KEY,
  erro    TEXT NOT NULL,
  em      TEXT NOT NULL
);

-- Busca textual: sem acento ("acao" encontra "ação"), com prefixo.
CREATE VIRTUAL TABLE IF NOT EXISTS dispositivo_fts USING fts5(
  rotulo, rubrica, texto, contexto,
  content='dispositivo', content_rowid='id',
  tokenize = 'unicode61 remove_diacritics 2'
);
CREATE TRIGGER IF NOT EXISTS dispositivo_ai AFTER INSERT ON dispositivo BEGIN
  INSERT INTO dispositivo_fts(rowid, rotulo, rubrica, texto, contexto)
  VALUES (new.id, new.rotulo, new.rubrica, new.texto, new.contexto);
END;
CREATE TRIGGER IF NOT EXISTS dispositivo_ad AFTER DELETE ON dispositivo BEGIN
  INSERT INTO dispositivo_fts(dispositivo_fts, rowid, rotulo, rubrica, texto, contexto)
  VALUES ('delete', old.id, old.rotulo, old.rubrica, old.texto, old.contexto);
END;

CREATE VIRTUAL TABLE IF NOT EXISTS norma_fts USING fts5(
  titulo, ementa, nome_popular, sigla,
  content='norma', content_rowid='rowid',
  tokenize = 'unicode61 remove_diacritics 2'
);
CREATE TRIGGER IF NOT EXISTS norma_ai AFTER INSERT ON norma BEGIN
  INSERT INTO norma_fts(rowid, titulo, ementa, nome_popular, sigla)
  VALUES (new.rowid, new.titulo, new.ementa, new.nome_popular, new.sigla);
END;
CREATE TRIGGER IF NOT EXISTS norma_ad AFTER DELETE ON norma BEGIN
  INSERT INTO norma_fts(norma_fts, rowid, titulo, ementa, nome_popular, sigla)
  VALUES ('delete', old.rowid, old.titulo, old.ementa, old.nome_popular, old.sigla);
END;
