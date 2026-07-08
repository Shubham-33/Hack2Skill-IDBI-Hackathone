"""Per-decision explainability — SHAP-flavoured local attributions + reason codes.

Banks must be able to tell an applicant *why* — RBI/Reg-B "adverse action reason
codes". This module produces a genuine, model-agnostic local explanation for any
scikit-learn classifier (GradientBoosting or Logistic alike) WITHOUT a heavy
`shap` dependency, using mean-baseline occlusion:

    baseline = model P(·) with every feature at its training-population mean
    contribution(feature_k) = model P(·) with ONLY feature_k moved to the
                              applicant's actual value  −  baseline

The result is a signed Δ-probability per feature — how much *this* applicant's
value of that feature pushed the score away from a typical applicant. Summed, the
contributions approximate the gap between the applicant's score and the baseline
(exact for linear models; a faithful local attribution for trees). Fair-lending
safe: the feature set already excludes prohibited attributes.
"""
from __future__ import annotations


def occlusion_attributions(model, base_vec: list[float], actual_vec: list[float]) -> tuple[float, list[float]]:
    """Return (baseline_prob, [Δprob per feature]) via one-feature-at-a-time swaps."""
    base_p = float(model.predict_proba([base_vec])[0][1])
    rows = []
    for i in range(len(base_vec)):
        v = list(base_vec)
        v[i] = actual_vec[i]
        rows.append(v)
    if not rows:
        return base_p, []
    probs = model.predict_proba(rows)[:, 1]
    return base_p, [float(p) - base_p for p in probs]


def reason_codes(feature_list, deltas, feat_dict, means, labels, fmt,
                 bad_outcome: bool, top_k: int = 4) -> list[dict]:
    """Turn signed Δ-probabilities into ranked, plain-language reason codes.

    bad_outcome=True  → model predicts something undesirable (e.g. default): a
                        POSITIVE Δ (raises the probability) is 'adverse'.
    bad_outcome=False → model predicts something desirable (e.g. conversion): a
                        NEGATIVE Δ (lowers the probability) is 'adverse'.
    """
    codes = []
    for k, d in zip(feature_list, deltas):
        adverse = (d > 0) if bad_outcome else (d < 0)
        codes.append({
            "feature": k,
            "label": labels.get(k, k),
            "value": fmt(k, feat_dict.get(k)),
            "typical": fmt(k, means.get(k)),
            "impact": round(abs(d), 3),           # magnitude, for ranking
            "signed_impact": round(d, 3),         # +ve raises the modelled probability
            "adverse": adverse,
        })
    codes.sort(key=lambda c: -c["impact"])
    return [c for c in codes if c["impact"] >= 0.005][:top_k]


def adverse_action_codes(codes: list[dict], top_k: int = 3) -> list[str]:
    """Plain-language 'principal reasons' string list (Reg-B style) from reason codes."""
    out = []
    for c in codes:
        if c["adverse"]:
            out.append(f"{c['label']} ({c['value']} vs. typical {c['typical']})")
        if len(out) >= top_k:
            break
    return out
