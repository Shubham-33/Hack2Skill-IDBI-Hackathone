"""Fill the IDBI Innovate 2026 prototype submission deck (python-pptx).

Reads the provided template, fills every content slide with Prospect Assist AI
content, builds native flow + architecture diagrams, embeds real prototype
screenshots, and writes a new .pptx (template left untouched).
"""
from __future__ import annotations
import struct
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "Prototype Submission Deck _ IDBI Innovate.pptx"
OUT = ROOT / "Prospect Assist AI - IDBI Innovate Submission Deck.pptx"
SHOTS = ROOT / ".tmp" / "shots"

GREEN = RGBColor(0x0A, 0x7D, 0x6B)
DARK = RGBColor(0x0A, 0x3D, 0x33)
SLATE = RGBColor(0x33, 0x41, 0x55)
GREY = RGBColor(0x64, 0x74, 0x8B)
ACCENT = RGBColor(0xF5, 0x9E, 0x0B)
LIGHT = RGBColor(0xE7, 0xF5, 0xF1)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

prs = Presentation(str(TEMPLATE))
slides = list(prs.slides)


def png_size(p):
    d = open(p, "rb").read(26)
    return struct.unpack(">II", d[16:24])


def body(slide, lines, top=1.62, left=0.4, width=9.2, height=3.6):
    """lines: list of dicts {t, sz, bold, color, bullet, level, space}"""
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = ln.get("level", 0)
        p.space_after = Pt(ln.get("space", 4))
        p.space_before = Pt(0)
        run = p.add_run()
        bullet = ln.get("bullet", False)
        run.text = ("•  " if bullet else "") + ln["t"]
        f = run.font
        f.size = Pt(ln.get("sz", 14))
        f.bold = ln.get("bold", False)
        f.color.rgb = ln.get("color", SLATE)
        f.name = "Calibri"
    return tb


def box(slide, l, t, w, h, text, fill=GREEN, font=WHITE, sz=10.5, bold=True, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    sp = slide.shapes.add_shape(shape, Inches(l), Inches(t), Inches(w), Inches(h))
    sp.fill.solid(); sp.fill.fore_color.rgb = fill
    sp.line.color.rgb = fill; sp.line.width = Pt(0.75)
    sp.shadow.inherit = False
    tf = sp.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.05); tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.03); tf.margin_bottom = Inches(0.03)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = text
    r.font.size = Pt(sz); r.font.bold = bold; r.font.color.rgb = font; r.font.name = "Calibri"
    return sp


def arrow(slide, l, t, w=0.32, h=0.0, color=GREY):
    sp = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(l), Inches(t), Inches(w), Inches(0.22))
    sp.fill.solid(); sp.fill.fore_color.rgb = color; sp.line.fill.background()
    sp.shadow.inherit = False
    return sp


def caption(slide, l, t, w, text):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(0.3))
    p = tb.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = text
    r.font.size = Pt(10); r.font.bold = True; r.font.color.rgb = DARK; r.font.name = "Calibri"
    return tb


def picture(slide, path, l, t, max_w, max_h, border=GREEN):
    w, h = png_size(path)
    ar = w / h
    tw, th = max_w, max_w / ar
    if th > max_h:
        th, tw = max_h, max_h * ar
    l2 = l + (max_w - tw) / 2
    pic = slide.shapes.add_picture(str(path), Inches(l2), Inches(t), Inches(tw), Inches(th))
    pic.line.color.rgb = border; pic.line.width = Pt(1.25)
    return pic


# ---------------------------------------------------------------- Slide 1 — Team
s = slides[0]
for shp in s.shapes:
    if shp.has_text_frame and shp.text_frame.text.strip().startswith("Team Details"):
        paras = shp.text_frame.paragraphs
        vals = {"Team name:": "  [ your team name ]",
                "Team leader name:": "  [ your name ]",
                "Problem Statement:": "  Open Track — AI copilot for channel-sourced retail lending "
                "(conversational AI, product advisory, financial-health scoring, default prediction)"}
        for p in paras:
            label = p.text.strip()
            if label in vals and p.runs:
                r = p.add_run(); r.text = vals[label]
                r.font.size = p.runs[0].font.size or Pt(16)
                r.font.bold = False
                r.font.color.rgb = GREEN

# ---------------------------------------------------------------- Slide 2 — Brief
body(slides[1], [
    {"t": "Prospect Assist AI — a channel-aware loan-origination & partner-relationship intelligence copilot for IDBI's relationship managers.", "sz": 15, "bold": True, "color": DARK, "space": 8},
    {"t": "Indian retail lending is sourced mostly through DSAs, dealers & connectors — and runs on TAT (turnaround time) and trust. Prospect Assist AI sits on top of the existing LOS / BRE / LMS and works all four sides at once:", "sz": 13, "space": 8},
    {"t": "Customer — only suitable, clearly-explained, instant offers", "bullet": True, "sz": 13},
    {"t": "RM / Bank — a queue ranked by risk-adjusted profit, not guesswork", "bullet": True, "sz": 13},
    {"t": "Channel partner (DSA) — instant decisions, transparent payouts, loyalty", "bullet": True, "sz": 13},
    {"t": "Risk / Regulator — explainable, fair, adverse-selection-aware lending", "bullet": True, "sz": 13, "space": 8},
    {"t": "One line:  Lend faster, safer, and win partner loyalty.", "sz": 14, "bold": True, "color": GREEN},
])

# ---------------------------------------------------------------- Slide 3 — Opportunities
body(slides[2], [
    {"t": "How it's different from existing ideas", "sz": 13, "bold": True, "color": GREEN, "space": 4},
    {"t": "Channel-first, not customer-only: models the DSA/dealer relationship — adverse-selection risk, TAT, tiering & churn — the part most tools ignore.", "bullet": True, "sz": 12},
    {"t": "Bank-grade economics: ranks by risk-adjusted value = P(convert) × (net interest income − expected credit loss), with risk-based pricing — not a flat lead score.", "bullet": True, "sz": 12},
    {"t": "Explainable by design: per-decision reason codes + Reg-B / RBI adverse-action codes; fair-lending feature exclusions.", "bullet": True, "sz": 12},
    {"t": "Integrates, not replaces: an intelligence layer on top of LOS / BRE / LMS.", "bullet": True, "sz": 12, "space": 8},
    {"t": "How it solves the problem", "sz": 13, "bold": True, "color": GREEN, "space": 4},
    {"t": "Right lead → right product → right price, instantly, with a professional offer.", "bullet": True, "sz": 12},
    {"t": "Flags risky sourcing before disbursal → fewer NPAs.", "bullet": True, "sz": 12},
    {"t": "Transparent, fast, tiered payouts → partner loyalty → more & better volume (the flywheel).", "bullet": True, "sz": 12},
], top=2.05, height=3.3)

# ---------------------------------------------------------------- Slide 4 — Features (2 columns)
body(slides[3], [
    {"t": "Customer & RM", "sz": 13, "bold": True, "color": GREEN, "space": 4},
    {"t": "ML conversion-propensity queue (risk-adjusted)", "bullet": True, "sz": 12},
    {"t": "Explainable financial-health scoring (0–100)", "bullet": True, "sz": 12},
    {"t": "Deterministic eligibility, rate & EMI engine", "bullet": True, "sz": 12},
    {"t": "Suitability-first next-best-product advisory", "bullet": True, "sz": 12},
    {"t": "Editable offer + risk-based pricing within band", "bullet": True, "sz": 12},
    {"t": "Premium branded PDF + WhatsApp / Gmail send", "bullet": True, "sz": 12},
    {"t": "Per-decision reason codes on every score", "bullet": True, "sz": 12},
], top=1.62, left=0.4, width=4.55, height=3.7)
body(slides[3], [
    {"t": "Channel & Partner", "sz": 13, "bold": True, "color": GREEN, "space": 4},
    {"t": "Partner/lead default-risk (adverse-selection detector)", "bullet": True, "sz": 12},
    {"t": "Channel-mix ROI + book concentration (HHI)", "bullet": True, "sz": 12},
    {"t": "Commission + clawback payout engine", "bullet": True, "sz": 12},
    {"t": "Duplicate / fraud lead detection", "bullet": True, "sz": 12},
    {"t": "Instant in-principle decision (<50 ms) + SLA/TAT", "bullet": True, "sz": 12},
    {"t": "Partner tiering + churn early-warning", "bullet": True, "sz": 12},
    {"t": "Agentic AI assistant (natural language → engine)", "bullet": True, "sz": 12},
], top=1.62, left=5.05, width=4.6, height=3.7)

# ---------------------------------------------------------------- Slide 5 — Process flow
s = slides[4]
stages = ["DSA submits\nlead", "Instant\nindicative decision", "ML-ranked\nqueue (RM)",
          "Recommend +\neditable offer", "Risk-based\nprice + PDF", "Disburse +\nlog outcome"]
n = len(stages); bw, gap, bh = 1.28, 0.22, 1.0
x0 = 0.35; y = 2.15
for i, txt in enumerate(stages):
    x = x0 + i * (bw + gap)
    fill = GREEN if i in (0, 5) else DARK if i in (1,) else RGBColor(0x11, 0x6A, 0x5B)
    box(s, x, y, bw, bh, txt, fill=fill, sz=10)
    if i < n - 1:
        arrow(s, x + bw - 0.02, y + bh / 2 - 0.11, w=gap + 0.06)
# feedback loop
fb = box(s, x0 + 1.0, y + bh + 0.55, (bw + gap) * 4, 0.5,
         "↑  Outcomes (won / lost / default) retrain the ML models — the compounding data moat",
         fill=LIGHT, font=DARK, sz=11)
body(s, [{"t": "Numbers boundary: the deterministic engine owns every rupee (eligibility, rate, EMI, ECL); ML owns probabilities; the LLM only phrases. RM stays in control — edits re-validate through the engine.",
          "sz": 11, "color": GREY}], top=4.75, height=0.7)

# ---------------------------------------------------------------- Slide 6 — Mockups
s = slides[5]
picture(s, SHOTS / "dashboard.png", 0.35, 1.75, 4.55, 3.15)
caption(s, 0.35, 1.5, 4.55, "RM dashboard — risk-adjusted, ML-ranked queue")
picture(s, SHOTS / "prospect.png", 5.1, 1.75, 4.55, 3.15)
caption(s, 5.1, 1.5, 4.55, "Prospect profile — reason codes & recommendation")

# ---------------------------------------------------------------- Slide 7 — Architecture
s = slides[4 + 2]  # slide 7
def down(sl, cx, ty):
    a = sl.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(cx), Inches(ty), Inches(0.22), Inches(0.18))
    a.fill.solid(); a.fill.fore_color.rgb = GREY; a.line.fill.background(); a.shadow.inherit = False
box(s, 1.6, 1.5, 6.8, 0.48, "Presentation  ·  FastAPI + Jinja2 + Tailwind   (RM dashboard · Partner portal · AI assistant)", fill=DARK, sz=11)
down(s, 4.9, 2.0)
box(s, 0.9, 2.28, 3.9, 0.48, "Layer 1 · Directives (SOPs in Markdown)", fill=RGBColor(0x11, 0x6A, 0x5B), sz=11)
box(s, 5.2, 2.28, 3.9, 0.48, "Layer 2 · AI Orchestration — NVIDIA NIM LLM (de-identified, phrasing only)", fill=RGBColor(0x11, 0x6A, 0x5B), sz=10)
down(s, 4.9, 2.78)
box(s, 0.9, 3.06, 8.2, 0.5, "Layer 3 · Deterministic Engine + ML  —  owns every number", fill=GREEN, sz=12)
subs = ["Eligibility · Rate · EMI", "Economics (ECL / RAROC) + Risk pricing", "ML: Propensity + Default-risk",
        "Explainability (reason codes)", "Commission + Clawback", "PDF (WeasyPrint)"]
sw = 2.63; sg = 0.16; sx = 0.9; sy = 3.64
for i, t in enumerate(subs):
    col = i % 3; row = i // 3
    box(s, sx + col * (sw + sg), sy + row * 0.48, sw, 0.42, t, fill=LIGHT, font=DARK, sz=9.5)
box(s, 0.9, 4.62, 8.2, 0.4, "Data — products · partners · prospects · history · trained model artifacts (.pkl)", fill=SLATE, sz=10)
body(s, [{"t": "Integration points (PoC): CIBIL bureau · KYC / e-consent (DPDP) · LOS / BRE / LMS · NVIDIA AI Enterprise / on-prem inference",
          "sz": 9.5, "color": GREY, "bold": True}], top=5.08, left=0.9, width=8.2, height=0.34)

# ---------------------------------------------------------------- Slide 8 — Technologies
body(slides[7], [
    {"t": "Backend:  Python 3.14 · FastAPI · Uvicorn (single service, no build step)", "bullet": True, "sz": 13},
    {"t": "Frontend:  Server-rendered Jinja2 + Tailwind CSS + vanilla JS", "bullet": True, "sz": 13},
    {"t": "Machine learning:  scikit-learn (GradientBoosting / Logistic auto-select), pandas, numpy, joblib", "bullet": True, "sz": 13},
    {"t": "Explainability:  model-agnostic occlusion attribution + reason codes (no heavy dependency)", "bullet": True, "sz": 13},
    {"t": "Documents:  WeasyPrint (branded PDF offers)", "bullet": True, "sz": 13},
    {"t": "LLM:  NVIDIA NIM — OpenAI-compatible, free tier · swappable to NVIDIA AI Enterprise / on-prem", "bullet": True, "sz": 13},
    {"t": "Quality:  pytest (44 automated tests) · Playwright (prototype capture)", "bullet": True, "sz": 13},
    {"t": "Deployment:  Docker → Render / Railway / Google Cloud Run", "bullet": True, "sz": 13},
])

# ---------------------------------------------------------------- Slide 9 — Cost
body(slides[8], [
    {"t": "Prototype (today):  ≈ ₹0", "sz": 14, "bold": True, "color": GREEN, "space": 4},
    {"t": "Open-source stack · NVIDIA NIM free tier · local / free-tier hosting. No licence cost.", "bullet": True, "sz": 12, "space": 10},
    {"t": "Production PoC (indicative, annual — assumptions stated):", "sz": 14, "bold": True, "color": DARK, "space": 4},
    {"t": "LLM / GPU inference (NVIDIA AI Enterprise or managed) — usage-based", "bullet": True, "sz": 12},
    {"t": "Cloud hosting + database + storage — modest (containerised single service)", "bullet": True, "sz": 12},
    {"t": "Integration effort — LOS / BRE / KYC / CIBIL connectors (one-time)", "bullet": True, "sz": 12},
    {"t": "Model-ops — monitoring, retraining, governance", "bullet": True, "sz": 12, "space": 10},
    {"t": "ROI: cost saved (NPA reduction + payout-leakage → 0 + RM selling hours) ≫ cost to run.", "sz": 13, "bold": True, "color": GREEN},
])

# ---------------------------------------------------------------- Slide 10 — Snapshots (2x2)
s = slides[9]
grid = [("offer.png", "Editable offer — live EMI & risk-based pricing"),
        ("channel.png", "Channel intelligence — adverse selection, ROI, HHI"),
        ("submit.png", "Instant decision + adverse-action reason codes"),
        ("deck.png", "Built-in pitch deck (live numbers)")]
cw, ch = 4.5, 1.62
xs = [0.35, 5.1]; ys = [1.85, 3.75]
for i, (img, cap) in enumerate(grid):
    x = xs[i % 2]; yy = ys[i // 2]
    caption(s, x, yy - 0.26, cw, cap)
    picture(s, SHOTS / img, x, yy, cw, ch)

# ---------------------------------------------------------------- Slide 11 — Performance
body(slides[10], [
    {"t": "Model performance (hold-out, synthetic data — indicative)", "sz": 13, "bold": True, "color": GREEN, "space": 4},
    {"t": "Conversion propensity:  AUC 0.69 · Gini 39", "bullet": True, "sz": 12},
    {"t": "Partner / lead default-risk:  AUC 0.81 · Gini 62 · partner-history feature share 0.22 (no target leakage) · Bayesian shrinkage for fairness", "bullet": True, "sz": 12, "space": 10},
    {"t": "System performance", "sz": 13, "bold": True, "color": GREEN, "space": 4},
    {"t": "Instant indicative decision latency:  < 50 ms", "bullet": True, "sz": 12},
    {"t": "LLM interactive latency:  ~1–2 s, 9 s hard timeout → deterministic fallback (never hangs)", "bullet": True, "sz": 12, "space": 10},
    {"t": "Business impact on the synthetic book", "sz": 13, "bold": True, "color": GREEN, "space": 4},
    {"t": "₹16.4 Cr pipeline → ₹0.68 Cr risk-adjusted value · 9 value-destructive leads down-ranked · 3 adverse-selection partners flagged", "bullet": True, "sz": 12},
    {"t": "Quality:  44 automated tests passing (engine · ML integrity · API · explainability)", "bullet": True, "sz": 12},
    {"t": "Metrics are on synthetic data — models retrain on IDBI's real conversion + NPA + TAT history in the PoC.", "sz": 10, "color": GREY, "space": 0},
], top=1.55, height=3.8)

# ---------------------------------------------------------------- Slide 12 — Future
body(slides[11], [
    {"t": "Real IDBI sandbox APIs · CIBIL bureau + KYC integration · e-consent (DPDP Act)", "bullet": True, "sz": 13},
    {"t": "Retrain models on real conversion / NPA / TAT history · SHAP + PSI drift monitoring", "bullet": True, "sz": 13},
    {"t": "Full partner-facing mobile portal + WhatsApp bot (OTP-gated secure offer delivery)", "bullet": True, "sz": 13},
    {"t": "Straight-through LOS / BRE / LMS integration", "bullet": True, "sz": 13},
    {"t": "Auth / RBAC, full audit trail, data residency", "bullet": True, "sz": 13},
    {"t": "Extend to collections & Early-Warning Signals (EWS) on the channel book", "bullet": True, "sz": 13},
    {"t": "Production inference on NVIDIA AI Enterprise / IDBI-approved on-prem / VPC", "bullet": True, "sz": 13},
])

# ---------------------------------------------------------------- Slide 13 — Links
body(slides[12], [
    {"t": "GitHub Public Repository", "sz": 13, "bold": True, "color": GREEN, "space": 2},
    {"t": "https://github.com/Shubham-33/Hack2Skill-IDBI-Hackathone", "sz": 13, "color": SLATE, "space": 12},
    {"t": "Final Product Link (live prototype)", "sz": 13, "bold": True, "color": GREEN, "space": 2},
    {"t": "https://prospect-assist-ai-2guf.onrender.com", "sz": 13, "color": SLATE, "space": 12},
    {"t": "Demo Video Link (3 minutes)", "sz": 13, "bold": True, "color": GREEN, "space": 2},
    {"t": "[ paste your unlisted YouTube / Drive link — 3-min script in DEMO_RUNBOOK.md ]", "sz": 12, "color": GREY},
], top=2.35, height=3.0)

# ---------------------------------------------------------------- Slide 15 — Closing
s = slides[14]
phs = [sh for sh in s.shapes if sh.is_placeholder]
if phs:
    phs[0].text_frame.text = "Prospect Assist AI"
    for p in phs[0].text_frame.paragraphs:
        for r in p.runs:
            r.font.color.rgb = GREEN; r.font.bold = True
    if len(phs) > 1:
        phs[1].text_frame.text = "Lend faster, safer, and win partner loyalty.  ·  IDBI Innovate 2026"

prs.save(str(OUT))
print("saved:", OUT.name, "|", len(slides), "slides")
