"""Risk-adjusted loan economics — the single source of truth for "what a lead is worth".

A credit/risk officer doesn't rank loans by a flat margin. They rank by
**risk-adjusted return**: net interest income earned over the loan's behavioural
life, MINUS the expected credit loss (PD × LGD × exposure). This module owns that
math so the prospect queue, the channel ROI and the deck all speak the same,
defensible language.

Key BFSI concepts made explicit:
  • NIM (net interest margin)  = offered rate − cost of funds        (product-specific)
  • Expected Credit Loss (ECL) = PD × LGD × EAD                       (Basel/IFRS-9 shape)
  • LGD (loss given default)   = share of principal lost, net of collateral recovery
  • Behavioural life           = how long the loan actually stays on book (prepayment-aware)
  • Risk-adjusted return       = NII − ECL   (can be NEGATIVE → value-destructive lead)

Assumptions are illustrative (synthetic prototype) but directionally bank-realistic
and clearly labelled. In the PoC these calibrate to IDBI's real cost of funds,
recovery and prepayment curves.
"""
from __future__ import annotations

# Bank-level assumption. IDBI's blended cost of funds ~6.5% (deposits + borrowings).
COST_OF_FUNDS = 0.065

# Loss Given Default by product — secured collateral recovers more, so LGD is lower.
# Unsecured personal/business default loses most of the principal.
LGD_BY_ID = {
    "home_loan": 0.20,       # mortgage-backed, strong recovery
    "lap": 0.25,             # property-backed
    "gold_loan": 0.10,       # liquid collateral, near-full recovery
    "auto_loan": 0.40,       # vehicle depreciates
    "education_loan": 0.55,  # partial collateral / co-obligant
    "two_wheeler": 0.50,
    "personal_loan": 0.70,   # unsecured
    "business_loan": 0.65,   # unsecured MSME
}
_DEFAULT_LGD = 0.60

# Behavioural life (years): how long the loan really sits on book. Long-tenor
# retail loans prepay/refinance, so effective life << contractual tenure.
BEHAVIOURAL_LIFE_Y = {
    "home_loan": 7.0, "lap": 6.0, "education_loan": 5.0, "auto_loan": 4.0,
    "business_loan": 3.0, "personal_loan": 2.5, "two_wheeler": 2.5, "gold_loan": 1.5,
}
_DEFAULT_LIFE_Y = 3.0


def lgd(product_id: str) -> float:
    return LGD_BY_ID.get(product_id, _DEFAULT_LGD)


def behavioural_life(product: dict) -> float:
    """Effective years on book — never longer than the product's max tenure."""
    life = BEHAVIOURAL_LIFE_Y.get(product["id"], _DEFAULT_LIFE_Y)
    return min(life, product["max_tenure_m"] / 12)


def loan_economics(principal: float, annual_rate: float, pd: float, product: dict) -> dict:
    """Risk-adjusted economics of ONE booked loan (before P(convert))."""
    principal = max(0.0, principal)
    pd = max(0.0, min(1.0, pd))
    nim = max(0.0, annual_rate / 100 - COST_OF_FUNDS)      # spread over cost of funds
    life = behavioural_life(product)
    nii = principal * nim * life                            # net interest income
    _lgd = lgd(product["id"])
    ecl = pd * _lgd * principal                             # expected credit loss
    risk_adj = nii - ecl                                    # RAROC-lite numerator
    return {
        "nii": round(nii),
        "ecl": round(ecl),
        "risk_adj_return": round(risk_adj),
        "nim": round(nim, 4),
        "lgd": _lgd,
        "life_years": life,
        "value_destructive": risk_adj < 0,
    }


def lead_expected_value(principal: float, annual_rate: float, pd: float,
                        propensity: float, product: dict) -> dict:
    """Expected value of a LEAD = P(convert) × risk-adjusted return of the loan.

    This is the queue's north-star: it rewards leads that will both close AND
    be profitable net of credit loss — and it correctly SINKS a high-propensity
    loan whose expected credit loss exceeds its margin.
    """
    econ = loan_economics(principal, annual_rate, pd, product)
    ev = round(max(0.0, min(1.0, propensity)) * econ["risk_adj_return"])
    return {**econ, "propensity": propensity, "ev": ev}


if __name__ == "__main__":
    from config import load_json
    prods = {p["id"]: p for p in load_json("products.json")}
    print(f"{'Product':28} {'rate':>5} {'NIM':>5} {'LGD':>4} {'life':>4}  "
          f"{'NII(10L,PD8%)':>13} {'ECL':>9} {'RiskAdj':>10}")
    for pid, p in prods.items():
        r = p["base_rate"] + p["rate_spread"] / 2
        e = loan_economics(1_000_000, r, 0.08, p)
        print(f"{p['name']:28} {r:5.1f} {e['nim']*100:4.1f}% {e['lgd']:.2f} "
              f"{e['life_years']:4.1f}  {e['nii']:13,} {e['ecl']:9,} {e['risk_adj_return']:10,}")
