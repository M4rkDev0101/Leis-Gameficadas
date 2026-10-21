"""Arena: conteúdo, simulados, casos, progresso do jogador e servidor."""

import copy
import datetime as dt
import json
import shutil
import sqlite3
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from vade_arena import bank, cases, exam
from vade_arena.player import Player

B = bank.load()


class TestContent(unittest.TestCase):
    def test_structure_is_valid(self):
        self.assertEqual(bank.validate_structure(B), [])

    def test_every_contest_has_enough_questions_per_level(self):
        for c in B.concursos:
            pool = [q for q in B.questoes if q["formato"] == c["formato"] and q["area"] in c["areas"]]
            self.assertGreaterEqual(len(pool), 20, c["id"])

    def test_validator_catches_broken_content(self):
        broken = copy.deepcopy(B)
        broken.questoes[0]["gabarito"] = "X"
        broken.questoes[1]["fundamentos"] = [{"chave": "NAOEXISTE#art-1", "trecho": "x"}]
        broken.casos[0]["cenas"]["c1"]["escolhas"][0]["proxima"] = "cena-fantasma"
        errs = "\n".join(bank.validate_structure(broken))
        self.assertIn("gabarito C/E inválido", errs)
        self.assertIn("alias de norma desconhecido", errs)
        self.assertIn("próxima cena inexistente", errs)

    def test_catalog_validation_detects_outdated_excerpt(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            db = sqlite3.connect(tmp / "c.sqlite")
            db.executescript("""CREATE TABLE norma (id TEXT PRIMARY KEY);
                CREATE TABLE dispositivo (chave TEXT, texto TEXT, rubrica TEXT);
                INSERT INTO norma VALUES ('constituicao');
                INSERT INTO dispositivo VALUES ('constituicao#art-5/inc-xi',
                  'a casa é asilo inviolável do indivíduo, ninguém nela podendo penetrar sem consentimento do morador, salvo em caso de flagrante delito ou desastre, ou para prestar socorro, ou, durante o dia, por determinação judicial;', NULL);""")
            db.commit()
            db.close()
            only = copy.deepcopy(B)
            only.questoes = [q for q in only.questoes if q["id"] in ("ce-001", "ce-002", "ce-005")]
            only.casos = []
            problems, checked, absent = bank.validate_against_catalog(only, tmp / "c.sqlite")
            self.assertEqual(checked, 3)
            self.assertEqual(len(problems), 1)  # ce-005 cita art-5/inc-lvii, ausente deste catálogo
            self.assertIn("inc-lvii não existe", problems[0])
            only.questoes[0]["fundamentos"][0]["trecho"] = "durante a noite, por determinação judicial"
            problems, _, _ = bank.validate_against_catalog(only, tmp / "c.sqlite")
            self.assertTrue(any("trecho não encontrado" in p for p in problems))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestExam(unittest.TestCase):
    def test_build_respects_contest_and_level(self):
        s = exam.build(B, "policial-cebraspe", "intermediario", seed=1)
        self.assertEqual(len(s.question_ids), 15)
        qs = [B.by_id[i] for i in s.question_ids]
        self.assertTrue(all(q["formato"] == "certo_errado" for q in qs))
        self.assertGreaterEqual(sum(q["nivel"] == "intermediario" for q in qs), 10)
        self.assertEqual(len(set(s.question_ids)), 15)

    def test_unseen_questions_come_first(self):
        first = exam.build(B, "policial-cebraspe", "basico", seed=1)
        second = exam.build(B, "policial-cebraspe", "basico", seen=set(first.question_ids), seed=2)
        self.assertFalse(set(first.question_ids) & set(second.question_ids))

    def test_minimum_level(self):
        with self.assertRaises(ValueError):
            exam.build(B, "magistratura-mp", "basico")

    def test_public_view_hides_answers(self):
        s = exam.build(B, "tribunais-fgv", "avancado", seed=3)
        dump = json.dumps(exam.public_view(B, s), ensure_ascii=False)
        for key in ("gabarito", "explicacao", "fundamentos", "pegadinha"):
            self.assertNotIn(f'"{key}"', dump)

    def test_cebraspe_rule_errors_cancel_hits(self):
        s = exam.build(B, "policial-cebraspe", "basico", seed=4)
        ids = s.question_ids
        ans = {}
        for i, qid in enumerate(ids):
            right = B.by_id[qid]["gabarito"]
            wrong = "E" if right == "C" else "C"
            ans[qid] = right if i < 6 else (wrong if i < 9 else None)  # 6 certas, 3 erradas, 1 branco
        r = exam.grade(B, s, ans)
        self.assertEqual((r["acertos"], r["erros"], r["brancos"], r["pontos"]), (6, 3, 1, 3))
        self.assertAlmostEqual(r["nota"], 0.3)
        self.assertFalse(r["aprovado"])
        self.assertIs(exam.grade(B, s, {}), r)  # entregar de novo não recorrige

    def test_oab_has_four_alternatives_and_keeps_answer(self):
        s = exam.build(B, "oab-fgv", "intermediario", seed=5)
        view = exam.public_view(B, s)
        for item in view["questoes"]:
            self.assertEqual(list(item["alternativas"]), ["A", "B", "C", "D"])
        ans = {}
        for qid in s.question_ids:
            q = B.by_id[qid]
            shown = next(k for k, v in s.letter_maps[qid].items() if v == q["gabarito"])
            ans[qid] = shown
        r = exam.grade(B, s, ans)
        self.assertEqual(r["acertos"], len(s.question_ids))
        self.assertTrue(r["aprovado"])
        self.assertGreater(r["xp"], B.niveis["intermediario"]["bonus_xp"])
        self.assertEqual(r["melhor_combo"], len(s.question_ids))

    def test_contest_with_real_pass_rule(self):
        s = exam.build(B, "oab-fgv", "avancado", seed=8)  # meta do nível Difícil seria 65%
        self.assertEqual(s.meta, 0.5)
        half = {qid: B.by_id[qid]["gabarito"] for qid in s.question_ids[: len(s.question_ids) // 2]}
        ans = {qid: next(k for k, v in s.letter_maps[qid].items() if v == orig) for qid, orig in half.items()}
        self.assertTrue(exam.grade(B, s, ans)["aprovado"])  # 50% aprova, como na prova real

    def test_lookup_enriches_corrections(self):
        s = exam.build(B, "policial-cebraspe", "basico", seed=6)
        r = exam.grade(B, s, {}, lookup=lambda k: {"texto": "TEXTO VIGENTE", "rotulo": "X", "rubrica": None, "norma": "CF"})
        f = r["questoes"][0]["fundamentos"][0]
        self.assertEqual((f["texto"], f["no_catalogo"]), ("TEXTO VIGENTE", True))


class TestCases(unittest.TestCase):
    def play(self, caso_id, pick):
        run = cases.start(B, caso_id)
        out = None
        while run.scene:
            view = cases.scene_view(B, run)
            self.assertNotIn("efeito", json.dumps(view))  # cliente não vê o efeito antes de escolher
            cena = B.caso(caso_id)["cenas"][run.scene]
            out = cases.choose(B, run, pick(cena["escolhas"]))
        return out

    def test_best_and_worst_paths_reach_best_and_worst_endings(self):
        for c in B.casos:
            score = lambda e: sum(e.get("efeito", {}).values())  # noqa: E731
            best = self.play(c["id"], lambda es: max(range(len(es)), key=lambda i: score(es[i])))
            worst = self.play(c["id"], lambda es: min(range(len(es)), key=lambda i: score(es[i])))
            top = max(c["finais"], key=lambda f: f["min"])
            self.assertEqual(best["final"]["titulo"], top["titulo"], c["id"])
            self.assertEqual(best["final"]["aproveitamento"], 1.0)
            self.assertEqual((best["final"]["faixa"], worst["final"]["faixa"]), ("otimo", "ruim"))
            self.assertEqual(worst["final"]["min"], -99, c["id"])

    def test_invalid_choice_and_finished_case(self):
        run = cases.start(B, "celular-augusta")
        with self.assertRaises(ValueError):
            cases.choose(B, run, 9)
        while run.scene:
            cases.choose(B, run, 0)
        with self.assertRaises(ValueError):
            cases.choose(B, run, 0)


class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.p = Player(self.tmp / "j.sqlite")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_xp_level_streak_and_history(self):
        s = exam.build(B, "policial-cebraspe", "basico", seed=7)
        r = exam.grade(B, s, {qid: B.by_id[qid]["gabarito"] for qid in s.question_ids})
        d = dt.date(2026, 10, 21)
        prog = self.p.record_exam(r, today=d)
        self.assertTrue(prog["subiu_de_nivel"])  # 10 acertos com combo + bônus passam de 100 XP
        run = cases.start(B, "vazamento-clinica")
        while run.scene:
            out = cases.choose(B, run, 0)
        self.p.record_case(run.id, B.caso("vazamento-clinica"), out["final"], today=d + dt.timedelta(days=1))
        prof = self.p.profile(today=d + dt.timedelta(days=1))
        self.assertEqual(prof["xp"], r["xp"] + out["final"]["xp"])
        self.assertEqual((prof["streak"], prof["jogou_hoje"]), (2, True))
        self.assertEqual((prof["simulados"]["jogadas"], prof["casos"]["jogadas"]), (1, 1))
        self.assertEqual(prof["questoes"]["respostas"], 10)
        self.assertEqual(self.p.seen_questions(), set(s.question_ids))
        self.assertEqual(self.p.profile(today=d + dt.timedelta(days=5))["streak"], 0)


class TestServer(unittest.TestCase):
    def setUp(self):
        from vade_arena.server import Arena, make_server
        from vade_ingest.updater import Updater

        self.tmp = Path(tempfile.mkdtemp())
        arena = Arena(str(self.tmp / "catalogo.sqlite"), str(self.tmp / "j.sqlite"))
        self.srv = make_server(Updater(self.tmp, self.tmp / "catalogo.sqlite"), arena, port=0)
        self.base = f"http://127.0.0.1:{self.srv.server_address[1]}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def req(self, path, body=None, header=True):
        data = None if body is None else json.dumps(body).encode()
        h = {"Content-Type": "application/json", **({"X-Vade": "1"} if header else {})}
        r = urllib.request.Request(self.base + path, data=data, headers=h, method="POST" if data else "GET")
        try:
            with urllib.request.urlopen(r, timeout=20) as resp:
                raw = resp.read()
                return resp.status, (json.loads(raw) if resp.headers.get_content_type() == "application/json" else raw.decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"null")

    def test_full_game_flow(self):
        code, page = self.req("/")
        self.assertEqual(code, 200)
        self.assertIn("Vade Arena", page)
        self.assertIn("Verificar atualização", self.req("/acervo")[1])
        self.assertEqual(self.req("/api/arena/simulado/iniciar", {"concurso": "oab-fgv", "nivel": "basico"}, header=False)[0], 403)

        code, s = self.req("/api/arena/simulado/iniciar", {"concurso": "oab-fgv", "nivel": "basico"})
        self.assertEqual(code, 200)
        self.assertNotIn('"gabarito"', json.dumps(s))
        code, r = self.req("/api/arena/simulado/entregar", {"sessao": s["sessao"], "respostas": {s["questoes"][0]["id"]: "A"}})
        self.assertEqual((code, r["total"]), (200, 10))
        self.assertIn("progresso", r)

        code, sc = self.req("/api/arena/caso/iniciar", {"caso": "usuario-ou-traficante"})
        self.assertEqual((code, sc["caso"]["papel"]), (200, "juiz"))
        out = None
        while True:
            code, out = self.req("/api/arena/caso/escolher", {"sessao": sc["sessao"], "indice": 0})
            self.assertEqual(code, 200)
            if "final" in out:
                break
        self.assertEqual(out["final"]["carimbo"], "SENTENÇA MANTIDA")

        code, prof = self.req("/api/arena/perfil")
        self.assertEqual((prof["simulados"]["jogadas"], prof["casos"]["jogadas"]), (1, 1))
        self.assertEqual(self.req("/api/arena/caso/escolher", {"sessao": "nao-existe", "indice": 0})[0], 404)
        self.assertEqual(self.req("/api/arena/simulado/iniciar", {"concurso": "magistratura-mp", "nivel": "basico"})[0], 400)


if __name__ == "__main__":
    unittest.main()
