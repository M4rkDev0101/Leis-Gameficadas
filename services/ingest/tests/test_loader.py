"""Integração: carga, busca, referências e sincronização incremental via git."""

import shutil
import subprocess
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from vade_ingest.loader import Catalog
from vade_ingest.sources import FsSource, GitSource, is_norm_path

CP = """---
titulo: "Decreto-Lei nº 2.848 de 07/12/1940"
tipo: "Decreto-Lei"
numero: "2848"
data: 1940-12-07
ementa: "Código Penal."
---
# Decreto-Lei nº 2.848 de 07/12/1940

**Legítima defesa**

**Art. 25.** Entende-se em legítima defesa quem, usando moderadamente dos meios necessários, repele injusta agressão, atual ou iminente, a direito seu ou de outrem.

**Parágrafo único.** Observados os requisitos previstos no caput deste artigo, considera-se também em legítima defesa o agente de segurança pública.
"""

SUMULA = """---
titulo: "Súmula nº 999 do STJ"
tipo: "Súmula"
numero: "999"
---
# Súmula nº 999 do STJ

DIREITO PENAL - LEGÍTIMA DEFESA

Enunciado
Enunciado fictício de teste sobre a legítima defesa do agente de segurança pública em serviço.

Referências Legislativas
LEG:FED DEL:002848 ANO:1940
ART:00025 PAR:ÚNICO
"""

LEI_UTIL = """---
titulo: "Lei nº 1 de 2019"
uf: "MG"
tipo: "Lei Ordinária"
numero: "1"
data: 2019-01-02
ementa: "Declara de utilidade pública a Associação X."
---
# Lei nº 1 de 2019

**Art. 1º** Fica declarada de utilidade pública a Associação Amigos do Bairro, com sede no Município de Belo Horizonte.
"""


def write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


class TestPaths(unittest.TestCase):
    def test_is_norm_path(self):
        self.assertTrue(is_norm_path("constituicao.md"))
        self.assertTrue(is_norm_path("federal/decretos-lei/1940/del-2848-1940-12-07.md"))
        self.assertFalse(is_norm_path("README.md"))
        self.assertFalse(is_norm_path("federal/_candidatos_x/a.md"))
        self.assertFalse(is_norm_path("scripts/x.md"))
        self.assertFalse(is_norm_path("municipais/_falhas.jsonl"))


class TestCatalog(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "acervo"
        write(self.root, "federal/decretos-lei/1940/del-2848-1940-12-07.md", CP)
        write(self.root, "jurisprudencia/stj/sumulas/sumula-999.md", SUMULA)
        write(self.root, "estaduais/MG/leis-ordinarias/2019/lei-1-2019.md", LEI_UTIL)
        write(self.root, "federal/_interno/nao-importar.md", CP)
        self.cat = Catalog(self.tmp / "c.sqlite")

    def tearDown(self):
        self.cat.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_fs_import_search_and_references(self):
        r = self.cat.sync(FsSource(self.root))
        self.assertEqual((r.inserted, r.failed), (3, 0))
        hits = {h["caminho"]: h for h in self.cat.search("legitima defesa")}  # sem acento
        self.assertEqual(hits["art-25"]["rubrica"], "Legítima defesa")
        self.assertIn("enunciado", hits)  # a súmula também aparece
        self.assertNotIn("art-1", hits)  # a lei de utilidade pública não
        ref = self.cat.db.execute(
            "SELECT r.alvo_norma_id, d.texto FROM referencia_legal r "
            "JOIN dispositivo d ON d.norma_id = r.alvo_norma_id AND d.caminho = r.alvo_caminho"
        ).fetchone()
        self.assertEqual(ref[0], "federal/decretos-lei/1940/del-2848-1940-12-07")
        self.assertIn("agente de segurança pública", ref[1])
        rel = dict(self.cat.db.execute("SELECT id, relevancia FROM norma"))
        self.assertEqual(rel["estaduais/MG/leis-ordinarias/2019/lei-1-2019"], "baixa")

    def test_context_lets_paragraphs_match_article_rubric(self):
        self.cat.sync(FsSource(self.root))
        hits = [h["caminho"] for h in self.cat.search('"legitima" "defesa" "agente"')]
        self.assertIn("art-25/par-unico", hits)
        hits = [h["caminho"] for h in self.cat.search('"codigo" "penal" "agressao"')]  # nome popular no contexto
        self.assertEqual(hits, ["art-25"])

    def test_migrates_v1_catalog(self):
        import sqlite3
        self.cat.close()
        db = sqlite3.connect(self.tmp / "v1.sqlite")
        db.executescript("""CREATE TABLE kv (chave TEXT PRIMARY KEY, valor TEXT);
            INSERT INTO kv VALUES ('ultimo_commit', 'abc');
            CREATE TABLE norma (id TEXT PRIMARY KEY, content_hash TEXT NOT NULL, esfera TEXT NOT NULL, tipo TEXT NOT NULL,
              titulo TEXT NOT NULL, numero TEXT, data TEXT, ano INTEGER, ementa TEXT, uf TEXT, municipio TEXT, orgao TEXT,
              tribunal TEXT, situacao TEXT, revogada INTEGER, versao_texto TEXT, urn TEXT, fonte TEXT, nome_popular TEXT,
              sigla TEXT, areas TEXT NOT NULL DEFAULT '[]', relevancia TEXT NOT NULL DEFAULT 'normal', qualidade REAL NOT NULL,
              faixa_qualidade TEXT NOT NULL, n_artigos INTEGER NOT NULL DEFAULT 0, meta TEXT NOT NULL DEFAULT '{}', importado_em TEXT NOT NULL);
            INSERT INTO norma (id, content_hash, esfera, tipo, titulo, qualidade, faixa_qualidade, importado_em)
              VALUES ('x', 'h', 'federal', 'Lei', 'X', 1, 'alta', 'agora');
            CREATE TABLE dispositivo (id INTEGER PRIMARY KEY, norma_id TEXT NOT NULL, chave TEXT NOT NULL UNIQUE, caminho TEXT NOT NULL,
              pai_id INTEGER, tipo TEXT NOT NULL, tipo_divisao TEXT, rotulo TEXT NOT NULL, rubrica TEXT, texto TEXT NOT NULL,
              revogado INTEGER NOT NULL DEFAULT 0, vetado INTEGER NOT NULL DEFAULT 0, ordem INTEGER NOT NULL, linha INTEGER NOT NULL);
            INSERT INTO norma (id, content_hash, esfera, tipo, titulo, qualidade, faixa_qualidade, importado_em)
              VALUES ('federal/decretos-lei/1940/del-2848-1940-12-07', 'velho', 'federal', 'Decreto-Lei', 'CP', 1, 'alta', 'agora');
            INSERT INTO dispositivo (norma_id, chave, caminho, tipo, rotulo, texto, ordem, linha)
              VALUES ('federal/decretos-lei/1940/del-2848-1940-12-07', 'cp#art-25', 'art-25', 'artigo', 'Art. 25', 'Entende-se em legítima defesa', 1, 1);
            CREATE VIRTUAL TABLE dispositivo_fts USING fts5(rotulo, rubrica, texto, content='dispositivo', content_rowid='id',
              tokenize = 'unicode61 remove_diacritics 2');
            INSERT INTO dispositivo_fts(dispositivo_fts) VALUES ('rebuild');""")
        db.close()
        self.cat = Catalog(self.tmp / "v1.sqlite")
        self.assertIsNone(self.cat.get("ultimo_commit"))  # força reimportação do recorte
        self.assertEqual(set(self.cat.hashes().values()), {""})
        self.assertEqual(self.cat.db.execute("PRAGMA user_version").fetchone()[0], 2)
        r = self.cat.sync(FsSource(self.root))  # substitui o CP antigo (DELETE em cascata no FTS)
        self.assertEqual((r.inserted, r.updated, r.failed), (2, 1, 0))
        self.assertEqual(self.cat.db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        self.cat.db.execute("INSERT INTO dispositivo_fts(dispositivo_fts) VALUES ('integrity-check')")
        self.assertTrue(self.cat.search('"legitima"'))

    def test_parser_upgrade_forces_reprocessing(self):
        from vade_ingest import loader
        self.cat.sync(FsSource(self.root))
        self.cat.close()
        with unittest.mock.patch.object(loader, "PARSER_VERSION", "versao-futura"):
            self.cat = Catalog(self.tmp / "c.sqlite")
            self.assertEqual(set(self.cat.hashes().values()), {""})
            r = self.cat.sync(FsSource(self.root))
            self.assertEqual((r.updated, r.unchanged), (3, 0))  # arquivos iguais, parse novo
            self.assertEqual(self.cat.get("versao_parser"), "versao-futura")

    def test_natural_keys_survive_reimport(self):
        self.cat.sync(FsSource(self.root))
        key = "federal/decretos-lei/1940/del-2848-1940-12-07#art-25/par-unico"
        before = self.cat.db.execute("SELECT id FROM dispositivo WHERE chave = ?", (key,)).fetchone()
        write(self.root, "federal/decretos-lei/1940/del-2848-1940-12-07.md", CP.replace("Código Penal.", "Código Penal (alterado)."))
        r = self.cat.sync(FsSource(self.root), full=True)
        self.assertEqual((r.updated, r.unchanged), (1, 2))
        after = self.cat.db.execute("SELECT id FROM dispositivo WHERE chave = ?", (key,)).fetchone()
        self.assertIsNotNone(before)
        self.assertIsNotNone(after)  # o id numérico pode mudar; a chave natural não


@unittest.skipUnless(shutil.which("git"), "git não instalado")
class TestGitIncremental(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "t@t")
        git(self.repo, "config", "user.name", "t")
        write(self.repo, "federal/decretos-lei/1940/del-2848-1940-12-07.md", CP)
        write(self.repo, "estaduais/MG/leis-ordinarias/2019/lei-1-2019.md", LEI_UTIL)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "c1")
        self.cat = Catalog(self.tmp / "c.sqlite")

    def tearDown(self):
        self.cat.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_incremental_sync_uses_diff(self):
        r1 = self.cat.sync(GitSource(self.repo))
        self.assertEqual(r1.inserted, 2)
        # commit 2: altera uma, remove outra, adiciona uma
        write(self.repo, "federal/decretos-lei/1940/del-2848-1940-12-07.md", CP + "\n**Art. 26.** É isento de pena o agente.\n")
        (self.repo / "estaduais/MG/leis-ordinarias/2019/lei-1-2019.md").unlink()
        write(self.repo, "jurisprudencia/stj/sumulas/sumula-999.md", SUMULA)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "c2")
        r2 = self.cat.sync(GitSource(self.repo))
        self.assertEqual((r2.seen, r2.updated, r2.inserted, r2.deleted), (2, 1, 1, 1))
        self.assertEqual(self.cat.get("ultimo_commit"), git(self.repo, "rev-parse", "HEAD"))
        n = self.cat.db.execute("SELECT n_artigos FROM norma WHERE sigla = 'CP'").fetchone()[0]
        self.assertEqual(n, 2)
        # sem commits novos: nada a fazer
        r3 = self.cat.sync(GitSource(self.repo))
        self.assertEqual((r3.seen, r3.inserted, r3.updated, r3.deleted), (0, 0, 0, 0))


if __name__ == "__main__":
    unittest.main()
