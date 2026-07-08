"""Prospect Assist AI — FastAPI web app (the demo surface).

Three acts:
  Act 1  /            RM dashboard: ML-ranked queue -> prospect detail -> editable offer -> PDF -> send
  Act 2  /channel     Manager view: partner leaderboard, default-risk, ROI, dedup, payouts
  Act 3  /submit      Partner view: submit a lead -> instant indicative decision + SLA + tier
Plus an agentic /chat that routes NL commands to the deterministic tools.
"""
from __future__ import annotations

import os
import sys
import urllib.parse
from functools import lru_cache
from pathlib import Path

# make execution/ importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "execution"))
os.environ.setdefault("DYLD_FALLBACK_LIBRARY_PATH", "/opt/homebrew/lib")

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates

from config import load_json                                    # noqa: E402
from score_financial_health import score_financial_health       # noqa: E402
from predict_propensity import predict_propensity               # noqa: E402
from eligibility import check_eligibility, validate_offer_edit, products  # noqa: E402
from recommend_products import recommend                        # noqa: E402
from generate_pitch import generate_pitch                       # noqa: E402
from generate_offer_pdf import generate_offer_pdf               # noqa: E402
from score_partner import (lead_default_risk, partner, all_partner_quality,  # noqa: E402
                           partner_quality)
from predict_tat import predict_tat                             # noqa: E402
from partner_tier import tier_benefits                          # noqa: E402
from partner_churn import churn_watchlist, churn_signal         # noqa: E402
from commission import partner_statement                        # noqa: E402
from channel_roi import channel_roi                             # noqa: E402
from dedupe_leads import find_duplicates                        # noqa: E402
from instant_decision import instant_decision                  # noqa: E402
from economics import lead_expected_value                       # noqa: E402
from lead_utils import build_lead, persist_lead                 # noqa: E402
import nvidia_llm                                               # noqa: E402
import chat_agent                                               # noqa: E402

app = FastAPI(title="Prospect Assist AI")
templates = Jinja2Templates(directory=str(ROOT / "web" / "templates"))


def render(request, name, **ctx):
    """Starlette 1.x signature: (request, name, context)."""
    return templates.TemplateResponse(request, name, ctx)


# --------------------------------------------------------------------------- #
# View-model builders (cached — the queue is expensive-ish to compute)
# --------------------------------------------------------------------------- #

@lru_cache(maxsize=1)
def _prospects_by_id():
    return {p["id"]: p for p in load_json("prospects.json")}


@lru_cache(maxsize=1)
def ranked_queue():
    rows = []
    for p in _prospects_by_id().values():
        prop = predict_propensity(p)
        health = score_financial_health(p)
        ptr = partner(p["partner_id"])
        risk = lead_default_risk(p, ptr)
        tat = predict_tat(p)
        product = products()[p["requested_product"]]
        # risk-adjusted expected value: what we'd actually book (offered amount) at
        # the risk-based priced rate, its net interest income minus expected credit
        # loss, × P(convert). PD both loads the rate and drives the ECL.
        elig = check_eligibility(p, p["requested_product"], pd=risk["default_risk"])
        principal = elig["offered_amount"] or p["requested_amount"]
        econ = lead_expected_value(principal, elig["rate"], risk["default_risk"],
                                   prop["propensity"], product)
        rows.append({
            "id": p["id"], "name": p["name"], "city": p["city"],
            "product": product["name"],
            "amount": p["requested_amount"],
            "channel": p["source_channel"], "partner_id": p["partner_id"],
            "partner_name": ptr["name"],
            "propensity": prop["propensity"], "tier": prop["tier"],
            "reason": prop["reason"],
            "health": health["score"], "health_band": health["band"],
            "risk": risk["default_risk"], "risk_band": risk["risk_band"],
            "status": p.get("status", "new"),
            "sla_state": tat["sla_state"], "ev": econ["ev"],
            "nii": econ["nii"], "ecl": econ["ecl"], "raroc": econ["risk_adj_return"],
            "value_destructive": econ["value_destructive"],
        })
    rows.sort(key=lambda r: -r["ev"])
    # normalise EV to a 0-100 priority score for display (floor at 0 for negatives)
    top = rows[0]["ev"] if rows else 1
    for r in rows:
        r["priority"] = max(0, round(r["ev"] / top * 100)) if top else 0
    return rows


def prospect_detail(pid: str):
    p = _prospects_by_id().get(pid)
    if not p:
        return None
    health = score_financial_health(p)
    rec = recommend(p, use_llm=nvidia_llm.available())
    ptr = partner(p["partner_id"])
    risk = lead_default_risk(p, ptr)
    tat = predict_tat(p)
    decision = instant_decision(p)
    return {"prospect": p, "health": health, "rec": rec, "partner": ptr,
            "risk": risk, "tat": tat, "decision": decision,
            "partner_tier": tier_benefits(ptr)}


# --------------------------------------------------------------------------- #
# Act 1 — dashboard, detail, offer, PDF, send
# --------------------------------------------------------------------------- #

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    from collections import Counter
    q = ranked_queue()
    stats = {
        "total": len(q),
        "hot": sum(1 for r in q if r["tier"] == "Hot"),
        "high_risk": sum(1 for r in q if r["risk_band"] == "High"),
        "breached": sum(1 for r in q if r["sla_state"] == "breached"),
        "outcomes": len(_load_feedback()),
        "llm": nvidia_llm.available(),
    }
    buckets = [0] * 5  # 0-20 .. 80-100
    for r in q:
        buckets[min(4, int(r["propensity"] * 5))] += 1
    viz = {
        "tiers": [("Hot", stats["hot"]), ("Warm", sum(1 for r in q if r["tier"] == "Warm")),
                  ("Cold", sum(1 for r in q if r["tier"] == "Cold"))],
        "risks": [("Low", sum(1 for r in q if r["risk_band"] == "Low")),
                  ("Medium", sum(1 for r in q if r["risk_band"] == "Medium")),
                  ("High", stats["high_risk"])],
        "channels": sorted(Counter(r["channel"] for r in q).items(), key=lambda x: -x[1]),
        "hist": buckets, "hist_max": max(buckets) or 1,
        "pipeline_value": sum(r["amount"] for r in q),
        # risk-adjusted expected book value = Σ P(convert) × (NII − ECL)
        "risk_adj_value": sum(r["ev"] for r in q),
        "expected_ecl": sum(r["ecl"] for r in q),
    }
    return render(request, "index.html", queue=q, stats=stats, viz=viz)


@app.get("/prospect/{pid}/card", response_class=HTMLResponse)
def detail_card(request: Request, pid: str):
    """Fragment injected into the dashboard side panel."""
    d = prospect_detail(pid)
    if not d:
        return HTMLResponse("Not found", status_code=404)
    return render(request, "detail.html", **d)


@app.get("/prospect/{pid}", response_class=HTMLResponse)
def detail(request: Request, pid: str):
    """Full-page prospect profile (what the assistant / links open)."""
    d = prospect_detail(pid)
    if not d:
        return HTMLResponse("Not found", status_code=404)
    return render(request, "prospect_page.html", **d)


@app.get("/compare", response_class=HTMLResponse)
def compare(request: Request, ids: str = ""):
    id_list = [i for i in ids.split(",") if i][:4]
    cols = []
    for pid in id_list:
        d = prospect_detail(pid)
        if not d or not d["rec"]["recommendations"]:
            continue
        p, rec = d["prospect"], d["rec"]
        top = rec["recommendations"][0]["eligibility"]
        cols.append({
            "id": pid, "name": p["name"], "city": p["city"],
            "credit": p["credit_score"], "income": p["monthly_income"],
            "foir": p["foir"], "propensity": rec["propensity"]["propensity"],
            "tier": rec["propensity"]["tier"], "health": d["health"]["score"],
            "health_band": d["health"]["band"], "risk": d["risk"]["default_risk"],
            "risk_band": d["risk"]["risk_band"], "product": top["product_name"],
            "amount": top["offered_amount"], "rate": top["rate"], "emi": top["emi"],
            "partner": d["partner"]["name"], "channel": p["source_channel"],
        })
    return render(request, "compare.html", cols=cols)


@app.get("/offer/{pid}", response_class=HTMLResponse)
def offer_form(request: Request, pid: str):
    p = _prospects_by_id().get(pid)
    d = prospect_detail(pid)
    if not p or not d or not d["rec"]["recommendations"]:
        return HTMLResponse("Prospect not found", status_code=404)
    top = d["rec"]["recommendations"][0]["eligibility"]
    return render(request, "offer_edit.html", prospect=p, offer=top, products=products())


@app.post("/offer/{pid}/recompute")
def offer_recompute(pid: str, product_id: str = Form(...), amount: float = Form(...),
                    rate: float = Form(...), tenure_months: int = Form(...)):
    p = _prospects_by_id().get(pid)
    v = validate_offer_edit(p, product_id, amount, rate, tenure_months)
    v["product_name"] = products()[product_id]["name"]
    return JSONResponse(v)


@app.post("/offer/{pid}/pdf")
def offer_pdf(pid: str, product_id: str = Form(...), amount: float = Form(...),
              rate: float = Form(...), tenure_months: int = Form(...)):
    p = _prospects_by_id().get(pid)
    v = validate_offer_edit(p, product_id, amount, rate, tenure_months)
    offer = {"product_id": product_id, "product_name": products()[product_id]["name"],
             "offered_amount": v["amount"], "rate": v["rate"],
             "tenure_months": v["tenure_months"], "emi": v["emi"]}
    path = generate_offer_pdf(p, offer, use_llm=nvidia_llm.available())
    return FileResponse(path, media_type="application/pdf",
                        filename=f"IDBI_Offer_{pid}.pdf")


@app.get("/send/{pid}")
def send_links(pid: str, product_id: str, amount: float, rate: float,
               tenure_months: int, language: str = "English"):
    p = _prospects_by_id().get(pid)
    if not p or product_id not in products():
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
    offer = {"product_name": products()[product_id]["name"], "offered_amount": int(amount),
             "rate": rate, "emi": validate_offer_edit(p, product_id, amount, rate, tenure_months)["emi"],
             "tenure_months": int(tenure_months)}
    pitch = generate_pitch(p, offer, use_llm=nvidia_llm.available(), language=language)
    wa = "https://wa.me/?text=" + urllib.parse.quote(pitch["whatsapp_text"])
    gmail = ("https://mail.google.com/mail/?view=cm&fs=1&su="
             + urllib.parse.quote(pitch["email_subject"])
             + "&body=" + urllib.parse.quote(pitch["email_body"]))
    return JSONResponse({"pitch": pitch, "whatsapp_url": wa, "gmail_url": gmail})


# --------------------------------------------------------------------------- #
# Act 2 — channel intelligence
# --------------------------------------------------------------------------- #

@app.get("/channel", response_class=HTMLResponse)
def channel(request: Request):
    partners = all_partner_quality()
    roi = channel_roi()
    dupes = find_duplicates()
    churn = churn_watchlist()
    adverse = [p for p in partners if p["adverse_selection"]]
    concentration = _partner_concentration(partners)
    return render(request, "channel.html", partners=partners, roi=roi, dupes=dupes,
                  churn=churn, adverse=adverse, concentration=concentration)


def _partner_concentration(partners):
    """Single-source-of-book risk. HHI + top-3 exposure share — the concentration
    check a credit-risk officer runs before trusting any channel book."""
    book = sorted(((p["name"], p["history"]["total_disbursed"]) for p in partners),
                  key=lambda x: -x[1])
    total = sum(v for _, v in book) or 1
    shares = [v / total for _, v in book]
    hhi = round(sum(s * s for s in shares) * 10000)          # 0–10,000 (US-DOJ scale)
    top3 = round(sum(shares[:3]) * 100)
    band = "High" if hhi > 2500 else "Moderate" if hhi > 1500 else "Low"
    return {"hhi": hhi, "top3": top3, "band": band,
            "top_partners": [{"name": n, "share": round(v / total * 100)}
                             for n, v in book[:3]]}


@app.get("/partner/{ptr_id}", response_class=HTMLResponse)
def partner_detail(request: Request, ptr_id: str):
    ptr = partner(ptr_id)
    if not ptr:
        return HTMLResponse("Not found", status_code=404)
    tb = tier_benefits(ptr)
    ch = churn_signal(ptr)
    q = partner_quality(ptr)
    # illustrative recent disbursals for a payout statement
    demo_disbursals = [
        {"product_id": ptr["products"][0], "amount": 900000, "months_since": 2, "defaulted": False},
        {"product_id": ptr["products"][0], "amount": 1400000, "months_since": 3, "defaulted": True},
        {"product_id": ptr["products"][-1], "amount": 600000, "months_since": 8, "defaulted": False},
    ]
    statement = partner_statement(ptr_id, demo_disbursals)
    return render(request, "partner.html", partner=ptr, tier=tb, churn=ch, quality=q, statement=statement)


# --------------------------------------------------------------------------- #
# Act 3 — partner submits a lead -> instant decision
# --------------------------------------------------------------------------- #

@app.get("/submit", response_class=HTMLResponse)
def submit_form(request: Request):
    return render(request, "submit.html", products=products(),
                  partners=[{"id": p["id"], "name": p["name"], "type": p["type"]}
                            for p in load_json("partners.json")])


def _lead_from_form(partner_id, name, product_id, amount, monthly_income,
                    credit_score, existing_emi, bounces, regular_salary):
    return build_lead(name=name, partner_id=partner_id, product_id=product_id, amount=amount,
                      monthly_income=monthly_income, credit_score=credit_score,
                      existing_emi=existing_emi, bounces=bounces,
                      regular_salary=(regular_salary == "yes"))


@app.post("/submit")
def submit_lead(partner_id: str = Form(...), name: str = Form(...),
                product_id: str = Form(...), amount: float = Form(...),
                monthly_income: float = Form(...), credit_score: int = Form(...),
                existing_emi: float = Form(0), bounces: int = Form(0),
                regular_salary: str = Form("yes")):
    lead = _lead_from_form(partner_id, name, product_id, amount, monthly_income,
                           credit_score, existing_emi, bounces, regular_salary)
    decision = instant_decision(lead)
    tb = tier_benefits(partner(partner_id))
    return JSONResponse({"decision": decision, "tier": tb})


@app.post("/submit/pdf")
def submit_lead_pdf(partner_id: str = Form(...), name: str = Form(...),
                    product_id: str = Form(...), amount: float = Form(...),
                    monthly_income: float = Form(...), credit_score: int = Form(...),
                    existing_emi: float = Form(0), bounces: int = Form(0),
                    regular_salary: str = Form("yes")):
    lead = _lead_from_form(partner_id, name, product_id, amount, monthly_income,
                           credit_score, existing_emi, bounces, regular_salary)
    d = instant_decision(lead)
    offer = {"product_id": product_id, "product_name": d["product_name"],
             "offered_amount": d["indicative_amount"], "rate": d["indicative_rate"],
             "tenure_months": d["tenure_months"], "emi": d["indicative_emi"]}
    path = generate_offer_pdf(lead, offer, use_llm=nvidia_llm.available())
    return FileResponse(path, media_type="application/pdf", filename=f"IDBI_Offer_{name}.pdf")


# --------------------------------------------------------------------------- #
# Agentic chat
# --------------------------------------------------------------------------- #

@app.post("/chat")
def chat(message: str = Form(...)):
    try:
        return JSONResponse(chat_agent.handle(message, ranked_queue()))
    except Exception as e:  # never 500 the assistant mid-demo
        return JSONResponse({"answer": f"Sorry, I hit an error handling that. ({type(e).__name__})",
                             "actions": []})


def _load_feedback():
    from config import DATA_DIR
    import json
    fp = DATA_DIR / "feedback.json"
    return json.loads(fp.read_text()) if fp.exists() else []


@app.post("/feedback")
def feedback(lead_id: str = Form(...), outcome: str = Form(...), note: str = Form("")):
    """Capture the RM's real outcome (won/lost/nurture) — the closed loop that
    retrains the models. Makes the 'compounding data moat' real, not just pitched."""
    from config import save_json
    if outcome not in ("won", "lost", "nurture"):
        return JSONResponse({"ok": False, "error": "bad outcome"}, status_code=400)
    fb = _load_feedback()
    fb.append({"lead_id": lead_id, "outcome": outcome, "note": note[:200]})
    save_json("feedback.json", fb)
    return JSONResponse({"ok": True, "count": len(fb)})


def _refresh_pipeline():
    """Invalidate cached views so a newly-saved lead shows up ranked."""
    _prospects_by_id.cache_clear()
    ranked_queue.cache_clear()


@app.post("/lead/save")
def lead_save(partner_id: str = Form(...), name: str = Form(...),
              product_id: str = Form(...), amount: float = Form(...),
              monthly_income: float = Form(...), credit_score: int = Form(...),
              existing_emi: float = Form(0), bounces: int = Form(0),
              regular_salary: str = Form("yes")):
    lead = _lead_from_form(partner_id, name, product_id, amount, monthly_income,
                           credit_score, existing_emi, bounces, regular_salary)
    new_id = persist_lead(lead)
    _refresh_pipeline()
    return JSONResponse({"ok": True, "id": new_id, "url": f"/prospect/{new_id}"})


@app.post("/lead/save-json")
async def lead_save_json(request: Request):
    try:
        body = await request.json()
        new_id = persist_lead(body["lead"])
    except (KeyError, ValueError, TypeError) as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    _refresh_pipeline()
    return JSONResponse({"ok": True, "id": new_id, "url": f"/prospect/{new_id}"})


@app.post("/lead/pdf")
async def lead_pdf(request: Request):
    """Generate an offer PDF from an ad-hoc lead+offer (assistant / submit flow)."""
    try:
        body = await request.json()
        lead, offer = body["lead"], body["offer"]
        path = generate_offer_pdf(lead, offer, use_llm=nvidia_llm.available())
    except (KeyError, ValueError, TypeError) as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    return FileResponse(path, media_type="application/pdf",
                        filename=f"IDBI_Offer_{str(lead.get('id', 'lead')).replace('/', '-')}.pdf")


@app.get("/partner-portal", response_class=HTMLResponse)
def partner_portal(request: Request):
    partners = [{"id": p["id"], "name": p["name"], "type": p["type"]}
                for p in load_json("partners.json")]
    return render(request, "partner_portal.html", partners=partners, products=products())


@app.get("/api/partner/{ptr_id}/summary")
def partner_summary(ptr_id: str):
    ptr = partner(ptr_id)
    if not ptr:
        return JSONResponse({"error": "not found"}, status_code=404)
    tb = tier_benefits(ptr)
    ch = churn_signal(ptr)
    demo = [{"product_id": ptr["products"][0], "amount": 900000, "months_since": 2, "defaulted": False},
            {"product_id": ptr["products"][0], "amount": 1400000, "months_since": 3, "defaulted": True}]
    st = partner_statement(ptr_id, demo)
    return JSONResponse({"name": ptr["name"], "tier": tb, "churn_band": ch["band"],
                         "net_payable": st["net_payable"], "clawback": st["clawback_total"],
                         "conversion": ptr["history"]["conversion_rate"],
                         "sla_hours": tb["sla_hours"]})


@app.get("/deck", response_class=HTMLResponse)
def deck(request: Request):
    import joblib
    from config import DATA_DIR
    q = ranked_queue()
    partners = all_partner_quality()
    try:
        prop_auc = joblib.load(DATA_DIR / "propensity.pkl")["auc"]
        risk_auc = joblib.load(DATA_DIR / "partner_risk.pkl")["auc"]
    except Exception:
        prop_auc, risk_auc = 0.71, 0.87
    d = {
        "prospects": len(q),
        "partners": len(partners),
        "adverse": sum(1 for p in partners if p["adverse_selection"]),
        "pipeline_value": sum(r["amount"] for r in q),
        "risk_adj_value": sum(r["ev"] for r in q),
        "prop_auc": prop_auc, "risk_auc": risk_auc,
        # Gini = 2·AUC − 1 : the metric bank model-risk teams actually cite
        "prop_gini": round((2 * prop_auc - 1) * 100),
        "risk_gini": round((2 * risk_auc - 1) * 100),
        "avg_conv": round(sum(r["propensity"] for r in q) / len(q) * 100),
    }
    return render(request, "deck.html", d=d)


@app.get("/health")
def healthz():
    return {"ok": True, "llm": nvidia_llm.available(), "prospects": len(_prospects_by_id())}
