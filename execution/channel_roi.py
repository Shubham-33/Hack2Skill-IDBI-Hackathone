"""Channel-mix ROI — which channel type actually makes IDBI money.

ROI blends volume, conversion, default drag and commission cost into an
illustrative profit-per-lead so the manager can rebalance the channel mix.
Numbers are directional (synthetic), for decision-support, not accounting.
"""
from __future__ import annotations

from collections import defaultdict

from config import load_json
from eligibility import products
from economics import COST_OF_FUNDS, LGD_BY_ID

# illustrative economics — same cost-of-funds basis as the prospect queue (economics.py)
AVG_TICKET = 800000          # ₹ average disbursed
AVG_LIFE_YEARS = 3
# blended NIM = average priced rate across the catalog − cost of funds
NIM_ANNUAL = round(sum((p["base_rate"] + p["rate_spread"] / 2) / 100
                       for p in products().values()) / len(products()) - COST_OF_FUNDS, 4)
LGD = round(sum(LGD_BY_ID.values()) / len(LGD_BY_ID), 3)   # blended loss-given-default


def _avg_commission_pct():
    return sum(p["commission_pct"] for p in products().values()) / len(products())


def channel_roi() -> list[dict]:
    partners = load_json("partners.json")
    by_type = defaultdict(lambda: {"partners": 0, "leads": 0, "conv": 0.0,
                                   "defw": 0.0, "disbursed": 0})
    for p in partners:
        h = p["history"]
        t = by_type[p["type"]]
        t["partners"] += 1
        t["leads"] += h["leads_sourced"]
        disbursed = h["leads_sourced"] * h["conversion_rate"]
        t["disbursed"] += disbursed
        t["conv"] += h["conversion_rate"]
        t["defw"] += h["default_rate"] * disbursed  # default-weighted by volume

    comm_pct = _avg_commission_pct()
    rows = []
    for ctype, t in by_type.items():
        disb = t["disbursed"] or 1
        avg_conv = t["conv"] / t["partners"]
        avg_default = t["defw"] / disb
        revenue = AVG_TICKET * NIM_ANNUAL * AVG_LIFE_YEARS
        credit_loss = AVG_TICKET * LGD * avg_default
        commission = AVG_TICKET * comm_pct / 100
        profit_per_disbursal = revenue - credit_loss - commission
        profit_per_lead = profit_per_disbursal * avg_conv
        rows.append({
            "channel": ctype, "partners": t["partners"],
            "leads": int(t["leads"]), "avg_conversion": round(avg_conv, 3),
            "avg_default": round(avg_default, 3),
            "profit_per_disbursal": round(profit_per_disbursal),
            "profit_per_lead": round(profit_per_lead),
            "total_profit": round(profit_per_lead * t["leads"]),
        })
    return sorted(rows, key=lambda r: -r["profit_per_lead"])


if __name__ == "__main__":
    print(f"{'Channel':12} {'ptnrs':>5} {'leads':>6} {'conv':>6} {'def':>6} "
          f"{'₹/lead':>9} {'₹/disb':>10}")
    for r in channel_roi():
        print(f"{r['channel']:12} {r['partners']:5} {r['leads']:6} "
              f"{r['avg_conversion']:6.0%} {r['avg_default']:6.0%} "
              f"{r['profit_per_lead']:9,} {r['profit_per_disbursal']:10,}")
