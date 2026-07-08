"""Partner tiering → concrete incentives.

Maps the quality tier to the rewards that actually build loyalty: commission
multiplier boost, priority processing, faster payout, and an SLA promise. Rewards
quality (not just volume), gamifies the relationship.
"""
from __future__ import annotations

from score_partner import partner_quality, all_partner_quality

TIER_BENEFITS = {
    "Platinum": {"commission_boost_pct": 15, "payout_days": 3, "priority": True,
                 "sla_hours": 24, "perks": ["Dedicated RM", "Priority underwriting", "Co-branded collateral"]},
    "Gold":     {"commission_boost_pct": 8, "payout_days": 5, "priority": True,
                 "sla_hours": 36, "perks": ["Priority underwriting", "Quarterly review"]},
    "Silver":   {"commission_boost_pct": 3, "payout_days": 7, "priority": False,
                 "sla_hours": 48, "perks": ["Standard processing"]},
    "Bronze":   {"commission_boost_pct": 0, "payout_days": 10, "priority": False,
                 "sla_hours": 72, "perks": ["Standard processing", "Quality improvement plan"]},
}


def tier_benefits(partner_obj: dict) -> dict:
    q = partner_quality(partner_obj)
    benefits = TIER_BENEFITS[q["tier"]]
    # what's the next tier and how far away?
    order = ["Bronze", "Silver", "Gold", "Platinum"]
    idx = order.index(q["tier"])
    next_tier = order[idx + 1] if idx < len(order) - 1 else None
    thresholds = {"Silver": 45, "Gold": 62, "Platinum": 78}
    to_next = (thresholds[next_tier] - q["quality_score"]) if next_tier else 0
    return {"tier": q["tier"], "quality_score": q["quality_score"],
            **benefits, "next_tier": next_tier, "points_to_next_tier": to_next}


if __name__ == "__main__":
    from collections import Counter
    dist = Counter()
    for r in all_partner_quality():
        from score_partner import partner
        b = tier_benefits(partner(r["id"]))
        dist[b["tier"]] += 1
    print("Tier distribution:", dict(dist))
    # show one example
    from score_partner import _partners
    sample = list(_partners().values())[0]
    b = tier_benefits(sample)
    print(f"\n{sample['name']}: {b['tier']} (Q={b['quality_score']}) "
          f"-> +{b['commission_boost_pct']}% commission, payout in {b['payout_days']}d, "
          f"SLA {b['sla_hours']}h; next: {b['next_tier']} in {b['points_to_next_tier']} pts")
