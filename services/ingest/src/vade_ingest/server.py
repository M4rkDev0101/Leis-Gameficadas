"""Servidor local do painel do acervo (só biblioteca padrão).

    python -m vade_ingest serve --repo ACERVO --db catalogo.sqlite [--porta 8765] [--verificar-a-cada 15] [--atualizar-auto]

Escuta só em 127.0.0.1. Rotas que alteram estado (POST) exigem o cabeçalho ``X-Vade: 1``: um
site de terceiros não consegue enviá-lo sem preflight CORS, que este servidor nunca autoriza.
Isso impede que uma página aberta no navegador dispare atualizações no seu computador.
"""

from __future__ import annotations

import json
import re
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from urllib.parse import parse_qs, urlparse

from .loader import Catalog
from .updater import Updater


def fts_query(text: str) -> str | None:
    """Texto livre → consulta FTS5 segura (cada palavra entre aspas, prefixo na última)."""
    words = re.findall(r"\w+", text, flags=re.UNICODE)
    if not words:
        return None
    parts = [f'"{w}"' for w in words[:12]]
    parts[-1] += "*"
    return " ".join(parts)


class _Handler(BaseHTTPRequestHandler):
    updater: Updater  # definido em make_server
    server_version = "Vade/0.1"

    def log_message(self, fmt: str, *args) -> None:  # silencioso, menos o essencial
        if not self.path.startswith("/api/job"):
            super().log_message(fmt, *args)

    # ---------------------------------------------------------------- respostas
    def _send(self, status: int, body: bytes, ctype: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data, status: int = 200) -> None:
        self._send(status, json.dumps(data, ensure_ascii=False, default=str).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        return json.loads(self.rfile.read(min(n, 1_000_000)) or b"{}")

    # ---------------------------------------------------------------- GET
    def do_GET(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        try:
            if url.path in ("/", "/index.html"):
                html = resources.files(__package__).joinpath("web/index.html").read_bytes()
                return self._send(200, html, "text/html; charset=utf-8")
            if url.path == "/api/status":
                return self._json(self.updater.status())
            if url.path == "/api/job":
                return self._json(self.updater.job())
            if url.path == "/api/busca":
                q = fts_query(parse_qs(url.query).get("q", [""])[0])
                if not q:
                    return self._json([])
                cat = Catalog(self.updater.db)
                try:
                    hits = cat.search(q, 20)
                    if not hits and " " in q:  # nenhuma linha tem todas as palavras: aceita qualquer uma
                        hits = cat.search(q.replace(" ", " OR "), 20)
                    return self._json([dict(r) for r in hits])
                finally:
                    cat.close()
            if url.path == "/api/arvore":
                prefix = parse_qs(url.query).get("prefixo", [""])[0].strip("/")
                return self._json(self.updater._source().children(prefix))
            return self._json({"erro": "não encontrado"}, 404)
        except Exception as exc:
            return self._json({"erro": str(exc)}, 500)

    # ---------------------------------------------------------------- POST
    def do_POST(self) -> None:  # noqa: N802
        if self.headers.get("X-Vade") != "1":
            return self._json({"erro": "cabeçalho X-Vade ausente"}, HTTPStatus.FORBIDDEN)
        url = urlparse(self.path)
        try:
            body = self._body()
            if url.path == "/api/verificar":
                from dataclasses import asdict
                return self._json(asdict(self.updater.check()))
            if url.path == "/api/atualizar":
                started = self.updater.start_update(full=bool(body.get("completo")), allow_all=bool(body.get("tudo")))
                return self._json({"iniciado": started, "job": self.updater.job()}, 202 if started else 409)
            if url.path == "/api/recorte":
                prefixes = body.get("prefixos")
                if not isinstance(prefixes, list) or not all(isinstance(p, str) for p in prefixes):
                    return self._json({"erro": "prefixos deve ser uma lista de textos"}, 400)
                self.updater.set_recorte(prefixes)
                return self._json({"recorte": self.updater.recorte()})
            return self._json({"erro": "não encontrado"}, 404)
        except ValueError as exc:
            return self._json({"erro": str(exc)}, 400)
        except Exception as exc:
            return self._json({"erro": str(exc)}, 500)


def make_server(updater: Updater, port: int = 8765, host: str = "127.0.0.1") -> ThreadingHTTPServer:
    handler = type("Handler", (_Handler,), {"updater": updater})
    return ThreadingHTTPServer((host, port), handler)


def start_auto_check(updater: Updater, minutes: float, auto_update: bool) -> threading.Thread:
    """Verifica a cada N minutos. Com auto_update, aplica sozinho quando há mudança no recorte.

    Como o acervo muda a cada poucos minutos, um intervalo de 15–60 min agrupa vários commits num
    único diff, o que é bem mais barato do que reagir a cada commit."""

    def loop() -> None:
        while True:
            try:
                r = updater.check()
                if auto_update and not r.atualizado and (r.no_recorte or r.primeira_importacao):
                    if updater.recorte():
                        updater.start_update()
            except Exception as exc:  # rede fora do ar etc.: tenta de novo no próximo ciclo
                print(f"[verificação automática] {exc!r}")
            time.sleep(max(1.0, minutes) * 60)

    t = threading.Thread(target=loop, daemon=True)
    t.start()
    return t
