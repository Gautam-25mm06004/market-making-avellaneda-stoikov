# Inventory-Aware Market Making: A Replication and Sensitivity Study of Avellaneda–Stoikov (2008)

**Gautam Jain** — IIT Bhubaneswar

## Abstract
We implement the Avellaneda–Stoikov (A-S) market-making model and compare its inventory-aware quotes with a symmetric
benchmark that uses the same spread but centres it on the mid-price. Over 1,000 simulated sessions with the paper's
parameters, the inventory-aware strategy at risk aversion γ = 0.1 reduces the standard deviation of final PnL from 12.8 to
6.5 and of final inventory from 8.2 to 3.0, at the cost of a 6% lower mean PnL. We then study how the trade-off changes
with risk aversion, order-book liquidity and hard inventory limits.

## 1. Model
The mid-price follows `dS = σ dW`. A quote at distance δ from the mid is filled by incoming market orders at Poisson
rate `λ(δ) = A e^{−kδ}`. A market maker with exponential utility and risk aversion γ, holding inventory q at time t,
quotes symmetrically around the reservation price

`r(s, q, t) = s − q γ σ² (T − t)`

with total spread `δ_a + δ_b = γ σ² (T − t) + (2/γ) ln(1 + γ/k)`.
The first term compensates inventory risk and vanishes at the horizon; the second is the liquidity term and tends to
`2/k` as γ → 0 (a risk-neutral market maker).

## 2. Simulation
Following the paper, the mid moves by ±σ√dt each step with equal probability; each side fills at most once per step with
probability `1 − exp(−λ(δ) dt)`; remaining inventory is marked to the final mid. Parameters: s₀ = 100, T = 1, σ = 2,
dt = 0.005 (200 steps), k = 1.5, A = 140. The symmetric benchmark uses the A-S spread at each t but centres it on s.

## 3. Results
**Replication (Table in `results/summary.md`).** For every γ tested, the inventory-aware strategy has lower PnL dispersion
and much tighter inventory. The paper reports the same ranking for γ = 0.1 (PnL std about 6 vs about 13; inventory std
about 3 vs about 9). Our mean PnL is a few units lower than the paper's, which we attribute to using `1 − e^{−λdt}` rather
than `λdt` as the fill probability, which caps fills slightly.

**Risk aversion.** Increasing γ moves the strategy along a frontier: from γ = 0.005 to 2, mean PnL falls from 60.1 to 14.1
while PnL std falls from 10.3 to 3.1. Higher γ widens the spread (fewer fills) and skews quotes harder against inventory.

**Liquidity.** With k = 0.5 (fills decay slowly with distance) the optimal spread is 3.8 and mean PnL 177; with k = 6 the
spread is 0.53 and PnL 12. The inventory-aware strategy reduces PnL std at every k, most strongly in liquid books
(k = 6: 2.2 vs 8.9).

**Inventory limits.** Adding a hard limit |q| ≤ 2 on top of A-S quotes halves inventory dispersion again (3.0 → 1.3) but
costs about 7% of mean PnL, because the strategy stops quoting one side and misses spread income.

## 4. Limitations
The mid-price is independent of our trades (no adverse selection), fills are one unit, and arrival intensities are
constant over time. Real books show order-flow toxicity, queue position effects and intraday seasonality in A and k.
Extensions such as Guéant, Lehalle & Fernandez-Tapia (2013) add inventory constraints in closed form.

## References
1. M. Avellaneda, S. Stoikov. High-frequency trading in a limit order book. *Quantitative Finance* 8(3), 217–224, 2008.
2. O. Guéant, C.-A. Lehalle, J. Fernandez-Tapia. Dealing with the inventory risk: a solution to the market making problem. *Mathematics and Financial Economics* 7, 477–507, 2013.
3. T. Ho, H. Stoll. Optimal dealer pricing under transactions and return uncertainty. *Journal of Financial Economics* 9, 47–73, 1981.
