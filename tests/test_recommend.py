"""Recommendation suitability tests — the A1 fix must stay fixed.

Guards that recommendations are ranked by CUSTOMER SUITABILITY and that bank
revenue never drives the order (fair-lending / anti-mis-selling).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "execution"))

from config import load_json
from eligibility import check_eligibility
from recommend_products import recommend


def _eligible_for_requested(prospect):
    return check_eligibility(prospect, prospect["requested_product"])["decision"] != "ineligible"


def test_requested_product_first_when_eligible():
    for p in load_json("prospects.json"):
        if _eligible_for_requested(p):
            r = recommend(p, use_llm=False)
            assert r["recommendations"][0]["is_requested"], \
                f"{p['name']}: requested product should rank first when eligible"
            return
    raise AssertionError("no eligible-for-requested prospect found")


def test_recommendations_sorted_by_suitability():
    p = next(x for x in load_json("prospects.json") if _eligible_for_requested(x))
    recs = recommend(p, use_llm=False)["recommendations"]
    non_requested = [r["suitability"] for r in recs if not r["is_requested"]]
    assert non_requested == sorted(non_requested, reverse=True)


def test_revenue_does_not_drive_ranking():
    """Find a case where the top rec is NOT the highest-revenue option —
    proves commission isn't the ranking key."""
    for p in load_json("prospects.json"):
        recs = recommend(p, use_llm=False)["recommendations"]
        if len(recs) < 2:
            continue
        top_rev = recs[0]["revenue_to_bank"]
        max_rev = max(r["revenue_to_bank"] for r in recs)
        if top_rev < max_rev:
            return  # found a lower-revenue product ranked first — proof
    raise AssertionError("revenue appears to drive ranking (no counter-example found)")


def test_every_rec_has_suitability_and_revenue_fields():
    p = load_json("prospects.json")[0]
    for r in recommend(p, use_llm=False)["recommendations"]:
        assert "suitability" in r and "revenue_to_bank" in r
        assert 0.0 <= r["suitability"] <= 1.0
