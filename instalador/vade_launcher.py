"""Vade Tribunal — instalador e lançador automático (vira VadeTribunal.exe com PyInstaller).

Ao abrir:
  1. se instala em %LOCALAPPDATA%\\VadeTribunal (caminho curto: o Windows limita caminhos a 260
     caracteres) e cria o atalho "Vade Tribunal" na Área de Trabalho;
  2. garante o git (oferece instalar pelo winget se faltar);
  3. baixa/atualiza o jogo (github.com/M4rkDev0101/Leis-Gameficadas);
  4. baixa/atualiza o acervo de leis (github.com/ctresb/leis) em clone parcial, sem os 2,5 GB;
  5. na 1ª vez importa as leis que o jogo usa (content/recorte.json), com barra de progresso;
  6. dublagem opcional: oferece baixar o pacote de vozes (release `vozes-vN`) e o atualiza depois;
  7. sobe o servidor local e abre o jogo no navegador; verifica atualizações das leis a cada 30 min.

O código do jogo NÃO vai dentro do .exe: ele é baixado com git e atualizado a cada abertura, então
o mesmo .exe continua servindo quando o jogo ganha conteúdo novo. O .exe traz só o Python e a
biblioteca padrão (por isso a lista de imports abaixo, que garante que o PyInstaller os inclua).
"""

from __future__ import annotations

# --- biblioteca padrão usada pelo jogo (o PyInstaller só empacota o que é importado aqui) ---
import argparse  # noqa: F401
import collections  # noqa: F401
import copy  # noqa: F401
import dataclasses  # noqa: F401
import datetime  # noqa: F401
import email.utils  # noqa: F401
import enum  # noqa: F401
import functools  # noqa: F401
import hashlib  # noqa: F401
import html  # noqa: F401
import http.server  # noqa: F401
import importlib.resources  # noqa: F401
import json
import math  # noqa: F401
import os
import queue
import random  # noqa: F401
import re  # noqa: F401
import shutil
import socket
import sqlite3  # noqa: F401
import subprocess
import sys
import threading
import time
import unicodedata  # noqa: F401
import urllib.parse  # noqa: F401
import urllib.request
import uuid  # noqa: F401
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vozes_pacote  # noqa: E402  (dublagem opcional; o PyInstaller o inclui a partir daqui)

APP_REPO = "https://github.com/M4rkDev0101/Leis-Gameficadas.git"
LEIS_REPO = "https://github.com/ctresb/leis.git"
BASE = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "VadeTribunal"
APP, ACERVO = BASE / "app", BASE / "acervo"
CATALOGO, JOGADOR = BASE / "catalogo.sqlite", BASE / "jogador.sqlite"
VOZES = Path(os.environ.get("VADE_VOZES") or BASE / "vozes")  # mesma regra do servidor do jogo
CONFIG = BASE / "config.json"
EXE_NAME = "VadeTribunal.exe"
PORTA = 8765
NO_WINDOW = 0x08000000 if os.name == "nt" else 0  # git sem piscar janela de console


# ======================================================================== interface (tkinter)
class UI:
    """Janela do lançador no estilo do sistema (docs/design_vade.md): tela escura, logotipo dourado, etapas com
    estado, barra fina e diálogos dentro da própria janela. Sem tkinter, cai para o console."""

    # tokens do guia visual
    BG, SURF, SURF2, LINE = "#0B0D11", "#181C24", "#222833", "#2C3340"
    TEXT, MUTED, FAINT = "#ECEEF2", "#9AA3B2", "#6B7383"
    GOLD, GOLD2, ON_GOLD = "#D4A24C", "#E8BE6A", "#16110A"
    OK, BAD = "#3FBF7F", "#E5534B"
    W, H = 640, 540
    # etapas mostradas na lista: (rótulo, porcentagem em que começa)
    STAGES = (("Verificar o computador", 0), ("Instalar e atualizar o jogo", 5), ("Acervo de leis", 25),
              ("Importar as leis", 35), ("Dublagem (opcional)", 90), ("Abrir o tribunal", 97))

    def __init__(self) -> None:
        self.q: queue.Queue = queue.Queue()
        self.ok = False
        try:
            if os.name == "nt":  # DPI correto: sem isso o Windows estica a janela e o texto fica borrado
                import ctypes

                try:
                    ctypes.windll.shcore.SetProcessDpiAwareness(2)
                except Exception:
                    ctypes.windll.user32.SetProcessDPIAware()
            import tkinter as tk

            self.tk = tk
            self.root = tk.Tk()
            self.k = max(1.0, self.root.winfo_fpixels("1i") / 96)  # fator de escala de pixels
            self.root.title("Vade Tribunal")
            self.root.configure(bg=self.BG)
            self.root.resizable(False, False)
            w, h = self.s(self.W), self.s(self.H)
            x = max(0, (self.root.winfo_screenwidth() - w) // 2)
            y = max(0, (self.root.winfo_screenheight() - h) // 3)
            self.root.geometry(f"{w}x{h}+{x}+{y}")
            self.cv = tk.Canvas(self.root, width=w, height=h, bg=self.BG, highlightthickness=0, bd=0)
            self.cv.pack(fill="both", expand=True)
            self.root.protocol("WM_DELETE_WINDOW", self._close)
            self.stage_i, self.pct, self.shown = 0, 0.0, 0.0
            self.step_txt = ""
            self.detail_txt = ""
            self.state = "run"  # run | done | fail
            self.headline = "Preparando o seu tribunal…"
            self.ask_state: tuple | None = None
            self.hover: str | None = None
            self.angle = 0
            self.btns: list[tuple] = []  # (rótulo, tipo, tag, comando)
            self._logo()
            self._redraw_all()
            self.root.bind("<Return>", lambda e: self._key("primary"))
            self.root.bind("<Escape>", lambda e: self._key("secondary"))
            self.ok = True
        except Exception:
            self.root = None

    # ------------------------------------------------------------------ desenho
    def s(self, v: float) -> int:
        return int(round(v * getattr(self, "k", 1.0)))

    @staticmethod
    def _font(fam: str, size: float, style: str = "") -> tuple:
        return (fam, size, style) if style else (fam, size)

    def _logo(self) -> None:
        cv, s = self.cv, self.s
        cx = s(self.W / 2)
        cv.create_text(cx, s(66), text="V A D E     T R I B U N A L", fill=self.TEXT,
                       font=self._font("Segoe UI", 15, "bold"), tags="logo")
        cv.create_line(cx - s(26), s(94), cx + s(26), s(94), fill=self.GOLD, width=max(2, s(2)), capstyle="round", tags="logo")

    @staticmethod
    def _rr_pts(x1, y1, x2, y2, r) -> list:
        r = min(r, (x2 - x1) / 2, (y2 - y1) / 2)
        return [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2, x2 - r, y2,
                x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]

    def _rr(self, x1, y1, x2, y2, r, **kw) -> int:
        return self.cv.create_polygon(self._rr_pts(x1, y1, x2, y2, r), smooth=True, **kw)

    def _redraw_all(self) -> None:
        self._draw_head()
        self._draw_steps()
        self._draw_bar()
        self._draw_buttons()
        self._draw_ask()

    def _draw_head(self) -> None:
        cv, s = self.cv, self.s
        cv.delete("head")
        col = self.BAD if self.state == "fail" else self.GOLD2 if self.state == "done" else self.MUTED
        cv.create_text(s(self.W / 2), s(128), text=self.headline, fill=col, font=self._font("Georgia", 12, "italic"), tags="head")

    def _stage_state(self, i: int) -> str:
        if self.state == "done" or i < self.stage_i:
            return "ok"
        if i == self.stage_i:
            return "bad" if self.state == "fail" else "run"
        return "pend"

    def _draw_steps(self) -> None:
        cv, s = self.cv, self.s
        cv.delete("steps")
        x0, y0, dy = s(96), s(186), s(36)
        w2 = max(2, s(2))
        for i, (label, _) in enumerate(self.STAGES):
            st = self._stage_state(i)
            y = y0 + i * dy
            cx, r = x0 + s(10), s(9)
            box = (cx - r, y - r, cx + r, y + r)
            if st == "ok":
                cv.create_oval(*box, fill=self.OK, outline="", tags="steps")
                cv.create_line(cx - s(4), y, cx - s(1), y + s(3.5), cx + s(5), y - s(3.5), fill=self.BG, width=w2,
                               capstyle="round", joinstyle="round", tags="steps")
            elif st == "run":
                cv.create_oval(*box, outline=self.LINE, width=w2, tags="steps")
                cv.create_arc(*box, start=self.angle, extent=110, style="arc", outline=self.GOLD, width=w2, tags="steps")
            elif st == "bad":
                cv.create_oval(*box, fill=self.BAD, outline="", tags="steps")
                d = s(3.5)
                cv.create_line(cx - d, y - d, cx + d, y + d, fill=self.BG, width=w2, capstyle="round", tags="steps")
                cv.create_line(cx - d, y + d, cx + d, y - d, fill=self.BG, width=w2, capstyle="round", tags="steps")
            else:
                cv.create_oval(*box, outline=self.LINE, width=max(1, s(1.5)), tags="steps")
            active = st in ("run", "bad")
            text = self.step_txt if (st == "run" and self.step_txt) else label
            col = self.TEXT if active else self.MUTED if st == "ok" else self.FAINT
            cv.create_text(x0 + s(34), y, text=text, anchor="w", fill=col,
                           font=self._font("Segoe UI", 11, "bold" if active else ""), width=s(430), tags="steps")
        cv.tag_raise("ov")

    def _draw_bar(self) -> None:
        cv, s = self.cv, self.s
        cv.delete("bar")
        cv.delete("detail")
        x1, x2, y = s(96), s(self.W - 96), s(418)
        wid = max(4, s(6))
        cv.create_line(x1, y, x2, y, fill=self.SURF2, width=wid, capstyle="round", tags="bar")
        frac = max(0.0, min(1.0, self.shown / 100))
        if frac > 0.004:
            cv.create_line(x1, y, x1 + (x2 - x1) * frac, y, fill=self.GOLD, width=wid, capstyle="round", tags="bar")
        cv.create_text(x2, y + s(18), text=f"{int(self.shown)}%", anchor="ne", fill=self.FAINT,
                       font=self._font("Segoe UI", 9), tags="bar")
        cv.create_text(x1, y + s(18), text=self.detail_txt, anchor="nw", fill=self.MUTED if self.state == "fail" else self.FAINT,
                       font=self._font("Segoe UI", 9), width=s(400), tags="detail")
        cv.tag_raise("ov")

    def _button(self, cx, cy, w, h, label, kind, tag, cmd) -> None:
        cv, s = self.cv, self.s
        hov = self.hover == tag
        x1, y1, x2, y2 = cx - s(w / 2), cy - s(h / 2), cx + s(w / 2), cy + s(h / 2)
        if kind == "primary":
            self._rr(x1, y1, x2, y2, s(8), fill=self.GOLD2 if hov else self.GOLD, outline="", tags=(tag, "btns"))
            fg = self.ON_GOLD
        else:
            self._rr(x1, y1, x2, y2, s(8), fill=self.SURF if hov else self.BG, outline=self.GOLD2 if hov else self.LINE,
                     width=max(1, s(1.5)), tags=(tag, "btns"))
            fg = self.TEXT
        cv.create_text(cx, cy, text=label, fill=fg, font=self._font("Segoe UI", 10, "bold"), tags=(tag, "btns"))
        cv.tag_bind(tag, "<Button-1>", lambda e, c=cmd: c())
        cv.tag_bind(tag, "<Enter>", lambda e, t=tag: self._hover(t))
        cv.tag_bind(tag, "<Leave>", lambda e: self._hover(None))

    def _hover(self, tag: str | None) -> None:
        self.hover = tag
        self.cv.config(cursor="hand2" if tag else "")
        self._draw_buttons()
        self._draw_ask(relayout=False)

    def _layout_buttons(self, cx, cy, specs) -> None:
        widths = [max(112, 24 + 8 * len(sp[0])) for sp in specs]
        gap = 14
        x = cx - self.s((sum(widths) + gap * (len(specs) - 1)) / 2)
        for sp, w in zip(specs, widths):
            self._button(x + self.s(w / 2), cy, w, 40, sp[0], sp[1], sp[2], sp[3])
            x += self.s(w + gap)

    def _draw_buttons(self) -> None:
        self.cv.delete("btns")
        if self.ask_state or not self.btns:
            return
        self._layout_buttons(self.s(self.W / 2), self.s(500), self.btns)

    def _draw_ask(self, relayout: bool = True) -> None:
        cv, s = self.cv, self.s
        cv.delete("ov")
        if not self.ask_state:
            return
        title, msg, _ = self.ask_state
        accent = self.BAD if self.state == "fail" else self.GOLD
        cv.create_rectangle(0, s(112), s(self.W), s(self.H), fill=self.BG, outline="", tags="ov")
        cx, x1, x2, top = s(self.W / 2), s(60), s(self.W - 60), s(170)
        card = self._rr(x1, top, x2, top + 10, s(16), fill=self.SURF, outline=self.LINE, tags="ov")
        cv.create_text(x1 + s(32), top + s(30), text=title, anchor="nw", fill=self.TEXT,
                       font=self._font("Georgia", 16), width=s(456), tags="ov")
        m = cv.create_text(x1 + s(32), top + s(72), text=msg, anchor="nw", fill=self.MUTED,
                           font=self._font("Segoe UI", 10), width=s(456), tags="ov")
        by = cv.bbox(m)[3] + s(46)
        cv.coords(card, *self._rr_pts(x1, top, x2, by + s(34), s(16)))
        cv.create_line(x1 + s(32), top + s(1), x2 - s(32), top + s(1), fill=accent, width=max(2, s(2)), tags="ov")
        if self.state == "fail":
            specs = [("Fechar", "primary", "b_close", self.root.destroy)]
        else:
            specs = [("Sim", "primary", "ask_yes", lambda: self._answer(True)),
                     ("Agora não", "secondary", "ask_no", lambda: self._answer(False))]
        self._layout_buttons(cx, by, specs)
        cv.addtag_withtag("ov", "btns")

    # ------------------------------------------------------------------ interação
    def _answer(self, v: bool) -> None:
        if not self.ask_state:
            return
        ev, box = self.ask_state[2]
        box["v"] = v
        self.ask_state = None
        self.hover = None
        self.cv.config(cursor="")
        self._draw_ask()
        self._draw_buttons()
        ev.set()

    def _key(self, which: str) -> None:
        if self.state == "fail":
            if which == "primary":
                self.root.destroy()
            return
        if self.ask_state:
            self._answer(which == "primary")
            return
        for _, kind, _, cmd in self.btns:
            if kind == which:
                cmd()
                return

    def _close(self) -> None:
        if self.ask_state and self.state != "fail":  # quem espera a resposta não pode ficar preso
            self._answer(False)
        self.root.destroy()

    def _tick(self) -> None:
        try:
            if self.state == "run":
                self.angle = (self.angle - 14) % 360
                self._draw_steps()
            diff = self.pct - self.shown
            if abs(diff) > 0.05:
                self.shown += diff * 0.25 if abs(diff) > 0.4 else diff
                self._draw_bar()
            self.root.after(40, self._tick)
        except self.tk.TclError:
            pass  # janela fechada

    # ------------------------------------------------------------------ API pública (thread-safe via fila)
    def set(self, step: str | None = None, pct: float | None = None, detail: str | None = None) -> None:
        if not self.ok:
            print(" · ".join(x for x in (step, f"{pct:.0f}%" if pct is not None else None, detail) if x))
            return
        self.q.put(("set", step, pct, detail))

    def ask(self, title: str, msg: str) -> bool:
        if not self.ok:
            return input(f"{msg} [s/N] ").strip().lower().startswith("s")
        ev, box = threading.Event(), {}
        self.q.put(("ask", title, msg, (ev, box)))
        ev.wait()
        return box.get("v", False)

    def done(self, url: str) -> None:
        if not self.ok:
            print(f"Jogo aberto em {url}. Ctrl+C para encerrar.")
            return
        self.q.put(("done", url))

    def fail(self, msg: str) -> None:
        if not self.ok:
            print("ERRO:", msg)
            return
        self.q.put(("fail", msg))

    def _pump(self) -> None:
        try:
            while True:
                item = self.q.get_nowait()
                if item[0] == "set":
                    _, step, pct, detail = item
                    if pct is not None:
                        self.pct = float(pct)
                        idx = max(i for i, (_, p0) in enumerate(self.STAGES) if p0 <= self.pct)
                        if idx != self.stage_i:
                            self.stage_i, self.step_txt = idx, ""
                    if step is not None:
                        self.step_txt = step
                    if detail is not None:
                        self.detail_txt = detail
                    self._draw_steps()
                    self._draw_bar()
                elif item[0] == "ask":
                    _, title, msg, (ev, box) = item
                    self.ask_state = (title, msg, (ev, box))
                    self._draw_buttons()
                    self._draw_ask()
                elif item[0] == "done":
                    url = item[1]
                    self.state, self.pct, self.step_txt = "done", 100.0, ""
                    self.headline = "Tudo pronto. O jogo abriu no seu navegador."
                    self.detail_txt = f"{url}\nDeixe esta janela aberta enquanto joga. Fechar a janela encerra o jogo."
                    self.btns = [("Abrir o jogo de novo", "primary", "b_open", lambda: webbrowser.open(url)),
                                 ("Sair", "secondary", "b_exit", self.root.destroy)]
                    self._redraw_all()
                elif item[0] == "fail":
                    self.state = "fail"
                    self.headline = "Não consegui terminar."
                    self.ask_state = ("Não consegui terminar", str(item[1]), None)  # cartão de erro
                    self.btns = []
                    self._redraw_all()
        except queue.Empty:
            pass
        except self.tk.TclError:
            return  # janela fechada
        self.root.after(100, self._pump)

    def run(self, worker) -> None:
        if not self.ok:
            worker()
            return
        threading.Thread(target=worker, daemon=True).start()
        self.root.after(100, self._pump)
        self.root.after(40, self._tick)
        self.root.mainloop()


# ======================================================================== etapas
def git(*args: str, cwd: Path | None = None, timeout: int = 3600) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-c", "core.longpaths=true", *args], cwd=str(cwd) if cwd else None,
                          capture_output=True, text=True, timeout=timeout, creationflags=NO_WINDOW)


def ensure_git(ui: UI) -> None:
    if shutil.which("git"):
        return
    for p in (r"C:\Program Files\Git\cmd\git.exe", r"C:\Program Files (x86)\Git\cmd\git.exe"):
        if Path(p).exists():
            os.environ["PATH"] = str(Path(p).parent) + os.pathsep + os.environ["PATH"]
            return
    if not shutil.which("winget"):
        webbrowser.open("https://git-scm.com/download/win")
        raise RuntimeError("O jogo precisa do Git. Abri a página de download: instale e abra o Vade Tribunal de novo.")
    if not ui.ask("Instalar o Git?", "O Vade Tribunal usa o Git para baixar e atualizar as leis.\n\n"
                  "Posso instalar o Git agora pelo winget (instalador oficial do Windows)?"):
        raise RuntimeError("Sem o Git não dá para baixar as leis. Instale o Git e abra o jogo de novo.")
    ui.set("Instalando o Git…", 5, "winget install Git.Git")
    r = subprocess.run(["winget", "install", "--id", "Git.Git", "-e", "--source", "winget",
                        "--accept-package-agreements", "--accept-source-agreements", "--silent"],
                       capture_output=True, text=True, creationflags=NO_WINDOW)
    os.environ["PATH"] = r"C:\Program Files\Git\cmd" + os.pathsep + os.environ["PATH"]
    if not shutil.which("git"):
        raise RuntimeError("A instalação do Git não terminou:\n" + (r.stdout + r.stderr)[-400:])


def sync_app(ui: UI) -> None:
    if (APP / ".git").exists():
        ui.set("Procurando atualizações do jogo…", 12)
        # fetch + reset em vez de pull: uma atualização interrompida (arquivos novos soltos, objeto
        # faltando no clone raso) se conserta sozinha na próxima abertura
        quiet = ("-c", "gc.auto=0", "-c", "maintenance.auto=false")
        r = git(*quiet, "fetch", "--depth", "1", "-q", "origin", "main", cwd=APP, timeout=300)
        if r.returncode == 0:
            r = git("reset", "-q", "--hard", "FETCH_HEAD", cwd=APP, timeout=120)
            git("clean", "-fdq", cwd=APP, timeout=120)
        ui.set(detail="jogo atualizado" if r.returncode == 0 else "sem internet: usando a versão instalada")
        return
    ui.set("Baixando o jogo…", 10, APP_REPO)
    BASE.mkdir(parents=True, exist_ok=True)
    r = git("clone", "--depth", "1", APP_REPO, str(APP), timeout=600)
    if r.returncode != 0:
        raise RuntimeError("Não consegui baixar o jogo. Verifique a internet.\n" + r.stderr[-400:])


def sync_acervo(ui: UI) -> None:
    if (ACERVO / ".git").exists():
        return  # o próprio jogo verifica e baixa atualizações das leis (botão e verificação automática)
    ui.set("Baixando o índice do acervo de leis…", 25, "clone parcial: só a lista de arquivos, sem o conteúdo (rápido)")
    r = git("clone", "--filter=blob:none", "--no-checkout", "--depth", "1", LEIS_REPO, str(ACERVO), timeout=3600)
    if r.returncode != 0:
        raise RuntimeError("Não consegui baixar o acervo de leis.\n" + r.stderr[-400:])


def load_game_modules() -> None:
    for pkg in ("ingest", "learning", "arena"):
        p = str(APP / "services" / pkg / "src")
        if p not in sys.path:
            sys.path.insert(0, p)


def first_import(ui: UI) -> None:
    from vade_ingest.loader import Catalog
    from vade_ingest.updater import Updater

    upd = Updater(ACERVO, CATALOGO)
    cat = Catalog(CATALOGO)
    try:
        needs = cat.get("ultimo_commit") is None or cat.counts()["normas"] == 0
    finally:
        cat.close()
    if not needs:
        return
    rec = json.loads((APP / "services" / "arena" / "src" / "vade_arena" / "content" / "recorte.json").read_text(encoding="utf-8"))
    if not upd.recorte():
        upd.set_recorte(rec["prefixos"])
    ui.set("Importando as leis do jogo (só na primeira vez)…", 35, "Constituição, códigos, leis especiais e súmulas")
    upd.start_update()
    while True:
        j = upd.job()
        if j["estado"] != "rodando":
            break
        pct = 35 + (60 * j["feito"] / j["total"] if j["total"] else 0)
        ui.set(pct=pct, detail=f"{j['etapa']}: {j['feito']}/{j['total']}" if j["total"] else f"{j['etapa']}…")
        time.sleep(0.4)
    if j["estado"] == "erro":
        raise RuntimeError("A importação das leis falhou:\n" + str(j["erro"])[-400:])


def sync_vozes(ui: UI) -> None:
    """Dublagem opcional: pacote de vozes publicado como release `vozes-vN` (nunca vai para o git do jogo).
    Qualquer falha é ignorada: sem pacote/sem internet o jogo segue com bipes. `--vozes` pergunta de novo."""
    api = os.environ.get("VADE_VOZES_API") or vozes_pacote.REPO_API
    ui.set("Verificando a dublagem…", 90)

    def dizer(texto: str, frac: float) -> None:
        ui.set(step="Baixando a dublagem (opcional)…" if frac < 1 else None, pct=90 + 6 * frac, detail=texto)

    r = vozes_pacote.sincronizar(VOZES, CONFIG, ui.ask, dizer, api, forcar="--vozes" in sys.argv)
    if r == "instalada":
        ui.set(detail="dublagem instalada")


def port_free(p: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", p)) != 0


def already_running(p: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{p}/api/arena/perfil", timeout=1.5) as r:
            return r.status == 200
    except Exception:
        return False


def start_server(ui: UI) -> str:
    if already_running(PORTA):
        return f"http://127.0.0.1:{PORTA}/tribunal"
    from vade_arena.server import Arena, make_server
    from vade_ingest.server import start_auto_check
    from vade_ingest.updater import Updater

    port = next(p for p in range(PORTA, PORTA + 20) if port_free(p))
    upd = Updater(ACERVO, CATALOGO)
    srv = make_server(upd, Arena(str(CATALOGO), str(JOGADOR)), port)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    start_auto_check(upd, 30, auto_update=True)  # leis novas entram sozinhas a cada 30 min
    return f"http://127.0.0.1:{port}/tribunal"


def install_self(ui: UI) -> None:
    """Copia o .exe para a pasta do jogo e cria o atalho na Área de Trabalho (só no .exe)."""
    if not getattr(sys, "frozen", False) or os.name != "nt":
        return
    BASE.mkdir(parents=True, exist_ok=True)
    me = Path(sys.executable)
    target = BASE / EXE_NAME
    if me.resolve() != target.resolve():
        try:
            shutil.copy2(me, target)
        except OSError:
            target = me  # em uso: o atalho aponta para onde está
    lnk = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop" / "Vade Tribunal.lnk"
    if lnk.exists():
        return
    ps = (f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{lnk}');"
          f"$s.TargetPath='{target}';$s.WorkingDirectory='{BASE}';$s.Description='Vade Tribunal';$s.Save()")
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
                   capture_output=True, creationflags=NO_WINDOW)


def redirect_logs() -> None:
    """Sem console (atalho/duplo clique), sys.stdout/stderr são None: mande os logs para um arquivo."""
    if sys.stdout is None or sys.stderr is None:
        BASE.mkdir(parents=True, exist_ok=True)
        log = open(BASE / "vade.log", "a", encoding="utf-8", buffering=1)  # noqa: SIM115
        sys.stdout = sys.stdout or log
        sys.stderr = sys.stderr or log


def main() -> None:
    redirect_logs()
    ui = UI()

    def worker() -> None:
        try:
            ui.set("Verificando o computador…", 2)
            install_self(ui)
            ensure_git(ui)
            sync_app(ui)
            sync_acervo(ui)
            load_game_modules()
            first_import(ui)
            sync_vozes(ui)
            ui.set("Abrindo o tribunal…", 97)
            url = start_server(ui)
            webbrowser.open(url)
            ui.done(url)
            if not ui.ok:  # modo console: mantém o servidor vivo
                while True:
                    time.sleep(3600)
        except Exception as exc:  # mensagem amigável na janela
            ui.fail(str(exc))

    ui.run(worker)


if __name__ == "__main__":
    main()
