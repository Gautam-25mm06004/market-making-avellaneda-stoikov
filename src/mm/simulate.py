"""Vectorised Monte Carlo simulator for the Avellaneda-Stoikov market-making problem."""
import numpy as np
from .model import MMParams, fill_prob


def simulate(strategy, p: MMParams, n_paths: int = 1000, seed: int = 0, record_path: bool = False):
    """Run n_paths independent trading sessions with the given quoting strategy.

    strategy(s, q, t, p) -> (bid, ask) arrays. Each step: quote, draw fills (one unit per side at most),
    then move the mid by sigma * sqrt(dt) * (+1/-1), as in the paper's binomial mid-price.
    Returns a dict with final PnL, final inventory and (optionally) one recorded path.
    """
    rng = np.random.default_rng(seed)
    s = np.full(n_paths, p.s0)
    q = np.zeros(n_paths)
    cash = np.zeros(n_paths)
    n_bid = np.zeros(n_paths)
    n_ask = np.zeros(n_paths)
    spreads = []
    path = {"t": [], "s": [], "bid": [], "ask": [], "q": [], "pnl": []} if record_path else None
    for i in range(p.n_steps):
        t = i * p.dt
        bid, ask = strategy(s, q, t, p)
        bid_ok = np.ones(n_paths, bool)
        ask_ok = np.ones(n_paths, bool)
        if p.q_max is not None:
            bid_ok = q < p.q_max
            ask_ok = q > -p.q_max
        hit_bid = (rng.random(n_paths) < fill_prob(s - bid, p)) & bid_ok
        hit_ask = (rng.random(n_paths) < fill_prob(ask - s, p)) & ask_ok
        q += hit_bid.astype(float) - hit_ask.astype(float)
        cash += np.where(hit_ask, ask, 0.0) - np.where(hit_bid, bid, 0.0)
        n_bid += hit_bid
        n_ask += hit_ask
        spreads.append(np.mean(ask - bid))
        if record_path:
            for key, val in (("t", t), ("s", s[0]), ("bid", bid[0]), ("ask", ask[0]), ("q", q[0]), ("pnl", cash[0] + q[0] * s[0])):
                path[key].append(float(val))
        s = s + p.sigma * np.sqrt(p.dt) * np.where(rng.random(n_paths) < 0.5, 1.0, -1.0)
    pnl = cash + q * s  # mark remaining inventory to the final mid
    return {"pnl": pnl, "q": q, "trades": n_bid + n_ask, "avg_spread": float(np.mean(spreads)), "path": path}


def summarize(res) -> dict:
    pnl, q = res["pnl"], res["q"]
    return {
        "mean_pnl": float(np.mean(pnl)),
        "std_pnl": float(np.std(pnl, ddof=1)),
        "sharpe_like": float(np.mean(pnl) / np.std(pnl, ddof=1)),
        "mean_final_q": float(np.mean(q)),
        "std_final_q": float(np.std(q, ddof=1)),
        "mean_abs_final_q": float(np.mean(np.abs(q))),
        "mean_trades": float(np.mean(res["trades"])),
        "avg_spread": res["avg_spread"],
        "pnl_p05": float(np.percentile(pnl, 5)),
    }
