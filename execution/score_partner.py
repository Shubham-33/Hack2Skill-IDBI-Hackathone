"""Partner intelligence: per-lead default risk + overall partner quality score.

- `lead_default_risk` runs the trained partner_risk model on a (lead, partner) pair.
- `partner_quality` blends conversion, default, TAT and doc-completeness into a
  0-100 quality score with a tier, and flags adverse-selection partners.
"""
from __future__ import annotations

import functools

import joblib

from config import load_json, DATA_DIR
from features import partner_risk_features, vectorize, PARTNER_RISK_FEATURES
from explain import occlusion_attributions, reason_codes, adverse_action_codes

# plain-language labels + value formatting for adverse-action reason codes
_RISK_LABELS = {
    "credit_score": "credit score", "foir": "debt burden (FOIR)",
    "monthly_bounces": "cheque bounces", "amount_to_annual_income": "loan-to-income",
    "savings_ratio": "savings rate", "regular_salary_credit": "regular salary credit",
    "new_emi_burden": "post-loan EMI burden",
    "partner_default_rate_shrunk": "sourcing partner default history",
    "partner_conversion_rate": "sourcing partner conversion", "partner_doc_completeness": "partner doc quality",
}


def _risk_fmt(k, v):
    if v is None:
        return "—"
    if k in ("foir", "savings_ratio", "new_emi_burden", "partner_default_rate_shrunk",
             "partner_conversion_rate", "partner_doc_completeness"):
        return f"{v*100:.0f}%"
    if k in ("credit_score", "monthly_bounces"):
        return f"{v:.0f}"
    if k == "regular_salary_credit":
        return "yes" if v >= 0.5 else "no"
    if k == "amount_to_annual_income":
        return f"{v:.1f}×"
    return f"{v:.2f}"


@functools.lru_cache(maxsize=1)
def _bundle():
    return joblib.load(DATA_DIR / "partner_risk.pkl")


@functools.lru_cache(maxsize=1)
def _risk_means():
    b = _bundle()
    if b.get("feature_means"):
        return b["feature_means"]
    parts = _partners()
    feats = [partner_risk_features(h, parts[h["partner_id"]]) for h in load_json("history.json")
             if h.get("partner_id") in parts and h["outcome"]["converted"]]
    return {k: sum(f[k] for f in feats) / len(feats) for k in PARTNER_RISK_FEATURES}


@functools.lru_cache(maxsize=1)
def _partners():
    return {p["id"]: p for p in load_json("partners.json")}


def partner(partner_id: str) -> dict:
    return _partners().get(partner_id)


def lead_default_risk(prospect: dict, partner_obj: dict | None = None) -> dict:
    partner_obj = partner_obj or partner(prospect["partner_id"])
    feat = partner_risk_features(prospect, partner_obj)
    x = vectorize(feat, PARTNER_RISK_FEATURES)
    prob = float(_bundle()["model"].predict_proba([x])[0][1])
    band = "High" if prob >= 0.35 else "Medium" if prob >= 0.15 else "Low"

    # per-decision explanation: which factors raised (or lowered) this default risk
    means = _risk_means()
    base_vec = vectorize(means, PARTNER_RISK_FEATURES)
    _, deltas = occlusion_attributions(_bundle()["model"], base_vec, x)
    codes = reason_codes(PARTNER_RISK_FEATURES, deltas, feat, means, _RISK_LABELS,
                         _risk_fmt, bad_outcome=True, top_k=5)
    return {
        "default_risk": round(prob, 3),
        "risk_band": band,
        "partner_default_rate": partner_obj["history"]["default_rate"],
        "reason_codes": codes,
        "adverse_action_codes": adverse_action_codes(codes, top_k=3),
    }


def partner_quality(partner_obj: dict) -> dict:
    h = partner_obj["history"]
    # 0..1 normalised sub-scores
    conv = min(1.0, h["conversion_rate"] / 0.5)
    low_default = 1 - min(1.0, h["default_rate"] / 0.25)
    fast_tat = 1 - min(1.0, h["avg_tat_days"] / 7.0)
    docs = h["doc_completeness"]
    score = round(100 * (0.30 * conv + 0.35 * low_default + 0.20 * fast_tat + 0.15 * docs))
    tier = ("Platinum" if score >= 78 else "Gold" if score >= 62
            else "Silver" if score >= 45 else "Bronze")
    # adverse selection: brings volume but defaults are high
    adverse = h["default_rate"] >= 0.14 and h["leads_sourced"] >= 120
    return {
        "quality_score": score,
        "tier": tier,
        "adverse_selection": adverse,
        "conversion_rate": h["conversion_rate"],
        "default_rate": h["default_rate"],
        "avg_tat_days": h["avg_tat_days"],
        "doc_completeness": h["doc_completeness"],
    }


def all_partner_quality() -> list[dict]:
    out = []
    for p in _partners().values():
        q = partner_quality(p)
        out.append({"id": p["id"], "name": p["name"], "type": p["type"],
                    "city": p["city"], **q, "history": p["history"]})
    return sorted(out, key=lambda x: -x["quality_score"])


if __name__ == "__main__":
    ranked = all_partner_quality()
    print(f"{'Partner':32} {'Tier':9} {'Q':>3} conv  def   tat  adverse")
    for r in ranked[:8]:
        print(f"{r['name']:32} {r['tier']:9} {r['quality_score']:3} "
              f"{r['conversion_rate']:.0%}  {r['default_rate']:.0%}  {r['avg_tat_days']:.1f}  "
              f"{'⚠ YES' if r['adverse_selection'] else ''}")
    adverse = [r for r in ranked if r["adverse_selection"]]
    print(f"\nAdverse-selection partners flagged: {len(adverse)}")
