# Manage Channel (Partner Intelligence)

## Goal
Score channel partners, catch adverse selection + duplicates, compute payouts, and rank channel ROI.

## Inputs
- Partners (`data/partners.json`), prospects, disbursals.

## Tools / Scripts
- `execution/score_partner.py` — partner quality score + tier; per-lead default risk (`partner_risk.pkl`).
- `execution/commission.py` — commission + clawback payout statements.
- `execution/dedupe_leads.py` — duplicate / multi-sourced lead detection.
- `execution/channel_roi.py` — profit-per-lead by channel.

## Steps
1. Rank partners by quality; flag adverse selection (high volume + high default).
2. Detect duplicate leads across channels.
3. Compute payouts with clawback; rank channel ROI.

## Outputs
- Channel dashboard (`/channel`) + partner detail (`/partner/{id}`).

## Edge cases & learnings
- Partner default risk uses Bayesian shrinkage so low-volume DSAs aren't unfairly penalised (`features.partner_risk_features`).
- Frame flags as collaborative "partner development", not blacklisting.
