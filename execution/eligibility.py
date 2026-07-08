"""Deterministic eligibility, EMI and risk-based pricing engine.

This module owns every NUMBER in an offer — eligibility, interest rate, EMI,
max loan amount. The LLM never computes these; it only phrases them. RM edits
in the offer screen are re-validated here (rate band + EMI recompute).
"""
from __future__ import annotations

from config import load_json

_PRODUCTS = None


def products():
    global _PRODUCTS
    if _PRODUCTS is None:
        _PRODUCTS = {p["id"]: p for p in load_json("products.json")}
    return _PRODUCTS


def emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    """Standard reducing-balance EMI."""
    r = annual_rate / 12 / 100
    n = int(tenure_months)
    if r == 0:
        return round(principal / n, 2)
    factor = (1 + r) ** n
    return round(principal * r * factor / (factor - 1), 2)


# Risk-based pricing: how much of the rate spread a high-PD lead can be loaded by.
_PD_CEIL = 0.35              # PD at/above which the full risk load applies (= High-risk band)
_RISK_LOAD_SHARE = 0.5      # a risky lead can consume up to half the spread as a premium


def price_rate(product: dict, credit_score: int, pd: float | None = None) -> float:
    """Risk-based pricing, always within the product's approved rate band.

    Two auditable, monotonic components:
      1. Credit grid — better CIBIL -> closer to base rate (830 -> base ; 640 -> base+spread).
      2. Risk-based loading — if a model PD is supplied, add a premium proportional to PD.
         This only ever RAISES the rate and is capped at the band ceiling, so pricing
         stays inside the regulator/credit-policy-approved band. PD is derived from
         features that exclude prohibited attributes (fair-lending safe).
    """
    frac = (830 - credit_score) / (830 - 640)
    frac = max(0.0, min(1.0, frac))
    rate = product["base_rate"] + frac * product["rate_spread"]
    if pd is not None:
        pd_frac = max(0.0, min(1.0, pd / _PD_CEIL))
        premium = pd_frac * _RISK_LOAD_SHARE * product["rate_spread"]
        ceiling = product["base_rate"] + product["rate_spread"]
        rate = min(ceiling, rate + premium)
    return round(rate, 2)


def rate_band(product: dict) -> tuple[float, float]:
    return product["base_rate"], round(product["base_rate"] + product["rate_spread"], 2)


def max_eligible_amount(prospect: dict, product: dict, annual_rate: float, tenure_months: int) -> int:
    """Largest principal whose EMI keeps total FOIR within the product cap."""
    income = prospect["monthly_income"]
    existing = prospect.get("existing_emi", 0)
    max_total_emi = product["max_foir"] * income
    headroom = max_total_emi - existing
    if headroom <= 0:
        return 0
    r = annual_rate / 12 / 100
    n = int(tenure_months)
    if r == 0:
        principal = headroom * n
    else:
        factor = (1 + r) ** n
        principal = headroom * (factor - 1) / (r * factor)
    return int(min(principal, product["max_amount"]) // 10000 * 10000)


def check_eligibility(prospect: dict, product_id: str,
                      amount: float | None = None, tenure_months: int | None = None,
                      pd: float | None = None) -> dict:
    """Full deterministic eligibility check + indicative terms.

    Returns decision in {eligible, conditional, ineligible} with reasons, plus
    rate / EMI / max-amount so it can drive an instant indicative offer. When a
    model PD is supplied, the offered rate is risk-loaded within the band and the
    premium is surfaced separately for transparency.
    """
    product = products()[product_id]
    tenure = int(tenure_months or _default_tenure(product))
    income = max(1, prospect.get("monthly_income", 0))          # guard against 0/negative income
    credit = max(300, min(900, prospect["credit_score"]))
    rate = price_rate(product, credit, pd)
    risk_premium = round(rate - price_rate(product, credit), 2)  # loading vs credit-only grid
    amount = max(0, amount or prospect.get("requested_amount") or product["min_amount"])

    reasons = []
    hard_fail = False
    conditional = False

    if prospect["monthly_income"] < product["min_income"]:
        reasons.append(f"Income ₹{prospect['monthly_income']:,} below minimum ₹{product['min_income']:,}")
        hard_fail = True
    if prospect["credit_score"] < product["min_credit"]:
        gap = product["min_credit"] - prospect["credit_score"]
        if gap <= 25:
            reasons.append(f"Credit {prospect['credit_score']} just under {product['min_credit']} — conditional")
            conditional = True
        else:
            reasons.append(f"Credit {prospect['credit_score']} below minimum {product['min_credit']}")
            hard_fail = True

    max_amt = max_eligible_amount(prospect, product, rate, tenure)
    new_emi = emi(min(amount, max_amt) if max_amt else amount, rate, tenure)
    projected_foir = round((prospect.get("existing_emi", 0) + new_emi) / income, 3)

    if max_amt == 0:
        reasons.append("No EMI headroom — existing obligations too high (FOIR)")
        hard_fail = True
    elif amount > max_amt:
        reasons.append(f"Requested ₹{amount:,.0f} exceeds eligible ₹{max_amt:,} — offer capped")
        conditional = True

    if hard_fail:
        decision = "ineligible"
    elif conditional:
        decision = "conditional"
    else:
        decision = "eligible"
        reasons.append("Meets income, credit and FOIR norms")

    offered_amount = amount if (max_amt and amount <= max_amt) else max_amt
    return {
        "product_id": product_id,
        "product_name": product["name"],
        "decision": decision,
        "reasons": reasons,
        "rate": rate,
        "risk_premium": risk_premium,
        "rate_band": rate_band(product),
        "tenure_months": tenure,
        "offered_amount": int(offered_amount or 0),
        "requested_amount": int(amount),
        "max_eligible_amount": max_amt,
        "emi": emi(offered_amount, rate, tenure) if offered_amount else 0,
        "projected_foir": projected_foir,
    }


def validate_offer_edit(prospect: dict, product_id: str, amount: float,
                        rate: float, tenure_months: int) -> dict:
    """Re-validate an RM-edited offer: clamp rate to band, recompute EMI, flag issues."""
    product = products()[product_id]
    lo, hi = rate_band(product)
    errors = []
    if rate < lo or rate > hi:
        errors.append(f"Rate {rate}% outside allowed band {lo}%–{hi}% (auto-clamped)")
        rate = max(lo, min(hi, rate))
    if not (product["min_tenure_m"] <= tenure_months <= product["max_tenure_m"]):
        errors.append(f"Tenure {tenure_months}m outside {product['min_tenure_m']}–{product['max_tenure_m']}m (auto-clamped)")
        tenure_months = max(product["min_tenure_m"], min(product["max_tenure_m"], tenure_months))
    max_amt = max_eligible_amount(prospect, product, rate, tenure_months)
    if amount > max_amt:
        errors.append(f"Amount ₹{amount:,.0f} exceeds eligible ₹{max_amt:,} (auto-capped)")
        amount = max_amt
    computed_emi = emi(amount, rate, tenure_months)
    return {
        "product_id": product_id, "amount": int(amount), "rate": round(rate, 2),
        "tenure_months": int(tenure_months), "emi": computed_emi,
        "max_eligible_amount": max_amt, "errors": errors, "valid": not errors,
    }


def _default_tenure(product):
    return min(product["max_tenure_m"], max(product["min_tenure_m"], 60))


if __name__ == "__main__":
    for p in load_json("prospects.json")[:4]:
        r = check_eligibility(p, p["requested_product"])
        print(f"{p['name']:20} {r['product_name']:28} {r['decision']:11} "
              f"rate={r['rate']}% EMI=₹{r['emi']:,.0f} offered=₹{r['offered_amount']:,}")
