"""Next-best-product recommendation.

Deterministic ranking (eligibility + fit + value + propensity) decides WHAT to
offer; the LLM only writes the WHY in plain language. Degrades to a template when
the LLM is unavailable, so the recommendation always renders.
"""
from __future__ import annotations

from config import load_json
from eligibility import check_eligibility, products
from predict_propensity import predict_propensity
from score_partner import lead_default_risk
import nvidia_llm


def _candidate_products(prospect):
    """Products relevant to this prospect's channel + a couple of cross-sell options."""
    ids = {prospect["requested_product"]}
    # add cross-sell candidates the customer segment plausibly wants
    income = prospect["monthly_income"]
    for pid, p in products().items():
        if income >= p["min_income"] and prospect["credit_score"] >= p["min_credit"] - 30:
            ids.add(pid)
    return list(ids)


def recommend(prospect: dict, top_k: int = 3, use_llm: bool = True) -> dict:
    """Rank by CUSTOMER SUITABILITY (need + eligibility + affordability).

    Bank revenue is computed and returned for RM context, but is NEVER a ranking
    input — this keeps the recommendation fair-lending / suitability compliant.
    """
    prop = predict_propensity(prospect)
    pd = lead_default_risk(prospect)["default_risk"]        # risk-based pricing input (per borrower)
    ranked = []
    for pid in _candidate_products(prospect):
        elig = check_eligibility(prospect, pid, pd=pd)
        if elig["decision"] == "ineligible":
            continue
        product = products()[pid]
        is_requested = pid == prospect["requested_product"]
        # --- suitability components (customer-centric) ---
        need_fit = 1.0 if is_requested else 0.55            # the customer's stated need matters most
        elig_strength = 1.0 if elig["decision"] == "eligible" else 0.5
        # comfortable repayment: how much FOIR headroom is left after this loan
        affordability = max(0.0, min(1.0, 1 - elig["projected_foir"] / max(product["max_foir"], 0.01)))
        suitability = round(0.45 * need_fit + 0.30 * elig_strength + 0.25 * affordability, 3)
        ranked.append({
            "eligibility": elig,
            "suitability": suitability,
            "score": suitability,                            # ranking key = suitability
            "is_requested": is_requested,
            "revenue_to_bank": round(elig["offered_amount"] * product["commission_pct"] / 100),
        })
    # customer's requested product first, then by suitability; revenue never breaks ties
    ranked.sort(key=lambda r: (-r["is_requested"], -r["suitability"]))
    ranked = ranked[:top_k]

    # LLM only phrases the TOP recommendation (latency: 1 call, not top_k);
    # the rest use the deterministic template.
    for i, r in enumerate(ranked):
        r["rationale"] = _rationale(prospect, r["eligibility"], prop, use_llm and i == 0)

    return {"propensity": prop, "recommendations": ranked}


def _rationale(prospect, elig, prop, use_llm):
    if use_llm and nvidia_llm.available():
        safe = nvidia_llm.deidentify(prospect)
        out = nvidia_llm.complete_json(
            "You are an IDBI Bank relationship-manager assistant. Write a crisp, factual, "
            "compliant one-line rationale for recommending a loan product. No guarantees, "
            "no invented numbers — use only the numbers provided.",
            f"Customer (de-identified): {safe}\n"
            f"Product decision: {elig}\nConversion tier: {prop['tier']}.\n"
            'Return {"rationale": "<=25 words"}.',
        )
        if out and out.get("rationale"):
            return out["rationale"]
    # deterministic fallback
    return (f"{elig['product_name']} fits — {prop['tier'].lower()} conversion, "
            f"eligible up to ₹{elig['offered_amount']:,} at {elig['rate']}% "
            f"(EMI ₹{elig['emi']:,.0f}/mo).")


if __name__ == "__main__":
    for p in load_json("prospects.json")[:3]:
        r = recommend(p, use_llm=False)
        print(f"\n{p['name']} — P(convert)={r['propensity']['propensity']:.0%}")
        for rec in r["recommendations"]:
            e = rec["eligibility"]
            print(f"  → {e['product_name']:28} score={rec['score']} — {rec['rationale']}")
