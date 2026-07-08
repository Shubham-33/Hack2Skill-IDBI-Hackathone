"""Instant in-principle (indicative) decision at lead submission.

The TAT win: the moment a DSA submits a lead, return an immediate indicative
decision + offer the DSA can relay on the spot. This is INDICATIVE only — the
hard decision follows bureau (CIBIL) + KYC (named integration points).
"""
from __future__ import annotations

from eligibility import check_eligibility
from predict_propensity import predict_propensity
from score_partner import lead_default_risk, partner


def instant_decision(prospect: dict) -> dict:
    prop = predict_propensity(prospect)
    ptr = partner(prospect["partner_id"])
    risk = lead_default_risk(prospect, ptr)
    elig = check_eligibility(prospect, prospect["requested_product"],
                             amount=prospect.get("requested_amount"),
                             pd=risk["default_risk"])          # risk-based pricing

    # indicative verdict combines eligibility with risk
    if elig["decision"] == "ineligible":
        verdict, tone = "Declined (indicative)", "decline"
    elif elig["decision"] == "conditional" or risk["risk_band"] == "High":
        verdict, tone = "Refer (indicative)", "refer"
    else:
        verdict, tone = "Approved in-principle", "approve"

    return {
        "lead_id": prospect["id"],
        "verdict": verdict,
        "tone": tone,
        "product_name": elig["product_name"],
        "indicative_amount": elig["offered_amount"],
        "indicative_rate": elig["rate"],
        "risk_premium": elig["risk_premium"],
        "indicative_emi": elig["emi"],
        "tenure_months": elig["tenure_months"],
        "conversion_tier": prop["tier"],
        "default_risk_band": risk["risk_band"],
        "reasons": elig["reasons"],
        # Reg-B / RBI-style adverse-action reason codes when not a clean approve
        "adverse_action_codes": risk.get("adverse_action_codes", []) if tone in ("decline", "refer") else [],
        "next_steps": ["Upload KYC documents", "Consent for CIBIL bureau pull",
                       "Income proof verification"],
        "disclaimer": "Indicative only. Final sanction subject to bureau check, KYC and IDBI credit policy.",
    }


if __name__ == "__main__":
    from config import load_json
    import time
    for p in load_json("prospects.json")[:5]:
        t0 = time.perf_counter()
        d = instant_decision(p)
        ms = (time.perf_counter() - t0) * 1000
        print(f"{p['name']:20} {d['verdict']:22} ₹{d['indicative_amount']:>9,} "
              f"@ {d['indicative_rate']}%  risk={d['default_risk_band']:6} ({ms:.0f} ms)")
