"""Score a prospect's conversion propensity + explain the ranking.

Loads data/propensity.pkl and returns P(convert) plus a transparent, per-prospect
"why" — the features pushing the score up/down — for the queue and the deck.
"""
from __future__ import annotations

import functools

import joblib

from config import load_json, DATA_DIR
from features import prospect_features, vectorize, PROPENSITY_FEATURES
from explain import occlusion_attributions, reason_codes


def _fmt(k, v):
    if v is None:
        return "—"
    if k in ("monthly_income", "balance_ratio", "income_headroom"):
        return f"₹{v:,.0f}" if k == "monthly_income" or k == "income_headroom" else f"{v:.1f}×"
    if k in ("foir", "savings_ratio", "product_fit"):
        return f"{v*100:.0f}%"
    if k in ("credit_score", "credit_headroom", "monthly_bounces"):
        return f"{v:.0f}"
    if k == "regular_salary_credit":
        return "yes" if v >= 0.5 else "no"
    if k == "amount_to_annual_income":
        return f"{v:.1f}×"
    return f"{v:.2f}"

# human labels for the raw feature names
_LABELS = {
    "monthly_income": "income", "credit_score": "credit score", "foir": "debt burden",
    "amount_to_annual_income": "loan-to-income", "savings_ratio": "savings rate",
    "balance_ratio": "balance cushion", "monthly_bounces": "cheque bounces",
    "regular_salary_credit": "regular salary", "credit_headroom": "credit vs. product floor",
    "income_headroom": "income vs. product floor", "product_fit": "product fit",
}
# does a HIGHER value help conversion (+1) or hurt it (-1)?
_DIRECTION = {
    "monthly_income": 1, "credit_score": 1, "foir": -1, "amount_to_annual_income": -1,
    "savings_ratio": 1, "balance_ratio": 1, "monthly_bounces": -1,
    "regular_salary_credit": 1, "credit_headroom": 1, "income_headroom": 1, "product_fit": 1,
}


@functools.lru_cache(maxsize=1)
def _bundle():
    return joblib.load(DATA_DIR / "propensity.pkl")


@functools.lru_cache(maxsize=1)
def _means():
    """Population means per feature — the baseline for occlusion attributions.
    Prefer the means stored at train time; fall back to computing from history."""
    b = _bundle()
    if b.get("feature_means"):
        return b["feature_means"]
    feats = [prospect_features(h) for h in load_json("history.json")]
    return {k: sum(f[k] for f in feats) / len(feats) for k in PROPENSITY_FEATURES}


def predict_propensity(prospect: dict) -> dict:
    bundle = _bundle()
    feat = prospect_features(prospect)
    x = vectorize(feat, PROPENSITY_FEATURES)
    prob = float(bundle["model"].predict_proba([x])[0][1])

    means = _means()
    base_vec = vectorize(means, PROPENSITY_FEATURES)
    baseline, deltas = occlusion_attributions(bundle["model"], base_vec, x)
    codes = reason_codes(PROPENSITY_FEATURES, deltas, feat, means, _LABELS, _fmt,
                         bad_outcome=False, top_k=5)

    ups = [c["label"] for c in codes if c["signed_impact"] > 0]
    downs = [c["label"] for c in codes if c["signed_impact"] < 0]
    return {
        "propensity": round(prob, 3),
        "tier": "Hot" if prob >= 0.66 else "Warm" if prob >= 0.4 else "Cold",
        "baseline": round(baseline, 3),
        "drivers_up": ups[:3],
        "drivers_down": downs[:2],
        "reason_codes": codes,
        "reason": _phrase([(u, 1) for u in ups], [(d, -1) for d in downs]),
    }


def _phrase(ups, downs):
    parts = []
    if ups:
        parts.append("strong " + ", ".join(u[0] for u in ups[:2]))
    if downs:
        parts.append("held back by " + ", ".join(d[0] for d in downs[:2]))
    return "; ".join(parts) or "average profile across the board"


if __name__ == "__main__":
    for p in load_json("prospects.json")[:5]:
        r = predict_propensity(p)
        print(f"{p['name']:20} P(convert)={r['propensity']:.0%} [{r['tier']:4}] — {r['reason']}")
