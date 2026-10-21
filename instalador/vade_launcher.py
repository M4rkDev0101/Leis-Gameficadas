"""Vade Tribunal — instalador e lançador automático (vira VadeTribunal.exe com PyInstaller).

Ao abrir:
  1. se instala em %LOCALAPPDATA%\\VadeTribunal (caminho curto: o Windows limita caminhos a 260
     caracteres) e cria o atalho "Vade Tribunal" na Área de Trabalho;
  2. garante o git (oferece instalar pelo winget se faltar);
  3. baixa/atualiza o jogo (github.com/M4rkDev0101/Leis-Gameficadas);
  4. baixa/atualiza o acervo de leis (github.com/ctresb/leis) em clone parcial, sem os 2,5 GB;
  5. na 1ª vez importa as leis que o jogo usa (content/recorte.json), com barra de progresso;
  6. sobe o servidor local e abre o jogo no navegador; verifica atualizações das leis a cada 30 min.

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

APP_REPO = "https://github.com/M4rkDev0101/Leis-Gameficadas.git"
LEIS_REPO = "https://github.com/ctresb/leis.git"
BASE = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "VadeTribunal"
APP, ACERVO = BASE / "app", BASE / "acervo"
CATALOGO, JOGADOR = BASE / "catalogo.sqlite", BASE / "jogador.sqlite"
EXE_NAME = "VadeTribunal.exe"
PORTA = 8765
NO_WINDOW = 0x08000000 if os.name == "nt" else 0  # git sem piscar janela de console


# ======================================================================== interface (tkinter)
class UI:
    """Janela pequena com etapas e barra de progresso. Sem tkinter, cai para o console."""

    def __init__(self) -> None:
        self.q: queue.Queue = queue.Queue()
        self.ok = False
        try:
            import tkinter as tk
            from tkinter import ttk

            self.tk, self.ttk = tk, ttk
            self.root = tk.Tk()
            self.root.title("Vade Tribunal")
            self.root.geometry("560x330")
            self.root.configure(bg="#14100c")
            self.root.resizable(False, False)
            tk.Label(self.root, text="⚖  Vade Tribunal", font=("Georgia", 22, "bold"), fg="#F5B700", bg="#14100c").pack(pady=(22, 2))
            tk.Label(self.root, text="Preparando o seu tribunal…", font=("Segoe UI", 10), fg="#d9c9a8", bg="#14100c").pack()
            self.step = tk.Label(self.root, text="", font=("Segoe UI", 11, "bold"), fg="#fff4d6", bg="#14100c", wraplength=500)
            self.step.pack(pady=(22, 8))
            style = ttk.Style(self.root)
            style.theme_use("default")
            style.configure("V.Horizontal.TProgressbar", troughcolor="#2a1f16", background="#F5B700", thickness=14)
            self.bar = ttk.Progressbar(self.root, length=480, mode="determinate", style="V.Horizontal.TProgressbar", maximum=100)
            self.bar.pack()
            self.detail = tk.Label(self.root, text="", font=("Consolas", 9), fg="#a3adbd", bg="#14100c", wraplength=500, justify="left")
            self.detail.pack(pady=(10, 0))
            self.btns = tk.Frame(self.root, bg="#14100c")
            self.btns.pack(side="bottom", pady=16)
            self.ok = True
        except Exception:
            self.root = None

    # chamadas da thread de trabalho (thread-safe via fila)
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
        from tkinter import messagebox

        try:
            while True:
                item = self.q.get_nowait()
                if item[0] == "set":
                    _, step, pct, detail = item
                    if step is not None:
                        self.step.config(text=step)
                    if pct is not None:
                        self.bar.config(mode="determinate")
                        self.bar["value"] = pct
                    if detail is not None:
                        self.detail.config(text=detail)
                elif item[0] == "ask":
                    _, title, msg, (ev, box) = item
                    box["v"] = messagebox.askyesno(title, msg, parent=self.root)
                    ev.set()
                elif item[0] == "done":
                    url = item[1]
                    self.step.config(text="Tudo pronto! O jogo abriu no seu navegador.")
                    self.bar["value"] = 100
                    self.detail.config(text=f"{url}\nDeixe esta janela aberta enquanto joga. Fechar a janela encerra o jogo.")
                    self.tk.Button(self.btns, text="Abrir o jogo de novo", command=lambda: webbrowser.open(url),
                                   bg="#F5B700", fg="#1a1206", font=("Segoe UI", 10, "bold"), relief="flat", padx=14, pady=6).pack(side="left", padx=6)
                    self.tk.Button(self.btns, text="Sair", command=self.root.destroy, bg="#30384a", fg="#fff",
                                   font=("Segoe UI", 10, "bold"), relief="flat", padx=14, pady=6).pack(side="left", padx=6)
                elif item[0] == "fail":
                    self.step.config(text="Não consegui terminar.", fg="#ff8a80")
                    self.detail.config(text=item[1])
                    self.tk.Button(self.btns, text="Fechar", command=self.root.destroy, bg="#30384a", fg="#fff",
                                   relief="flat", padx=14, pady=6).pack()
        except queue.Empty:
            pass
        self.root.after(120, self._pump)

    def run(self, worker) -> None:
        if not self.ok:
            worker()
            return
        threading.Thread(target=worker, daemon=True).start()
        self.root.after(120, self._pump)
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
        r = git("pull", "--ff-only", "-q", cwd=APP, timeout=180)
        ui.set(detail="jogo atualizado" if r.returncode == 0 else "sem internet ou sem atualização: usando a versão instalada")
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


def main() -> None:
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
