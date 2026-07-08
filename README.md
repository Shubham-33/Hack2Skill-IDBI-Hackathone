# Prospect Assist AI — IDBI Innovate 2026

> **Lend faster, safer, and win partner loyalty.**
> An AI channel-and-relationship intelligence layer + copilot on top of the bank's loan origination stack.

Built for **IDBI Innovate 2026** (IDBI Bank × Hack2skill). Retail lending in India runs on **DSAs / dealers / connectors** and on **TAT + partner relationships** — Prospect Assist AI is built for that reality. It works four sides: **customer, RM, bank, and channel partner.**

## Quick start

```bash
./run.sh setup     # generate synthetic data + train the two ML models (first time)
./run.sh           # start the app at http://localhost:8000
```

`run.sh` sets `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib` (WeasyPrint needs Homebrew's pango/cairo). To enable AI-written copy, put `NVIDIA_API_KEY=nvapi-...` in `.env` (free key at build.nvidia.com). Without it, the app runs in **degraded mode** with deterministic fallbacks — nothing breaks.

**LLM latency:** the interactive paths use a fast small model (`meta/llama-3.1-8b-instruct`, ~1-2s/call) with a hard 9s timeout — a slow or rate-limited call falls back to deterministic text instantly rather than hanging. Override the model via `NVIDIA_MODEL` in `.env`.

## The three demo acts

| Act | Route | What it shows |
|---|---|---|
| **1 — Customer conversion** | `/` | Queue ranked by **risk-adjusted value** → prospect detail (health + **per-decision reason codes** + recommendation) → **editable offer** (live EMI recompute, **risk-based pricing**) → **premium PDF** → send via WhatsApp/Gmail |
| **2 — Channel intelligence** | `/channel` | Partner leaderboard, **adverse-selection** flags, **channel ROI**, **book-concentration (HHI)**, duplicate leads, **churn** watchlist, payout statements with **clawback** |
| **3 — Partner relationship / TAT** | `/submit` | Submit a lead → **instant indicative decision** (<50 ms) + **Reg-B adverse-action reason codes** on declines + SLA promise + partner tier |

Plus an **agentic assistant** (💬) that routes NL commands ("top 5 prospects", "which partners are at churn risk", "best channel ROI") to the real engine.

## Architecture (3-layer, per CLAUDE.md)

- **Layer 1 `directives/`** — SOPs the agent follows.
- **Layer 3 `execution/`** — deterministic Python tools + the ML models. **Owns every number** (eligibility, rate, EMI, commission, clawback, health score). The LLM only phrases.
- **`web/`** — FastAPI + Jinja/Tailwind demo surface.

### ML models (`data/*.pkl`)
1. **Conversion propensity** — ranks the queue (AUC ~0.70; auto-selects Logistic vs GBM).
2. **Partner / lead default risk** — the *adverse-selection* detector: customer signals dominate, the sourcing partner's shrunk track record is a real but **secondary** signal (AUC ~0.80, no target leakage — partner-history feature share ~0.22).

> **AUC figures are on synthetic data and are indicative only.** The generators are grounded in realistic distributions; in production the models retrain on IDBI's real conversion + NPA history. Deterministic, explainable components (eligibility, EMI, health score) don't depend on training data at all.

### Credit-risk engineering (bank-grade, in `execution/economics.py` + `eligibility.py`)
- **Risk-adjusted queue** — leads ranked by **P(convert) × (net interest income − expected credit loss)**, where ECL = PD × LGD × exposure (product-specific NIM over a 6.5% cost of funds; secured vs. unsecured LGD; behavioural life). A loan that would *convert* but *destroy value* is correctly down-ranked (16 flagged on the synthetic book).
- **Risk-based pricing** — the ML default probability loads the offered rate **within the approved band** (only ever raises it, capped at the band ceiling). The premium is surfaced transparently.
- **Per-decision explainability** — genuine model-agnostic local attribution (mean-baseline occlusion, no `shap` dependency) → signed reason codes on every score, and **Reg-B / RBI adverse-action reason codes** on declines.
- **Portfolio concentration** — HHI + top-3 partner exposure share on the channel book.
- **Model governance** — AUC reported as **Gini (2·AUC−1)**; Bayesian shrinkage on partner risk; documented feature exclusions. See [MODEL_CARD.md](MODEL_CARD.md).

### Compliance-by-design
De-identify before any LLM call · fair-lending feature exclusions · banned-phrase check on copy · rate always clamped to band · indicative-only decisions (bureau + KYC as integration points) · swappable OpenAI-compatible LLM · adverse-action reason codes on declines.

## Verify the pieces

```bash
./run.sh test                              # full suite — 44 tests, LLM-off, offline
source .venv/bin/activate
python execution/train_propensity.py      # AUC + Gini + feature importances
python execution/train_partner_risk.py
python execution/economics.py              # risk-adjusted return by product (NIM/LGD/ECL)
python execution/score_partner.py          # partner leaderboard + adverse flags
python execution/channel_roi.py            # profit per lead by channel
python execution/instant_decision.py       # instant decisions + latency
python execution/generate_offer_pdf.py     # writes a sample PDF to .tmp/
```

## Not in the prototype (roadmap)
Real IDBI sandbox APIs, bureau/KYC integration, auth, mobile-native app, WhatsApp partner portal, models trained on real conversion + NPA history. Free NVIDIA tier is dev/eval-only → production uses NVIDIA AI Enterprise / IDBI-approved inference.
