# Manage Partner Relationship (TAT + Loyalty)

## Goal
Win partner loyalty via instant decisions, SLA transparency, tiering incentives, and churn prevention — the moat.

## Inputs
- A submitted lead; a partner.

## Tools / Scripts
- `execution/instant_decision.py` — instant indicative decision + offer at submission.
- `execution/predict_tat.py` — expected decision TAT + SLA state.
- `execution/partner_tier.py` — tier → commission boost, priority, faster payout, SLA promise.
- `execution/partner_churn.py` — churn early-warning + recommended RM action.

## Steps
1. On `/submit`, return an instant indicative decision the DSA relays on the spot.
2. Track each lead on the SLA clock; escalate breaches.
3. Reward quality via tiers; flag churning partners for proactive re-engagement.

## Outputs
- Instant decision card; SLA states; tier benefits; churn watchlist.

## Edge cases & learnings
- "Instant" = INDICATIVE only; hard decision after bureau (CIBIL) + KYC — state the disclaimer.
- Instant decision must stay fast (<~50ms without LLM); keep the LLM off the submission hot path.
