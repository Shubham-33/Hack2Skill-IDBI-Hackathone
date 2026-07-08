# Prospect Assist AI — IDBI Innovate 2026 Submission

> **Lend faster, safer, and win partner loyalty.**
> An AI channel-and-relationship intelligence layer + RM copilot that sits *on top of* the bank's existing LOS/BRE/LMS — integrate, don't replace.

**Event:** IDBI Innovate 2026 (IDBI Bank × Hack2skill) · **Track:** Open · **Stage:** Working prototype

---

## 1. The problem

Most Indian retail-loan volume is **not walk-in** — it's sourced through **DSAs, dealers, connectors and aggregators**, and that business runs on two things: **TAT (turnaround time)** and **relationships**. Today that channel leaks money and hides risk:

- RMs chase the wrong leads; there's no view of *which lead is actually profitable*.
- DSAs paid on disbursal push **high-default loans** (adverse selection) → NPAs.
- Decisions are slow and opaque → the DSA's customer goes to a faster lender, and the DSA churns.
- Commission disputes and payout leakage erode trust.

## 2. The solution — a four-sided win

| Party | What they get |
|---|---|
| **RM / Bank** | A queue ranked by **risk-adjusted profit**, auto health-scoring, adverse-selection flags, channel ROI, concentration risk, zero-leakage payouts |
| **Customer** | Only *suitable*, eligible, clearly-explained offers; an **instant in-principle decision**; a premium personalized PDF |
| **Channel partner (DSA)** | Instant decisions, a live SLA clock, transparent auto-payouts, quality-based **tiering**, and feedback — the loyalty moat |
| **Regulator / Risk** | Explainable scores, **adverse-action reason codes**, fair-lending exclusions, rate always within band |

**North-star metric:** *profitable disbursals per RM per month* — conversion × loan quality × efficiency.

## 3. What's built (working today, not slideware)

Three live acts + an agentic copilot:

1. **Customer conversion** (`/`) — queue ranked by **risk-adjusted value** = `P(convert) × (net interest income − expected credit loss)` → prospect profile with **per-decision reason codes** → **editable offer** (live EMI recompute, **risk-based pricing within band**) → **premium branded PDF** → WhatsApp/Gmail send.
2. **Channel intelligence** (`/channel`) — partner leaderboard, **adverse-selection** flags, **channel-mix ROI**, **book concentration (HHI)**, duplicate/fraud detection, **churn** watchlist, payout statements with **clawback**.
3. **Partner relationship / TAT** (`/submit`) — a DSA submits a lead → **instant indicative decision (<50 ms)** with **Reg-B / RBI adverse-action reason codes** on declines → SLA promise → partner tier.
4. **AI Copilot** (💬) — natural-language commands ("top 5 prospects", "which partners are at churn risk", "create a lead for…") routed to the real deterministic engine. Numbers never hallucinated.

## 4. Problem-statement coverage

| Statement | How we address it |
|---|---|
| **Conversational AI** | Agentic assistant that *executes* engine commands, de-identified LLM input |
| **Wealth / product advisory** | Suitability-first next-best-product recommendation (revenue never drives ranking) |
| **Financial Health Scoring** | Transparent weighted rubric → 0–100, fully auditable |
| **Default Prediction / ML** | Two models: conversion propensity + a novel **partner/lead adverse-selection** detector |

## 5. The intelligence (real ML + bank-grade economics)

- **Conversion propensity** — AUC **0.69 (Gini 39)**, auto-selects Logistic vs GBM.
- **Partner / lead default-risk** — the adverse-selection detector; AUC **0.81 (Gini 62)**; customer signals dominate, the sourcing partner's **Bayesian-shrunk** track record is a *secondary* signal (feature share 0.22 — **no target leakage**).
- **Risk-adjusted economics** ([economics.py](execution/economics.py)) — product-specific NIM over a 6.5% cost of funds, secured/unsecured **LGD**, behavioural life, **ECL = PD × LGD × exposure**.
- **Risk-based pricing** — PD loads the offered rate within the approved band; on the synthetic book this **rescued 7 loans** from value-destructive to viable by pricing for risk (9 remain flagged and down-ranked).
- **Per-decision explainability** — genuine model-agnostic local attribution (mean-baseline occlusion, no `shap` dependency), signed reason codes + adverse-action codes. See [MODEL_CARD.md](MODEL_CARD.md).

## 6. Business impact (illustrative — assumptions stated)

On the synthetic book: **141 leads · ₹16.4 Cr pipeline · ₹0.68 Cr risk-adjusted expected value · 9 value-destructive leads down-ranked · 3 adverse-selection partners flagged.**

- **TAT:** channel decision days → **hours** (instant indicative) → higher capture.
- **NPA:** adverse-selection flagging → illustrative **20–30 bps** off the channel book.
- **Payout leakage:** manual errors → **~0** via the deterministic clawback engine.
- **Flywheel:** win the partner → more & better volume → more data → sharper models.

## 7. Architecture (3-layer — reliability by design)

**Directives (SOPs) → AI orchestration (LLM) → Deterministic engine + ML.** The engine owns *every number* (eligibility, rate, EMI, commission, clawback, health, economics); ML owns prediction; the LLM only phrases. RM stays in control via the editable offer; edits re-validate through the engine.

**Stack:** Python · FastAPI · Jinja2 + Tailwind (server-rendered, no build step) · scikit-learn · WeasyPrint (PDF) · NVIDIA NIM (OpenAI-compatible, free tier) · **44 automated tests**.

## 8. Compliance-by-design

De-identify before any LLM call · fair-lending feature exclusions (no gender/religion/caste/city) · banned-phrase check on generated copy · rate clamped to band · **indicative-only** decisions (CIBIL bureau + KYC as named integration points) · **adverse-action reason codes** on declines · swappable OpenAI-compatible LLM (→ NVIDIA AI Enterprise / on-prem in production).

## 9. Prototype vs. production roadmap

**Prototype now:** synthetic data + synthetically-trained models, local demo, indicative decisions.
**Post-shortlist PoC:** IDBI sandbox APIs, real bureau/KYC, models retrained on IDBI's real conversion + NPA + TAT history, auth, full partner portal, LOS/LMS integration, NVIDIA AI Enterprise / IDBI-approved inference.

## 10. Run it

```bash
./run.sh setup     # generate synthetic data + train the two ML models
./run.sh           # http://localhost:8000
./run.sh test      # 44 tests, offline, LLM-off
```

See [README.md](README.md) for details and [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md) for the 3-minute demo script.

---

*Team: [add member names / roles here] · Repo: [add link] · Demo video: [add link]*
