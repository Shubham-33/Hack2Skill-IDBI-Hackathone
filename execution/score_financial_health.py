"""Deterministic, explainable financial-health score (0-100).

No ML, no LLM — a transparent weighted rubric so every score is auditable and
reproducible. Returns the score plus a factor-by-factor breakdown that the UI
and the LLM turn into a plain-language "because…".
"""
from __future__ import annotations


# (label, weight, scorer(prospect) -> 0..1)
def _f_credit(p):
    # 560..830 mapped to 0..1
    return _clamp((p["credit_score"] - 560) / (830 - 560))


def _f_foir(p):
    # lower FOIR (existing-EMI / income) is healthier; 0 -> 1.0, 0.5+ -> 0
    return _clamp(1 - p.get("foir", 0) / 0.5)


def _f_savings(p):
    return _clamp(p["transactions"]["savings_ratio"] / 0.3)


def _f_balance(p):
    # avg balance relative to a month's income
    ratio = p["transactions"]["avg_balance"] / max(1, p["monthly_income"])
    return _clamp(ratio / 2.0)


def _f_bounces(p):
    return _clamp(1 - p["transactions"]["monthly_bounces"] / 3.0)


def _f_salary(p):
    return 1.0 if p["transactions"]["regular_salary_credit"] else 0.4


FACTORS = [
    ("Credit score (CIBIL)", 0.30, _f_credit),
    ("Debt burden (FOIR)", 0.22, _f_foir),
    ("Savings behaviour", 0.18, _f_savings),
    ("Balance cushion", 0.12, _f_balance),
    ("Cheque/ACH bounces", 0.10, _f_bounces),
    ("Income regularity", 0.08, _f_salary),
]


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def score_financial_health(prospect: dict) -> dict:
    breakdown = []
    total = 0.0
    for label, weight, fn in FACTORS:
        raw = _clamp(fn(prospect))
        contribution = raw * weight
        total += contribution
        breakdown.append({
            "factor": label,
            "weight": weight,
            "sub_score": round(raw * 100),
            "points": round(contribution * 100, 1),
        })
    score = round(total * 100)
    band = ("Excellent" if score >= 80 else "Good" if score >= 65
            else "Fair" if score >= 50 else "Weak")
    # rank factors by how much they *cost* the prospect (headroom * weight) => top improvement levers
    levers = sorted(
        ({"factor": b["factor"], "lost_points": round((b["weight"] * 100) - b["points"], 1)}
         for b in breakdown),
        key=lambda x: x["lost_points"], reverse=True,
    )
    return {
        "score": score,
        "band": band,
        "breakdown": breakdown,
        "top_strengths": [b["factor"] for b in sorted(breakdown, key=lambda x: -x["sub_score"])[:2]],
        "top_gaps": [l["factor"] for l in levers[:2]],
    }


if __name__ == "__main__":
    from config import load_json
    for p in load_json("prospects.json")[:3]:
        r = score_financial_health(p)
        print(f"{p['name']:20} score={r['score']:3} ({r['band']:9}) "
              f"strengths={r['top_strengths']} gaps={r['top_gaps']}")
