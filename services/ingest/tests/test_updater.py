"""Botão "Verificar atualização": um repositório local faz o papel do GitHub (ctresb/leis) e
recebe commits durante o teste; o acervo é um clone parcial dele, como em produção."""

import json
import shutil
import subprocess
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

from vade_ingest.server import fts_query, make_server
from vade_ingest.sources import GitSource
from vade_ingest.updater import Updater

from test_loader import CP, LEI_UTIL, SUMULA, write


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


def commit(repo: Path, msg: str) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", msg)


@unittest.skipUnless(shutil.which("git"), "git não instalado")
class UpdaterTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.up = self.tmp / "github"
        self.up.mkdir()
        git(self.up, "init", "-q", "-b", "main")
        git(self.up, "config", "user.email", "t@t")
        git(self.up, "config", "user.name", "t")
        git(self.up, "config", "uploadpack.allowFilter", "true")
        git(self.up, "config", "uploadpack.allowAnySHA1InWant", "true")
        write(self.up, "federal/decretos-lei/1940/del-2848-1940-12-07.md", CP)
        write(self.up, "jurisprudencia/stj/sumulas/sumula-999.md", SUMULA)
        commit(self.up, "c1")
        self.acervo = self.tmp / "acervo"
        subprocess.run(["git", "clone", "-q", "--filter=blob:none", "--no-checkout",
                        self.up.as_uri(), str(self.acervo)], check=True, capture_output=True)
        self.u = Updater(self.acervo, self.tmp / "cat.sqlite")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestUpdater(UpdaterTestBase):
    def test_full_cycle(self):
        with self.assertRaises(ValueError):  # recorte vazio importaria tudo
            self.u.run_update_blocking()

        self.u.set_recorte(["federal"])
        r = self.u.check()
        self.assertTrue(r.primeira_importacao)
        self.assertEqual(r.no_recorte, 1)

        job = self.u.run_update_blocking()
        self.assertEqual((job["estado"], job["resultado"]["inserted"]), ("concluido", 1))
        self.assertTrue(self.u.check().atualizado)

        # o "GitHub" recebe um commit: muda o CP e cria uma lei estadual fora do recorte
        write(self.up, "federal/decretos-lei/1940/del-2848-1940-12-07.md", CP + "\n**Art. 26.** É isento de pena.\n")
        write(self.up, "estaduais/MG/leis-ordinarias/2019/lei-1-2019.md", LEI_UTIL)
        commit(self.up, "Acrescenta normas")
        r = self.u.check()
        self.assertFalse(r.atualizado)
        self.assertEqual((r.commits_novos, r.arquivos_alterados, r.no_recorte), (1, 2, 1))
        self.assertEqual(r.commits[0]["mensagem"], "Acrescenta normas")
        self.assertEqual(dict(r.por_area), {"federal/decretos-lei": 1, "estaduais/MG": 1})

        job = self.u.run_update_blocking()
        self.assertEqual(job["resultado"]["updated"], 1)
        self.assertEqual(job["resultado"]["changed"][0]["acao"], "alterada")
        st = self.u.status()
        self.assertEqual(st["contagens"]["normas"], 1)  # a estadual ficou de fora
        self.assertEqual(st["commit_local"]["sha"], git(self.up, "rev-parse", "HEAD"))
        self.assertEqual(len(st["historico"]), 2)

    def test_several_commits_collapse_into_one_diff(self):
        self.u.set_recorte(["federal"])
        self.u.run_update_blocking()
        for i in range(5):
            write(self.up, "federal/decretos-lei/1940/del-2848-1940-12-07.md", CP + f"\n**Art. {30 + i}.** Texto {i}.\n")
            commit(self.up, f"c{i}")
        r = self.u.check()
        self.assertEqual((r.commits_novos, r.arquivos_alterados), (5, 1))
        job = self.u.run_update_blocking()
        self.assertEqual(job["resultado"]["updated"], 1)  # 5 commits, 1 reimportação

    def test_scope_changes_after_first_import(self):
        self.u.set_recorte(["federal"])
        self.u.run_update_blocking()
        # adicionar pasta que não mudou no GitHub: precisa entrar mesmo sem diff
        self.u.set_recorte(["federal", "jurisprudencia"])
        r = self.u.check()
        self.assertFalse(r.atualizado)
        self.assertEqual((r.recorte_adicionar, r.no_recorte), (["jurisprudencia"], 1))
        job = self.u.run_update_blocking()
        self.assertEqual(job["resultado"]["inserted"], 1)
        self.assertTrue(self.u.check().atualizado)
        # remover pasta: as normas dela saem
        self.u.set_recorte(["jurisprudencia"])
        job = self.u.run_update_blocking()
        self.assertEqual(job["resultado"]["deleted"], 1)
        self.assertEqual(self.u.status()["contagens"]["normas"], 1)

    def test_unavailable_blob_is_failure_and_retried(self):
        self.u.set_recorte(["federal"])
        self.u.run_update_blocking()
        write(self.up, "federal/decretos-lei/1940/del-2848-1940-12-07.md", CP + "\n**Art. 26.** Novo.\n")
        commit(self.up, "c2")

        def offline(self_src, entries):  # rede caiu no meio: nenhum conteúdo chega
            for e in entries:
                yield e, None

        with mock.patch.object(GitSource, "read", offline):
            job = self.u.run_update_blocking()
        self.assertEqual((job["resultado"]["failed"], job["resultado"]["updated"]), (1, 0))
        self.assertEqual(self.u.status()["contagens"]["falhas"], 1)
        # sem commits novos, a próxima atualização tenta de novo o que falhou
        job = self.u.run_update_blocking()
        self.assertEqual((job["resultado"]["failed"], job["resultado"]["updated"]), (0, 1))
        self.assertEqual(self.u.status()["contagens"]["falhas"], 0)

    def test_only_one_update_at_a_time(self):
        self.u.set_recorte(["federal"])
        self.u._lock.acquire()
        try:
            self.assertFalse(self.u.start_update())
            with self.assertRaises(RuntimeError):
                self.u.run_update_blocking()
        finally:
            self.u._lock.release()


class TestServer(UpdaterTestBase):
    def setUp(self):
        super().setUp()
        self.srv = make_server(self.u, port=0)
        self.base = f"http://127.0.0.1:{self.srv.server_address[1]}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        super().tearDown()

    def req(self, path, body=None, header=True):
        data = None if body is None else json.dumps(body).encode()
        headers = {"Content-Type": "application/json"}
        if header:
            headers["X-Vade"] = "1"
        r = urllib.request.Request(self.base + path, data=data, headers=headers, method="POST" if data else "GET")
        try:
            with urllib.request.urlopen(r, timeout=30) as resp:
                return resp.status, json.loads(resp.read() or b"null")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"null")

    def test_page_and_api(self):
        with urllib.request.urlopen(self.base + "/", timeout=10) as resp:
            self.assertIn("Verificar atualização", resp.read().decode("utf-8"))
        self.assertEqual(self.req("/api/recorte", {"prefixos": ["federal"]}, header=False)[0], 403)
        self.assertEqual(self.req("/api/recorte", {"prefixos": ["federal"]}), (200, {"recorte": ["federal"]}))
        code, chk = self.req("/api/verificar", {})
        self.assertEqual((code, chk["primeira_importacao"]), (200, True))
        code, _ = self.req("/api/atualizar", {})
        self.assertIn(code, (202, 409))
        for _ in range(200):
            job = self.req("/api/job")[1]
            if job["estado"] != "rodando":
                break
            threading.Event().wait(0.05)
        self.assertEqual(job["estado"], "concluido")
        code, hits = self.req("/api/busca?q=" + urllib.request.quote("legítima defesa"))
        self.assertTrue(any(h["caminho"] == "art-25" for h in hits))
        self.assertEqual(self.req("/api/busca?q=" + urllib.request.quote('"; DROP --'))[0], 200)
        names = [i["caminho"] for i in self.req("/api/arvore?prefixo=")[1]]
        self.assertEqual(names, ["federal", "jurisprudencia"])

    def test_empty_scope_is_rejected(self):
        code, body = self.req("/api/atualizar", {})
        self.assertEqual(code, 400)
        self.assertIn("recorte vazio", body["erro"])


class TestFtsQuery(unittest.TestCase):
    def test_sanitizes(self):
        self.assertEqual(fts_query("legítima defesa"), '"legítima" "defesa"*')
        self.assertEqual(fts_query('a" OR 1=1 --'), '"a" "OR" "1" "1"*')
        self.assertIsNone(fts_query("  -- "))


if __name__ == "__main__":
    unittest.main()
