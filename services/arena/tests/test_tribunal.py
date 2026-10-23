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

    def test_dica_field_is_validated(self):
        d = copy.deepcopy(DATA)
        ep = tribunal.episode(d, "ep1-celular")
        cena = next(c for c in ep["cenas"].values() if c["tipo"] == "escolha" and not c.get("livre"))
        cena["dica"] = ["vaga", "específica"]
        self.assertEqual(tribunal.validate(d, NORMAS), [])
        cena["dica"] = ["a", "b", "c"]
        self.assertTrue(any("dica" in e for e in tribunal.validate(d, NORMAS)))

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
        self.assertEqual([e["id"] for e in eps[:3]], ["a1-tutorial", "ep1-celular", "a1-pao"])
        self.assertEqual([e["status"] for e in eps[:3]], ["disponivel", "bloqueado", "bloqueado"])
        c = tribunal.career(DATA, {"a1-tutorial": 240, "ep1-celular": 240}, {"a1-pao"})
        eps = [e for a in c["atos"] for e in a["episodios"]]
        self.assertEqual([e["status"] for e in eps[:4]], ["concluido", "concluido", "disponivel", "bloqueado"])
        self.assertTrue(eps[2]["salvo"])
        self.assertGreater(c["horas_jogadas"], 0)

    def test_cover_and_progress(self):
        mid = list(tribunal.episode(DATA, "ep1-celular")["cenas"])[3]
        c = tribunal.career(DATA, {}, {"ep1-celular"}, {"ep1-celular": mid})
        eps = [e for a in c["atos"] for e in a["episodios"]] + c["avulsos"]
        for e in eps:
            self.assertIn("capa", e)
            self.assertGreater(e["capa"]["cenas"], 2)
        withkey = [e for e in eps if e["capa"].get("visual")]
        self.assertGreater(len(withkey), len(eps) * 0.9)
        self.assertNotIn("voce", {e["capa"].get("q") for e in eps})
        e = next(e for e in eps if e["id"] == "ep1-celular")
        self.assertTrue(0 < e["progresso"] < 1)
        self.assertEqual(next(x for x in eps if x["id"] == "a1-tutorial")["progresso"], None)
        self.assertGreater(len({e["capa"].get("q") for e in eps}), 15)

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


class TestEscolhas(unittest.TestCase):
    def _with_dilemma(self):
        d = copy.deepcopy(DATA)
        ep = tribunal.episode(d, "ep1-celular")
        ep["cenas"]["a9"]["proxima"] = "dil"
        ep["cenas"]["dil"] = {"tipo": "escolha", "livre": True, "pergunta": "Ajudar o Lucas?", "falas": [], "proxima": "a10",
                              "opcoes": [{"t": "Sim", "marca": "a1_lucas", "falas": [{"q": "voce", "t": "Vamos."}]},
                                         {"t": "Não", "falas": [{"q": "voce", "t": "Não."}]}]}
        ep["cenas"]["a10"]["variantes"] = [{"se": "a1_lucas", "texto": "Lucas foi contratado."}]
        return d, ep

    def test_dilemma_is_valid_and_marks_are_declared(self):
        d, ep = self._with_dilemma()
        self.assertEqual(tribunal.validate(d, NORMAS), [])
        self.assertEqual(tribunal.episode_marks(ep), {"a1_lucas"})
        self.assertEqual(tribunal.choice_texts(d)["a1_lucas"]["texto"], "Sim")

    def test_conditions_need_a_declared_mark(self):
        d, ep = self._with_dilemma()
        ep["cenas"]["a2"]["falas"][0]["se"] = "!marca_fantasma"
        ep["cenas"]["dil"]["opcoes"][0]["certa"] = True
        errs = "\n".join(tribunal.validate(d, NORMAS))
        self.assertIn("marca_fantasma", errs)
        self.assertIn("nenhuma 'certa'", errs)

    def test_achievements(self):
        a = {x["id"]: x["ok"] for x in tribunal.achievements(DATA, {"ep1-celular": 1.0}, {"ep1-celular"}, set())}
        self.assertTrue(a["primeiro"] and a["perfeito"])
        self.assertFalse(a["carreira"] or a["ato-ato1"])

    def test_player_marks_replace_on_replay(self):
        from vade_arena.player import Player
        tmp = Path(tempfile.mkdtemp())
        try:
            pl = Player(tmp / "j.sqlite")
            pl.set_marks("ep", {"x_sim", "x_nao"}, {"x_sim", "intrusa"})
            self.assertEqual(pl.marks(), {"x_sim"})
            pl.set_marks("ep", {"x_sim", "x_nao"}, {"x_nao"})
            self.assertEqual(pl.marks(), {"x_nao"})
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestPontuacao(unittest.TestCase):
    ep = tribunal.episode(DATA, "ep1-celular")

    def test_perfect_run(self):
        r = tribunal.score(self.ep, 5, 0)
        self.assertEqual((r["venceu"], r["perfeito"], r["xp"]), (True, True, tribunal.xp_base(self.ep) + 100 + 60))

    def test_with_mistakes(self):
        r = tribunal.score(self.ep, 3, 2)
        self.assertEqual((r["perfeito"], r["xp"], r["faixa"]), (False, tribunal.xp_base(self.ep) + 60, "medio"))

    def test_game_over(self):
        r = tribunal.score(self.ep, 0, 5)
        self.assertEqual((r["venceu"], r["carimbo"], r["xp"]), (False, "DESTITUÍDO", 25))

    def test_client_cannot_inflate_score(self):
        r = tribunal.score(self.ep, 999, -7)
        self.assertEqual((r["credibilidade"], r["erros"], r["xp"]), (5, 0, tribunal.xp_base(self.ep) + 100 + 60))


class TestBalanceamento(unittest.TestCase):
    def ep(self, nivel, palavras):
        fala = {"q": "voce", "t": " ".join(["palavra"] * palavras)}
        return {"nivel": nivel, "cenas": {"a": {"tipo": "dialogo", "falas": [fala]}}}

    def test_duration_adjustment_formula(self):
        ref = round(tribunal.DUR_REF * 170)  # só leitura: 12 min -> sem ajuste
        self.assertEqual(tribunal.xp_base(self.ep("avancado", ref)), 170)
        self.assertEqual(tribunal.xp_base(self.ep("avancado", ref + 170 * 5)), 170 + 15)  # +5 min = +15 XP
        self.assertEqual(tribunal.xp_base(self.ep("basico", 10)), 80 + tribunal.DUR_MIN)  # curtíssimo: piso
        self.assertEqual(tribunal.xp_base(self.ep("especialista", 170 * 60)), 230 + tribunal.DUR_MAX)  # longuíssimo: teto

    def test_xp_follows_duration_within_a_level(self):
        for nivel in tribunal.XP_BASE:
            eps = sorted((e for e in DATA["episodios"] if e["nivel"] == nivel), key=tribunal.estimate_minutes)
            xps = [tribunal.xp_base(e) for e in eps]
            self.assertEqual(xps, sorted(xps), nivel)

    def test_levels_stay_ordered_on_average(self):
        media = {n: [tribunal.xp_base(e) for e in DATA["episodios"] if e["nivel"] == n] for n in tribunal.XP_BASE}
        medias = [sum(v) / len(v) for n, v in media.items() if v]
        self.assertEqual(medias, sorted(medias))

    def test_xp_stays_in_bounds(self):
        for e in DATA["episodios"]:
            self.assertTrue(tribunal.XP_BASE[e["nivel"]] + tribunal.DUR_MIN <= tribunal.xp_base(e) <= tribunal.XP_BASE[e["nivel"]] + tribunal.DUR_MAX)


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
        self.assertEqual([e["id"] for e in eps][:3], ["a1-tutorial", "ep1-celular", "a1-pao"])
        self.assertTrue({"ep2-protetiva", "ep3-sentenca"} <= {e["id"] for e in eps})
        self.assertEqual(self.req("/api/arena/perfil/avatar", {"nome": "Dra. Teste", "avatar": {"pele": "#8D5524", "cabelo": "coque"}})[0], 200)
        code, ep = self.req("/api/arena/tribunal/ep3-sentenca")
        self.assertEqual(ep["personagens"]["voce"]["nome"], "Dra. Teste")
        self.assertEqual(ep["personagens"]["voce"]["visual"]["cabelo"], "coque")
        self.assertNotIn("helena", ep["personagens"])  # só os personagens do episódio
        code, tut = self.req("/api/arena/tribunal/a1-tutorial")
        com_bio = [k for k, v in tut["personagens"].items() if v.get("bio")]
        self.assertTrue(com_bio)  # a tela de elenco depende de bio na API
        code, r = self.req("/api/arena/tribunal/concluir", {"episodio": "ep3-sentenca", "credibilidade": 4, "erros": 1})
        extra = r["recompensas"]["xp_combo"] + r["recompensas"]["xp_melhora"] + r["recompensas"]["xp_bau"]  # baú é sorteado pelo run_id
        self.assertEqual((code, r["xp"] - extra, r["carimbo"]), (200, tribunal.xp_base(tribunal.episode(DATA, "ep3-sentenca")) + 80, "SENTENÇA MANTIDA"))
        prof = self.req("/api/arena/perfil")[1]
        self.assertEqual((prof["xp"], prof["casos"]["jogadas"], prof["nome"]), (r["xp"], 1, "Dra. Teste"))
        self.assertEqual(self.req("/api/arena/tribunal/nao-existe")[0], 404)
        # jogo salvo: só cenas e provas válidas, credibilidade limitada
        code, salvo = self.req("/api/arena/tribunal/salvar", {"episodio": "a1-pao", "estado": {"cena": "p5", "credibilidade": 99, "erros": 2, "autos": ["cupom", "hack"]}})
        self.assertEqual((code, salvo["credibilidade"], salvo["autos"]), (200, 5, ["cupom"]))
        self.assertEqual(self.req("/api/arena/tribunal/salvar", {"episodio": "a1-pao", "estado": {"cena": "zz"}})[0], 400)
        self.assertEqual(self.req("/api/arena/tribunal/a1-pao")[1]["salvo"]["cena"], "p5")
        car = self.req("/api/arena/carreira")[1]
        self.assertEqual(car["atos"][0]["episodios"][2]["salvo"], True)
        self.req("/api/arena/tribunal/recomecar", {"episodio": "a1-pao"})
        self.assertIsNone(self.req("/api/arena/tribunal/a1-pao")[1]["salvo"])
        self.assertEqual(self.req("/api/arena/perfil/avatar", {"avatar": "x"})[0], 400)


if __name__ == "__main__":
    unittest.main()
