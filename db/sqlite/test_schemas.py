"""Os esquemas SQLite aplicam, são idempotentes e fazem valer as regras de integridade.

    python -m unittest discover -s db/sqlite
"""

import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent


def apply(path: Path, script: str) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.execute("PRAGMA foreign_keys = ON")
    sql = (HERE / script).read_text(encoding="utf-8")
    db.executescript(sql)
    db.executescript(sql)  # idempotente
    return db


class TestSchemas(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.u = apply(self.tmp / "usuarios.sqlite", "usuarios.sql")
        self.e = apply(self.tmp / "eventos-2026-10.sqlite", "eventos.sql")
        self.u.execute("INSERT INTO usuario (id, criado_em) VALUES ('u1', '2026-10-21')")
        self.u.execute("INSERT INTO perfil (usuario_id) VALUES ('u1')")

    def tearDown(self):
        self.u.close()
        self.e.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_integrity_rules(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.u.execute("INSERT INTO perfil (usuario_id) VALUES ('nao-existe')")
        with self.assertRaises(sqlite3.IntegrityError):
            self.u.execute("UPDATE perfil SET liga = 'lendario' WHERE usuario_id = 'u1'")
        with self.assertRaises(sqlite3.IntegrityError):
            self.u.execute("INSERT INTO parametros_fsrs (usuario_id, pesos, retencao_desejada) VALUES ('u1', '[]', 0.5)")

    def test_event_resend_is_idempotent(self):
        row = ("r1", "u1", "fc:1", 3, "2026-10-21T12:00:00Z", 0, None, 0, 3.17, 5.3, 1200, "fsrs-5", "h1")
        for _ in range(3):  # o cliente offline pode reenviar
            self.e.execute("INSERT OR IGNORE INTO revisao VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", row)
        self.assertEqual(self.e.execute("SELECT count(*) FROM revisao").fetchone()[0], 1)

    def test_account_deletion_cascades(self):
        self.u.execute("INSERT INTO cartao VALUES ('u1', 'fc:1', 'cf#art-5', 2, 5.0, 10.0, NULL, NULL, 1, 0)")
        self.u.execute("DELETE FROM usuario WHERE id = 'u1'")
        for table in ("perfil", "cartao"):
            self.assertEqual(self.u.execute(f"SELECT count(*) FROM {table}").fetchone()[0], 0)

    def test_review_queue_uses_index(self):
        plan = " ".join(r[3] for r in self.u.execute(
            "EXPLAIN QUERY PLAN SELECT * FROM cartao WHERE usuario_id = 'u1' AND vence_em <= '2026-10-21' ORDER BY vence_em"))
        self.assertIn("cartao_fila", plan)


if __name__ == "__main__":
    unittest.main()
