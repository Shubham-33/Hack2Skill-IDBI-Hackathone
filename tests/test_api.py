"""Full API integration tests — every route, happy path + edge/404/400.

Runs against the FastAPI app via TestClient in deterministic (LLM-off) mode.
PDF routes need native pango/cairo → run with DYLD_FALLBACK_LIBRARY_PATH set
(see run.sh / the make-test command).
"""


# ---- pages ----
def test_home(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Prospect Queue" in r.text and "Priority" in r.text


def test_health(client):
    j = client.get("/health").json()
    assert j["ok"] is True and j["prospects"] > 0


def test_channel_partner_portal_deck(client):
    for path, needle in [("/channel", "Partner Leaderboard"),
                         ("/partner-portal", "Partner Portal"),
                         ("/deck", "Prospect Assist AI"),
                         ("/submit", "Instant In-Principle Decision")]:
        r = client.get(path)
        assert r.status_code == 200 and needle in r.text


def test_prospect_page_and_card(client, first_pid):
    assert client.get(f"/prospect/{first_pid}").status_code == 200
    assert "How this prospect is ranked" in client.get(f"/prospect/{first_pid}").text
    assert client.get(f"/prospect/{first_pid}/card").status_code == 200


def test_prospect_not_found(client):
    assert client.get("/prospect/NOPE").status_code == 404


# ---- offer flow ----
def test_offer_form_and_404(client, first_pid):
    assert client.get(f"/offer/{first_pid}").status_code == 200
    assert client.get("/offer/NOPE").status_code == 404


def test_offer_recompute_clamps_rate(client, first_pid):
    r = client.post(f"/offer/{first_pid}/recompute",
                    data={"product_id": "personal_loan", "amount": 500000,
                          "rate": 99, "tenure_months": 60})
    j = r.json()
    assert r.status_code == 200 and j["emi"] > 0
    assert j["rate"] <= 16.0 and any("band" in e for e in j["errors"])


def test_offer_pdf(client, first_pid):
    r = client.post(f"/offer/{first_pid}/pdf",
                    data={"product_id": "personal_loan", "amount": 400000,
                          "rate": 13, "tenure_months": 48})
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    assert len(r.content) > 5000


def test_send_links_and_404(client, first_pid):
    r = client.get(f"/send/{first_pid}", params={"product_id": "personal_loan",
                   "amount": 400000, "rate": 13, "tenure_months": 48})
    j = r.json()
    assert r.status_code == 200 and j["whatsapp_url"].startswith("https://wa.me")
    assert client.get("/send/NOPE", params={"product_id": "personal_loan", "amount": 1,
                      "rate": 13, "tenure_months": 48}).status_code == 404


# ---- partner ----
def test_partner_and_summary(client):
    assert client.get("/partner/PTR001").status_code == 200
    s = client.get("/api/partner/PTR001/summary").json()
    assert "tier" in s and s["sla_hours"] > 0
    assert client.get("/partner/NOPE").status_code == 404
    assert client.get("/api/partner/NOPE/summary").status_code == 404


# ---- submit / instant decision ----
def test_submit_happy(client):
    r = client.post("/submit", data={"partner_id": "PTR001", "name": "Test",
        "product_id": "auto_loan", "amount": 1200000, "monthly_income": 90000,
        "credit_score": 760, "existing_emi": 8000, "bounces": 0, "regular_salary": "yes"})
    d = r.json()["decision"]
    assert r.status_code == 200 and d["indicative_amount"] >= 0


def test_submit_degenerate_inputs_no_500(client):
    r = client.post("/submit", data={"partner_id": "PTR001", "name": "Edge",
        "product_id": "personal_loan", "amount": -5000, "monthly_income": 0,
        "credit_score": 800, "existing_emi": 0, "bounces": 0, "regular_salary": "yes"})
    assert r.status_code == 200  # clamped, not crashed


def test_submit_pdf(client):
    r = client.post("/submit/pdf", data={"partner_id": "PTR001", "name": "PdfUser",
        "product_id": "home_loan", "amount": 5000000, "monthly_income": 120000,
        "credit_score": 760, "existing_emi": 15000, "bounces": 0, "regular_salary": "yes"})
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"


# ---- lead persistence ----
def test_lead_save_and_appears(client):
    r = client.post("/lead/save", data={"partner_id": "PTR001", "name": "ZZ Saved",
        "product_id": "personal_loan", "amount": 300000, "monthly_income": 70000,
        "credit_score": 750, "existing_emi": 0, "bounces": 0, "regular_salary": "yes"})
    j = r.json()
    assert j["ok"] and j["id"].startswith("LADD")
    assert client.get(j["url"]).status_code == 200


def test_lead_save_json_bad_400(client):
    assert client.post("/lead/save-json", json={"lead": {"name": "x"}}).status_code == 400


def test_lead_pdf_json_and_bad(client):
    lead = {"id": "LX", "name": "Jli", "city": "-", "monthly_income": 80000,
            "existing_emi": 0, "foir": 0, "credit_score": 760, "requested_product": "personal_loan",
            "requested_amount": 400000, "partner_id": "PTR001", "source_channel": "DSA",
            "transactions": {"avg_balance": 80000, "savings_ratio": 0.15,
                             "monthly_bounces": 0, "regular_salary_credit": True}}
    offer = {"product_id": "personal_loan", "product_name": "IDBI Personal Loan",
             "offered_amount": 400000, "rate": 13, "tenure_months": 48, "emi": 10000}
    r = client.post("/lead/pdf", json={"lead": lead, "offer": offer})
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    assert client.post("/lead/pdf", json={"bad": 1}).status_code == 400


# ---- compare ----
def test_compare(client):
    r = client.get("/compare", params={"ids": "L0001,L0003"})
    assert r.status_code == 200 and "Compare Prospects" in r.text
    assert client.get("/compare", params={"ids": ""}).status_code == 200  # prompt, no crash


# ---- feedback ----
def test_feedback(client, first_pid):
    r = client.post("/feedback", data={"lead_id": first_pid, "outcome": "won"})
    assert r.json()["ok"] and r.json()["count"] >= 1
    assert client.post("/feedback", data={"lead_id": first_pid, "outcome": "banana"}).status_code == 400


# ---- assistant ----
def _ask(client, msg):
    return client.post("/chat", data={"message": msg}).json()


def test_chat_intents(client):
    assert "IDBI" in _ask(client, "tell me about home loan")["answer"] or "Home" in _ask(client, "tell me about home loan")["answer"]
    assert "EMI" in _ask(client, "EMI for 10 lakh at 9% for 20 years")["answer"]
    assert "propensity" in _ask(client, "top 5 prospects")["answer"].lower()
    assert _ask(client, "portfolio summary")["answer"]
    assert _ask(client, "which partners are at churn risk")["answer"]
    assert _ask(client, "best channel ROI")["answer"]
    assert _ask(client, "what can you do")["answer"]


def test_chat_create_lead_has_actions(client):
    j = _ask(client, "create a lead for Ramesh, home loan 50 lakh, income 1.2 lakh, CIBIL 760")
    labels = [a["type"] for a in j["actions"]]
    assert "pdf" in labels and "save" in labels


def test_chat_compare_returns_link(client):
    j = _ask(client, "compare Kavya Singh and Deepa Gupta")
    assert j["actions"] and j["actions"][0]["payload"]["url"].startswith("/compare?ids=")


def test_chat_never_500(client):
    # even gibberish returns a graceful answer
    assert client.post("/chat", data={"message": "@@@###"}).status_code == 200
