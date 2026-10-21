"""Modo Tribunal: roteiro, pontuação, servidor e avatar."""

import copy
import json
import shutil
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from vade_arena import bank, tribunal

DATA = tribunal.load()
NORMAS = bank.load().normas


class TestRoteiro(unittest.TestCase):
    def test_script_is_valid(self):
        self.assertEqual(tribunal.validate(DATA, NORMAS), [])

    def test_one_episode_per_role(self):
        self.assertEqual({ep["papel"] for ep in DATA["episodios"]}, {"advogado", "promotor", "juiz"})

    def test_validator_catches_broken_script(self):
        d = copy.deepcopy(DATA)
        ep = tribunal.episode(d, "ep1-celular")
        ep["cenas"]["a4"]["contradicao"]["provas"] = ["prova-que-nao-existe"]
        ep["cenas"]["a8"]["opcoes"][0]["certa"] = True  # duas certas
        ep["cenas"]["a3"]["falas"][0]["e"] = "dançando"
        ep["cenas"]["a6"]["proxima"] = "a3"  # ciclo
        errs = "\n".join(tribunal.validate(d, NORMAS))
        for msg in ("prova inexistente", "exatamente 1 certa", "expressão inválida", "ciclo"):
            self.assertIn(msg, errs)

    def test_required_evidence_is_given_before_use(self):
        d = copy.deepcopy(DATA)
        for f in tribunal.episode(d, "ep1-celular")["cenas"]["a2"]["falas"]:
            f.pop("recebe", None)
        self.assertTrue(any("nunca é entregue" in e for e in tribunal.validate(d, NORMAS)))

    def test_contradictions_point_to_real_statements(self):
        for ep in DATA["episodios"]:
            for c in ep["cenas"].values():
                if c["tipo"] == "depoimento":
                    self.assertLess(c["contradicao"]["afirmacao"], len(c["afirmacoes"]))

    def test_laws_are_in_fundamentos_for_catalog_check(self):
        chaves = {f["chave"] for _, f in tribunal.all_fundamentos(DATA)}
        for must in ("CPP#art-212", "CPP#art-155", "CP#art-155/par-6/inc-ii", "LMP#art-41", "LD#art-28/par-2"):
            self.assertIn(must, chaves)


class TestCarreira(unittest.TestCase):
    def test_only_next_case_is_unlocked(self):
        c = tribunal.career(DATA, {}, set())
        eps = [e for a in c["atos"] for e in a["episodios"]]
        self.assertEqual(eps[0]["id"], "ep1-celular")
        self.assertEqual([e["status"] for e in eps[:3]], ["disponivel", "bloqueado", "bloqueado"])
        c = tribunal.career(DATA, {"ep1-celular": 240}, {"a1-pao"})
        eps = [e for a in c["atos"] for e in a["episodios"]]
        self.assertEqual([e["status"] for e in eps[:3]], ["concluido", "disponivel", "bloqueado"])
        self.assertTrue(eps[1]["salvo"])
        self.assertGreater(c["horas_jogadas"], 0)

    def test_every_act_episode_has_unique_order(self):
        seen = set()
        for ep in DATA["episodios"]:
            if ep.get("ato"):
                self.assertNotIn((ep["ato"], ep["ordem"]), seen)
                seen.add((ep["ato"], ep["ordem"]))

    def test_estimate_counts_reading_and_decisions(self):
        ep = tribunal.episode(DATA, "ep1-celular")
        self.assertGreater(tribunal.estimate_minutes(ep), 5)

    def test_investigation_rules(self):
        d = copy.deepcopy(DATA)
        cena = tribunal.episode(d, "ep1-celular")["cenas"]["a2b"]
        cena["requer"] = ["laudo-fantasma"]
        cena["pontos"][0]["x"] = 140
        cena["local"] = "lua"
        errs = "\n".join(tribunal.validate(d, NORMAS))
        for msg in ("lua", "coordenada x", "laudo-fantasma"):
            self.assertIn(msg, errs)
        d = copy.deepcopy(DATA)
        cena = tribunal.episode(d, "ep1-celular")["cenas"]["a2b"]
        cena["pontos"][1]["falas"][1].pop("recebe")
        self.assertTrue(tribunal.validate(d, NORMAS))


class TestPontuacao(unittest.TestCase):
    ep = tribunal.episode(DATA, "ep1-celular")

    def test_perfect_run(self):
        r = tribunal.score(self.ep, 5, 0)
        self.assertEqual((r["venceu"], r["perfeito"], r["xp"]), (True, True, 80 + 100 + 60))

    def test_with_mistakes(self):
        r = tribunal.score(self.ep, 3, 2)
        self.assertEqual((r["perfeito"], r["xp"], r["faixa"]), (False, 140, "medio"))

    def test_game_over(self):
        r = tribunal.score(self.ep, 0, 5)
        self.assertEqual((r["venceu"], r["carimbo"], r["xp"]), (False, "DESTITUÍDO", 25))

    def test_client_cannot_inflate_score(self):
        r = tribunal.score(self.ep, 999, -7)
        self.assertEqual((r["credibilidade"], r["erros"], r["xp"]), (5, 0, 240))


class TestServidor(unittest.TestCase):
    def setUp(self):
        from vade_arena.server import Arena, make_server
        from vade_ingest.updater import Updater

        self.tmp = Path(tempfile.mkdtemp())
        self.srv = make_server(Updater(self.tmp, self.tmp / "c.sqlite"), Arena(str(self.tmp / "c.sqlite"), str(self.tmp / "j.sqlite")), port=0)
        self.base = f"http://127.0.0.1:{self.srv.server_address[1]}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def req(self, path, body=None):
        data = None if body is None else json.dumps(body).encode()
        r = urllib.request.Request(self.base + path, data=data, method="POST" if data else "GET",
                                   headers={"Content-Type": "application/json", "X-Vade": "1"})
        try:
            with urllib.request.urlopen(r, timeout=20) as resp:
                raw = resp.read()
                return resp.status, json.loads(raw) if resp.headers.get_content_type() == "application/json" else raw.decode()
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"null")

    def test_flow(self):
        code, page = self.req("/tribunal")
        self.assertEqual(code, 200)
        self.assertIn("Vade Tribunal", page)
        code, eps = self.req("/api/arena/tribunal")
        self.assertEqual([e["id"] for e in eps][:2], ["ep1-celular", "a1-pao"])
        self.assertTrue({"ep2-protetiva", "ep3-sentenca"} <= {e["id"] for e in eps})
        self.assertEqual(self.req("/api/arena/perfil/avatar", {"nome": "Dra. Teste", "avatar": {"pele": "#8D5524", "cabelo": "coque"}})[0], 200)
        code, ep = self.req("/api/arena/tribunal/ep3-sentenca")
        self.assertEqual(ep["personagens"]["voce"]["nome"], "Dra. Teste")
        self.assertEqual(ep["personagens"]["voce"]["visual"]["cabelo"], "coque")
        self.assertNotIn("helena", ep["personagens"])  # só os personagens do episódio
        code, r = self.req("/api/arena/tribunal/concluir", {"episodio": "ep3-sentenca", "credibilidade": 4, "erros": 1})
        self.assertEqual((code, r["xp"], r["carimbo"]), (200, 170 + 80, "SENTENÇA MANTIDA"))
        prof = self.req("/api/arena/perfil")[1]
        self.assertEqual((prof["xp"], prof["casos"]["jogadas"], prof["nome"]), (250, 1, "Dra. Teste"))
        self.assertEqual(self.req("/api/arena/tribunal/nao-existe")[0], 404)
        # jogo salvo: só cenas e provas válidas, credibilidade limitada
        code, salvo = self.req("/api/arena/tribunal/salvar", {"episodio": "a1-pao", "estado": {"cena": "p5", "credibilidade": 99, "erros": 2, "autos": ["cupom", "hack"]}})
        self.assertEqual((code, salvo["credibilidade"], salvo["autos"]), (200, 5, ["cupom"]))
        self.assertEqual(self.req("/api/arena/tribunal/salvar", {"episodio": "a1-pao", "estado": {"cena": "zz"}})[0], 400)
        self.assertEqual(self.req("/api/arena/tribunal/a1-pao")[1]["salvo"]["cena"], "p5")
        car = self.req("/api/arena/carreira")[1]
        self.assertEqual(car["atos"][0]["episodios"][1]["salvo"], True)
        self.req("/api/arena/tribunal/recomecar", {"episodio": "a1-pao"})
        self.assertIsNone(self.req("/api/arena/tribunal/a1-pao")[1]["salvo"])
        self.assertEqual(self.req("/api/arena/perfil/avatar", {"avatar": "x"})[0], 400)


if __name__ == "__main__":
    unittest.main()
