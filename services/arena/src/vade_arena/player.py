"""Perfil do jogador local (XP, nível, sequência, histórico), num arquivo SQLite.

É a versão de um jogador só, para o app local. No servidor multiusuário, o mesmo papel é cumprido
pelas tabelas ``perfil`` e ``lancamento`` de ``db/sqlite`` (ver docs/04-modelo-de-dados.md).
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

from vade_learning import gamification as g

TITLES = [  # (nível mínimo, título)
    (1, "Estagiário(a)"), (3, "Bacharel"), (6, "Advogado(a) Júnior"), (10, "Advogado(a) Pleno"),
    (15, "Associado(a) Sênior"), (21, "Sócio(a)"), (28, "Sócio(a)-Gestor(a)"), (36, "Desembargador(a)"),
    (45, "Ministro(a)"),
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS jogador (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  nome TEXT NOT NULL DEFAULT 'Você',
  xp_total INTEGER NOT NULL DEFAULT 0,
  streak_atual INTEGER NOT NULL DEFAULT 0,
  streak_max INTEGER NOT NULL DEFAULT 0,
  streak_dia TEXT,
  protetores INTEGER NOT NULL DEFAULT 1
);
INSERT OR IGNORE INTO jogador (id) VALUES (1);
CREATE TABLE IF NOT EXISTS partida (
  id TEXT PRIMARY KEY,
  tipo TEXT NOT NULL CHECK (tipo IN ('simulado', 'caso')),
  ref TEXT NOT NULL,
  nivel TEXT,
  nota REAL NOT NULL,
  sucesso INTEGER NOT NULL,
  xp INTEGER NOT NULL,
  resumo TEXT NOT NULL,
  criado_em TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS partida_tipo ON partida (tipo, criado_em);
CREATE TABLE IF NOT EXISTS tribunal_save (
  ep_id TEXT PRIMARY KEY,
  estado TEXT NOT NULL,
  atualizado TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS marca (
  nome TEXT PRIMARY KEY,
  ep_id TEXT NOT NULL,
  criado_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS questao_vista (
  questao_id TEXT PRIMARY KEY,
  vezes INTEGER NOT NULL,
  acertos INTEGER NOT NULL,
  ultima TEXT NOT NULL
);
"""


def title_for(level: int) -> str:
    return [t for lvl, t in TITLES if level >= lvl][-1]


class Player:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        db = self._db()
        try:
            db.executescript(SCHEMA)
            self._migrate(db)
            db.commit()
        finally:
            db.close()

    def _db(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout = 5000")
        return db

    def _migrate(self, db: sqlite3.Connection) -> None:
        cols = {r[1] for r in db.execute("PRAGMA table_info(jogador)")}
        if "avatar" not in cols:
            db.execute("ALTER TABLE jogador ADD COLUMN avatar TEXT")

    def save_trial(self, ep_id: str, estado: dict) -> None:
        db = self._db()
        try:
            with db:
                db.execute("INSERT INTO tribunal_save VALUES (?, ?, ?) ON CONFLICT(ep_id) DO UPDATE SET estado = excluded.estado,"
                           " atualizado = excluded.atualizado", (ep_id, json.dumps(estado, ensure_ascii=False),
                                                                  dt.datetime.now().isoformat(timespec="seconds")))
        finally:
            db.close()

    def load_trial(self, ep_id: str) -> dict | None:
        db = self._db()
        try:
            row = db.execute("SELECT estado FROM tribunal_save WHERE ep_id = ?", (ep_id,)).fetchone()
            return json.loads(row[0]) if row else None
        finally:
            db.close()

    def clear_trial(self, ep_id: str) -> None:
        db = self._db()
        try:
            with db:
                db.execute("DELETE FROM tribunal_save WHERE ep_id = ?", (ep_id,))
        finally:
            db.close()

    def saved_trials(self) -> set[str]:
        db = self._db()
        try:
            return {r[0] for r in db.execute("SELECT ep_id FROM tribunal_save")}
        finally:
            db.close()

    def saved_scenes(self) -> dict[str, str]:
        db = self._db()
        try:
            return {r[0]: (json.loads(r[1]) or {}).get("cena") for r in db.execute("SELECT ep_id, estado FROM tribunal_save")}
        finally:
            db.close()

    def set_marks(self, ep_id: str, declared: set[str], chosen: set[str]) -> None:
        """Troca as marcas de um episódio: rejogar o caso com outra escolha muda a história."""
        db = self._db()
        try:
            with db:
                db.executemany("DELETE FROM marca WHERE nome = ?", [(m,) for m in declared])
                now = dt.datetime.now().isoformat(timespec="seconds")
                db.executemany("INSERT INTO marca VALUES (?, ?, ?)", [(m, ep_id, now) for m in sorted(chosen & declared)])
        finally:
            db.close()

    def marks(self) -> set[str]:
        db = self._db()
        try:
            return {r[0] for r in db.execute("SELECT nome FROM marca")}
        finally:
            db.close()

    def perfect_cases(self) -> set[str]:
        db = self._db()
        try:
            return {r[0] for r in db.execute("SELECT DISTINCT ref FROM partida WHERE tipo = 'caso' AND sucesso = 1")}
        finally:
            db.close()

    def set_avatar(self, nome: str, avatar: dict) -> None:
        nome = (nome or "Você").strip()[:32] or "Você"
        db = self._db()
        try:
            with db:
                db.execute("UPDATE jogador SET nome = ?, avatar = ? WHERE id = 1", (nome, json.dumps(avatar)))
        finally:
            db.close()

    def avatar(self) -> tuple[str, dict | None]:
        db = self._db()
        try:
            row = db.execute("SELECT nome, avatar FROM jogador WHERE id = 1").fetchone()
            return row["nome"], (json.loads(row["avatar"]) if row["avatar"] else None)
        finally:
            db.close()

    def record_trial(self, run_id: str, ep: dict, result: dict, today: dt.date | None = None) -> dict:
        db = self._db()
        try:
            with db:
                resumo = {"titulo": ep["titulo"], "papel": ep["papel"], "carimbo": result["carimbo"], "modo": "tribunal",
                          "credibilidade": result["credibilidade"], "erros": result["erros"]}
                db.execute("INSERT OR IGNORE INTO partida VALUES (?, 'caso', ?, ?, ?, ?, ?, ?, ?)",
                           (run_id, ep["id"], ep["nivel"], result["aproveitamento"], int(result["perfeito"]),
                            result["xp"], json.dumps(resumo, ensure_ascii=False), dt.datetime.now().isoformat(timespec="seconds")))
                return self._register(db, result["xp"], today or dt.date.today())
        finally:
            db.close()

    def _register(self, db: sqlite3.Connection, xp: int, today: dt.date) -> dict:
        row = db.execute("SELECT * FROM jogador WHERE id = 1").fetchone()
        before = g.level_from_xp(row["xp_total"])
        streak = g.register_activity(
            g.Streak(row["streak_atual"], row["streak_max"],
                     dt.date.fromisoformat(row["streak_dia"]) if row["streak_dia"] else None, row["protetores"]),
            today)
        total = row["xp_total"] + xp
        db.execute("UPDATE jogador SET xp_total = ?, streak_atual = ?, streak_max = ?, streak_dia = ?, protetores = ? WHERE id = 1",
                   (total, streak.current, streak.longest, streak.last_day.isoformat(), streak.freezes))
        after = g.level_from_xp(total)
        return {"subiu_de_nivel": after > before, "nivel": after, "titulo": title_for(after), "streak": streak.current}

    def record_exam(self, result: dict, today: dt.date | None = None) -> dict:
        db = self._db()
        try:
            with db:
                for q in result["questoes"]:
                    db.execute("""INSERT INTO questao_vista VALUES (?, 1, ?, ?)
                                  ON CONFLICT(questao_id) DO UPDATE SET vezes = vezes + 1,
                                  acertos = acertos + excluded.acertos, ultima = excluded.ultima""",
                               (q["id"], int(q["status"] == "certa"), dt.datetime.now().isoformat(timespec="seconds")))
                resumo = {k: result[k] for k in ("concurso", "nivel_nome", "acertos", "erros", "brancos", "total", "meta")}
                db.execute("INSERT OR IGNORE INTO partida VALUES (?, 'simulado', ?, ?, ?, ?, ?, ?, ?)",
                           (result["sessao"], result["concurso"], result["nivel"], result["nota"], int(result["aprovado"]),
                            result["xp"], json.dumps(resumo, ensure_ascii=False), dt.datetime.now().isoformat(timespec="seconds")))
                return self._register(db, result["xp"], today or dt.date.today())
        finally:
            db.close()

    def record_case(self, run_id: str, caso: dict, final: dict, today: dt.date | None = None) -> dict:
        db = self._db()
        try:
            with db:
                resumo = {"titulo": caso["titulo"], "papel": caso["papel"], "carimbo": final["carimbo"], "final": final["titulo"]}
                db.execute("INSERT OR IGNORE INTO partida VALUES (?, 'caso', ?, ?, ?, ?, ?, ?, ?)",
                           (run_id, caso["id"], caso["nivel"], final["aproveitamento"],
                            int(final.get("faixa") == "otimo"), final["xp"], json.dumps(resumo, ensure_ascii=False),
                            dt.datetime.now().isoformat(timespec="seconds")))
                return self._register(db, final["xp"], today or dt.date.today())
        finally:
            db.close()

    def seen_questions(self) -> set[str]:
        db = self._db()
        try:
            return {r[0] for r in db.execute("SELECT questao_id FROM questao_vista")}
        finally:
            db.close()

    def profile(self, today: dt.date | None = None) -> dict:
        today = today or dt.date.today()
        db = self._db()
        try:
            row = db.execute("SELECT * FROM jogador WHERE id = 1").fetchone()
            level = g.level_from_xp(row["xp_total"])
            floor, ceil = g.xp_for_level(level), g.xp_for_level(level + 1)
            stats = {r["tipo"]: dict(r) for r in db.execute(
                "SELECT tipo, count(*) AS jogadas, sum(sucesso) AS sucessos, max(nota) AS melhor FROM partida GROUP BY tipo")}
            best_cases = {r["ref"]: r["nota"] for r in db.execute(
                "SELECT ref, max(nota) AS nota FROM partida WHERE tipo = 'caso' GROUP BY ref")}
            recent = [{**dict(r), "resumo": json.loads(r["resumo"])} for r in db.execute(
                "SELECT tipo, ref, nivel, nota, sucesso, xp, resumo, criado_em FROM partida ORDER BY criado_em DESC LIMIT 8")]
            q = db.execute("SELECT count(*) AS vistas, coalesce(sum(vezes), 0) AS respostas, coalesce(sum(acertos), 0) AS acertos FROM questao_vista").fetchone()
            streak = g.Streak(row["streak_atual"], row["streak_max"],
                              dt.date.fromisoformat(row["streak_dia"]) if row["streak_dia"] else None, row["protetores"])
            return {
                "nome": row["nome"], "avatar": json.loads(row["avatar"]) if row["avatar"] else None,
                "xp": row["xp_total"], "nivel": level, "titulo": title_for(level),
                "xp_nivel_atual": row["xp_total"] - floor, "xp_proximo_nivel": ceil - floor,
                "streak": streak.current if g.is_alive(streak, today) else 0, "streak_max": streak.longest,
                "jogou_hoje": streak.last_day == today, "protetores": streak.freezes,
                "simulados": stats.get("simulado", {"jogadas": 0, "sucessos": 0, "melhor": None}),
                "casos": stats.get("caso", {"jogadas": 0, "sucessos": 0, "melhor": None}),
                "melhor_por_caso": best_cases, "recentes": recent,
                "questoes": dict(q),
            }
        finally:
            db.close()
