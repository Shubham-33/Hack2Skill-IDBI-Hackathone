"""Unit tests for the deterministic engine — the part that must never be wrong.

Run:  python tests/test_engine.py     (or: python -m pytest tests/)
Covers EMI math, eligibility guards, rate banding, commission + clawback, and
the financial-health rubric. No LLM, no network.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "execution"))

from eligibility import emi, price_rate, rate_band, check_eligibility, validate_offer_edit, products
from commission import commission_for, clawback_for
from score_financial_health import score_financial_health
from lead_utils import build_lead


def approx(a, b, tol=1.0):
    return abs(a - b) <= tol


def test_emi_known_value():
    # ₹10,00,000 @ 9% for 240 months ≈ ₹8,997/mo
    assert approx(emi(1_000_000, 9.0, 240), 8997, 2)


def test_emi_zero_rate():
    assert emi(120000, 0, 12) == 10000


def test_rate_within_band():
    for pid, p in products().items():
        lo, hi = rate_band(p)
        assert lo <= price_rate(p, 800) <= hi
        assert lo <= price_rate(p, 600) <= hi
        # better credit -> not more expensive
        assert price_rate(p, 820) <= price_rate(p, 640) + 1e-9


def test_risk_based_pricing_loads_within_band():
    """A higher model PD raises the rate, but never outside the approved band,
    and never below the credit-only rate."""
    for pid, p in products().items():
        lo, hi = rate_band(p)
        base = price_rate(p, 760)                 # credit-only
        low_pd = price_rate(p, 760, pd=0.02)
        high_pd = price_rate(p, 760, pd=0.50)     # above the PD ceiling -> full load
        assert base <= low_pd <= high_pd <= hi + 1e-9
        assert lo <= high_pd <= hi + 1e-9
        # monotonic in PD
        assert price_rate(p, 760, pd=0.10) <= price_rate(p, 760, pd=0.30) + 1e-9


def test_check_eligibility_surfaces_risk_premium():
    lead = build_lead("R", "PTR001", "personal_loan", 400000, 90000, 720)
    clean = check_eligibility(lead, "personal_loan", pd=0.01)
    risky = check_eligibility(lead, "personal_loan", pd=0.50)
    assert risky["rate"] >= clean["rate"]
    assert risky["risk_premium"] >= 0 and risky["rate"] <= risky["rate_band"][1] + 1e-9


def test_eligibility_zero_income_no_crash():
    lead = build_lead("Z", "PTR001", "personal_loan", 500000, 0, 800)
    r = check_eligibility(lead, "personal_loan")            # must not raise
    assert r["decision"] in ("eligible", "conditional", "ineligible")
    assert r["emi"] >= 0


def test_offer_edit_clamps_rate():
    lead = build_lead("A", "PTR001", "personal_loan", 400000, 80000, 760)
    v = validate_offer_edit(lead, "personal_loan", 400000, 99.0, 60)
    lo, hi = rate_band(products()["personal_loan"])
    assert lo <= v["rate"] <= hi
    assert any("band" in e for e in v["errors"])


def test_commission_and_clawback():
    from config import load_json
    partner = load_json("partners.json")[0]
    c = commission_for("personal_loan", 1_000_000, partner)
    assert c["gross_commission"] > 0
    # clawback triggers only on default within window
    cb_in = clawback_for(c["gross_commission"], partner, months_since_disbursal=2, defaulted=True)
    cb_out = clawback_for(c["gross_commission"], partner, months_since_disbursal=99, defaulted=True)
    cb_none = clawback_for(c["gross_commission"], partner, months_since_disbursal=2, defaulted=False)
    assert cb_in["clawback_amount"] > 0
    assert cb_out["clawback_amount"] == 0
    assert cb_none["clawback_amount"] == 0


def test_health_score_bounds_and_monotonic():
    weak = build_lead("W", "PTR001", "personal_loan", 100000, 20000, 560, existing_emi=9000, bounces=3)
    strong = build_lead("S", "PTR001", "personal_loan", 100000, 200000, 820, existing_emi=0, bounces=0)
    sw = score_financial_health(weak)["score"]
    ss = score_financial_health(strong)["score"]
    assert 0 <= sw <= 100 and 0 <= ss <= 100
    assert ss > sw


def _run():
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    passed = 0
    for t in tests:
        t()
        print(f"  ✓ {t.__name__}")
        passed += 1
    print(f"\n{passed}/{len(tests)} deterministic-engine tests passed.")


if __name__ == "__main__":
    _run()
