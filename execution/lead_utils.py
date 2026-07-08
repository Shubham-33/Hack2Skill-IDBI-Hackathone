"""Helpers to build ad-hoc leads and look up prospects — shared by the web app,
the submit flow, and the agentic assistant.
"""
from __future__ import annotations

import re

from config import load_json, save_json
from eligibility import products
from score_partner import partner

PRODUCT_KEYWORDS = {
    "home_loan": ["home", "house", "housing"],
    "lap": ["property", "lap", "against property"],
    "auto_loan": ["car", "auto", "vehicle", "four wheeler"],
    "two_wheeler": ["bike", "two wheeler", "two-wheeler", "scooter", "motorcycle"],
    "personal_loan": ["personal"],
    "business_loan": ["business", "msme", "working capital"],
    "education_loan": ["education", "student", "study", "college"],
    "gold_loan": ["gold"],
}


def build_lead(name, partner_id, product_id, amount, monthly_income, credit_score,
               existing_emi=0, bounces=0, regular_salary=True, city="—", lead_id="LNEW"):
    ptr = partner(partner_id)
    # clamp to sane ranges so degenerate inputs can't crash or produce nonsense
    monthly_income = max(1000.0, float(monthly_income or 0))
    amount = max(0.0, float(amount or 0))
    credit_score = max(300, min(900, int(credit_score or 700)))
    existing_emi = max(0.0, float(existing_emi or 0))
    bounces = max(0, int(bounces or 0))
    if product_id not in products():
        product_id = "personal_loan"
    return {
        "id": lead_id, "name": name or "New Prospect", "city": city, "age": 35,
        "occupation": "Salaried",
        "monthly_income": monthly_income, "existing_emi": existing_emi,
        "foir": round(existing_emi / monthly_income, 3),
        "credit_score": credit_score, "requested_product": product_id,
        "requested_amount": amount,
        "source_channel": ptr["type"] if ptr else "DSA",
        "partner_id": partner_id,
        "transactions": {"avg_balance": float(monthly_income), "savings_ratio": 0.15,
                         "monthly_bounces": int(bounces),
                         "regular_salary_credit": bool(regular_salary)},
        "status": "new", "submitted_hours_ago": 0,
    }


def persist_lead(lead: dict) -> str:
    """Append a created lead to the live pipeline (prospects.json) and return its new id.

    De-dupes by name+product+partner so re-saving the same lead doesn't pile up.
    """
    # minimal validation: a lead must carry the fields the engine needs
    required = ("name", "requested_product", "partner_id", "monthly_income",
                "credit_score", "requested_amount")
    if not all(k in lead for k in required):
        raise ValueError("lead is missing required fields")
    prospects = load_json("prospects.json")
    added = [p for p in prospects if str(p["id"]).startswith("LADD")]
    key = (lead["name"].strip().lower(), lead["requested_product"], lead["partner_id"])
    for p in added:
        if (p["name"].strip().lower(), p["requested_product"], p["partner_id"]) == key:
            return p["id"]  # already saved
    if len(added) >= 100:                                   # cap to prevent unbounded growth
        raise ValueError("pipeline lead cap reached (100)")
    n = 1 + max([int(str(p["id"])[4:]) for p in added] or [0])
    new_id = f"LADD{n:03d}"
    saved = dict(lead, id=new_id, status="new", submitted_hours_ago=1,
                 created_date="2026-07-07")
    saved.pop("_latent_convert", None)
    prospects.append(saved)
    save_json("prospects.json", prospects)
    return new_id


def find_prospect_by_name(name: str):
    if not name:
        return None
    name = name.strip().lower()
    best = None
    for p in load_json("prospects.json"):
        pn = p["name"].lower()
        if name == pn:
            return p
        if name in pn or pn.split()[0] == name.split()[0]:
            best = best or p
    return best


def parse_amount(text: str):
    """Parse Indian money phrases: '50 lakh', '1.2cr', '₹6,00,000', '600000'."""
    t = text.lower().replace(",", "")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(crore|cr|lakh|lac|l|k|thousand)?", t)
    if not m:
        return None
    val = float(m.group(1))
    unit = m.group(2) or ""
    if unit in ("crore", "cr"):
        val *= 1_00_00_000
    elif unit in ("lakh", "lac", "l"):
        val *= 1_00_000
    elif unit in ("k", "thousand"):
        val *= 1_000
    return val


def detect_product(text: str):
    t = text.lower()
    for pid, kws in PRODUCT_KEYWORDS.items():
        if any(k in t for k in kws):
            return pid
    return None


def default_partner_id(product_id=None):
    parts = load_json("partners.json")
    if product_id:
        for p in parts:
            if product_id in p["products"]:
                return p["id"]
    return parts[0]["id"]
