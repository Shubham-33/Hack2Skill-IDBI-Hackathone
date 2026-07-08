"""Predict decision TAT (turnaround time) per lead + SLA-breach flagging.

Ends the black box DSAs hate: each lead gets an expected decision time and a live
SLA status. TAT rises with case complexity and the partner's historical slowness,
and falls for clean, high-tier partners (priority processing).
"""
from __future__ import annotations

from score_partner import partner, partner_quality

# SLA promise (hours to decision) by product category
SLA_HOURS = {"Unsecured": 24, "Secured": 72}


def predict_tat(prospect: dict) -> dict:
    from eligibility import products
    product = products()[prospect["requested_product"]]
    ptr = partner(prospect["partner_id"])
    q = partner_quality(ptr)

    base = SLA_HOURS.get(product["category"], 48)
    # complexity multipliers
    mult = 1.0
    if prospect.get("foir", 0) > product["max_foir"]:
        mult += 0.4
    if prospect["credit_score"] < product["min_credit"]:
        mult += 0.4
    if prospect["transactions"]["monthly_bounces"] >= 2:
        mult += 0.2
    if not prospect["transactions"]["regular_salary_credit"]:
        mult += 0.2
    # partner effect: good docs + high tier => priority (faster)
    mult *= (1.3 - 0.4 * q["doc_completeness"])
    if q["tier"] in ("Platinum", "Gold"):
        mult *= 0.8  # priority processing perk

    predicted = round(base * mult, 1)
    elapsed = prospect.get("submitted_hours_ago", 0)
    sla = base
    breached = elapsed > sla and prospect.get("status") not in ("approved", "disbursed")
    at_risk = (not breached) and elapsed > 0.7 * sla and prospect.get("status") in ("new", "verifying")

    return {
        "lead_id": prospect["id"],
        "sla_hours": sla,
        "predicted_tat_hours": predicted,
        "elapsed_hours": elapsed,
        "status": prospect.get("status", "new"),
        "sla_state": "breached" if breached else "at_risk" if at_risk else "on_track",
        "priority": q["tier"] in ("Platinum", "Gold"),
    }


if __name__ == "__main__":
    from config import load_json
    counts = {"on_track": 0, "at_risk": 0, "breached": 0}
    for p in load_json("prospects.json"):
        counts[predict_tat(p)["sla_state"]] += 1
    print("SLA states across live queue:", counts)
    for p in load_json("prospects.json")[:6]:
        t = predict_tat(p)
        print(f"  {p['id']} {t['status']:9} elapsed={t['elapsed_hours']:3}h "
              f"pred={t['predicted_tat_hours']:5}h SLA={t['sla_hours']}h -> {t['sla_state']}"
              f"{'  ⚡priority' if t['priority'] else ''}")
