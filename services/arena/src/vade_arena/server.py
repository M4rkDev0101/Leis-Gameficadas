"""Servidor do jogo: Arena (simulados e casos) + painel do acervo, num endereço só.

    /           Arena (Início, Simulados, Casos)
    /acervo     painel do acervo com o botão "Verificar atualização"
    /api/arena  API do jogo;  /api/...  API do acervo (vade_ingest)

As sessões de simulado e de caso ficam em memória no servidor, com o gabarito: o navegador só
recebe o que pode ver.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import threading
import time
from collections import OrderedDict
from importlib import resources
from pathlib import Path
from urllib.parse import urlparse

from vade_ingest import server as ingest_server
from vade_ingest.updater import Updater

import uuid

from . import bank as bank_mod
from . import cases, exam
from . import tribunal as tribunal_mod
from .player import Player

MAX_SESSIONS = 200
SESSION_TTL_S = 6 * 3600


class Sessions:
    def __init__(self) -> None:
        self._d: OrderedDict[str, tuple[float, object]] = OrderedDict()
        self._lock = threading.Lock()

    def put(self, sid: str, obj: object) -> None:
        with self._lock:
            self._d[sid] = (time.time(), obj)
            while len(self._d) > MAX_SESSIONS:
                self._d.popitem(last=False)

    def get(self, sid: str):
        with self._lock:
            item = self._d.get(sid)
            if not item or time.time() - item[0] > SESSION_TTL_S:
                self._d.pop(sid, None)
                raise KeyError("sessão expirada ou inexistente")
            return item[1]


class Arena:
    def __init__(self, catalog_db: str, player_db: str, content_dir: Path | None = None) -> None:
        self.catalog_db = catalog_db
        self.bank = bank_mod.load(content_dir)
        errors = bank_mod.validate_structure(self.bank)
        if errors:
            raise ValueError("conteúdo da Arena inválido:\n" + "\n".join(errors))
        self.player = Player(player_db)
        self.sessions = Sessions()
        self.tribunal = tribunal_mod.load()
        terrs = tribunal_mod.validate(self.tribunal, self.bank.normas)
        if terrs:
            raise ValueError("roteiro do Tribunal inválido:\n" + "\n".join(terrs))
        # dublagem opcional (services/arena/tools/vozes.py): <id>.mp3 numa pasta fora do repositório
        self.vozes = Path(os.environ.get("VADE_VOZES") or Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "VadeTribunal" / "vozes")

    def vozes_disponiveis(self) -> list[str]:
        return sorted(p.stem for p in self.vozes.glob("*.mp3")) if self.vozes.is_dir() else []

    def lookup(self, chave: str) -> dict | None:
        """Texto vigente do dispositivo no catálogo (se a norma estiver no recorte importado)."""
        if not Path(self.catalog_db).exists():
            return None
        db = sqlite3.connect(f"file:{self.catalog_db}?mode=ro", uri=True)
        try:
            row = db.execute(
                """SELECT d.rotulo, d.rubrica, d.texto, coalesce(n.sigla, n.nome_popular, n.titulo)
                     FROM dispositivo d JOIN norma n ON n.id = d.norma_id WHERE d.chave = ?""", (chave,)).fetchone()
        except sqlite3.Error:
            return None
        finally:
            db.close()
        if not row:
            return None
        return {"rotulo": row[0], "rubrica": row[1], "texto": row[2], "norma": row[3]}

    # ------------------------------------------------------------ ações
    def concursos(self) -> dict:
        out = []
        for c in self.bank.concursos:
            pool = [q for q in self.bank.questoes if q["formato"] == c["formato"] and q["area"] in c["areas"]]
            out.append({**c, "questoes_no_banco": len(pool)})
        return {"niveis": self.bank.niveis, "concursos": out}

    def casos(self) -> list[dict]:
        best = self.player.profile()["melhor_por_caso"]
        return [{**cases.summary(self.bank, c), "melhor": best.get(c["id"])} for c in self.bank.casos]

    # ------------------------------------------------------------ tribunal
    def episodios(self) -> list[dict]:
        best = self.player.profile()["melhor_por_caso"]
        return [{**tribunal_mod.summary(ep), "melhor": best.get(ep["id"])} for ep in self.tribunal["episodios"]]

    def episodio(self, ep_id: str) -> dict:
        ep = tribunal_mod.episode(self.tribunal, ep_id)
        nome, avatar = self.player.avatar()
        out = tribunal_mod.public_episode(self.tribunal, ep, lambda k: self.lookup(self.bank.resolve(k)), avatar, nome)
        out["salvo"] = self.player.load_trial(ep_id)
        out["marcas"] = sorted(self.player.marks())
        out["minutos"] = tribunal_mod.estimate_minutes(ep)
        return out

    def carreira(self) -> dict:
        won = self.player.profile()["melhor_por_caso"]
        out = tribunal_mod.career(self.tribunal, won, self.player.saved_trials())
        marks = self.player.marks()
        out["marcas"] = sorted(marks)
        texts = tribunal_mod.choice_texts(self.tribunal)
        out["escolhas"] = [{"marca": m, **texts[m]} for m in sorted(marks) if m in texts]
        out["conquistas"] = tribunal_mod.achievements(self.tribunal, won, self.player.perfect_cases(), marks)
        return out

    def salvar_episodio(self, ep_id: str, estado: dict) -> dict:
        ep = tribunal_mod.episode(self.tribunal, ep_id)
        cena = estado.get("cena")
        if cena not in ep["cenas"]:
            raise ValueError("cena inválida")
        provas = {p["id"] for p in ep["provas"]}
        limpo = {"cena": cena, "credibilidade": max(1, min(5, int(estado.get("credibilidade", 5)))),
                 "erros": max(0, min(99, int(estado.get("erros", 0)))),
                 "autos": [a for a in estado.get("autos", []) if a in provas],
                 "marcas": [m for m in estado.get("marcas", []) if m in tribunal_mod.episode_marks(ep)]}
        self.player.save_trial(ep_id, limpo)
        return limpo

    def concluir_episodio(self, ep_id: str, credibilidade, erros, marcas=()) -> dict:
        ep = tribunal_mod.episode(self.tribunal, ep_id)
        result = tribunal_mod.score(ep, credibilidade, erros)
        if result["venceu"]:  # só a escolha de quem chegou ao veredicto vale para a história
            self.player.set_marks(ep_id, tribunal_mod.episode_marks(ep), {str(m) for m in (marcas or [])})
        result["progresso"] = self.player.record_trial(uuid.uuid4().hex, ep, result)
        if result["venceu"]:
            self.player.clear_trial(ep_id)
        return result

    def iniciar_simulado(self, concurso: str, nivel: str) -> dict:
        s = exam.build(self.bank, concurso, nivel, seen=self.player.seen_questions())
        self.sessions.put(s.id, s)
        return exam.public_view(self.bank, s)

    def entregar_simulado(self, sid: str, respostas: dict) -> dict:
        s = self.sessions.get(sid)
        if not isinstance(s, exam.ExamSession):
            raise KeyError("sessão não é de simulado")
        already = s.finished
        result = exam.grade(self.bank, s, respostas or {}, self.lookup)
        if not already:
            result["progresso"] = self.player.record_exam(result)
        return result

    def iniciar_caso(self, caso_id: str) -> dict:
        run = cases.start(self.bank, caso_id)
        self.sessions.put(run.id, run)
        return cases.scene_view(self.bank, run)

    def escolher(self, sid: str, indice: int) -> dict:
        run = self.sessions.get(sid)
        if not isinstance(run, cases.CaseRun):
            raise KeyError("sessão não é de caso")
        out = cases.choose(self.bank, run, indice, self.lookup)
        if "final" in out:
            out["progresso"] = self.player.record_case(run.id, self.bank.caso(run.caso_id), out["final"])
        return out


class ArenaHandler(ingest_server._Handler):
    arena: Arena

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            if path in ("/", "/index.html", "/arena"):
                html = resources.files(__package__).joinpath("web/app.html").read_bytes()
                return self._send(200, html, "text/html; charset=utf-8")
            if path == "/tribunal":
                html = resources.files(__package__).joinpath("web/tribunal.html").read_bytes()
                return self._send(200, html, "text/html; charset=utf-8")
            if path == "/api/arena/tribunal":
                return self._json(self.arena.episodios())
            if path == "/api/arena/vozes":
                return self._json(self.arena.vozes_disponiveis())
            if path.startswith("/voz/"):
                vid = path[5:].removesuffix(".mp3")
                f = self.arena.vozes / f"{vid}.mp3"
                if not re.fullmatch(r"[0-9a-f]{12}", vid) or not f.is_file():
                    return self._json({"erro": "áudio não encontrado"}, 404)
                return self._send(200, f.read_bytes(), "audio/mpeg")
            if path == "/api/arena/carreira":
                return self._json(self.arena.carreira())
            if path.startswith("/api/arena/tribunal/"):
                return self._json(self.arena.episodio(path.rsplit("/", 1)[-1]))
            if path == "/acervo":
                html = resources.files(ingest_server.__package__).joinpath("web/index.html").read_bytes()
                return self._send(200, html, "text/html; charset=utf-8")
            if path == "/api/arena/perfil":
                return self._json(self.arena.player.profile())
            if path == "/api/arena/concursos":
                return self._json(self.arena.concursos())
            if path == "/api/arena/casos":
                return self._json(self.arena.casos())
        except KeyError as exc:
            return self._json({"erro": str(exc).strip("'\"")}, 404)
        except Exception as exc:
            return self._json({"erro": str(exc)}, 500)
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if not path.startswith("/api/arena/"):
            return super().do_POST()
        if self.headers.get("X-Vade") != "1":
            return self._json({"erro": "cabeçalho X-Vade ausente"}, 403)
        try:
            body = self._body()
            if path == "/api/arena/simulado/iniciar":
                return self._json(self.arena.iniciar_simulado(str(body.get("concurso")), str(body.get("nivel"))))
            if path == "/api/arena/simulado/entregar":
                return self._json(self.arena.entregar_simulado(str(body.get("sessao")), body.get("respostas") or {}))
            if path == "/api/arena/tribunal/concluir":
                return self._json(self.arena.concluir_episodio(str(body.get("episodio")), body.get("credibilidade", 0),
                                                               body.get("erros", 0), body.get("marcas") or []))
            if path == "/api/arena/tribunal/salvar":
                return self._json(self.arena.salvar_episodio(str(body.get("episodio")), body.get("estado") or {}))
            if path == "/api/arena/tribunal/recomecar":
                self.arena.player.clear_trial(str(body.get("episodio")))
                return self._json({"ok": True})
            if path == "/api/arena/perfil/avatar":
                avatar = body.get("avatar")
                if not isinstance(avatar, dict) or len(json.dumps(avatar)) > 2000:
                    return self._json({"erro": "avatar inválido"}, 400)
                self.arena.player.set_avatar(str(body.get("nome", "")), avatar)
                return self._json({"ok": True})
            if path == "/api/arena/caso/iniciar":
                return self._json(self.arena.iniciar_caso(str(body.get("caso"))))
            if path == "/api/arena/caso/escolher":
                return self._json(self.arena.escolher(str(body.get("sessao")), int(body.get("indice"))))
            return self._json({"erro": "não encontrado"}, 404)
        except KeyError as exc:
            return self._json({"erro": str(exc).strip("'\"")}, 404)
        except (ValueError, TypeError) as exc:
            return self._json({"erro": str(exc)}, 400)
        except Exception as exc:
            return self._json({"erro": str(exc)}, 500)


def make_server(updater: Updater, arena: Arena, port: int = 8765, host: str = "127.0.0.1"):
    from http.server import ThreadingHTTPServer

    handler = type("Handler", (ArenaHandler,), {"updater": updater, "arena": arena})
    return ThreadingHTTPServer((host, port), handler)
