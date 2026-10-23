"""Laço de recompensa: nota por caso, combo, baú, álbum, desafio do dia, folga semanal e migração do save."""

import datetime as dt
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from vade_arena import bank, recompensas as rw, tribunal
from vade_arena.player import Player
from vade_arena.server import Arena

DATA = tribunal.load()
EP = tribunal.episode(DATA, "ep1-celular")
D1 = dt.date(2026, 10, 19)  # segunda-feira


def venceu(erros=0, cred=5):
    return tribunal.score(EP, cred, erros)


class TestRegras(unittest.TestCase):
    def test_nota(self):
        self.assertEqual([rw.nota_do_caso(True, e) for e in (0, 1, 2, 3, 4)], ["S", "A", "B", "B", "C"])
        self.assertIsNone(rw.nota_do_caso(False, 0))

    def test_combo_tem_teto_e_nunca_e_negativo(self):
        self.assertEqual(rw.bonus_combo(500, 0), 0)
        self.assertEqual(rw.bonus_combo(500, 5), 50)
        self.assertEqual(rw.bonus_combo(500, 999), 100)  # teto: +20%
        self.assertEqual(rw.bonus_combo(500, -3), 0)

    def test_bau_deterministico_e_sem_perda(self):
        for rid in ("a", "b", "c"):
            self.assertEqual(rw.bau(rid, "S"), rw.bau(rid, "S"))
        tipos = {rw.bau(str(i), "A")["tipo"] for i in range(300)}
        self.assertEqual(tipos, {"comum", "bom", "raro"})
        self.assertTrue(all(rw.bau(str(i), "C")["xp"] >= 0 for i in range(100)))
        self.assertEqual(rw.bau("x", None)["tipo"], "vazio")

    def test_chance_rara_cresce_com_a_nota(self):
        raros = lambda n: sum(rw.bau(str(i), n)["tipo"] == "raro" for i in range(2000))
        self.assertGreater(raros("S"), raros("C"))

    def test_dia_e_igual_para_todos_e_muda_por_data(self):
        qs = bank.load().questoes
        a = rw.dia_questoes(qs, D1)
        self.assertEqual(a, rw.dia_questoes(qs, D1))
        self.assertEqual(len(set(a)), rw.DIA_QUESTOES)
        self.assertNotEqual(a, rw.dia_questoes(qs, D1 + dt.timedelta(days=1)))


class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Player(self.tmp / "j.sqlite")
        self.cartas = tribunal.episode_cards(DATA, EP["id"])

    def trial(self, rid, erros, day=D1, **extras):
        return self.p.record_trial(rid, EP, venceu(erros, 5 - min(erros, 4)), day, extras, self.cartas)

    def test_save_antigo_migra_sem_perder_dados(self):
        antigo = self.tmp / "velho.sqlite"
        db = sqlite3.connect(antigo)
        db.executescript("""CREATE TABLE jogador (id INTEGER PRIMARY KEY CHECK (id = 1), nome TEXT NOT NULL DEFAULT 'Você',
            xp_total INTEGER NOT NULL DEFAULT 0, streak_atual INTEGER NOT NULL DEFAULT 0, streak_max INTEGER NOT NULL DEFAULT 0,
            streak_dia TEXT, protetores INTEGER NOT NULL DEFAULT 1);
            INSERT INTO jogador (id, nome, xp_total, streak_atual, streak_max, streak_dia, protetores) VALUES (1, 'Ana', 777, 3, 5, '2026-10-18', 1);""")
        db.commit()
        db.close()
        for _ in range(2):  # idempotente
            pl = Player(antigo)
            prof = pl.profile(D1)
        self.assertEqual((prof["nome"], prof["xp"]), ("Ana", 777))
        self.assertEqual(prof["protetores"], 1)  # primeira vez na semana nova: não ganha nem perde

    def test_nota_recorde_e_bonus_de_melhora(self):
        r1 = self.trial("r1", 3, segundos=600)["recompensas"]
        self.assertEqual((r1["nota"], r1["recorde"]["primeira_vez"], r1["xp_melhora"]), ("B", True, 0))
        r2 = self.trial("r2", 0, segundos=400)["recompensas"]
        self.assertEqual(r2["nota"], "S")
        self.assertTrue(r2["recorde"]["melhorou_nota"] and r2["recorde"]["melhorou_tempo"] and r2["recorde"]["selo_dourado"])
        self.assertEqual(r2["xp_melhora"], 2 * rw.BONUS_MELHORA)
        r3 = self.trial("r3", 2)["recompensas"]  # pior: nada muda no recorde, nada é tirado
        self.assertEqual((r3["xp_melhora"], r3["recorde"]["melhorou_nota"], r3["recorde"]["selo_dourado"]), (0, False, True))
        self.assertEqual(self.p.grades()[EP["id"]]["nota"], "S")
        self.assertEqual(self.p.grades()[EP["id"]]["vezes"], 3)

    def test_combo_paga_com_teto_e_derrota_nao_paga(self):
        sem = self.trial("a", 0)["recompensas"]["xp_combo"]
        com = self.trial("b", 0, combo_max=999)["recompensas"]
        self.assertEqual(sem, 0)
        self.assertEqual(com["combo_max"], rw.COMBO_TETO)
        self.assertGreater(com["xp_combo"], 0)
        derrota = self.p.record_trial("d", EP, tribunal.score(EP, 0, 5), D1, {"combo_max": 9}, self.cartas)
        self.assertEqual(derrota["recompensas"]["xp_combo"], 0)

    def test_cartas_so_na_vitoria_e_douradas_no_caso_perfeito(self):
        self.p.record_trial("d", EP, tribunal.score(EP, 0, 5), D1, {}, self.cartas)
        self.assertEqual(self.p.cards(), {})
        r = self.trial("v", 2)["recompensas"]
        self.assertEqual(len(r["cartas_novas"]), len(self.cartas))
        self.assertFalse(any(c["dourada"] for c in r["cartas_novas"]))  # (o baú raro pode banhar a ouro uma delas)
        self.trial("w", 0)
        self.assertTrue(all(c["dourada"] for c in self.p.cards().values()))
        self.assertEqual(self.trial("x", 0)["recompensas"]["cartas_novas"], [])

    def test_mesma_partida_nao_paga_duas_vezes(self):
        a = self.trial("dup", 0)
        xp = self.p.profile(D1)["xp"]
        b = self.trial("dup", 0)
        self.assertEqual(self.p.profile(D1)["xp"], xp)
        self.assertEqual(b["recompensas"]["xp_combo"], 0)
        self.assertEqual(a["nota"], "S")

    def test_contadores_para_conquistas(self):
        self.trial("c1", 0, certeiras=4, combo_max=6)
        self.trial("c2", 0, certeiras=3, combo_max=4)
        self.assertEqual(self.p.counters(), {"contradicoes": 7, "combo_max": 6})

    def test_entrada_do_cliente_e_limitada(self):
        r = self.trial("big", 0, combo_max=10**9, certeiras=10**9, segundos=-5)["recompensas"]
        self.assertEqual(r["combo_max"], rw.COMBO_TETO)
        self.assertEqual(self.p.counters()["contradicoes"], 50)
        self.assertEqual(r["recorde"]["tempo_s"], 0)

    def test_patente_nova_e_proxima(self):
        prof = self.p.profile(D1)
        self.assertEqual(prof["proxima_patente"]["titulo"], "Bacharel")
        self.assertGreater(prof["proxima_patente"]["faltam_xp"], 0)
        db = sqlite3.connect(self.p.path)
        db.execute("UPDATE jogador SET xp_total = 190 WHERE id = 1")
        db.commit()
        db.close()
        prog = self.p.record_trial("lv", EP, venceu(0), D1, {}, [])
        self.assertTrue(prog["subiu_de_nivel"] and prog["patente_nova"])

    def test_folga_semanal_gratis_com_teto(self):
        self.p.profile(D1)
        self.assertEqual(self.p.profile(D1)["protetores"], 1)
        self.assertEqual(self.p.profile(D1 + dt.timedelta(days=7))["protetores"], 2)
        self.assertEqual(self.p.profile(D1 + dt.timedelta(days=14))["protetores"], 2)  # teto

    def test_folga_cobre_um_dia_sem_jogar(self):
        self.trial("s1", 0, day=D1)
        prog = self.trial("s2", 0, day=D1 + dt.timedelta(days=2))  # pulou um dia
        self.assertEqual(prog["streak"], 2)
        self.assertTrue(prog["protetor_usado"])


class TestApi(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.a = Arena(str(self.tmp / "c.sqlite"), str(self.tmp / "j.sqlite"))
        self.hoje = D1
        self.a.today = lambda: self.hoje

    def test_dia_nao_vaza_gabarito_e_paga_uma_vez(self):
        d = self.a.dia()
        self.assertEqual(len(d["questoes"]), 3)
        self.assertFalse(any("gabarito" in q or "explicacao" in q for q in d["questoes"]))
        q = d["questoes"][0]
        r = self.a.dia_responder(q["id"], "Z")  # inválida vira branco
        self.assertFalse(r["correta"])
        with self.assertRaises(ValueError):
            self.a.dia_responder(q["id"], "A")
        with self.assertRaises(ValueError):
            self.a.dia_responder("nao-e-do-dia", "A")
        for q in d["questoes"][1:]:
            gab = self.a.bank.by_id[q["id"]]["gabarito"]
            r = self.a.dia_responder(q["id"], gab)
            self.assertTrue(r["correta"])
        fim = self.a.dia()
        self.assertTrue(fim["completo"])
        self.assertEqual(r["progresso"]["xp"], rw.DIA_XP_ACERTO + rw.DIA_XP_COMPLETO)
        self.assertEqual(fim["dias_completos"], 1)
        self.assertEqual(fim["streak"], 1)
        self.assertIn("gabarito", fim["questoes"][0])

    def test_album_esconde_o_texto_das_cartas_bloqueadas(self):
        al = self.a.album()
        self.assertEqual(al["ok"], 0)
        self.assertEqual(al["total"], len(tribunal.cards_catalog(DATA)))
        self.assertTrue(all("texto" not in c for c in al["cartas"]))
        self.a.concluir_episodio("ep1-celular", 5, 0, [], {"combo_max": 4, "certeiras": 2, "segundos": 300})
        al = self.a.album()
        self.assertEqual(al["ok"], len(tribunal.episode_cards(DATA, "ep1-celular")))
        self.assertEqual(al["douradas"], al["ok"])

    def test_conquistas_com_progresso_e_raridade(self):
        self.a.concluir_episodio("ep1-celular", 5, 0, [], {"certeiras": 7})
        car = self.a.carreira()
        c = {x["id"]: x for x in car["conquistas"]}
        self.assertEqual(c["contradicoes10"]["progresso"], {"atual": 7, "meta": 10})
        self.assertFalse(c["contradicoes10"]["ok"])
        self.assertTrue(c["primeiro"]["ok"])
        self.assertIn(c["carreira"]["raridade"], {"lendaria"})
        self.assertEqual(car["notas"]["ep1-celular"]["nota"], "S")
        self.assertTrue(all("progresso" in x and "raridade" in x for x in car["conquistas"]))


if __name__ == "__main__":
    unittest.main()
