# Demo Runbook — Prospect Assist AI (≈3 minutes)

**One-liner to open with:** *"Retail lending doesn't walk in — it comes through DSAs and dealers, and it runs on turnaround time and relationships. Prospect Assist AI is the AI copilot for exactly that."*

## Before you start
```bash
./run.sh                      # http://localhost:8000  (models + data auto-load)
```
- Confirm `/health` shows `"llm": true`.
- Open tabs: **Dashboard (/)**, **Partner Portal**, and **Pitch Deck** (▶ top-right).
- Pre-open the 🤖 assistant once so it's warm.

## The spine (don't deviate — everything else is "and there's more")

### Act 1 — RM converts a lead (≈70s)
1. **Dashboard**: "The queue is ranked by **risk-adjusted value** — P(convert) × (net interest income − expected credit loss). We don't chase who'll just *convert*; we chase who's *profitable net of expected loss*." Point at the **charts** and the **Risk-adj. value** stat.
2. Click the **top prospect** → show **"How this prospect is ranked"** with the **reason codes** (Δ P(convert) per factor, ▲/▼) and **Key risk factors**. *"Genuine per-decision attribution — no black box."*
3. **Create Offer** → nudge the **amount** up → *"EMI recomputes live, an out-of-band rate auto-clamps, and the rate is **risk-based-priced** — the model's default probability loads it within the approved band. The RM can't send a non-compliant offer."*
4. **Generate PDF** → the branded offer opens, incl. **"You may also qualify for"** cross-sell. **Send** → WhatsApp prefilled.

### Act 2 — The moat: the partner's view (≈60s)
5. **Partner Portal** → pick a DSA → **➕ Submit a lead** → **Send to IDBI ⚡**.
6. *"Instant in-principle decision, back on WhatsApp in milliseconds — the DSA answers the customer on the spot. That's how we win the TAT battle."* On a declined lead, point at the **adverse-action reason codes**: *"and a decline comes with Reg-B / RBI reason codes — exactly what a lender must give an applicant."*
7. **🏅 My tier & payout** → *"Transparent, fast, tier-based payouts — with clawback. This is why partners route more business to us."*

### Act 3 — Channel intelligence (≈40s)
8. **Channel Intelligence** → point at a **⚠ adverse-selection** partner. *"This DSA brings volume but high defaults — our partner-aware risk model flags it before disbursal."* Show **channel ROI**, **book concentration (HHI)** — *"how much of the book rides on one partner"* — and the **churn watchlist**.

### Close (≈15s)
9. Open the 🤖 assistant: *"create a lead for Meera, personal loan 5 lakh, income 70000, cibil 750"* → it scores + explains + offers a PDF. *"A pro RM copilot that does the whole job in plain language."*
10. Land the line: **"Faster decisions, fewer defaults, loyal partners."**

## Backups if something misbehaves
- LLM slow/rate-limited → it **auto-falls back to deterministic copy**; keep going, the numbers are identical.
- PDF didn't pop → it **downloads**; open it from the download bar.
- Odd input → engine **clamps** it; no crash.
- Whole app down → present from the **Pitch Deck** (arrow keys); it carries the live numbers.

## Numbers to have ready
- Propensity AUC ~0.69 (Gini 39) · Partner default-risk AUC ~0.81 (Gini 62) (**synthetic data — indicative**).
- Queue ranks by **risk-adjusted value** = P(convert) × (NII − ECL), ECL = PD × LGD × exposure; recommendations are **suitability-first** (bank revenue shown to the RM but never drives the ranking).
- ~₹16 Cr pipeline · ₹0.68 Cr risk-adjusted value · 9 value-destructive leads down-ranked · 3 adverse-selection partners.
- Impact (illustrative): TAT days→hours · NPA −20–30 bps · payout leakage → 0 · partner loyalty ↑.
- Coverage: Conversational AI · Wealth Advisory · Financial Health Scoring · Default Prediction. · **44 tests pass.**

## If a judge pushes
- *"Synthetic data?"* → "Yes, and disclosed. The deterministic + explainable core doesn't depend on training data; models retrain on your real conversion/NPA history in the PoC."
- *"Isn't partner-risk circular?"* → "We deliberately kept the partner signal secondary (feature share ~0.22) and customer-driven; no target leakage. Bayesian shrinkage keeps it fair to small DSAs."
- *"How do you explain a decision / a decline?"* → "Every score ships per-decision reason codes via occlusion attribution, and declines get Reg-B / RBI adverse-action codes — see MODEL_CARD.md."
- *"NVIDIA free tier in production?"* → "The LLM is swappable (OpenAI-compatible) — NVIDIA AI Enterprise or on-prem/VPC; PII is de-identified before any LLM call."
