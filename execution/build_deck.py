"""Fill the IDBI Innovate 2026 prototype submission deck — MINIMAL style.

Design language: generous whitespace, sharp typographic hierarchy, thin hairline
structure, a single restrained accent (IDBI green) used sparingly. No shadows, no
filled cards, no decoration — definition comes from alignment and space.
"""
from __future__ import annotations
import struct
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "Prototype Submission Deck _ IDBI Innovate.pptx"
OUT = ROOT / "Prospect Assist AI - IDBI Innovate Submission Deck.pptx"
SHOTS = ROOT / ".tmp" / "shots"

INK = RGBColor(0x1B, 0x24, 0x21)      # near-black text
GREEN = RGBColor(0x0A, 0x7D, 0x6B)    # the one accent
DEEP = RGBColor(0x0A, 0x3D, 0x33)
GREY = RGBColor(0x84, 0x8C, 0x93)     # secondary / labels
HAIR = RGBColor(0xDA, 0xDF, 0xE2)     # hairline rules
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

prs = Presentation(str(TEMPLATE))
slides = list(prs.slides)


def png_size(p):
    d = open(p, "rb").read(26); return struct.unpack(">II", d[16:24])


def text(slide, l, t, w, h, runs, align=PP_ALIGN.LEFT, anchor=None, line_spacing=None):
    """runs: list of paragraphs; each paragraph is a list of (txt, opts) run tuples,
    OR a single dict for a one-run paragraph."""
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    if anchor: tf.vertical_anchor = anchor
    for i, para in enumerate(runs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if line_spacing: p.line_spacing = line_spacing
        p.space_after = Pt(0); p.space_before = Pt(0)
        items = para if isinstance(para, list) else [para]
        for d in items:
            r = p.add_run(); r.text = d["t"]
            r.font.size = Pt(d.get("sz", 12)); r.font.bold = d.get("bold", False)
            r.font.italic = d.get("italic", False)
            r.font.color.rgb = d.get("color", INK); r.font.name = "Calibri"
    return tb


def rule_h(slide, l, t, w, color=HAIR, thick=0.014):
    r = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(thick))
    r.fill.solid(); r.fill.fore_color.rgb = color; r.line.fill.background(); r.shadow.inherit = False


def rule_v(slide, l, t, h, color=HAIR, thick=0.014):
    r = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(thick), Inches(h))
    r.fill.solid(); r.fill.fore_color.rgb = color; r.line.fill.background(); r.shadow.inherit = False


def kicker(slide, txt, t=1.32):
    text(slide, 0.5, t, 6.0, 0.26, [{"t": txt.upper(), "sz": 10.5, "bold": True, "color": GREEN}])
    rule_h(slide, 0.52, t + 0.28, 0.42, GREEN, thick=0.028)


def counter(slide, n, total=12, t=1.32):
    """Editorial slide counter, e.g. 03 / 12 — top-right, like the reference."""
    text(slide, 8.4, t, 1.18, 0.26,
         [[{"t": f"{n:02d}", "sz": 10.5, "bold": True, "color": GREEN},
           {"t": f" / {total}", "sz": 10.5, "bold": True, "color": GREY}]], align=PP_ALIGN.RIGHT)


def label(slide, l, t, w, txt, color=GREEN, sz=11):
    text(slide, l, t, w, 0.28, [{"t": txt.upper(), "sz": sz, "bold": True, "color": color}])


def item(slide, l, t, w, body, lead=None, sz=12):
    """Editorial list row: short green tick + optional bold green lead + ink text."""
    rule_h(slide, l, t + 0.11, 0.15, GREEN, thick=0.032)
    para = []
    if lead: para.append({"t": lead + "  ", "sz": sz, "bold": True, "color": DEEP})
    para.append({"t": body, "sz": sz, "color": INK})
    text(slide, l + 0.28, t - 0.03, w - 0.28, 0.6, [para], line_spacing=1.05)


def stat(slide, l, t, w, number, lab, nsz=30, ncolor=INK, align=PP_ALIGN.LEFT):
    text(slide, l, t, w, 0.55, [{"t": number, "sz": nsz, "bold": True, "color": ncolor}], align=align)
    text(slide, l, t + nsz / 58.0 + 0.08, w, 0.34,
         [{"t": lab.upper(), "sz": 9.5, "bold": True, "color": GREY}], align=align)


def obox(slide, l, t, w, h, txt, border=HAIR, tcolor=INK, sz=10.5, bold=False, fill=WHITE):
    sp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
    if fill is None: sp.fill.background()
    else: sp.fill.solid(); sp.fill.fore_color.rgb = fill
    sp.line.color.rgb = border; sp.line.width = Pt(1.0); sp.shadow.inherit = False
    tf = sp.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.06); tf.margin_top = tf.margin_bottom = Inches(0.02)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = txt; r.font.size = Pt(sz); r.font.bold = bold
    r.font.color.rgb = tcolor; r.font.name = "Calibri"
    return sp


def connect_down(slide, cx, t, h=0.2):
    rule_v(slide, cx, t, h, GREEN, thick=0.02)


def picture(slide, path, l, t, max_w, max_h):
    w, h = png_size(path); ar = w / h
    tw, th = max_w, max_w / ar
    if th > max_h: th, tw = max_h, max_h * ar
    pic = slide.shapes.add_picture(str(path), Inches(l + (max_w - tw) / 2), Inches(t), Inches(tw), Inches(th))
    pic.line.color.rgb = HAIR; pic.line.width = Pt(0.75); pic.shadow.inherit = False
    return pic


# ================================================================ Slide 1 — Team
s = slides[0]
for shp in s.shapes:
    if shp.has_text_frame and shp.text_frame.text.strip().startswith("Team Details"):
        vals = {"Team name:": "  Black Bulls",
                "Team leader name:": "  Shubham",
                "Problem Statement:": "  Open Track — AI copilot for channel-sourced retail lending "
                "(conversational AI · product advisory · financial-health scoring · default prediction)"}
        for p in shp.text_frame.paragraphs:
            if p.text.strip() in vals and p.runs:
                r = p.add_run(); r.text = vals[p.text.strip()]
                r.font.size = p.runs[0].font.size or Pt(16); r.font.bold = False; r.font.color.rgb = GREEN

# ================================================================ Slide 2 — Brief
s = slides[1]; kicker(s, "The Idea"); counter(s, 1)
text(s, 0.5, 1.78, 9.0, 0.9,
     [[{"t": "A channel-aware loan-origination & partner-relationship copilot, ", "sz": 17, "color": INK},
       {"t": "built on top of IDBI's existing LOS / BRE / LMS.", "sz": 17, "color": GREEN}]],
     line_spacing=1.12)
rule_h(s, 0.5, 2.82, 9.0)
text(s, 0.5, 2.95, 9.0, 0.28, [{"t": "It works all four sides at once", "sz": 11, "color": GREY}])
quad = [("Customer", "Only suitable, clearly-explained, instant offers."),
        ("RM / Bank", "A queue ranked by risk-adjusted profit, with reasons."),
        ("Channel partner (DSA)", "Instant decisions, transparent payouts, loyalty."),
        ("Risk / Regulator", "Explainable, fair, adverse-selection-aware lending.")]
xs, ys = [0.5, 5.15], [3.4, 4.35]
rule_v(s, 5.0, 3.35, 1.65)
rule_h(s, 0.5, 3.9, 9.0)
for i, (lab, body) in enumerate(quad):
    x, y = xs[i % 2], ys[i // 2]
    label(s, x, y, 4.3, lab)
    text(s, x, y + 0.3, 4.3, 0.5, [{"t": body, "sz": 11.5, "color": INK}], line_spacing=1.05)
text(s, 0.5, 5.18, 9.0, 0.3, [{"t": "Lend faster, safer, and win partner loyalty.", "sz": 12, "bold": True, "color": GREEN}])

# ================================================================ Slide 3 — Opportunities
s = slides[2]; counter(s, 2)
rule_v(s, 5.0, 2.2, 3.05)
label(s, 0.5, 2.12, 4.3, "How it's different")
for i, (lead, body) in enumerate([
        ("Channel-first.", "Models the DSA relationship — adverse-selection, TAT, tiering, churn."),
        ("Bank-grade economics.", "Ranks by P(convert) × (net interest income − expected credit loss)."),
        ("Explainable.", "Per-decision reason codes + Reg-B / RBI adverse-action codes."),
        ("Integrates, not replaces.", "An intelligence layer on top of LOS / BRE / LMS.")]):
    item(s, 0.5, 2.6 + i * 0.66, 4.3, body, lead=lead, sz=11.5)
label(s, 5.25, 2.12, 4.3, "How it solves the problem")
for i, (lead, body) in enumerate([
        ("Speed + fit.", "Right lead → right product → right price, instantly, with a professional offer."),
        ("Lower NPAs.", "Flags risky sourcing before disbursal."),
        ("Partner loyalty.", "Transparent, fast, tiered payouts → more & better volume."),
        ("The flywheel.", "Win the partner → volume → data → sharper models.")]):
    item(s, 5.25, 2.6 + i * 0.66, 4.3, body, lead=lead, sz=11.5)

# ================================================================ Slide 4 — Features
s = slides[3]; kicker(s, "Features"); counter(s, 3)
rule_v(s, 5.0, 1.85, 3.4)
label(s, 0.5, 1.85, 4.3, "Customer & RM")
for i, t in enumerate([
        "ML conversion-propensity queue (risk-adjusted)",
        "Explainable financial-health score (0–100)",
        "Deterministic eligibility, rate & EMI engine",
        "Suitability-first next-best-product advisory",
        "Editable offer + risk-based pricing in-band",
        "Premium branded PDF + WhatsApp / Gmail send",
        "Per-decision reason codes on every score"]):
    item(s, 0.5, 2.35 + i * 0.42, 4.4, t, sz=11)
label(s, 5.25, 1.85, 4.3, "Channel & Partner")
for i, t in enumerate([
        "Partner / lead default-risk (adverse-selection)",
        "Channel-mix ROI + book concentration (HHI)",
        "Commission + clawback payout engine",
        "Duplicate / fraud lead detection",
        "Instant decision (<50 ms) + SLA / TAT clock",
        "Partner tiering + churn early-warning",
        "Agentic AI assistant (natural language)"]):
    item(s, 5.25, 2.35 + i * 0.42, 4.4, t, sz=11)

# ================================================================ Slide 5 — Process flow
s = slides[4]; kicker(s, "Process Flow"); counter(s, 4)
stages = ["Lead\nsubmitted", "Instant\ndecision", "Ranked\nqueue", "Offer +\nprice", "PDF +\nsend", "Outcome\nlogged"]
n = len(stages); iw, aw, x0, y = 1.28, 0.22, 0.5, 2.75
for i, txt in enumerate(stages):
    x = x0 + i * (iw + aw)
    text(s, x, y, iw, 0.5, [{"t": f"0{i+1}", "sz": 24, "bold": True, "color": GREEN}], align=PP_ALIGN.CENTER)
    text(s, x, y + 0.6, iw, 0.6, [{"t": txt, "sz": 11.5, "color": INK}], align=PP_ALIGN.CENTER, line_spacing=1.0)
    if i < n - 1:
        text(s, x + iw, y + 0.08, aw, 0.4, [{"t": "→", "sz": 17, "bold": True, "color": GREEN}], align=PP_ALIGN.CENTER)
rule_h(s, 0.5, 4.35, 9.0)
text(s, 0.5, 4.5, 9.1, 0.3,
     [[{"t": "↻  ", "sz": 12, "bold": True, "color": GREEN},
       {"t": "Outcomes (won / lost / default) retrain the ML models — the compounding data moat.", "sz": 11.5, "color": INK}]])
text(s, 0.5, 4.9, 9.1, 0.5,
     [{"t": "Numbers boundary — the deterministic engine owns every rupee; ML owns probabilities; the LLM only phrases. RM edits re-validate through the engine.", "sz": 10.5, "color": GREY}], line_spacing=1.1)

# ================================================================ Slide 6 — Mockups
s = slides[5]; kicker(s, "Interface"); counter(s, 5)
label(s, 0.5, 1.82, 4.55, "RM dashboard — risk-adjusted queue", GREEN, sz=10.5)
picture(s, SHOTS / "dashboard.png", 0.5, 2.12, 4.4, 3.0)
label(s, 5.15, 1.82, 4.55, "Prospect profile — reason codes", GREEN, sz=10.5)
picture(s, SHOTS / "prospect.png", 5.15, 2.12, 4.4, 3.0)

# ================================================================ Slide 7 — Architecture
s = slides[6]; kicker(s, "Architecture"); counter(s, 6)
obox(s, 1.5, 1.85, 7.0, 0.46, "Presentation — FastAPI + Jinja2 + Tailwind  (RM dashboard · Partner portal · AI assistant)", border=GREEN, tcolor=DEEP, sz=10.5)
connect_down(s, 5.0, 2.33)
obox(s, 0.9, 2.58, 3.95, 0.46, "Layer 1 — Directives (SOPs in Markdown)", border=GREEN, tcolor=DEEP, sz=10.5)
obox(s, 5.15, 2.58, 3.95, 0.46, "Layer 2 — AI Orchestration (NVIDIA NIM LLM, de-identified)", border=GREEN, tcolor=DEEP, sz=10)
connect_down(s, 5.0, 3.06)
obox(s, 0.9, 3.3, 8.2, 0.46, "Layer 3 — Deterministic Engine + ML   ·   owns every number", border=GREEN, tcolor=WHITE, sz=11.5, fill=GREEN)
subs = ["Eligibility · Rate · EMI", "Economics (ECL / RAROC) + pricing", "ML: Propensity + Default-risk",
        "Explainability (reason codes)", "Commission + Clawback", "PDF (WeasyPrint)"]
sw, sg, sx, sy = 2.63, 0.16, 0.9, 3.86
for i, t in enumerate(subs):
    obox(s, sx + (i % 3) * (sw + sg), sy + (i // 3) * 0.44, sw, 0.38, t, border=HAIR, tcolor=INK, sz=9.5)
obox(s, 0.9, 4.76, 8.2, 0.38, "Data — products · partners · prospects · history · model artifacts (.pkl)", border=HAIR, tcolor=GREY, sz=9.5)
text(s, 0.9, 5.2, 8.2, 0.3, [{"t": "Integration (PoC): CIBIL bureau · KYC / e-consent (DPDP) · LOS / BRE / LMS · NVIDIA AI Enterprise", "sz": 9.5, "color": GREY}])

# ================================================================ Slide 8 — Technologies
s = slides[7]; kicker(s, "Technology"); counter(s, 7)
groups = [("Backend & Web", "Python 3.14 · FastAPI · Uvicorn · Jinja2 · Tailwind CSS · vanilla JS"),
          ("Machine learning & AI", "scikit-learn · NumPy / SciPy · joblib · occlusion XAI · NVIDIA NIM LLM"),
          ("Documents & PDF", "WeasyPrint · pango / cairo"),
          ("Quality & Deployment", "pytest (44 tests) · Playwright · Docker · Render / Railway / Cloud Run")]
y = 1.9
for name, items in groups:
    label(s, 0.5, y, 9.0, name)
    text(s, 0.5, y + 0.32, 9.0, 0.4, [{"t": items, "sz": 13, "color": INK}])
    rule_h(s, 0.5, y + 0.78, 9.0)
    y += 0.92

# ================================================================ Slide 9 — Cost
s = slides[8]; kicker(s, "Investment"); counter(s, 8)
rule_v(s, 5.0, 1.95, 2.75)
label(s, 0.5, 1.95, 4.3, "Prototype — today")
text(s, 0.5, 2.35, 4.3, 0.9, [{"t": "≈ ₹0", "sz": 46, "bold": True, "color": GREEN}])
text(s, 0.5, 3.35, 4.3, 1.0, [
    {"t": "Open-source stack", "sz": 11.5, "color": INK},
    {"t": "NVIDIA NIM free tier", "sz": 11.5, "color": INK},
    {"t": "Free-tier hosting · no licence cost", "sz": 11.5, "color": INK}], line_spacing=1.3)
label(s, 5.25, 1.95, 4.3, "Production PoC — indicative (annual)")
for i, t in enumerate(["LLM / GPU inference — usage-based",
                       "Cloud hosting + DB + storage — modest",
                       "Integration — LOS / BRE / KYC / CIBIL (one-time)",
                       "Model-ops — monitoring, retraining, governance"]):
    item(s, 5.25, 2.42 + i * 0.5, 4.3, t, sz=11.5)
rule_h(s, 0.5, 4.92, 9.0)
text(s, 0.5, 5.05, 9.0, 0.3,
     [[{"t": "ROI  ", "sz": 12, "bold": True, "color": GREEN},
       {"t": "— cost saved (NPA reduction + payout-leakage → 0 + RM selling hours)  ≫  cost to run.", "sz": 12, "color": INK}]])

# ================================================================ Slide 10 — Snapshots
s = slides[9]; kicker(s, "Prototype"); counter(s, 9)
grid = [("offer.png", "Editable offer — live EMI & risk-based pricing"),
        ("channel.png", "Channel intelligence — adverse selection, ROI, HHI"),
        ("submit.png", "Instant decision + adverse-action reason codes"),
        ("deck.png", "Built-in pitch deck (live numbers)")]
xs, ys = [0.5, 5.15], [2.02, 3.82]
for i, (img, cap) in enumerate(grid):
    x, yy = xs[i % 2], ys[i // 2]
    label(s, x, yy - 0.24, 4.5, cap, GREEN, sz=9.5)
    picture(s, SHOTS / img, x, yy, 4.4, 1.55)

# ================================================================ Slide 11 — Performance
s = slides[10]; kicker(s, "Benchmarks"); counter(s, 10)
label(s, 0.5, 1.8, 9.0, "Model performance — hold-out, synthetic (indicative)")
rule_v(s, 5.0, 2.12, 0.82)
stat(s, 0.5, 2.12, 4.3, "0.69 / 39", "Conversion propensity — AUC / Gini", nsz=26, ncolor=GREEN)
stat(s, 5.25, 2.12, 4.3, "0.81 / 62", "Partner default-risk — AUC / Gini", nsz=26, ncolor=GREEN)
rule_h(s, 0.5, 3.06, 9.0)
label(s, 0.5, 3.17, 9.0, "Speed & integrity")
rule_v(s, 3.55, 3.47, 0.66); rule_v(s, 6.6, 3.47, 0.66)
stat(s, 0.5, 3.47, 2.9, "< 50 ms", "Instant decision latency", nsz=22)
stat(s, 3.75, 3.47, 2.7, "~1–2 s", "LLM reply · 9 s timeout", nsz=22)
stat(s, 6.8, 3.47, 2.8, "0.22", "Feature share — no leakage", nsz=22)
rule_h(s, 0.5, 4.28, 9.0)
label(s, 0.5, 4.39, 9.0, "Business impact (synthetic book)")
rule_v(s, 3.55, 4.68, 0.6); rule_v(s, 6.6, 4.68, 0.6)
stat(s, 0.5, 4.66, 2.9, "₹16.4 Cr", "pipeline value", nsz=20)
stat(s, 3.75, 4.66, 2.7, "₹0.68 Cr", "risk-adjusted value", nsz=20)
stat(s, 6.8, 4.66, 2.8, "44 / 44", "automated tests passing", nsz=20)

# ================================================================ Slide 12 — Future
s = slides[11]; kicker(s, "Roadmap"); counter(s, 11)
phases = [("Integrate", ["IDBI sandbox APIs", "CIBIL bureau + KYC", "e-consent (DPDP Act)", "LOS / BRE / LMS hooks"]),
          ("Harden", ["Retrain on real conv / NPA / TAT", "SHAP + PSI drift monitoring", "Auth / RBAC + audit trail", "Data residency"]),
          ("Scale", ["Partner mobile portal + WhatsApp", "OTP-gated secure delivery", "Collections & Early-Warning", "NVIDIA AI Enterprise / on-prem"])]
cw = 3.0
for i, (name, items) in enumerate(phases):
    l = 0.5 + i * (cw + 0.3)
    if i: rule_v(s, l - 0.16, 1.95, 3.2)
    text(s, l, 1.9, cw, 0.6, [{"t": f"0{i+1}", "sz": 26, "bold": True, "color": GREEN}])
    text(s, l + 0.75, 2.02, cw, 0.4, [{"t": name, "sz": 15, "bold": True, "color": DEEP}])
    rule_h(s, l, 2.6, cw - 0.2)
    for j, t in enumerate(items):
        item(s, l, 2.78 + j * 0.56, cw - 0.15, t, sz=10.8)

# ================================================================ Slide 13 — Links
s = slides[12]; counter(s, 12)
rows = [("GitHub Public Repository", "https://github.com/Shubham-33/Hack2Skill-IDBI-Hackathone"),
        ("Final Product Link (live prototype)", "https://prospect-assist-ai-2guf.onrender.com"),
        ("Demo Video Link (3 minutes)", "[ paste your unlisted YouTube / Drive link ]")]
y = 2.25
for lab, url in rows:
    rule_h(s, 0.5, y - 0.12, 9.0, GREEN, thick=0.024)
    label(s, 0.5, y, 9.0, lab, GREEN, sz=11)
    text(s, 0.5, y + 0.32, 9.0, 0.34, [{"t": url, "sz": 13, "color": INK}])
    y += 0.95

# ================================================================ Slide 15 — Closing
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
