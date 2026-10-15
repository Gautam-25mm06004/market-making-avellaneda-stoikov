import sys, unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from mm import MMParams, as_quotes, symmetric_quotes, optimal_spread, reservation_price, simulate, summarize  # noqa: E402


class TestFormulas(unittest.TestCase):
    def setUp(self):
        self.p = MMParams()

    def test_reservation_price_moves_against_inventory(self):
        s, t = 100.0, 0.2
        self.assertLess(reservation_price(s, 5, t, self.p), s)      # long -> lower quotes to sell
        self.assertGreater(reservation_price(s, -5, t, self.p), s)  # short -> higher quotes to buy
        self.assertAlmostEqual(reservation_price(s, 0, t, self.p), s)

    def test_reservation_price_converges_to_mid_at_horizon(self):
        self.assertAlmostEqual(reservation_price(100.0, 10, self.p.T, self.p), 100.0)

    def test_spread_formula(self):
        p = self.p
        expected = p.gamma * p.sigma ** 2 * p.T + 2 / p.gamma * np.log(1 + p.gamma / p.k)
        self.assertAlmostEqual(optimal_spread(0.0, p), expected)
        self.assertGreater(optimal_spread(0.0, p), optimal_spread(0.9, p))  # spread narrows near the end

    def test_small_gamma_limit(self):
        # as gamma -> 0 the spread tends to 2/k (risk-neutral market maker)
        p = replace(self.p, gamma=1e-6)
        self.assertAlmostEqual(optimal_spread(0.0, p), 2 / p.k, places=3)

    def test_symmetric_quotes_centred_on_mid(self):
        b, a = symmetric_quotes(100.0, 7, 0.1, self.p)
        self.assertAlmostEqual((a + b) / 2, 100.0)


class TestSimulation(unittest.TestCase):
    def test_inventory_strategy_controls_inventory(self):
        p = MMParams()
        a = summarize(simulate(as_quotes, p, 300, seed=1))
        b = summarize(simulate(symmetric_quotes, p, 300, seed=1))
        self.assertLess(a["std_final_q"], b["std_final_q"])
        self.assertLess(a["std_pnl"], b["std_pnl"])

    def test_inventory_limit_respected(self):
        p = replace(MMParams(), q_max=3)
        res = simulate(symmetric_quotes, p, 200, seed=2)
        self.assertLessEqual(np.max(np.abs(res["q"])), 3)

    def test_deterministic_with_seed(self):
        p = MMParams()
        r1 = simulate(as_quotes, p, 50, seed=5)["pnl"]
        r2 = simulate(as_quotes, p, 50, seed=5)["pnl"]
        np.testing.assert_allclose(r1, r2)


if __name__ == "__main__":
    unittest.main()
