"""Shared feature engineering for the ML models.

One source of truth so training and inference never drift. Deliberately EXCLUDES
prohibited attributes (name, gender, religion, caste, city) for fair-lending
compliance — only financial/behavioural signals are used.
"""
from __future__ import annotations

from eligibility import products, price_rate, emi

# order matters — models are trained on this exact sequence
PROPENSITY_FEATURES = [
    "monthly_income", "credit_score", "foir", "amount_to_annual_income",
    "savings_ratio", "balance_ratio", "monthly_bounces", "regular_salary_credit",
    "credit_headroom", "income_headroom", "product_fit",
]

PARTNER_RISK_FEATURES = [
    "credit_score", "foir", "monthly_bounces", "amount_to_annual_income",
    "savings_ratio", "regular_salary_credit", "new_emi_burden",
    # channel signals — the novel part: the sourcing partner's track record
    "partner_default_rate_shrunk", "partner_conversion_rate", "partner_doc_completeness",
]


def _fit(prospect, product):
    score = 1.0
    if prospect["monthly_income"] < product["min_income"]:
        score -= 0.4
    if prospect["credit_score"] < product["min_credit"]:
        score -= 0.4
    if prospect.get("foir", 0) > product["max_foir"]:
        score -= 0.3
    return max(0.0, min(1.0, score))


def prospect_features(prospect: dict) -> dict:
    product = products()[prospect["requested_product"]]
    income = max(1, prospect["monthly_income"])
    tx = prospect["transactions"]
    return {
        "monthly_income": prospect["monthly_income"],
        "credit_score": prospect["credit_score"],
        "foir": prospect.get("foir", 0.0),
        "amount_to_annual_income": prospect["requested_amount"] / (income * 12),
        "savings_ratio": tx["savings_ratio"],
        "balance_ratio": tx["avg_balance"] / income,
        "monthly_bounces": tx["monthly_bounces"],
        "regular_salary_credit": 1 if tx["regular_salary_credit"] else 0,
        "credit_headroom": prospect["credit_score"] - product["min_credit"],
        "income_headroom": prospect["monthly_income"] - product["min_income"],
        "product_fit": _fit(prospect, product),
    }


def partner_risk_features(prospect: dict, partner: dict) -> dict:
    product = products()[prospect["requested_product"]]
    income = max(1, prospect["monthly_income"])
    tx = prospect["transactions"]
    rate = price_rate(product, prospect["credit_score"])
    new_emi = emi(prospect["requested_amount"], rate, min(product["max_tenure_m"], 60))
    h = partner["history"]
    # Bayesian shrinkage: pull a partner's default rate toward the population mean
    # when their volume is low, so small/new DSAs aren't unfairly penalised.
    n = h["leads_sourced"]
    prior, strength = 0.08, 40.0
    shrunk = (h["default_rate"] * n + prior * strength) / (n + strength)
    return {
        "credit_score": prospect["credit_score"],
        "foir": prospect.get("foir", 0.0),
        "monthly_bounces": tx["monthly_bounces"],
        "amount_to_annual_income": prospect["requested_amount"] / (income * 12),
        "savings_ratio": tx["savings_ratio"],
        "regular_salary_credit": 1 if tx["regular_salary_credit"] else 0,
        "new_emi_burden": (prospect.get("existing_emi", 0) + new_emi) / income,
        "partner_default_rate_shrunk": round(shrunk, 4),
        "partner_conversion_rate": h["conversion_rate"],
        "partner_doc_completeness": h["doc_completeness"],
    }


def vectorize(feat: dict, order: list[str]) -> list[float]:
    return [float(feat[k]) for k in order]
