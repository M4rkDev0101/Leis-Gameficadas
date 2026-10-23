"""Perfil do jogador local (XP, nível, sequência, histórico), num arquivo SQLite.

É a versão de um jogador só, para o app local. No servidor multiusuário, o mesmo papel é cumprido
pelas tabelas ``perfil`` e ``lancamento`` de ``db/sqlite`` (ver docs/04-modelo-de-dados.md).
"""

from __future__ import annotations

import datetime as dt
import json
import random
import sqlite3
from pathlib import Path

from vade_learning import gamification as g

from . import recompensas as rw

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
CREATE TABLE IF NOT EXISTS nota_caso (
  ep_id TEXT PRIMARY KEY,
  nota TEXT NOT NULL,
  erros INTEGER NOT NULL,
  segundos INTEGER,
  vezes INTEGER NOT NULL DEFAULT 1,
  atualizado TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS carta (
  chave TEXT PRIMARY KEY,
  ep_id TEXT NOT NULL,
  dourada INTEGER NOT NULL DEFAULT 0,
  criado_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS contador (
  nome TEXT PRIMARY KEY,
  valor INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS dia_resposta (
  dia TEXT NOT NULL,
  questao_id TEXT NOT NULL,
  resposta TEXT,
  correta INTEGER NOT NULL,
  PRIMARY KEY (dia, questao_id)
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
        if "protetor_semana" not in cols:  # idempotente: saves antigos ganham a coluna sem perder nada
            db.execute("ALTER TABLE jogador ADD COLUMN protetor_semana TEXT")

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

    def record_trial(self, run_id: str, ep: dict, result: dict, today: dt.date | None = None,
                     extras: dict | None = None, cartas: list[dict] | None = None) -> dict:
        """Grava o caso e entrega as recompensas (nota, combo, baú, cartas). ``extras``: combo_max, certeiras, segundos."""
        today = today or dt.date.today()
        extras = extras or {}
        db = self._db()
        try:
            with db:
                nota = rw.nota_do_caso(result["venceu"], result["erros"])
                novo = db.execute("SELECT 1 FROM partida WHERE id = ?", (run_id,)).fetchone() is None
                recomp = {"nota": nota, "combo_max": 0, "xp_combo": 0, "xp_melhora": 0, "xp_bau": 0, "bau": None,
                          "recorde": None, "cartas_novas": [], "carta_dourada": None}
                if novo and nota:
                    recomp = self._recompensas(db, run_id, ep, result, nota, extras, cartas or [])
                result["xp"] += recomp["xp_combo"] + recomp["xp_melhora"] + recomp["xp_bau"]
                result["nota"] = nota
                result["recompensas"] = recomp
                resumo = {"titulo": ep["titulo"], "papel": ep["papel"], "carimbo": result["carimbo"], "modo": "tribunal",
                          "credibilidade": result["credibilidade"], "erros": result["erros"], "nota": nota}
                db.execute("INSERT OR IGNORE INTO partida VALUES (?, 'caso', ?, ?, ?, ?, ?, ?, ?)",
                           (run_id, ep["id"], ep["nivel"], result["aproveitamento"], int(result["perfeito"]),
                            result["xp"], json.dumps(resumo, ensure_ascii=False), dt.datetime.now().isoformat(timespec="seconds")))
                prog = self._register(db, result["xp"] if novo else 0, today)
                prog["recompensas"], prog["nota"] = recomp, nota
                return prog
        finally:
            db.close()

    def _recompensas(self, db, run_id, ep, result, nota, extras, cartas) -> dict:
        agora = dt.datetime.now().isoformat(timespec="seconds")
        combo = max(0, min(int(extras.get("combo_max") or 0), rw.COMBO_TETO))
        segundos = extras.get("segundos")
        segundos = max(0, min(int(segundos), 86400)) if isinstance(segundos, (int, float)) else None
        base = result["xp"]
        prev = db.execute("SELECT * FROM nota_caso WHERE ep_id = ?", (ep["id"],)).fetchone()
        recorde = {"nota_anterior": prev["nota"] if prev else None, "melhorou_nota": False, "melhorou_tempo": False,
                   "primeira_vez": prev is None, "tempo_s": segundos}
        degraus = 0
        if prev is None:
            db.execute("INSERT INTO nota_caso VALUES (?, ?, ?, ?, 1, ?)", (ep["id"], nota, result["erros"], segundos, agora))
        else:
            degraus = max(0, rw.rank(nota) - rw.rank(prev["nota"]))
            melhor_nota = nota if degraus else prev["nota"]
            melhor_erros = result["erros"] if degraus or (nota == prev["nota"] and result["erros"] < prev["erros"]) else prev["erros"]
            tempo_ant = prev["segundos"]
            melhor_t = segundos if segundos is not None and (tempo_ant is None or segundos < tempo_ant) else tempo_ant
            recorde["melhorou_nota"] = degraus > 0
            recorde["melhorou_tempo"] = segundos is not None and tempo_ant is not None and segundos < tempo_ant
            db.execute("UPDATE nota_caso SET nota = ?, erros = ?, segundos = ?, vezes = vezes + 1, atualizado = ? WHERE ep_id = ?",
                       (melhor_nota, melhor_erros, melhor_t, agora, ep["id"]))
        recorde["selo_dourado"] = nota == "S" or (prev is not None and prev["nota"] == "S")
        # cartas: o dispositivo aplicado ao vencer o caso entra no álbum; caso perfeito = carta dourada
        novas = []
        for c in cartas:
            if db.execute("SELECT 1 FROM carta WHERE chave = ?", (c["chave"],)).fetchone() is None:
                db.execute("INSERT INTO carta VALUES (?, ?, ?, ?)", (c["chave"], ep["id"], int(nota == "S"), agora))
                novas.append({**c, "dourada": nota == "S"})
            elif nota == "S":
                db.execute("UPDATE carta SET dourada = 1 WHERE chave = ?", (c["chave"],))
        bau = rw.bau(run_id, nota)
        dourada = None
        if bau["carta_dourada"]:  # a carta rara do baú "banha a ouro" uma carta que o jogador já tem
            cand = [r[0] for r in db.execute("SELECT chave FROM carta WHERE dourada = 0 ORDER BY chave")]
            if cand:
                dourada = random.Random(run_id).choice(cand)
                db.execute("UPDATE carta SET dourada = 1 WHERE chave = ?", (dourada,))
        self._add(db, "contradicoes", max(0, min(int(extras.get("certeiras") or 0), 50)))
        self._max(db, "combo_max", combo)
        return {"nota": nota, "combo_max": combo, "xp_combo": rw.bonus_combo(base, combo),
                "xp_melhora": degraus * rw.BONUS_MELHORA, "xp_bau": bau["xp"], "bau": bau["tipo"],
                "recorde": recorde, "cartas_novas": novas, "carta_dourada": dourada}

    @staticmethod
    def _add(db, nome: str, n: int) -> None:
        db.execute("INSERT INTO contador VALUES (?, ?) ON CONFLICT(nome) DO UPDATE SET valor = valor + excluded.valor", (nome, n))

    @staticmethod
    def _max(db, nome: str, n: int) -> None:
        db.execute("INSERT INTO contador VALUES (?, ?) ON CONFLICT(nome) DO UPDATE SET valor = max(valor, excluded.valor)", (nome, n))

    def counters(self) -> dict[str, int]:
        db = self._db()
        try:
            return {r[0]: r[1] for r in db.execute("SELECT nome, valor FROM contador")}
        finally:
            db.close()

    def grades(self) -> dict[str, dict]:
        db = self._db()
        try:
            return {r["ep_id"]: {"nota": r["nota"], "erros": r["erros"], "segundos": r["segundos"], "vezes": r["vezes"]}
                    for r in db.execute("SELECT * FROM nota_caso")}
        finally:
            db.close()

    def cards(self) -> dict[str, dict]:
        db = self._db()
        try:
            return {r["chave"]: {"ep_id": r["ep_id"], "dourada": bool(r["dourada"]), "desde": r["criado_em"]}
                    for r in db.execute("SELECT * FROM carta")}
        finally:
            db.close()

    # ---------------------------------------------------------- desafio do dia
    def day_answers(self, day: dt.date) -> dict[str, dict]:
        db = self._db()
        try:
            return {r["questao_id"]: {"resposta": r["resposta"], "correta": bool(r["correta"])}
                    for r in db.execute("SELECT * FROM dia_resposta WHERE dia = ?", (day.isoformat(),))}
        finally:
            db.close()

    def days_completed(self) -> int:
        db = self._db()
        try:
            return db.execute("SELECT count(*) FROM (SELECT dia FROM dia_resposta GROUP BY dia HAVING count(*) >= ?)",
                              (rw.DIA_QUESTOES,)).fetchone()[0]
        finally:
            db.close()

    def record_day_answer(self, day: dt.date, qid: str, resposta: str | None, correta: bool, total: int) -> dict:
        """Grava uma resposta do desafio do dia (uma por questão) e paga o XP; ao fechar as três, o bônus do dia."""
        db = self._db()
        try:
            with db:
                if db.execute("SELECT 1 FROM dia_resposta WHERE dia = ? AND questao_id = ?", (day.isoformat(), qid)).fetchone():
                    raise ValueError("questão do dia já respondida")
                db.execute("INSERT INTO dia_resposta VALUES (?, ?, ?, ?)", (day.isoformat(), qid, resposta, int(correta)))
                feitas = db.execute("SELECT count(*) FROM dia_resposta WHERE dia = ?", (day.isoformat(),)).fetchone()[0]
                completo = feitas >= total
                xp = (rw.DIA_XP_ACERTO if correta else 2) + (rw.DIA_XP_COMPLETO if completo else 0)
                prog = self._register(db, xp, day)
                prog.update({"xp": xp, "completo": completo, "feitas": feitas})
                return prog
        finally:
            db.close()

    def _refill(self, db: sqlite3.Connection, today: dt.date) -> sqlite3.Row:
        """1 dia de folga grátis por semana (acumula até 2). Nada é tirado de quem some, além da sequência."""
        row = db.execute("SELECT * FROM jogador WHERE id = 1").fetchone()
        sem = rw.semana(today)
        if row["protetor_semana"] != sem:
            primeira = row["protetor_semana"] is None
            novo = row["protetores"] if primeira else min(rw.PROTETORES_MAX, row["protetores"] + 1)
            db.execute("UPDATE jogador SET protetores = ?, protetor_semana = ? WHERE id = 1", (novo, sem))
            row = db.execute("SELECT * FROM jogador WHERE id = 1").fetchone()
        return row

    def _register(self, db: sqlite3.Connection, xp: int, today: dt.date) -> dict:
        row = self._refill(db, today)
        before = g.level_from_xp(row["xp_total"])
        streak = g.register_activity(
            g.Streak(row["streak_atual"], row["streak_max"],
                     dt.date.fromisoformat(row["streak_dia"]) if row["streak_dia"] else None, row["protetores"]),
            today)
        total = row["xp_total"] + xp
        db.execute("UPDATE jogador SET xp_total = ?, streak_atual = ?, streak_max = ?, streak_dia = ?, protetores = ? WHERE id = 1",
                   (total, streak.current, streak.longest, streak.last_day.isoformat(), streak.freezes))
        after = g.level_from_xp(total)
        return {"subiu_de_nivel": after > before, "nivel": after, "titulo": title_for(after), "streak": streak.current,
                "patente_nova": title_for(after) != title_for(before), "protetores": streak.freezes,
                "protetor_usado": streak.freezes < row["protetores"]}

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
            with db:
                row = self._refill(db, today)
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
                "proxima_patente": next(({"nivel": lvl, "titulo": t, "faltam_xp": g.xp_for_level(lvl) - row["xp_total"]}
                                         for lvl, t in TITLES if lvl > level), None),
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
