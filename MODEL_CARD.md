# Model Card — Prospect Assist AI

Governance sheet for the two ML models, written for a bank model-risk / credit-risk review. Both are **synthetically trained** for the prototype; the framework, features and controls are what would carry into a production PoC on IDBI's real data.

---

## Model 1 — Conversion Propensity

| | |
|---|---|
| **Purpose** | Rank the RM's prospect queue by P(the lead converts to a disbursed loan). |
| **Type** | Binary classifier; auto-selects the better of GradientBoosting vs. Logistic (scaled) on held-out AUC. Prototype selects **Logistic**. |
| **Target** | `outcome.converted` on ~2,500 historical leads (38% positive). |
| **Performance** | Hold-out **AUC 0.69 · Gini 39** (25% test split, stratified). Directional on synthetic data. |
| **Output** | `propensity` (0–1), tier (Hot/Warm/Cold), `baseline`, ranked per-decision `reason_codes`. |
| **Use** | Feeds the **risk-adjusted** queue value `P(convert) × (NII − ECL)` — never the sole ranking key. |

## Model 2 — Partner / Lead Default-Risk (adverse-selection detector)

| | |
|---|---|
| **Purpose** | Flag likely-to-default loans *before* disbursal, incorporating the **sourcing partner's** track record — catching DSA adverse selection. |
| **Type** | Binary classifier (Logistic/GBM auto-select). Trained only on **disbursed** loans (default is undefined otherwise). |
| **Target** | `outcome.defaulted` among converted leads (~13% positive). |
| **Performance** | Hold-out **AUC 0.81 · Gini 62**. |
| **Anti-leakage** | Partner-history features contribute **0.22** of importance (asserted `< 0.4` in tests) — customer signals dominate; the partner track record is a *secondary* signal, not a circular label. |
| **Fairness** | Partner effect uses **Bayesian shrinkage** (prior 0.08, strength 40) → new/small DSAs are pulled toward the population mean, not penalised for low volume. |
| **Output** | `default_risk`, band (Low/Med/High), `reason_codes`, **`adverse_action_codes`**. |
| **Use** | Drives ECL in the queue, **risk-based pricing** (loads rate within band), and the channel adverse-selection flag. |

---

## Features & exclusions (fair lending)

Single source of truth: [`execution/features.py`](execution/features.py).

- **Propensity:** income, credit score, FOIR, loan-to-income, savings ratio, balance cushion, cheque bounces, regular-salary flag, credit/income headroom vs. product floor, product fit.
- **Default-risk:** credit score, FOIR, bounces, loan-to-income, savings ratio, regular-salary flag, post-loan EMI burden, partner default-rate (shrunk), partner conversion, partner doc quality.
- **Deliberately EXCLUDED** — name, **gender, religion, caste**, city/location. Only financial/behavioural signals are modelled.

## Explainability

Every score ships **per-decision reason codes** via model-agnostic **mean-baseline occlusion** ([`execution/explain.py`](execution/explain.py)) — no `shap` dependency. For each feature, the contribution is the Δ in predicted probability when only that feature is moved from the population mean to the applicant's actual value (exact for linear models; a faithful local attribution for trees). Declined leads receive **Reg-B / RBI-style adverse-action reason codes** (principal reasons + the applicant's value vs. a typical value).

## The numbers boundary

ML outputs **probabilities only**. Every rupee figure — eligibility, rate, EMI, commission, clawback, ECL, risk-adjusted value — comes from the **deterministic engine** ([`eligibility.py`](execution/eligibility.py), [`economics.py`](execution/economics.py)). The LLM only phrases text and is given **de-identified** input. RM edits re-validate through the engine (rate clamped to band, EMI recomputed).

## Assumptions (economics)

Cost of funds **6.5%** · product-specific NIM (rate − CoF) · LGD by product (home 20% … personal 70%) · behavioural life 1.5–7 yrs · risk-based-pricing load capped at half the spread and the band ceiling. Illustrative; recalibrated to IDBI curves in the PoC.

## Monitoring & retraining (production plan)

- **Closed loop:** RM outcome capture (won/lost/nurture) + disbursal/default/TAT feedback → periodic retraining. The compounding data moat.
- **Drift:** track **PSI** on key features and score distributions; alert on population shift.
- **Stability:** monitor AUC/Gini and calibration by vintage; re-fit thresholds.
- **Governance:** versioned model artifacts, documented feature lineage, challenger models, human override with audit trail.

## Known limitations

Synthetic training data (indicative metrics only) · indicative decisions require bureau + KYC to become sanctions · free NVIDIA tier is dev/eval-only · no real PII or auth in the prototype.
