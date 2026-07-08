"""Fill the IDBI Innovate 2026 prototype submission deck — infographic style.

Reads the provided template, fills every content slide with Prospect Assist AI
content using a card / badge / stat / chip / chart visual system, builds native
flow + architecture diagrams, embeds real prototype screenshots, and writes a new
.pptx (template left untouched).
"""
from __future__ import annotations
import struct
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "Prototype Submission Deck _ IDBI Innovate.pptx"
OUT = ROOT / "Prospect Assist AI - IDBI Innovate Submission Deck.pptx"
SHOTS = ROOT / ".tmp" / "shots"

# palette
GREEN = RGBColor(0x0A, 0x7D, 0x6B); DARK = RGBColor(0x0A, 0x3D, 0x33)
SLATE = RGBColor(0x33, 0x41, 0x55); GREY = RGBColor(0x64, 0x74, 0x8B)
AMBER = RGBColor(0xE0, 0x8A, 0x0B); BLUE = RGBColor(0x25, 0x63, 0xEB)
VIOLET = RGBColor(0x7C, 0x3A, 0xED); ROSE = RGBColor(0xE1, 0x1D, 0x48)
TEAL = RGBColor(0x0E, 0x74, 0x90); WHITE = RGBColor(0xFF, 0xFF, 0xFF)
# light tints
T_GREEN = RGBColor(0xE7, 0xF5, 0xF1); T_BLUE = RGBColor(0xEA, 0xF1, 0xFE)
T_AMBER = RGBColor(0xFE, 0xF3, 0xE2); T_VIOLET = RGBColor(0xF2, 0xEC, 0xFD)
T_ROSE = RGBColor(0xFD, 0xEC, 0xEF); T_TEAL = RGBColor(0xE6, 0xF3, 0xF7)
T_SLATE = RGBColor(0xF1, 0xF5, 0xF9)

prs = Presentation(str(TEMPLATE))
slides = list(prs.slides)


def png_size(p):
    d = open(p, "rb").read(26); return struct.unpack(">II", d[16:24])


def _txt(tf, lines, anchor=None):
    if anchor: tf.vertical_anchor = anchor
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = ln.get("align", PP_ALIGN.LEFT)
        p.space_after = Pt(ln.get("space", 3)); p.space_before = Pt(0)
        if ln.get("level"): p.level = ln["level"]
        r = p.add_run(); r.text = ln["t"]
        r.font.size = Pt(ln.get("sz", 13)); r.font.bold = ln.get("bold", False)
        r.font.color.rgb = ln.get("color", SLATE); r.font.name = "Calibri"


def textbox(slide, l, t, w, h, lines, anchor=None):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tb.text_frame.word_wrap = True
    _txt(tb.text_frame, lines, anchor)
    return tb


def rect(slide, l, t, w, h, fill, line=None, lw=0.75, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    sp = slide.shapes.add_shape(shape, Inches(l), Inches(t), Inches(w), Inches(h))
    sp.fill.solid(); sp.fill.fore_color.rgb = fill
    if line is None: sp.line.fill.background()
    else: sp.line.color.rgb = line; sp.line.width = Pt(lw)
    sp.shadow.inherit = False
    return sp


def badge(slide, l, t, d, glyph, fill, gcolor=WHITE, sz=13):
    sp = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(l), Inches(t), Inches(d), Inches(d))
    sp.fill.solid(); sp.fill.fore_color.rgb = fill; sp.line.fill.background(); sp.shadow.inherit = False
    tf = sp.text_frame; tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = glyph; r.font.size = Pt(sz); r.font.bold = True
    r.font.color.rgb = gcolor; r.font.name = "Calibri"
    return sp


def card(slide, l, t, w, h, glyph, title, desc, accent, tint):
    rect(slide, l, t, w, h, tint, line=accent, lw=1.0)
    badge(slide, l + 0.16, t + 0.15, 0.42, glyph, accent, sz=15)
    textbox(slide, l + 0.68, t + 0.12, w - 0.8, 0.4, [{"t": title, "sz": 12.5, "bold": True, "color": accent}])
    textbox(slide, l + 0.18, t + 0.62, w - 0.34, h - 0.7, [{"t": desc, "sz": 11, "color": SLATE}])


def icon_row(slide, l, t, w, glyph, text, accent, sz=11.5):
    badge(slide, l, t, 0.3, glyph, accent, sz=11)
    textbox(slide, l + 0.42, t - 0.04, w - 0.42, 0.6, [{"t": text, "sz": sz, "color": SLATE}])


def stat(slide, l, t, w, h, number, label, accent, tint=None):
    rect(slide, l, t, w, h, tint or WHITE, line=accent, lw=1.0)
    textbox(slide, l, t + 0.1, w, h - 0.5,
            [{"t": number, "sz": 26, "bold": True, "color": accent, "align": PP_ALIGN.CENTER}],
            anchor=MSO_ANCHOR.MIDDLE)
    textbox(slide, l, t + h - 0.42, w, 0.36,
            [{"t": label, "sz": 10.5, "color": GREY, "align": PP_ALIGN.CENTER}])


def ribbon(slide, l, t, w, h, text, fill, font=WHITE, sz=13):
    sp = rect(slide, l, t, w, h, fill)
    tf = sp.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = text; r.font.size = Pt(sz); r.font.bold = True
    r.font.color.rgb = font; r.font.name = "Calibri"
    return sp


def chip(slide, l, t, text, fill, font=WHITE, sz=10.5):
    w = 0.092 * len(text) + 0.34
    sp = rect(slide, l, t, w, 0.34, fill)
    tf = sp.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.06); tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = text; r.font.size = Pt(sz); r.font.bold = True
    r.font.color.rgb = font; r.font.name = "Calibri"
    return l + w


def chip_flow(slide, l, t, items, fill, font=WHITE, rightmax=9.65, gap=0.12, line_h=0.44):
    x, y = l, t
    for text in items:
        w = 0.092 * len(text) + 0.34
        if x + w > rightmax:
            x = l; y += line_h
        chip(slide, x, y, text, fill, font)
        x += w + gap
    return y + line_h


def arrow(slide, l, t, w=0.32, color=GREY):
    sp = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(l), Inches(t), Inches(w), Inches(0.22))
    sp.fill.solid(); sp.fill.fore_color.rgb = color; sp.line.fill.background(); sp.shadow.inherit = False


def down(slide, cx, ty):
    a = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(cx), Inches(ty), Inches(0.22), Inches(0.18))
    a.fill.solid(); a.fill.fore_color.rgb = GREY; a.line.fill.background(); a.shadow.inherit = False


def box(slide, l, t, w, h, text, fill=GREEN, font=WHITE, sz=10.5, bold=True):
    sp = rect(slide, l, t, w, h, fill)
    tf = sp.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.05)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = text; r.font.size = Pt(sz); r.font.bold = bold
    r.font.color.rgb = font; r.font.name = "Calibri"
    return sp


def caption(slide, l, t, w, text):
    textbox(slide, l, t, w, 0.3, [{"t": text, "sz": 10, "bold": True, "color": DARK, "align": PP_ALIGN.CENTER}])


def picture(slide, path, l, t, max_w, max_h, border=GREEN):
    w, h = png_size(path); ar = w / h
    tw, th = max_w, max_w / ar
    if th > max_h: th, tw = max_h, max_h * ar
    pic = slide.shapes.add_picture(str(path), Inches(l + (max_w - tw) / 2), Inches(t), Inches(tw), Inches(th))
    pic.line.color.rgb = border; pic.line.width = Pt(1.25)
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
s = slides[1]
ribbon(s, 0.4, 1.5, 9.2, 0.62,
       "A channel-aware loan-origination & partner-relationship copilot — on top of IDBI's LOS / BRE / LMS", DARK, sz=13)
textbox(s, 0.4, 2.2, 9.2, 0.32, [{"t": "Retail lending is sourced through DSAs & dealers and runs on TAT + trust. We work all four sides at once:", "sz": 11.5, "color": GREY}])
cw, ch = 4.5, 1.12
card(s, 0.4, 2.58, cw, ch, "★", "Customer", "Only suitable, clearly-explained, instant offers — no spam, no black box.", BLUE, T_BLUE)
card(s, 5.1, 2.58, cw, ch, "●", "RM / Bank", "A queue ranked by risk-adjusted profit, auto-scoring & recommendations.", GREEN, T_GREEN)
card(s, 0.4, 3.78, cw, ch, "◆", "Channel partner (DSA)", "Instant decisions, transparent payouts, tiering — the loyalty moat.", AMBER, T_AMBER)
card(s, 5.1, 3.78, cw, ch, "▲", "Risk / Regulator", "Explainable, fair, adverse-selection-aware lending with audit trail.", VIOLET, T_VIOLET)
ribbon(s, 0.4, 5.0, 9.2, 0.34, "One line:  Lend faster, safer, and win partner loyalty.", GREEN, sz=13)

# ================================================================ Slide 3 — Opportunities
s = slides[2]
rect(s, 0.4, 2.05, 4.5, 3.25, T_GREEN, line=GREEN, lw=1.0)
textbox(s, 0.62, 2.15, 4.1, 0.4, [{"t": "How it's different", "sz": 13, "bold": True, "color": GREEN}])
diffs = [("◆", "Channel-first, not customer-only — models the DSA relationship: adverse-selection, TAT, tiering, churn."),
         ("₹", "Bank-grade economics — ranks by P(convert) × (net interest income − expected credit loss)."),
         ("▲", "Explainable — per-decision reason codes + Reg-B / RBI adverse-action codes; fair-lending exclusions."),
         ("●", "Integrates, not replaces — an intelligence layer on top of LOS / BRE / LMS.")]
for i, (g, t) in enumerate(diffs):
    icon_row(s, 0.62, 2.62 + i * 0.66, 4.1, g, t, GREEN, sz=10.5)
rect(s, 5.1, 2.05, 4.5, 3.25, T_BLUE, line=BLUE, lw=1.0)
textbox(s, 5.32, 2.15, 4.1, 0.4, [{"t": "How it solves the problem", "sz": 13, "bold": True, "color": BLUE}])
sol = [("✓", "Right lead → right product → right price, instantly, with a professional offer."),
       ("✓", "Flags risky sourcing before disbursal → fewer NPAs."),
       ("✓", "Transparent, fast, tiered payouts → partner loyalty → more & better volume."),
       ("★", "The flywheel: win the partner → volume → data → sharper models.")]
for i, (g, t) in enumerate(sol):
    icon_row(s, 5.32, 2.62 + i * 0.66, 4.1, g, t, BLUE, sz=10.5)

# ================================================================ Slide 4 — Features
s = slides[3]
def feat_panel(l, header, accent, tint, items):
    rect(s, l, 1.55, 4.5, 3.8, tint, line=accent, lw=1.0)
    ribbon(s, l + 0.0, 1.55, 4.5, 0.5, header, accent, sz=13)
    for i, t in enumerate(items):
        icon_row(s, l + 0.22, 2.28 + i * 0.42, 4.1, "✓", t, accent, sz=10.8)
feat_panel(0.4, "Customer & RM", GREEN, T_GREEN, [
    "ML conversion-propensity queue (risk-adjusted)",
    "Explainable financial-health score (0–100)",
    "Deterministic eligibility, rate & EMI engine",
    "Suitability-first next-best-product advisory",
    "Editable offer + risk-based pricing in-band",
    "Premium branded PDF + WhatsApp / Gmail",
    "Per-decision reason codes on every score"])
feat_panel(5.1, "Channel & Partner", TEAL, T_TEAL, [
    "Partner/lead default-risk (adverse-selection)",
    "Channel-mix ROI + book concentration (HHI)",
    "Commission + clawback payout engine",
    "Duplicate / fraud lead detection",
    "Instant decision (<50 ms) + SLA / TAT clock",
    "Partner tiering + churn early-warning",
    "Agentic AI assistant (natural language)"])

# ================================================================ Slide 5 — Process flow
s = slides[4]
stages = [("①", "DSA submits\nlead"), ("②", "Instant\nindicative decision"), ("③", "ML-ranked\nqueue (RM)"),
          ("④", "Recommend +\neditable offer"), ("⑤", "Risk-based\nprice + PDF"), ("⑥", "Disburse +\nlog outcome")]
bw, gap, bh, x0, y = 1.28, 0.22, 1.0, 0.35, 2.2
for i, (num, txt) in enumerate(stages):
    x = x0 + i * (bw + gap)
    fill = GREEN if i in (0, 5) else DARK if i == 1 else RGBColor(0x11, 0x6A, 0x5B)
    box(s, x, y, bw, bh, txt, fill=fill, sz=10)
    badge(s, x + bw / 2 - 0.16, y - 0.2, 0.32, num, AMBER, sz=12)
    if i < len(stages) - 1:
        arrow(s, x + bw - 0.02, y + bh / 2 - 0.11, w=gap + 0.06)
ribbon(s, x0 + 1.0, y + bh + 0.5, (bw + gap) * 4, 0.5,
       "↻  Outcomes (won / lost / default) retrain the ML models — the compounding data moat", GREEN, sz=11)
textbox(s, 0.35, 4.7, 9.3, 0.7, [{"t": "Numbers boundary: the deterministic engine owns every rupee (eligibility, rate, EMI, ECL); ML owns probabilities; the LLM only phrases. RM stays in control — edits re-validate through the engine.", "sz": 10.5, "color": GREY}])

# ================================================================ Slide 6 — Mockups
s = slides[5]
caption(s, 0.35, 1.5, 4.55, "RM dashboard — risk-adjusted, ML-ranked queue")
picture(s, SHOTS / "dashboard.png", 0.35, 1.75, 4.55, 3.15)
caption(s, 5.1, 1.5, 4.55, "Prospect profile — reason codes & recommendation")
picture(s, SHOTS / "prospect.png", 5.1, 1.75, 4.55, 3.15)

# ================================================================ Slide 7 — Architecture
s = slides[6]
box(s, 1.6, 1.5, 6.8, 0.48, "Presentation  ·  FastAPI + Jinja2 + Tailwind   (RM dashboard · Partner portal · AI assistant)", fill=DARK, sz=11)
down(s, 4.9, 2.0)
box(s, 0.9, 2.28, 3.9, 0.48, "Layer 1 · Directives (SOPs in Markdown)", fill=RGBColor(0x11, 0x6A, 0x5B), sz=11)
box(s, 5.2, 2.28, 3.9, 0.48, "Layer 2 · AI Orchestration — NVIDIA NIM LLM (de-identified, phrasing only)", fill=RGBColor(0x11, 0x6A, 0x5B), sz=10)
down(s, 4.9, 2.78)
box(s, 0.9, 3.06, 8.2, 0.5, "Layer 3 · Deterministic Engine + ML  —  owns every number", fill=GREEN, sz=12)
subs = ["Eligibility · Rate · EMI", "Economics (ECL / RAROC) + Risk pricing", "ML: Propensity + Default-risk",
        "Explainability (reason codes)", "Commission + Clawback", "PDF (WeasyPrint)"]
sw, sg, sx, sy = 2.63, 0.16, 0.9, 3.64
for i, t in enumerate(subs):
    box(s, sx + (i % 3) * (sw + sg), sy + (i // 3) * 0.48, sw, 0.42, t, fill=T_GREEN, font=DARK, sz=9.5)
box(s, 0.9, 4.62, 8.2, 0.4, "Data — products · partners · prospects · history · trained model artifacts (.pkl)", fill=SLATE, sz=10)
textbox(s, 0.9, 5.08, 8.2, 0.34, [{"t": "Integration points (PoC): CIBIL bureau · KYC / e-consent (DPDP) · LOS / BRE / LMS · NVIDIA AI Enterprise / on-prem", "sz": 9.5, "bold": True, "color": GREY}])

# ================================================================ Slide 8 — Technologies (chips)
s = slides[7]
groups = [("Backend & Web", GREEN, ["Python 3.14", "FastAPI", "Uvicorn", "Jinja2", "Tailwind CSS", "vanilla JS"]),
          ("Machine learning & AI", BLUE, ["scikit-learn", "NumPy / SciPy", "joblib", "occlusion XAI", "NVIDIA NIM LLM"]),
          ("Documents & PDF", AMBER, ["WeasyPrint", "pango / cairo"]),
          ("Quality & Deployment", VIOLET, ["pytest · 44 tests", "Playwright", "Docker", "Render / Railway / Cloud Run"])]
y = 1.55
for name, col, items in groups:
    textbox(s, 0.4, y, 9.2, 0.32, [{"t": name, "sz": 12.5, "bold": True, "color": col}])
    y = chip_flow(s, 0.4, y + 0.4, items, col) + 0.1

# ================================================================ Slide 9 — Cost
s = slides[8]
rect(s, 0.4, 1.7, 4.5, 2.9, T_GREEN, line=GREEN, lw=1.0)
textbox(s, 0.4, 1.9, 4.5, 0.4, [{"t": "Prototype — today", "sz": 13, "bold": True, "color": GREEN, "align": PP_ALIGN.CENTER}])
textbox(s, 0.4, 2.35, 4.5, 0.9, [{"t": "≈ ₹0", "sz": 44, "bold": True, "color": GREEN, "align": PP_ALIGN.CENTER}])
textbox(s, 0.55, 3.35, 4.2, 1.1, [
    {"t": "Open-source stack", "sz": 11.5, "color": SLATE, "align": PP_ALIGN.CENTER},
    {"t": "NVIDIA NIM free tier", "sz": 11.5, "color": SLATE, "align": PP_ALIGN.CENTER},
    {"t": "Free-tier hosting · no licence cost", "sz": 11.5, "color": SLATE, "align": PP_ALIGN.CENTER}])
rect(s, 5.1, 1.7, 4.5, 2.9, T_SLATE, line=SLATE, lw=1.0)
textbox(s, 5.1, 1.9, 4.5, 0.4, [{"t": "Production PoC — indicative (annual)", "sz": 12.5, "bold": True, "color": DARK, "align": PP_ALIGN.CENTER}])
for i, t in enumerate(["LLM / GPU inference — usage-based",
                       "Cloud hosting + DB + storage — modest",
                       "Integration — LOS/BRE/KYC/CIBIL (one-time)",
                       "Model-ops — monitoring, retraining, governance"]):
    icon_row(s, 5.32, 2.45 + i * 0.5, 4.1, "▸", t, TEAL, sz=10.8)
ribbon(s, 0.4, 4.78, 9.2, 0.5, "ROI:  cost saved (NPA reduction + payout-leakage → 0 + RM selling hours)  ≫  cost to run", GREEN, sz=12.5)

# ================================================================ Slide 10 — Snapshots
s = slides[9]
grid = [("offer.png", "Editable offer — live EMI & risk-based pricing"),
        ("channel.png", "Channel intelligence — adverse selection, ROI, HHI"),
        ("submit.png", "Instant decision + adverse-action reason codes"),
        ("deck.png", "Built-in pitch deck (live numbers)")]
xs, ys = [0.35, 5.1], [1.85, 3.75]
for i, (img, cap) in enumerate(grid):
    x, yy = xs[i % 2], ys[i // 2]
    caption(s, x, yy - 0.26, 4.5, cap)
    picture(s, SHOTS / img, x, yy, 4.5, 1.62)

# ================================================================ Slide 11 — Performance (chart + stats)
s = slides[10]
cd = CategoryChartData()
cd.categories = ["Conversion\nPropensity", "Partner\nDefault-Risk"]
cd.add_series("AUC ×100", (69, 81))
cd.add_series("Gini", (39, 62))
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.4), Inches(1.65), Inches(4.7), Inches(2.5), cd)
ch = gf.chart
ch.has_title = True; ch.chart_title.text_frame.text = "Model performance (hold-out, synthetic — indicative)"
ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(10)
ch.has_legend = True; ch.legend.position = XL_LEGEND_POSITION.BOTTOM; ch.legend.include_in_layout = False
ch.legend.font.size = Pt(9)
try:
    ch.series[0].format.fill.solid(); ch.series[0].format.fill.fore_color.rgb = GREEN
    ch.series[1].format.fill.solid(); ch.series[1].format.fill.fore_color.rgb = AMBER
    ch.value_axis.has_major_gridlines = True
    for ax in (ch.value_axis, ch.category_axis):
        ax.tick_labels.font.size = Pt(9)
except Exception:
    pass
stat(s, 5.25, 1.65, 2.15, 1.15, "< 50 ms", "Instant decision latency", GREEN, T_GREEN)
stat(s, 7.5, 1.65, 2.1, 1.15, "~1–2 s", "LLM reply (9 s timeout → fallback)", BLUE, T_BLUE)
stat(s, 5.25, 2.95, 4.35, 1.2, "0.22", "Partner-history feature share — no target leakage · Bayesian shrinkage", VIOLET, T_VIOLET)
# impact band
textbox(s, 0.4, 4.28, 9.2, 0.3, [{"t": "Business impact on the synthetic book", "sz": 12, "bold": True, "color": DARK}])
stat(s, 0.4, 4.62, 2.9, 0.72, "₹16.4 Cr", "pipeline value", GREEN, T_GREEN)
stat(s, 3.45, 4.62, 2.9, 0.72, "₹0.68 Cr", "risk-adjusted value", AMBER, T_AMBER)
stat(s, 6.5, 4.62, 3.1, 0.72, "44 / 44", "automated tests passing", BLUE, T_BLUE)

# ================================================================ Slide 12 — Future (3 phases)
s = slides[11]
phases = [("Phase 1 · Integrate", GREEN, T_GREEN,
           ["IDBI sandbox APIs", "CIBIL bureau + KYC", "e-consent (DPDP Act)", "LOS / BRE / LMS hooks"]),
          ("Phase 2 · Harden", BLUE, T_BLUE,
           ["Retrain on real conversion / NPA / TAT", "SHAP + PSI drift monitoring", "Auth / RBAC + audit trail", "Data residency"]),
          ("Phase 3 · Scale", VIOLET, T_VIOLET,
           ["Partner mobile portal + WhatsApp bot", "OTP-gated secure delivery", "Collections & Early-Warning (EWS)", "NVIDIA AI Enterprise / on-prem"])]
pw = 3.0
for i, (name, col, tint, items) in enumerate(phases):
    l = 0.4 + i * (pw + 0.2)
    rect(s, l, 1.7, pw, 3.5, tint, line=col, lw=1.0)
    ribbon(s, l, 1.7, pw, 0.5, name, col, sz=12)
    for j, t in enumerate(items):
        icon_row(s, l + 0.2, 2.42 + j * 0.66, pw - 0.35, "▸", t, col, sz=10.5)

# ================================================================ Slide 13 — Links
s = slides[12]
links = [("⌥", "GitHub Public Repository", "https://github.com/Shubham-33/Hack2Skill-IDBI-Hackathone", DARK, T_SLATE),
         ("◉", "Final Product Link (live prototype)", "https://prospect-assist-ai-2guf.onrender.com", GREEN, T_GREEN),
         ("►", "Demo Video Link (3 minutes)", "[ paste your unlisted YouTube / Drive link ]", AMBER, T_AMBER)]
for i, (g, label, url, col, tint) in enumerate(links):
    t = 2.15 + i * 1.02
    rect(s, 0.4, t, 9.2, 0.86, tint, line=col, lw=1.0)
    badge(s, 0.62, t + 0.23, 0.42, g, col, sz=15)
    textbox(s, 1.3, t + 0.12, 8.1, 0.35, [{"t": label, "sz": 12.5, "bold": True, "color": col}])
    textbox(s, 1.3, t + 0.46, 8.1, 0.35, [{"t": url, "sz": 12.5, "color": SLATE}])

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
