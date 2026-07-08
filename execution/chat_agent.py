"""Agentic RM copilot — knows the book and the bank, and can take actions.

Query + act + explain:
  • Create a lead from NL → instant decision WITH ranking transparency + "Generate PDF"
  • Look up any prospect / partner → profile + open/offer actions
  • Eligibility check · EMI calculator · product info · portfolio summary
  • Explain how ranking / scoring / risk works
  • Top prospects · churn risk · channel ROI · adverse-selection partners
  • Anything else → grounded LLM answer using a live knowledge context
Every number comes from the engine; the LLM parses + phrases.

Returns {"answer": str, "actions": [{label,type,payload}], "cards": [...]}
"""
from __future__ import annotations

import re

from channel_roi import channel_roi
from partner_churn import churn_watchlist
from score_partner import all_partner_quality, partner, lead_default_risk
from predict_propensity import predict_propensity
from score_financial_health import score_financial_health
from eligibility import check_eligibility, products, emi as calc_emi
from instant_decision import instant_decision
from config import load_json
import lead_utils
import nvidia_llm


def handle(message: str, queue: list[dict]) -> dict:
    m = message.lower().strip()

    # 0. help / capabilities
    if _hit(m, ["what can you do", "what do you do", "help", "capabilities", "commands",
                "how to use", "what are you"]):
        return _help()

    # 1. actions
    if _hit(m, ["create lead", "new lead", "add lead", "generate lead", "make a lead",
                "create a lead", "submit a lead", "onboard", "register a lead"]):
        return _create_lead(message)

    # 2. EMI calculator
    if _hit(m, ["emi", "calculate", "instalment", "installment", "monthly payment"]) and re.search(r"\d", m):
        r = _emi_calc(message)
        if r:
            return r

    # 3. explain how it works
    if _hit(m, ["how does", "how is", "how do you", "explain", "what is propensity",
                "how ranking", "how are leads ranked", "how scoring", "why is"]):
        return _explain(message, queue)

    # 4. portfolio / pipeline stats
    if _hit(m, ["how many", "portfolio", "pipeline", "summary", "overview", "total leads",
                "book", "dashboard"]):
        return _portfolio(queue)

    # 5. product info
    if _hit(m, ["product", "interest rate", "rate of", "tell me about", "eligibility criteria",
                "what products", "which products", "offerings", "loan types"]):
        r = _product_info(message)
        if r:
            return r

    # 5b. compare prospects
    if _hit(m, ["compare", "versus", " vs ", "difference between"]):
        return _compare(message, queue)

    # 6. channel/partner analytics
    if _hit(m, ["churn", "leaving", "disengag", "losing partner"]):
        return _churn()
    if _hit(m, ["roi", "which channel", "profitable channel", "channel mix"]):
        return _roi()
    if _hit(m, ["risky partner", "adverse", "worst partner", "bad partner"]):
        return _adverse()
    if _hit(m, ["top", "best prospect", "hot lead", "call first", "priorit"]):
        return _top(m, queue)

    # 7. named prospect
    who = _find_named(message, queue)
    if who:
        if _hit(m, ["eligib", "qualif", "how much can", "can .* get"]):
            return _eligibility(who)
        if _hit(m, ["offer", "pdf", "quote"]):
            return _offer_for(who)
        return _profile(who)

    # 8. general grounded answer
    return _general(message, queue)


# --------------------------------------------------------------------------- #
# Create lead — with ranking transparency
# --------------------------------------------------------------------------- #

def _create_lead(message: str) -> dict:
    f = _extract_lead(message)
    missing = [k for k in ("monthly_income", "credit_score") if not f.get(k)]
    product_id = f.get("product") or lead_utils.detect_product(message) or "personal_loan"
    amount = f.get("amount") or lead_utils.parse_amount(message) or products()[product_id]["min_amount"]
    partner_id = f.get("partner_id") or lead_utils.default_partner_id(product_id)
    lead = lead_utils.build_lead(
        name=f.get("name") or "New Prospect", partner_id=partner_id, product_id=product_id,
        amount=amount, monthly_income=f.get("monthly_income") or 60000,
        credit_score=f.get("credit_score") or 720, existing_emi=f.get("existing_emi") or 0)

    d = instant_decision(lead)
    prop = predict_propensity(lead)
    health = score_financial_health(lead)
    assumed = f" (assumed income ₹{lead['monthly_income']:,.0f}, CIBIL {lead['credit_score']})" if missing else ""
    answer = (
        f"Lead created — {lead['name']}, {d['product_name']} via {partner(partner_id)['name']}.{assumed}\n"
        f"➤ {d['verdict']}: up to ₹{d['indicative_amount']:,} @ {d['indicative_rate']}% (EMI ₹{d['indicative_emi']:,.0f}/mo).\n\n"
        f"WHY IT'S SCORED THIS WAY (not a black box):\n"
        f"• Conversion propensity {prop['propensity']:.0%} ({prop['tier']}) — {prop['reason']}\n"
        f"• Financial health {health['score']}/100 ({health['band']}) — strengths: {', '.join(health['top_strengths'])}\n"
        f"• Default risk {d['default_risk_band']} — partner-aware (factors {partner(partner_id)['name']}'s track record)")
    if d["indicative_amount"] < amount:
        answer += f"\n• Note: requested ₹{amount:,.0f} was capped to ₹{d['indicative_amount']:,} by FOIR/eligibility."
    offer = {"product_id": product_id, "product_name": d["product_name"],
             "offered_amount": d["indicative_amount"], "rate": d["indicative_rate"],
             "tenure_months": d["tenure_months"], "emi": d["indicative_emi"]}
    return {"answer": answer,
            "cards": [{"type": "decision", "verdict": d["verdict"], "tone": d["tone"]}],
            "actions": [{"label": "💾 Save to Pipeline", "type": "save", "payload": {"lead": lead}},
                        {"label": "📄 Generate PDF Offer", "type": "pdf",
                         "payload": {"lead": lead, "offer": offer}}]}


def _extract_lead(message: str) -> dict:
    if nvidia_llm.available():
        out = nvidia_llm.complete_json(
            "Extract loan-lead fields. Products: home_loan, lap, auto_loan, two_wheeler, "
            "personal_loan, business_loan, education_loan, gold_loan. Amounts in rupees "
            "(expand lakh/crore). null when absent.",
            f'Message: "{message}"\nReturn {{"name":str|null,"product":str|null,"amount":number|null,'
            '"monthly_income":number|null,"credit_score":number|null,"existing_emi":number|null}}.')
        if out:
            return {k: out.get(k) for k in
                    ("name", "product", "amount", "monthly_income", "credit_score", "existing_emi")}
    f = {}
    inc = re.search(r"income[^0-9]*([\d.,]+\s*(?:lakh|lac|l|k|cr|crore)?)", message, re.I)
    if inc:
        f["monthly_income"] = lead_utils.parse_amount(inc.group(1))
    cib = re.search(r"(?:cibil|credit|score)[^0-9]*(\d{3})", message, re.I)
    if cib:
        f["credit_score"] = int(cib.group(1))
    nm = re.search(r"for\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)", message)
    if nm:
        f["name"] = nm.group(1)
    f["product"] = lead_utils.detect_product(message)
    return f


# --------------------------------------------------------------------------- #
# Tools
# --------------------------------------------------------------------------- #

def _emi_calc(message: str):
    amount = lead_utils.parse_amount(message)
    # rate: prefer a number next to '%' or after 'at'/'rate'
    rm = (re.search(r"(\d+(?:\.\d+)?)\s*%", message)
          or re.search(r"(?:at|@|rate\s*(?:of)?)\s*(\d+(?:\.\d+)?)", message, re.I))
    rate = float(rm.group(1)) if rm else None
    ten = re.search(r"(\d+)\s*(year|yr|month|mo)", message, re.I)
    if not (amount and rate and ten):
        return None
    months = int(ten.group(1)) * (12 if ten.group(2).lower().startswith(("y", "yr")) else 1)
    e = calc_emi(amount, rate, months)
    total = e * months
    return {"answer": f"EMI for ₹{amount:,.0f} at {rate}% for {months} months = "
                      f"₹{e:,.0f}/month.\nTotal repayable ≈ ₹{total:,.0f} "
                      f"(interest ≈ ₹{total-amount:,.0f}).", "actions": []}


def _product_info(message: str):
    t = message.lower()
    pid = lead_utils.detect_product(message)
    if pid:
        p = products()[pid]
        return {"answer": f"{p['name']} ({p['category']}):\n"
                          f"• Amount ₹{p['min_amount']:,}–₹{p['max_amount']:,}\n"
                          f"• Rate {p['base_rate']}–{round(p['base_rate']+p['rate_spread'],2)}% p.a. (risk-based)\n"
                          f"• Tenure {p['min_tenure_m']}–{p['max_tenure_m']} months\n"
                          f"• Min income ₹{p['min_income']:,}/mo · min CIBIL {p['min_credit']} · max FOIR {int(p['max_foir']*100)}%\n"
                          f"• Channel commission {p['commission_pct']}%", "actions": []}
    lines = "\n".join(f"• {p['name']} — {p['base_rate']}–{round(p['base_rate']+p['rate_spread'],2)}%, "
                      f"₹{p['min_amount']:,}–₹{p['max_amount']:,}" for p in products().values())
    return {"answer": "IDBI retail loan products:\n" + lines, "actions": []}


def _portfolio(queue: list[dict]) -> dict:
    n = len(queue)
    hot = sum(1 for r in queue if r["tier"] == "Hot")
    high = sum(1 for r in queue if r["risk_band"] == "High")
    breached = sum(1 for r in queue if r.get("sla_state") == "breached")
    avg = sum(r["propensity"] for r in queue) / n
    val = sum(r["amount"] for r in queue)
    partners = all_partner_quality()
    adverse = sum(1 for p in partners if p["adverse_selection"])
    return {"answer": f"Portfolio snapshot:\n"
                      f"• {n} live leads · avg conversion {avg:.0%} · ₹{val:,} pipeline value\n"
                      f"• {hot} Hot · {high} high default-risk · {breached} SLA-breached\n"
                      f"• {len(partners)} partners ({adverse} flagged for adverse selection)",
            "actions": [{"label": "Open dashboard", "type": "link", "payload": {"url": "/"}},
                        {"label": "Channel view", "type": "link", "payload": {"url": "/channel"}}]}


def _explain(message: str, queue) -> dict:
    base = (
        "How Prospect Assist AI scores & ranks (fully explainable):\n"
        "• QUEUE PRIORITY — leads are ranked by RISK-ADJUSTED VALUE = P(convert) × (net interest "
        "income − expected credit loss), where expected loss = PD × LGD × exposure. So RMs work the "
        "most VALUE-CREATING leads first — a loan that would convert but destroy value sinks.\n"
        "• CONVERSION PROPENSITY — a trained ML model ranks P(convert) from income, credit, FOIR, "
        "savings, product-fit. Each lead shows its up/down drivers.\n"
        "• FINANCIAL HEALTH — a transparent weighted rubric (credit 30%, FOIR 22%, savings 18%, "
        "balance 12%, bounces 10%, income 8%) → 0-100, auditable.\n"
        "• DEFAULT RISK — a second ML model (AUC ~0.87) that adds the SOURCING PARTNER's track "
        "record to catch adverse selection before disbursal.\n"
        "• All NUMBERS (eligibility, rate, EMI) come from a deterministic engine — the AI never "
        "invents a figure, it only explains and phrases.")
    if nvidia_llm.available():
        out = nvidia_llm.complete_text(
            "You are an IDBI RM copilot. Answer the user's 'how does it work' question using ONLY "
            "the facts below. Be concise and concrete.",
            f"Question: {message}\n\nFacts:\n{base}", max_tokens=260)
        if out:
            return {"answer": out.strip(), "actions": []}
    return {"answer": base, "actions": []}


def _general(message: str, queue) -> dict:
    if nvidia_llm.available():
        out = nvidia_llm.complete_text(
            "You are a pro IDBI Bank relationship-manager copilot inside Prospect Assist AI. "
            "Answer helpfully and concisely using the CONTEXT. If the user wants an action you "
            "support (create lead, show a prospect, eligibility, EMI, product info, portfolio, "
            "channel ROI, churn), tell them the exact phrase to use. Never invent numbers beyond context.",
            f"User: {message}\n\nCONTEXT:\n{_knowledge(queue)}", max_tokens=300)
        if out:
            return {"answer": out.strip(), "actions": []}
    return _help()


def _knowledge(queue) -> str:
    prods = "; ".join(f"{p['name']} {p['base_rate']}-{round(p['base_rate']+p['rate_spread'],2)}%"
                      for p in products().values())
    n = len(queue)
    hot = sum(1 for r in queue if r["tier"] == "Hot")
    avg = sum(r["propensity"] for r in queue) / n
    top = ", ".join(f"{r['name']} ({r['propensity']:.0%})" for r in queue[:3])
    return (f"Products: {prods}.\nPipeline: {n} leads, avg conversion {avg:.0%}, {hot} hot. "
            f"Top prospects: {top}.\nCapabilities: create leads, prospect lookup, eligibility, "
            f"EMI calc, product info, portfolio stats, channel ROI, churn, adverse-selection, PDF offers.")


# ---- named lookups ----

def _profile(p) -> dict:
    prop = predict_propensity(p)
    health = score_financial_health(p)
    risk = lead_default_risk(p, partner(p["partner_id"]))
    answer = (f"{p['name']} — {p['city']}, {p['occupation']}, CIBIL {p['credit_score']}.\n"
              f"Conversion {prop['propensity']:.0%} ({prop['tier']}; {prop['reason']}) · "
              f"Health {health['score']}/100 · Default risk {risk['risk_band']}.\n"
              f"Wants {products()[p['requested_product']]['name']} ₹{p['requested_amount']:,} "
              f"via {partner(p['partner_id'])['name']}.")
    return {"answer": answer,
            "actions": [{"label": f"Open {p['name'].split()[0]}'s profile", "type": "link",
                         "payload": {"url": f"/prospect/{p['id']}"}},
                        {"label": "Create Offer", "type": "link", "payload": {"url": f"/offer/{p['id']}"}}]}


def _eligibility(p) -> dict:
    e = check_eligibility(p, p["requested_product"])
    return {"answer": f"{p['name']} for {e['product_name']}: {e['decision'].upper()}. "
                      f"Up to ₹{e['offered_amount']:,} at {e['rate']}% (EMI ₹{e['emi']:,.0f}/mo, "
                      f"projected FOIR {e['projected_foir']:.0%}). " + "; ".join(e["reasons"][:2]),
            "actions": [{"label": "Create Offer", "type": "link", "payload": {"url": f"/offer/{p['id']}"}}]}


def _offer_for(p) -> dict:
    e = check_eligibility(p, p["requested_product"])
    offer = {"product_id": p["requested_product"], "product_name": e["product_name"],
             "offered_amount": e["offered_amount"], "rate": e["rate"],
             "tenure_months": e["tenure_months"], "emi": e["emi"]}
    return {"answer": f"Draft offer for {p['name']}: {e['product_name']} ₹{e['offered_amount']:,} "
                      f"@ {e['rate']}% (EMI ₹{e['emi']:,.0f}/mo).",
            "actions": [{"label": "📄 Generate PDF Offer", "type": "pdf",
                         "payload": {"lead": p, "offer": offer}},
                        {"label": "Open offer editor", "type": "link", "payload": {"url": f"/offer/{p['id']}"}}]}


def _compare(message, queue) -> dict:
    # split the message into candidate names on compare/and/vs/commas, then resolve each
    text = re.sub(r"\b(compare|versus|vs|difference between|and|between)\b", ",", message, flags=re.I)
    parts = [s.strip() for s in text.split(",") if len(s.strip()) > 2]
    found = []
    for part in parts:
        p = lead_utils.find_prospect_by_name(part)
        if p and p["id"] not in [f["id"] for f in found]:
            found.append(p)
    found = found[:4]
    if len(found) < 2:
        return {"answer": "Tell me at least two names to compare, e.g. \"compare "
                          f"{queue[0]['name']} and {queue[1]['name']}\".", "actions": []}
    names = ", ".join(f["name"] for f in found)
    ids = ",".join(f["id"] for f in found)
    return {"answer": f"Comparing {names} side-by-side — propensity, health, risk, eligibility "
                      f"and recommended action.",
            "actions": [{"label": "Open comparison", "type": "link",
                         "payload": {"url": f"/compare?ids={ids}"}}]}


def _top(m, queue) -> dict:
    n = _num(m, 5)
    rows = queue[:n]
    return {"answer": f"Top {n} prospects by conversion propensity:\n" + "\n".join(
        f"  {i+1}. {r['name']} — {r['propensity']:.0%} ({r['product']}, via {r['channel']})"
        for i, r in enumerate(rows)),
        "actions": [{"label": f"Open {rows[0]['name'].split()[0]}", "type": "link",
                     "payload": {"url": f"/prospect/{rows[0]['id']}"}}]}


def _churn() -> dict:
    wl = churn_watchlist()
    return {"answer": f"{len(wl)} partners on the churn watchlist:\n" + "\n".join(
        f"  • {r['name']} — risk {r['churn_risk']:.0%} ({r['band']}), last active {r['last_activity_days']}d"
        for r in wl[:6]),
        "actions": [{"label": "Open Channel view", "type": "link", "payload": {"url": "/channel"}}]}


def _roi() -> dict:
    roi = channel_roi()
    a = "Channel ROI (profit/lead):\n" + "\n".join(
        f"  • {r['channel']}: ₹{r['profit_per_lead']:,} (conv {r['avg_conversion']:.0%}, default {r['avg_default']:.0%})"
        for r in roi) + f"\n→ Best: {roi[0]['channel']}; review {roi[-1]['channel']}."
    return {"answer": a, "actions": [{"label": "Open Channel view", "type": "link", "payload": {"url": "/channel"}}]}


def _adverse() -> dict:
    parts = [p for p in all_partner_quality() if p["adverse_selection"]]
    a = (f"{len(parts)} adverse-selection partners:\n" + "\n".join(
        f"  • {p['name']} — default {p['default_rate']:.0%}, quality {p['quality_score']}/100"
        for p in parts)) or "None flagged."
    return {"answer": a, "actions": ([{"label": f"Open {parts[0]['name']}", "type": "link",
             "payload": {"url": f"/partner/{parts[0]['id']}"}}] if parts else [])}


def _help() -> dict:
    return {"answer": "I'm your RM copilot. I can:\n"
                      "• Create leads — \"create a lead for Ramesh, home loan 50 lakh, income 1.2 lakh, CIBIL 760\"\n"
                      "• Look up anyone — \"show me Kavya Singh\" · \"is Deepa eligible?\"\n"
                      "• Calculate — \"EMI for 10 lakh at 9% for 20 years\"\n"
                      "• Explain — \"how does ranking work?\"\n"
                      "• Analytics — \"top 5 prospects\" · \"portfolio summary\" · \"best channel ROI\" · \"churn risk\"",
            "actions": []}


def _find_named(message, queue):
    ml = message.lower()
    # full-name match is always safe
    for r in queue:
        if r["name"].lower() in ml:
            return lead_utils.find_prospect_by_name(r["name"])
    # first-name-only match ONLY when the message reads like a lookup (avoids hijacking
    # general questions that happen to contain a common first name)
    if _hit(ml, ["show", "about", "detail", "who is", "profile", "eligib",
                 "offer for", "pull up", "open ", "look up"]):
        for r in queue:
            first = r["name"].split()[0].lower()
            if len(first) > 3 and re.search(r"\b" + re.escape(first) + r"\b", ml):
                return lead_utils.find_prospect_by_name(r["name"])
    return None


def _maybe_name(message):
    m = re.search(r"(?:show|about|details?|who is|for|is)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)", message)
    return m.group(1) if m else None


def _hit(m, keys):
    return any(re.search(k, m) if any(c in k for c in ".*") else k in m for k in keys)


def _num(m, default):
    mo = re.search(r"\b(\d{1,2})\b", m)
    return int(mo.group(1)) if mo else default


if __name__ == "__main__":
    q = sorted(({"id": p["id"], "name": p["name"], "amount": p["requested_amount"],
                 "propensity": predict_propensity(p)["propensity"], "tier": predict_propensity(p)["tier"],
                 "risk_band": "Low", "product": products()[p["requested_product"]]["name"],
                 "channel": p["source_channel"]} for p in load_json("prospects.json")),
                key=lambda r: -r["propensity"])
    for msg in ["Create a lead for Ramesh, home loan 50 lakh, income 1.2 lakh, CIBIL 760",
                "EMI for 10 lakh at 9% for 20 years", "how does ranking work",
                "portfolio summary", "tell me about home loan", "what can you do"]:
        print(f"\n> {msg}\n{handle(msg, q)['answer'][:400]}")
