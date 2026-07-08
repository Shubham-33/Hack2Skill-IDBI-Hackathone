"""Partner-churn early-warning.

Flags DSAs disengaging BEFORE they leave for a competitor — the relationship
equivalent of customer-churn prediction. Signals: declining submission trend,
days since last activity, and a weak recent-vs-earlier ratio.
"""
from __future__ import annotations

from score_partner import _partners


def churn_signal(partner_obj: dict) -> dict:
    h = partner_obj["history"]
    trend = h["monthly_submissions"]            # 6 months, oldest -> newest
    last_activity = h["last_activity_days"]

    early = sum(trend[:3]) or 1
    recent = sum(trend[3:])
    momentum = recent / early                    # <1 means slowing down

    # composite risk 0..1
    risk = 0.0
    if momentum < 0.6:
        risk += 0.45
    elif momentum < 0.85:
        risk += 0.25
    if last_activity > 45:
        risk += 0.35
    elif last_activity > 21:
        risk += 0.2
    if trend[-1] == 0:
        risk += 0.2
    risk = min(1.0, risk)

    band = "High" if risk >= 0.55 else "Medium" if risk >= 0.3 else "Low"
    action = None
    if band != "Low":
        action = (f"RM outreach: {partner_obj['name']} submissions down "
                  f"{(1-momentum)*100:.0f}%, last active {last_activity}d ago — "
                  f"re-engage before they route to a competitor.")
    return {"partner_id": partner_obj["id"], "name": partner_obj["name"],
            "churn_risk": round(risk, 2), "band": band,
            "momentum": round(momentum, 2), "last_activity_days": last_activity,
            "trend": trend, "recommended_action": action}


def churn_watchlist() -> list[dict]:
    rows = [churn_signal(p) for p in _partners().values()]
    return sorted((r for r in rows if r["band"] != "Low"), key=lambda r: -r["churn_risk"])


if __name__ == "__main__":
    wl = churn_watchlist()
    print(f"Partners on churn watchlist: {len(wl)}")
    for r in wl[:8]:
        print(f"  {r['name']:32} risk={r['churn_risk']:.2f} [{r['band']:6}] "
              f"momentum={r['momentum']:.2f} last={r['last_activity_days']}d")
