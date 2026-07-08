"""Deterministic commission + clawback payout engine.

Computes what a partner is owed on a disbursed loan from the product commission %
and the partner's structure (flat multiplier or volume slab bonus), and applies
clawback when a loan forecloses/defaults within the clawback window. Fully
auditable — this is where banks lose money to manual error today.
"""
from __future__ import annotations

from config import load_json
from eligibility import products


def _partner(pid):
    return {p["id"]: p for p in load_json("partners.json")}.get(pid)


def commission_for(product_id: str, disbursed_amount: float, partner: dict,
                   ytd_disbursed: float = 0.0) -> dict:
    product = products()[product_id]
    struct = partner["commission_structure"]
    base_pct = product["commission_pct"]

    # volume slab bonus (on top of base), by YTD disbursed
    bonus_pct = 0.0
    for slab in sorted(struct["slabs"], key=lambda s: s["min_disbursed"]):
        if ytd_disbursed >= slab["min_disbursed"]:
            bonus_pct = slab["bonus_pct"]
    effective_pct = round((base_pct + bonus_pct) * struct["multiplier"], 3)
    gross = round(disbursed_amount * effective_pct / 100, 2)
    return {
        "disbursed_amount": disbursed_amount,
        "base_pct": base_pct, "bonus_pct": bonus_pct, "multiplier": struct["multiplier"],
        "effective_pct": effective_pct, "gross_commission": gross,
    }


def clawback_for(gross_commission: float, partner: dict, months_since_disbursal: int,
                 defaulted: bool) -> dict:
    struct = partner["commission_structure"]
    window = struct["clawback_months"]
    triggered = defaulted and months_since_disbursal <= window
    amount = round(gross_commission * struct["clawback_pct"], 2) if triggered else 0.0
    return {"clawback_triggered": triggered, "clawback_window_m": window,
            "clawback_amount": amount}


def partner_statement(partner_id: str, disbursals: list[dict]) -> dict:
    """Build a payout statement. Each disbursal: {product_id, amount, months_since, defaulted}."""
    partner = _partner(partner_id)
    ytd = 0.0
    lines, gross_total, clawback_total = [], 0.0, 0.0
    for d in disbursals:
        c = commission_for(d["product_id"], d["amount"], partner, ytd)
        cb = clawback_for(c["gross_commission"], partner,
                          d.get("months_since", 1), d.get("defaulted", False))
        ytd += d["amount"]
        gross_total += c["gross_commission"]
        clawback_total += cb["clawback_amount"]
        lines.append({**c, **cb, "product_id": d["product_id"]})
    return {
        "partner_id": partner_id, "partner_name": partner["name"],
        "lines": lines, "gross_total": round(gross_total, 2),
        "clawback_total": round(clawback_total, 2),
        "net_payable": round(gross_total - clawback_total, 2),
    }


if __name__ == "__main__":
    partners = load_json("partners.json")
    p = partners[0]
    demo = [
        {"product_id": "personal_loan", "amount": 800000, "months_since": 2, "defaulted": False},
        {"product_id": "auto_loan", "amount": 1200000, "months_since": 3, "defaulted": True},
        {"product_id": "home_loan", "amount": 6000000, "months_since": 10, "defaulted": True},
    ]
    st = _partner and partner_statement(p["id"], demo)
    print(f"Statement for {st['partner_name']}")
    for ln in st["lines"]:
        print(f"  {ln['product_id']:14} gross ₹{ln['gross_commission']:>10,.0f} "
              f"@ {ln['effective_pct']}%  clawback ₹{ln['clawback_amount']:,.0f}"
              f"{'  (default in window)' if ln['clawback_triggered'] else ''}")
    print(f"  Gross ₹{st['gross_total']:,.0f}  Clawback ₹{st['clawback_total']:,.0f}  "
          f"NET ₹{st['net_payable']:,.0f}")
