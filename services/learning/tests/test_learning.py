"""Testes do núcleo de aprendizagem. Propriedades do FSRS em vez de números mágicos,
mais vetores de referência para paridade com a futura implementação TypeScript."""

import datetime as dt
import json
import unittest
from pathlib import Path

from vade_learning import difficulty, gamification as g
from vade_learning.fsrs import Card, Grade, Scheduler, State, grade_from_answer

UTC = dt.timezone.utc
T0 = dt.datetime(2026, 10, 21, 12, 0, tzinfo=UTC)
VECTORS = Path(__file__).with_name("vectors.json")


def days(n: float) -> dt.timedelta:
    return dt.timedelta(days=n)


class TestFsrsFormulas(unittest.TestCase):
    def setUp(self):
        self.s = Scheduler()

    def test_retrievability_is_90_percent_at_stability(self):
        self.assertAlmostEqual(self.s.retrievability(7.0, 7.0), 0.9, places=9)
        self.assertEqual(self.s.retrievability(0, 5), 1.0)

    def test_interval_equals_stability_at_90_retention(self):
        self.assertEqual(self.s.interval_days(30.0), 30)
        longer = Scheduler(desired_retention=0.8).interval_days(30.0)
        shorter = Scheduler(desired_retention=0.95).interval_days(30.0)
        self.assertGreater(longer, 30)
        self.assertLess(shorter, 30)

    def test_initial_difficulty_decreases_with_grade(self):
        ds = [self.s.init_difficulty(gr) for gr in Grade]
        self.assertEqual(ds, sorted(ds, reverse=True))
        self.assertTrue(all(1 <= d <= 10 for d in ds))

    def test_validates_inputs(self):
        with self.assertRaises(ValueError):
            Scheduler(w=(1.0,) * 18)
        with self.assertRaises(ValueError):
            Scheduler(desired_retention=0.5)
        with self.assertRaises(ValueError):
            self.s.review(Card("x"), Grade.GOOD, dt.datetime(2026, 1, 1))  # sem fuso


class TestFsrsScheduling(unittest.TestCase):
    def setUp(self):
        self.s = Scheduler()
        self.card = Card("constituicao#art-5/inc-lxxiii")

    def test_new_card_grades_order_due_dates(self):
        due = self.s.preview(self.card, T0)
        self.assertLess(due[Grade.AGAIN], due[Grade.HARD])
        self.assertLessEqual(due[Grade.HARD], due[Grade.GOOD])
        self.assertLess(due[Grade.GOOD], due[Grade.EASY])
        self.assertEqual(due[Grade.AGAIN] - T0, dt.timedelta(minutes=10))

    def test_successful_reviews_grow_intervals(self):
        c, _ = self.s.review(self.card, Grade.GOOD, T0)
        intervals, now = [], T0
        for _ in range(5):
            now = c.due
            c, log = self.s.review(c, Grade.GOOD, now)
            self.assertAlmostEqual(log.retrievability, 0.9, delta=0.02)  # revisou no ponto ótimo
            intervals.append((c.due - now).days)
        self.assertEqual(intervals, sorted(intervals))
        self.assertGreater(intervals[-1], intervals[0] * 3)
        self.assertEqual((c.state, c.reps, c.lapses), (State.REVIEW, 6, 0))

    def test_lapse_reduces_stability_and_counts(self):
        c, _ = self.s.review(self.card, Grade.GOOD, T0)
        c, _ = self.s.review(c, Grade.GOOD, c.due)
        before = c.stability
        c2, log = self.s.review(c, Grade.AGAIN, c.due)
        self.assertLess(c2.stability, before)
        self.assertGreater(c2.difficulty, c.difficulty)
        self.assertEqual((c2.state, c2.lapses), (State.RELEARNING, 1))
        self.assertEqual(log.stability_before, before)

    def test_late_review_gives_bigger_boost_than_early(self):
        c, _ = self.s.review(self.card, Grade.GOOD, T0)
        c, _ = self.s.review(c, Grade.GOOD, c.due)
        early, _ = self.s.review(c, Grade.GOOD, c.last_review + days(1))
        late, _ = self.s.review(c, Grade.GOOD, c.due + days(10))
        self.assertGreater(late.stability, early.stability)

    def test_forgetting_probability(self):
        self.assertEqual(self.s.forgetting_probability(self.card, T0), 1.0)
        c, _ = self.s.review(self.card, Grade.GOOD, T0)
        p_now = self.s.forgetting_probability(c, T0)
        p_due = self.s.forgetting_probability(c, c.due)
        p_later = self.s.forgetting_probability(c, c.due + days(30))
        self.assertAlmostEqual(p_now, 0.0)
        self.assertLess(p_due, p_later)

    def test_same_day_review_uses_short_term_update(self):
        c, _ = self.s.review(self.card, Grade.AGAIN, T0)
        c2, log = self.s.review(c, Grade.GOOD, T0 + dt.timedelta(minutes=10))
        self.assertLess(log.elapsed_days, 1)
        self.assertEqual(c2.state, State.REVIEW)
        self.assertGreater(c2.stability, c.stability)

    def test_reference_vectors(self):
        """Sequência fixa → estados esperados. Gera o arquivo na primeira execução; a
        implementação TypeScript do cliente roda os mesmos vetores."""
        seq = [Grade.GOOD, Grade.GOOD, Grade.AGAIN, Grade.GOOD, Grade.EASY, Grade.HARD]
        c, now, out = Card("vetor"), T0, []
        for gr in seq:
            c, _ = self.s.review(c, gr, now)
            out.append({"grade": int(gr), "stability": round(c.stability, 6),
                        "difficulty": round(c.difficulty, 6), "due": c.due.isoformat()})
            now = c.due
        if not VECTORS.exists():
            VECTORS.write_text(json.dumps({"weights": list(self.s.w), "start": T0.isoformat(), "steps": out}, indent=2))
        expected = json.loads(VECTORS.read_text())["steps"]
        self.assertEqual(out, expected)


class TestGradeFromAnswer(unittest.TestCase):
    def test_mapping(self):
        self.assertEqual(grade_from_answer(False, 1000, 20000), Grade.AGAIN)
        self.assertEqual(grade_from_answer(True, 40000, 20000), Grade.HARD)
        self.assertEqual(grade_from_answer(True, 15000, 20000, used_hint=True), Grade.HARD)
        self.assertEqual(grade_from_answer(True, 5000, 20000), Grade.EASY)
        self.assertEqual(grade_from_answer(True, 15000, 20000), Grade.GOOD)


class TestGamification(unittest.TestCase):
    def test_xp(self):
        self.assertEqual(g.xp_for_answer(True, "basico"), 10)
        self.assertEqual(g.xp_for_answer(False, "especialista"), g.EFFORT_XP)
        self.assertEqual(g.xp_for_answer(True, "avancado", combo=5), 38)  # 25 * 1.5
        self.assertEqual(g.xp_for_answer(True, "basico", combo=100), 20)  # teto 2x
        self.assertEqual(g.xp_for_answer(True, "basico", on_time_review=True), 12)
        with self.assertRaises(ValueError):
            g.xp_for_answer(True, "impossivel")

    def test_daily_soft_cap(self):
        self.assertEqual(g.daily_xp_after_cap(150, 50), 150)
        self.assertEqual(g.daily_xp_after_cap(350, 50), 200)

    def test_levels_roundtrip(self):
        self.assertEqual(g.xp_for_level(1), 0)
        self.assertEqual(g.xp_for_level(2), 100)
        for lvl in range(1, 200):
            xp = g.xp_for_level(lvl)
            self.assertEqual(g.level_from_xp(xp), lvl)
            self.assertEqual(g.level_from_xp(xp - 1), max(1, lvl - 1))

    def test_streak(self):
        d = dt.date(2026, 10, 1)
        s = g.register_activity(g.Streak(), d)
        s = g.register_activity(s, d)  # mesmo dia
        s = g.register_activity(s, d + dt.timedelta(days=1))
        self.assertEqual((s.current, s.longest), (2, 2))
        s = g.register_activity(g.Streak(2, 2, d, freezes=1), d + dt.timedelta(days=2))
        self.assertEqual((s.current, s.freezes), (3, 0))  # protetor cobriu 1 dia
        s = g.register_activity(s, d + dt.timedelta(days=5))
        self.assertEqual((s.current, s.longest), (1, 3))
        self.assertTrue(g.is_alive(g.Streak(3, 3, d), d + dt.timedelta(days=1)))
        self.assertFalse(g.is_alive(g.Streak(3, 3, d), d + dt.timedelta(days=2)))

    def test_league_week(self):
        standings = [(f"u{i}", 1000 - i * 10) for i in range(30)]
        out = g.resolve_league_week(standings, "ouro")
        self.assertEqual([out[f"u{i}"] for i in range(7)], ["platina"] * 7)
        self.assertEqual([out[f"u{i}"] for i in range(25, 30)], ["prata"] * 5)
        self.assertEqual(out["u10"], "ouro")
        self.assertEqual(g.resolve_league_week([("a", 0), ("b", 5)], "bronze"), {"a": "bronze", "b": "prata"})
        self.assertEqual(g.resolve_league_week([("a", 9)], "grao-mestre"), {"a": "grao-mestre"})

    def test_coins(self):
        self.assertEqual(g.coins_for_day(False, 7, 3), 0)
        self.assertEqual(g.coins_for_day(True, 14, 2), 29)


class TestDifficulty(unittest.TestCase):
    def test_smoothing_keeps_new_items_near_prior(self):
        self.assertAlmostEqual(difficulty.smoothed_error_rate(1, 1), 4 / 11)
        self.assertAlmostEqual(difficulty.smoothed_error_rate(900, 1000), 903 / 1010)

    def test_tiers_follow_signals(self):
        easy = difficulty.DifficultySignals(5, 200, 40, "Todos são iguais perante a lei.")
        hard = difficulty.DifficultySignals(
            160, 200, 2,
            "Salvo disposição em contrário, aplica-se o disposto no art. 5º, exceto nos casos do § 2º "
            "do art. 7º e do inciso III do art. 9º, desde que observado o prazo, ainda que " + "palavra " * 80,
            expert_share=0.8,
        )
        self.assertEqual(difficulty.tier(easy), "basico")
        self.assertEqual(difficulty.tier(hard), "especialista")

    def test_incidence_lowers_difficulty(self):
        base = dict(errors=60, attempts=200, text="Texto médio do artigo.")
        rare = difficulty.difficulty_score(difficulty.DifficultySignals(exam_incidence=0, **base))
        common = difficulty.difficulty_score(difficulty.DifficultySignals(exam_incidence=50, **base))
        self.assertLess(common, rare)


if __name__ == "__main__":
    unittest.main()
