"""Reproduce the Avellaneda-Stoikov comparison and run extension experiments.

Writes results/results.json, results/summary.md and figures to results/figures/.
Usage:  python scripts/run_experiments.py [--paths 1000]
"""
import argparse, json, sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from mm import MMParams, as_quotes, symmetric_quotes, simulate, summarize  # noqa: E402

OUT = ROOT / "results"
FIG = OUT / "figures"
FIG.mkdir(parents=True, exist_ok=True)


def table(rows, cols):
    head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    return head + "".join("| " + " | ".join(str(r[c]) for c in cols) + " |\n" for r in rows)


def main(n_paths: int):
    base = MMParams()
    results = {"params": base.__dict__, "n_paths": n_paths}

    # 1) Paper replication: inventory strategy vs symmetric strategy for three risk aversions
    rep = []
    for g in (0.01, 0.1, 0.5):
        p = replace(base, gamma=g)
        for name, strat in (("inventory (A-S)", as_quotes), ("symmetric", symmetric_quotes)):
            s = summarize(simulate(strat, p, n_paths, seed=42))
            rep.append({"gamma": g, "strategy": name, **{k: round(v, 3) for k, v in s.items()}})
    results["replication"] = rep

    # 2) Risk-return frontier over gamma
    frontier = []
    for g in np.geomspace(0.005, 2.0, 12):
        p = replace(base, gamma=float(g))
        s = summarize(simulate(as_quotes, p, n_paths, seed=7))
        frontier.append({"gamma": round(float(g), 4), **{k: round(v, 3) for k, v in s.items()}})
    sym = summarize(simulate(symmetric_quotes, replace(base, gamma=0.1), n_paths, seed=7))
    results["frontier"] = frontier
    results["symmetric_reference"] = {k: round(v, 3) for k, v in sym.items()}

    # 3) Liquidity sensitivity (k) at gamma = 0.1
    liq = []
    for k in (0.5, 1.0, 1.5, 3.0, 6.0):
        p = replace(base, k=k)
        a = summarize(simulate(as_quotes, p, n_paths, seed=11))
        b = summarize(simulate(symmetric_quotes, p, n_paths, seed=11))
        liq.append({"k": k, "AS_mean_pnl": round(a["mean_pnl"], 2), "AS_std_pnl": round(a["std_pnl"], 2),
                    "SYM_mean_pnl": round(b["mean_pnl"], 2), "SYM_std_pnl": round(b["std_pnl"], 2),
                    "AS_spread": round(a["avg_spread"], 3), "AS_trades": round(a["mean_trades"], 1)})
    results["liquidity"] = liq

    # 4) Hard inventory limits on top of the A-S quotes
    lim = []
    for qm in (None, 10, 5, 2):
        p = replace(base, q_max=qm)
        s = summarize(simulate(as_quotes, p, n_paths, seed=13))
        lim.append({"q_max": "none" if qm is None else qm, **{k: round(v, 3) for k, v in s.items()}})
    results["inventory_limits"] = lim

    # Figures
    p = replace(base, gamma=0.1)
    one = simulate(as_quotes, p, 1, seed=3, record_path=True)["path"]
    fig, ax = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    ax[0].plot(one["t"], one["s"], label="mid", lw=1)
    ax[0].plot(one["t"], one["bid"], label="bid", lw=0.7)
    ax[0].plot(one["t"], one["ask"], label="ask", lw=0.7)
    ax[0].set_ylabel("price"); ax[0].legend(); ax[0].set_title("One session, A-S quotes (gamma = 0.1)")
    ax[1].step(one["t"], one["q"], where="post"); ax[1].set_ylabel("inventory"); ax[1].set_xlabel("time")
    fig.tight_layout(); fig.savefig(FIG / "sample_path.png", dpi=130); plt.close(fig)

    a = simulate(as_quotes, p, n_paths, seed=42)
    b = simulate(symmetric_quotes, p, n_paths, seed=42)
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].hist(a["pnl"], bins=40, alpha=0.6, label="inventory (A-S)"); ax[0].hist(b["pnl"], bins=40, alpha=0.6, label="symmetric")
    ax[0].set_title("Final PnL"); ax[0].legend()
    ax[1].hist(a["q"], bins=30, alpha=0.6, label="inventory (A-S)"); ax[1].hist(b["q"], bins=30, alpha=0.6, label="symmetric")
    ax[1].set_title("Final inventory"); ax[1].legend()
    fig.tight_layout(); fig.savefig(FIG / "pnl_inventory_hist.png", dpi=130); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot([r["std_pnl"] for r in frontier], [r["mean_pnl"] for r in frontier], "o-", label="A-S, varying gamma")
    for r in frontier[::3]:
        ax.annotate(f"g={r['gamma']:.2g}", (r["std_pnl"], r["mean_pnl"]), fontsize=7)
    ax.plot(sym["std_pnl"], sym["mean_pnl"], "rs", label="symmetric (gamma=0.1 spread)")
    ax.set_xlabel("std of final PnL"); ax.set_ylabel("mean final PnL"); ax.legend(); ax.set_title("Risk-return frontier")
    fig.tight_layout(); fig.savefig(FIG / "frontier.png", dpi=130); plt.close(fig)

    (OUT / "results.json").write_text(json.dumps(results, indent=2))
    cols = ["gamma", "strategy", "avg_spread", "mean_pnl", "std_pnl", "mean_final_q", "std_final_q", "mean_trades"]
    md = f"# Results ({n_paths} simulated sessions per row)\n\n## Inventory strategy vs symmetric strategy\n\n" + table(rep, cols)
    md += "\n## Liquidity sensitivity (gamma = 0.1)\n\n" + table(liq, list(liq[0]))
    md += "\n## Hard inventory limits (gamma = 0.1)\n\n" + table(lim, ["q_max", "mean_pnl", "std_pnl", "std_final_q", "mean_trades"])
    md += "\n## Frontier (A-S, varying gamma)\n\n" + table(frontier, ["gamma", "avg_spread", "mean_pnl", "std_pnl", "std_final_q"])
    (OUT / "summary.md").write_text(md)
    print(md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", type=int, default=1000)
    main(ap.parse_args().paths)
