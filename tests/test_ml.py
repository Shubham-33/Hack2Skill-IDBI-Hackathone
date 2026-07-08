"""ML sanity tests — guardrails on the trained models.

Not chasing accuracy; asserting the models are trustworthy: probabilities in
range, sensible discrimination, calibration roughly holds, and — critically —
NO target leakage in the partner-risk model.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "execution"))

import joblib
from config import DATA_DIR, load_json
from predict_propensity import predict_propensity
from score_partner import lead_default_risk, partner


def test_models_exist():
    assert (DATA_DIR / "propensity.pkl").exists()
    assert (DATA_DIR / "partner_risk.pkl").exists()


def test_propensity_auc_reasonable():
    auc = joblib.load(DATA_DIR / "propensity.pkl")["auc"]
    assert 0.6 <= auc <= 0.95, f"propensity AUC {auc} out of sane range"


def test_partner_risk_no_leakage():
    b = joblib.load(DATA_DIR / "partner_risk.pkl")
    share = sum(w for f, w in b["importances"] if f.startswith("partner_"))
    assert share < 0.4, f"partner-history feature share {share:.2f} too high (leakage risk)"
    assert 0.6 <= b["auc"] <= 0.9


def test_probabilities_in_range():
    for p in load_json("prospects.json")[:20]:
        pr = predict_propensity(p)["propensity"]
        rk = lead_default_risk(p, partner(p["partner_id"]))["default_risk"]
        assert 0.0 <= pr <= 1.0 and 0.0 <= rk <= 1.0


def test_propensity_discriminates():
    """A strong profile should out-score a weak one for the same product."""
    from lead_utils import build_lead
    strong = build_lead("S", "PTR001", "personal_loan", 400000, 200000, 820, existing_emi=0)
    weak = build_lead("W", "PTR001", "personal_loan", 400000, 25000, 610, existing_emi=9000)
    assert predict_propensity(strong)["propensity"] > predict_propensity(weak)["propensity"]


def test_propensity_reason_codes():
    """Every score ships genuine per-decision reason codes (occlusion attribution)."""
    p = load_json("prospects.json")[0]
    r = predict_propensity(p)
    assert r["reason_codes"] and "baseline" in r
    c = r["reason_codes"][0]
    assert {"label", "value", "typical", "signed_impact", "impact"} <= set(c)
    # ranked by magnitude
    imps = [c["impact"] for c in r["reason_codes"]]
    assert imps == sorted(imps, reverse=True)


def test_default_risk_reason_codes_and_adverse_action():
    p = load_json("prospects.json")[0]
    r = lead_default_risk(p, partner(p["partner_id"]))
    assert "reason_codes" in r and isinstance(r["adverse_action_codes"], list)


def test_adverse_action_codes_present_on_decline():
    from instant_decision import instant_decision
    declined = [instant_decision(p) for p in load_json("prospects.json")]
    declined = [d for d in declined if d["tone"] == "decline"]
    # a declined lead must be able to state principal reason codes (Reg-B)
    assert not declined or any(d["adverse_action_codes"] for d in declined)


def test_calibration_monotonic():
    """Higher predicted-probability buckets should show higher actual conversion."""
    hist = load_json("history.json")
    buckets = {}
    for h in hist:
        pr = predict_propensity(h)["propensity"]
        b = min(4, int(pr * 5))
        buckets.setdefault(b, []).append(1 if h["outcome"]["converted"] else 0)
    rates = [sum(v) / len(v) for _, v in sorted(buckets.items()) if len(v) > 20]
    # broadly increasing (allow tiny noise)
    assert rates == sorted(rates) or all(b - a > -0.05 for a, b in zip(rates, rates[1:]))
