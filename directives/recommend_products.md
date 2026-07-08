# Recommend Products (Next-Best-Product)

## Goal
Recommend the eligible IDBI product(s) most likely to convert, with a plain-language rationale.

## Inputs
- A prospect record.

## Tools / Scripts
- `execution/recommend_products.py` — `recommend(prospect)`.
- `execution/eligibility.py` — deterministic eligibility + rate/EMI.
- `execution/nvidia_llm.py` — writes the rationale (fallback to template).

## Steps
1. Deterministic eligibility across candidate products (rules own the numbers).
2. Rank by decision × value × fit; take top-k.
3. LLM writes a ≤25-word rationale per product; falls back to a template in degraded mode.

## Outputs
- Ranked recommendations with eligibility terms + rationale.

## Edge cases & learnings
- LLM never computes a number — it only phrases. De-identify before sending (`nvidia_llm.deidentify`).
