"""Generate realistic synthetic data for Prospect Assist AI.

Produces (in data/):
  products.json  — IDBI retail loan catalog + eligibility + rate/commission tables
  partners.json  — DSAs / dealers / connectors with commission structures + history
  prospects.json — the live prospect/lead queue the RM works
  history.json    — ~2500 past leads with outcomes (converted / defaulted) for ML training

Deterministic (seeded) so the demo is reproducible. Conversion and default are
generated from a realistic latent process so the ML models learn genuine signal.
"""
from __future__ import annotations

import random
from datetime import date, timedelta

from config import save_json

SEED = 42
random.seed(SEED)

# --------------------------------------------------------------------------- #
# Reference tables
# --------------------------------------------------------------------------- #

PRODUCTS = [
    {
        "id": "home_loan", "name": "IDBI Home Loan", "category": "Secured",
        "min_amount": 500000, "max_amount": 15000000, "min_tenure_m": 60, "max_tenure_m": 360,
        "base_rate": 8.4, "rate_spread": 1.8, "min_income": 30000, "min_credit": 700,
        "max_foir": 0.55, "commission_pct": 0.5, "channels": ["Builder", "DSA", "Connector"],
    },
    {
        "id": "lap", "name": "IDBI Loan Against Property", "category": "Secured",
        "min_amount": 500000, "max_amount": 20000000, "min_tenure_m": 60, "max_tenure_m": 180,
        "base_rate": 9.5, "rate_spread": 2.2, "min_income": 40000, "min_credit": 720,
        "max_foir": 0.55, "commission_pct": 0.9, "channels": ["DSA", "Connector"],
    },
    {
        "id": "auto_loan", "name": "IDBI Auto Loan", "category": "Secured",
        "min_amount": 200000, "max_amount": 3000000, "min_tenure_m": 12, "max_tenure_m": 84,
        "base_rate": 9.1, "rate_spread": 2.0, "min_income": 25000, "min_credit": 680,
        "max_foir": 0.5, "commission_pct": 1.2, "channels": ["Dealer", "DSA"],
    },
    {
        "id": "two_wheeler", "name": "IDBI Two-Wheeler Loan", "category": "Secured",
        "min_amount": 40000, "max_amount": 300000, "min_tenure_m": 12, "max_tenure_m": 48,
        "base_rate": 11.5, "rate_spread": 3.0, "min_income": 15000, "min_credit": 650,
        "max_foir": 0.5, "commission_pct": 2.0, "channels": ["Dealer"],
    },
    {
        "id": "personal_loan", "name": "IDBI Personal Loan", "category": "Unsecured",
        "min_amount": 50000, "max_amount": 2000000, "min_tenure_m": 12, "max_tenure_m": 72,
        "base_rate": 11.0, "rate_spread": 5.0, "min_income": 25000, "min_credit": 700,
        "max_foir": 0.5, "commission_pct": 2.5, "channels": ["DSA", "Connector", "Aggregator"],
    },
    {
        "id": "business_loan", "name": "IDBI MSME / Business Loan", "category": "Unsecured",
        "min_amount": 100000, "max_amount": 5000000, "min_tenure_m": 12, "max_tenure_m": 84,
        "base_rate": 12.0, "rate_spread": 4.5, "min_income": 40000, "min_credit": 710,
        "max_foir": 0.55, "commission_pct": 2.0, "channels": ["DSA", "Connector"],
    },
    {
        "id": "education_loan", "name": "IDBI Education Loan", "category": "Secured",
        "min_amount": 100000, "max_amount": 4000000, "min_tenure_m": 24, "max_tenure_m": 180,
        "base_rate": 9.8, "rate_spread": 2.5, "min_income": 20000, "min_credit": 670,
        "max_foir": 0.6, "commission_pct": 0.8, "channels": ["Connector", "DSA"],
    },
    {
        "id": "gold_loan", "name": "IDBI Gold Loan", "category": "Secured",
        "min_amount": 20000, "max_amount": 2500000, "min_tenure_m": 6, "max_tenure_m": 36,
        "base_rate": 9.0, "rate_spread": 2.5, "min_income": 10000, "min_credit": 600,
        "max_foir": 0.6, "commission_pct": 1.0, "channels": ["DSA", "Aggregator"],
    },
]
PRODUCT_BY_ID = {p["id"]: p for p in PRODUCTS}

CHANNEL_TYPES = ["DSA", "Dealer", "Connector", "Aggregator", "Builder"]
CITIES = ["Mumbai", "Delhi", "Bengaluru", "Pune", "Hyderabad", "Chennai",
          "Ahmedabad", "Kolkata", "Jaipur", "Lucknow", "Indore", "Surat"]
OCCUPATIONS = ["Salaried", "Self-Employed Professional", "Self-Employed Business"]
FIRST = ["Rahul", "Priya", "Amit", "Sneha", "Vikram", "Anjali", "Ravi", "Deepa",
         "Suresh", "Kavya", "Arjun", "Meera", "Rohit", "Pooja", "Karan", "Neha",
         "Sanjay", "Divya", "Manish", "Ritu", "Aditya", "Shreya", "Nikhil", "Isha"]
LAST = ["Sharma", "Verma", "Patel", "Reddy", "Nair", "Iyer", "Gupta", "Singh",
        "Mehta", "Joshi", "Rao", "Desai", "Kapoor", "Malhotra", "Bose", "Shah"]
DSA_BRANDS = ["FinConnect", "QuickLoan", "TrustCapital", "SwiftFinance", "ApexBrokers",
              "PrimeLeads", "SafeHarbor", "MetroFin", "RapidCredit", "GoldGate",
              "UrbanMoney", "NextGen Advisors", "PinnacleFin", "CapitalBridge",
              "EliteLoans", "SpeedyFunds", "GreenFinance", "SterlingCredit"]

TODAY = date(2026, 7, 6)


def _name():
    return f"{random.choice(FIRST)} {random.choice(LAST)}"


def _round_amount(x):
    return int(round(x / 10000.0)) * 10000


# --------------------------------------------------------------------------- #
# Partners
# --------------------------------------------------------------------------- #

def make_partners(n=32):
    partners = []
    for i in range(n):
        ctype = random.choices(CHANNEL_TYPES, weights=[40, 20, 20, 12, 8])[0]
        # products this partner handles, aligned to its channel type
        handled = [p["id"] for p in PRODUCTS if ctype in p["channels"]]
        if not handled:
            handled = ["personal_loan"]
        # latent quality drives their real conversion + default behaviour
        quality = random.betavariate(2.5, 2.0)          # 0..1, higher = better
        volume = random.choices(["low", "mid", "high"], weights=[45, 35, 20])[0]
        base_subs = {"low": random.randint(8, 25),
                     "mid": random.randint(25, 70),
                     "high": random.randint(70, 160)}[volume]
        conv_rate = round(0.12 + 0.45 * quality + random.uniform(-0.05, 0.05), 3)
        conv_rate = min(max(conv_rate, 0.05), 0.7)
        # partners paid on disbursal -> some low-quality ones push bad loans.
        # NOTE: this is a NOISY observed estimate of past cohorts, deliberately
        # decoupled from the per-lead label to avoid target leakage.
        default_rate = round(0.03 + 0.12 * (1 - quality) + random.uniform(-0.03, 0.05), 3)
        default_rate = min(max(default_rate, 0.005), 0.28)
        avg_tat = round(1.5 + 4.5 * (1 - quality) + random.uniform(-0.5, 1.5), 1)
        doc_completeness = round(0.6 + 0.38 * quality + random.uniform(-0.05, 0.05), 2)
        doc_completeness = min(doc_completeness, 0.99)
        # engagement trend (last 6 months of submissions) — some are churning
        churning = random.random() < 0.22
        trend = []
        cur = base_subs
        for _ in range(6):
            drift = random.uniform(-0.28, 0.05) if churning else random.uniform(-0.1, 0.18)
            cur = max(0, int(cur * (1 + drift)))
            trend.append(cur)
        last_activity_days = random.randint(20, 75) if churning else random.randint(0, 12)

        commission_structure = {
            "type": random.choice(["flat", "slab"]),
            # slab bonus rewards volume; flat is a single pct multiplier on product commission
            "multiplier": round(random.uniform(0.85, 1.25), 2),
            "slabs": [
                {"min_disbursed": 0, "bonus_pct": 0.0},
                {"min_disbursed": 5000000, "bonus_pct": 0.1},
                {"min_disbursed": 20000000, "bonus_pct": 0.25},
            ],
            "clawback_months": 6,
            "clawback_pct": 0.5,
        }

        partners.append({
            "id": f"PTR{i+1:03d}",
            "name": f"{random.choice(DSA_BRANDS)} {ctype}",
            "type": ctype,
            "city": random.choice(CITIES),
            "products": handled,
            "commission_structure": commission_structure,
            "_quality": round(quality, 3),            # latent, used by generator (not shown to model directly)
            "history": {
                "leads_sourced": base_subs * 6,
                "conversion_rate": conv_rate,
                "default_rate": default_rate,
                "avg_tat_days": avg_tat,
                "doc_completeness": doc_completeness,
                "total_disbursed": _round_amount(base_subs * 6 * conv_rate * random.uniform(300000, 900000)),
                "monthly_submissions": trend,
                "last_activity_days": last_activity_days,
            },
        })
    return partners


# --------------------------------------------------------------------------- #
# Prospect / lead generation
# --------------------------------------------------------------------------- #

def make_prospect(pid, partners, historical=False):
    partner = random.choice(partners)
    occupation = random.choice(OCCUPATIONS)
    age = random.randint(23, 58)
    # income depends loosely on occupation
    base_income = {"Salaried": 55000,
                   "Self-Employed Professional": 90000,
                   "Self-Employed Business": 75000}[occupation]
    monthly_income = _round_amount(max(15000, random.lognormvariate(0, 0.45) * base_income))
    credit_score = int(min(830, max(560, random.gauss(720, 55))))
    existing_emi = _round_amount(max(0, random.uniform(0, 0.35) * monthly_income))

    # pick a product this partner can source
    product_id = random.choice(partner["products"])
    product = PRODUCT_BY_ID[product_id]
    requested_amount = _round_amount(
        random.uniform(product["min_amount"], min(product["max_amount"], monthly_income * random.uniform(8, 60)))
    )
    requested_amount = max(product["min_amount"], requested_amount)

    # transaction / behaviour signals
    savings_ratio = round(min(0.6, max(0.0, random.gauss(0.18, 0.12))), 3)
    avg_balance = _round_amount(monthly_income * random.uniform(0.3, 3.0))
    bounce_count = random.choices([0, 0, 0, 1, 2, 3], weights=[45, 20, 15, 10, 6, 4])[0]
    salary_credits_regular = random.random() < (0.85 if occupation == "Salaried" else 0.5)

    foir = round((existing_emi) / monthly_income, 3) if monthly_income else 1.0

    prospect = {
        "id": pid,
        "name": _name(),
        "age": age,
        "city": partner["city"] if random.random() < 0.7 else random.choice(CITIES),
        "occupation": occupation,
        "monthly_income": monthly_income,
        "existing_emi": existing_emi,
        "foir": foir,
        "credit_score": credit_score,
        "requested_product": product_id,
        "requested_amount": requested_amount,
        "source_channel": partner["type"],
        "partner_id": partner["id"],
        "transactions": {
            "avg_balance": avg_balance,
            "savings_ratio": savings_ratio,
            "monthly_bounces": bounce_count,
            "regular_salary_credit": salary_credits_regular,
        },
        "goal": random.choice([
            "Buy a home", "Upgrade car", "Expand business", "Child's education",
            "Consolidate debt", "Home renovation", "Working capital", "Medical/emergency",
        ]),
    }

    # ---- latent outcome model (for training + demo realism) ----
    fit = _latent_fit(prospect, product)
    p_convert = _sigmoid(
        -1.7                                          # realistic ~20-25% base lead->disbursal rate
        + 3.0 * (partner["_quality"] - 0.5)
        + 2.2 * (fit - 0.5)
        + 1.4 * (savings_ratio - 0.15) / 0.15 * 0.3
        + (0.4 if salary_credits_regular else -0.3)
        + (credit_score - 720) / 120.0
    )
    converted = random.random() < p_convert

    # default only meaningful for converted/disbursed.
    # Customer signals DOMINATE; the sourcing partner is a real but weaker factor,
    # plus idiosyncratic noise — so the model can't shortcut via partner history
    # (avoids the target-leakage that inflated AUC in the first cut).
    defaulted = False
    if converted:
        p_default = _sigmoid(
            -2.6
            + 1.5 * (partner["_quality"] < 0.35)      # partner effect: real but not dominant
            + 1.4 * (1 - fit)
            + 1.0 * bounce_count
            - (credit_score - 700) / 80.0
            + 2.5 * max(0, foir - 0.45)
            + random.gauss(0, 0.9)                     # idiosyncratic borrower risk
        )
        defaulted = random.random() < p_default

    if historical:
        created = TODAY - timedelta(days=random.randint(60, 720))
        prospect["created_date"] = created.isoformat()
        prospect["outcome"] = {"converted": converted, "defaulted": defaulted}
        prospect["_p_convert"] = round(p_convert, 3)
    else:
        # live queue: recent, no outcome yet; carries a pipeline status + submission time
        created = TODAY - timedelta(days=random.randint(0, 21))
        prospect["created_date"] = created.isoformat()
        prospect["status"] = random.choices(
            ["new", "verifying", "approved", "disbursed"], weights=[45, 30, 15, 10]
        )[0]
        prospect["submitted_hours_ago"] = random.randint(1, 120)
        prospect["_latent_convert"] = round(p_convert, 3)   # hidden truth, for sanity-checking ranking
    return prospect


def _latent_fit(prospect, product):
    """0..1 how well the prospect fits the product on hard-ish criteria."""
    score = 1.0
    if prospect["monthly_income"] < product["min_income"]:
        score -= 0.4
    if prospect["credit_score"] < product["min_credit"]:
        score -= 0.4
    if prospect["foir"] > product["max_foir"]:
        score -= 0.3
    return max(0.0, min(1.0, score + random.uniform(-0.1, 0.1)))


def _sigmoid(x):
    import math
    return 1.0 / (1.0 + math.exp(-max(-12, min(12, x))))


# --------------------------------------------------------------------------- #

def main():
    partners = make_partners()
    history = [make_prospect(f"H{i+1:05d}", partners, historical=True) for i in range(2500)]
    prospects = [make_prospect(f"L{i+1:04d}", partners, historical=False) for i in range(140)]

    # inject a couple of curated near-duplicate leads (same person via 2 channels) for the dedup demo
    dup = dict(prospects[3])
    other = random.choice([p for p in partners if p["id"] != dup["partner_id"]])
    dup = dict(dup, id="L9001", partner_id=other["id"], source_channel=other["type"],
               submitted_hours_ago=6)
    prospects.append(dup)

    save_json("products.json", PRODUCTS)
    save_json("partners.json", partners)
    save_json("prospects.json", prospects)
    save_json("history.json", history)

    n_conv = sum(h["outcome"]["converted"] for h in history)
    n_def = sum(h["outcome"]["defaulted"] for h in history)
    print(f"products : {len(PRODUCTS)}")
    print(f"partners : {len(partners)}")
    print(f"prospects: {len(prospects)} (live queue, +1 planted duplicate)")
    print(f"history  : {len(history)} | converted={n_conv} ({n_conv/len(history):.0%}) "
          f"| defaulted={n_def} ({n_def/max(1,n_conv):.0%} of converted)")


if __name__ == "__main__":
    main()
