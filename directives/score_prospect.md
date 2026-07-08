# Score Prospect (Financial Health)

## Goal
Produce an explainable 0-100 financial-health score that drives eligibility and recommendations.

## Inputs
- A prospect record (income, credit score, FOIR, transaction summary).

## Tools / Scripts
- `execution/score_financial_health.py` — `score_financial_health(prospect)` → score, band, factor breakdown, top strengths/gaps.

## Steps
1. Run the weighted rubric (credit 30%, FOIR 22%, savings 18%, balance 12%, bounces 10%, income regularity 8%).
2. Surface the factor breakdown so the score is auditable and the LLM can phrase a "because…".

## Outputs
- Score (0-100), band (Weak→Excellent), per-factor contributions.

## Edge cases & learnings
- Deterministic only — no ML, no LLM on the number. This is what makes it defensible to banking judges.
