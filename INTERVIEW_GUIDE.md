# Interview guide — Market Making (Avellaneda–Stoikov)

## The 30-second version
"A market maker earns the bid-ask spread but carries inventory risk. Avellaneda–Stoikov solve for the quotes that maximise
risk-adjusted profit. The key idea is a reservation price that shifts down when you are long and up when you are short, so
you are more likely to sell when long and buy when short. I implemented it from the formulas, simulated 1,000 sessions, and
showed that versus quoting symmetrically around the mid, it cuts PnL volatility roughly in half for about 6% less mean profit."

## Things you must be able to explain
- **Reservation price** `r = s − qγσ²(T−t)`: your personal indifference price. Long inventory (q > 0) → r below mid → your
  ask gets closer to the mid (sells faster) and your bid moves away (buys slower).
- **Spread** `γσ²(T−t) + (2/γ)ln(1+γ/k)`: first term pays for inventory risk (bigger when volatile, risk-averse, or far from
  the end); second term comes from the order book: if fills fall off fast with distance (large k), quote tight.
- **Fill model**: intensity `A·e^(−kδ)`. A = how much flow there is; k = how quickly fills disappear as you quote further away.
- **Why mean PnL is lower but the strategy is "better"**: it trades some expected profit for much lower variance. A Sharpe-like
  ratio (mean/std) is ~8.8 vs ~4.7 for symmetric at γ = 0.1.

## Likely questions
1. *What happens as γ → 0?* The skew disappears and the spread tends to 2/k — a risk-neutral market maker. Our frontier shows
   that PnL std grows as γ falls.
2. *What is missing vs real markets?* Adverse selection (informed traders move the price after they hit you), queue position,
   discrete ticks, latency, time-varying intensity. Fills here do not move the mid.
3. *How would you estimate A and k from data?* Count market-order arrivals that reach each depth δ in trade-and-quote data,
   fit `log λ(δ) = log A − kδ` by regression.
4. *Why do hard limits cost PnL?* When |q| hits the limit you stop quoting one side, so you lose that side's spread income.
5. *How did you check the code?* Unit tests: reservation price equals mid when q = 0 or t = T, spread tends to 2/k for tiny γ,
   inventory limits are never breached, results are reproducible with a seed.

## Numbers to remember (γ = 0.1)
PnL std 6.5 vs 12.8 · inventory std 3.0 vs 8.2 · mean PnL 57.2 vs 60.8.
