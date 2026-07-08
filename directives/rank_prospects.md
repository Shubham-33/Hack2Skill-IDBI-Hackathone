# Rank Prospects

## Goal
Order the RM's lead queue by likelihood to convert, so the highest-value prospects surface first.

## Inputs
- Live prospects (`data/prospects.json`).

## Tools / Scripts
- `execution/predict_propensity.py` — `predict_propensity(prospect)` → P(convert), tier (Hot/Warm/Cold), and per-prospect drivers.
- Model artifact `data/propensity.pkl` (retrain via `execution/train_propensity.py`).

## Steps
1. For each prospect, compute propensity + drivers.
2. Sort descending by propensity; surface tier + the "why ranked here" reason.
3. The dashboard (`GET /`) caches this via `ranked_queue()`.

## Outputs
- Ranked queue with propensity %, tier, and explanation.

## Edge cases & learnings
- Conversion signal is fairly linear → `train_propensity.py` auto-selects Logistic over GBM (AUC ~0.71).
- Only financial/behavioural features are used — prohibited attributes (gender, religion, caste, city) are excluded for fair-lending compliance (see `execution/features.py`).
