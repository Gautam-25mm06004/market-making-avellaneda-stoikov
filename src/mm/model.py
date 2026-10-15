"""Closed-form quotes from Avellaneda & Stoikov (2008), 'High-frequency trading in a limit order book'.

Setup: the mid-price follows dS = sigma dW. Market orders hit our ask (bid) with intensity
lambda(delta) = A * exp(-k * delta), where delta is the distance of our quote from the mid.
A market maker with exponential utility (risk aversion gamma) and horizon T quotes around a
*reservation price* that is shifted against its inventory q.
"""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class MMParams:
    s0: float = 100.0      # initial mid-price
    T: float = 1.0         # horizon
    sigma: float = 2.0     # mid-price volatility (price units per sqrt(time))
    dt: float = 0.005      # time step
    gamma: float = 0.1     # risk aversion
    k: float = 1.5         # order-book liquidity: decay of fill intensity with distance
    A: float = 140.0       # fill intensity at zero distance
    q_max: int | None = None  # optional hard inventory limit (stop quoting the side that would breach it)

    @property
    def n_steps(self) -> int:
        return int(round(self.T / self.dt))


def reservation_price(s, q, t, p: MMParams):
    """r(s, q, t) = s - q * gamma * sigma^2 * (T - t)   (eq. 29 in the paper)."""
    return s - q * p.gamma * p.sigma ** 2 * (p.T - t)


def optimal_spread(t, p: MMParams):
    """Total bid-ask spread delta_a + delta_b = gamma sigma^2 (T - t) + (2/gamma) ln(1 + gamma/k)   (eq. 30)."""
    return p.gamma * p.sigma ** 2 * (p.T - t) + (2.0 / p.gamma) * np.log1p(p.gamma / p.k)


def as_quotes(s, q, t, p: MMParams):
    """Inventory-aware quotes: centred on the reservation price."""
    r = reservation_price(s, q, t, p)
    half = optimal_spread(t, p) / 2.0
    return r - half, r + half


def symmetric_quotes(s, q, t, p: MMParams):
    """Benchmark from the paper: same spread, but centred on the mid-price (ignores inventory)."""
    half = optimal_spread(t, p) / 2.0
    return s - half, s + half


def fill_prob(delta, p: MMParams):
    """Probability of at least one fill in dt for a quote at distance delta: 1 - exp(-lambda dt) ~ lambda dt."""
    lam = p.A * np.exp(-p.k * np.maximum(delta, 0.0))
    return 1.0 - np.exp(-lam * p.dt)
