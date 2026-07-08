"""Fill the IDBI Innovate 2026 prototype submission deck — clean, well-filled.

Keeps the IDBI template (branded header/footer are baked-in raster images). Fixes:
one strong restyled heading per slide (no redundant kicker), light-grey container
panels + denser content so slides feel full and defined, tighter typography.
"""
from __future__ import annotations
import struct
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "Prototype Submission Deck _ IDBI Innovate.pptx"
OUT = ROOT / "Prospect Assist AI - IDBI Innovate Submission Deck.pptx"
SHOTS = ROOT / ".tmp" / "shots"

INK = RGBColor(0x1B, 0x24, 0x21); GREEN = RGBColor(0x0A, 0x7D, 0x6B)
DEEP = RGBColor(0x0A, 0x3D, 0x33); GREY = RGBColor(0x6E, 0x76, 0x80)
HAIR = RGBColor(0xD7, 0xDD, 0xE0); PANEL = RGBColor(0xF2, 0xF5, 0xF6)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

prs = Presentation(str(TEMPLATE))
slides = list(prs.slides)


def png_size(p):
    d = open(p, "rb").read(26); return struct.unpack(">II", d[16:24])


def text(slide, l, t, w, h, runs, align=PP_ALIGN.LEFT, anchor=None, line_spacing=None):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    if anchor: tf.vertical_anchor = anchor
    for i, para in enumerate(runs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if line_spacing: p.line_spacing = line_spacing
        p.space_after = Pt(0); p.space_before = Pt(0)
        for d in (para if isinstance(para, list) else [para]):
            r = p.add_run(); r.text = d["t"]
            r.font.size = Pt(d.get("sz", 12)); r.font.bold = d.get("bold", False)
            r.font.italic = d.get("italic", False)
            r.font.color.rgb = d.get("color", INK); r.font.name = "Arial"
    return tb


def frect(slide, l, t, w, h, fill, line=None, lw=0.75, shp=MSO_SHAPE.ROUNDED_RECTANGLE):
    sp = slide.shapes.add_shape(shp, Inches(l), Inches(t), Inches(w), Inches(h))
    if fill is None: sp.fill.background()
    else: sp.fill.solid(); sp.fill.fore_color.rgb = fill
    if line is None: sp.line.fill.background()
    else: sp.line.color.rgb = line; sp.line.width = Pt(lw)
    sp.shadow.inherit = False
    ge = sp._element.spPr
    return sp


def rule(slide, l, t, w, h, color):
    frect(slide, l, t, w, h, color, shp=MSO_SHAPE.RECTANGLE)


def style_title(slide, accent=True):
    """Restyle the template's own title into one strong heading; grey any sub-prompts."""
    for sh in slide.shapes:
        if not sh.has_text_frame or sh.shape_type == 13:
            continue
        top = Emu(sh.top).inches; wid = Emu(sh.width).inches
        if 0.7 <= top <= 0.95 and wid > 8 and sh.text_frame.text.strip():
            paras = sh.text_frame.paragraphs
            for r in paras[0].runs:
                r.font.size = Pt(23); r.font.bold = True; r.font.color.rgb = DEEP; r.font.name = "Arial"
            for p in paras[1:]:
                for r in p.runs:
                    r.font.size = Pt(10.5); r.font.bold = False; r.font.color.rgb = GREY
            single = len([p for p in paras if p.text.strip()]) == 1
            if accent and single:
                rule(slide, 0.36, 1.44, 0.55, 0.05, GREEN)
            return single
    return True


def panel(slide, l, t, w, h, header=None, hcolor=GREEN):
    frect(slide, l, t, w, h, PANEL)
    if header:
        text(slide, l + 0.28, t + 0.2, w - 0.5, 0.32,
             [{"t": header.upper(), "sz": 11, "bold": True, "color": hcolor}])


def bullet(slide, l, t, w, body, lead=None, sz=11.5):
    rule(slide, l, t + 0.1, 0.14, 0.03, GREEN)
    para = []
    if lead: para.append({"t": lead + "  ", "sz": sz, "bold": True, "color": DEEP})
    para.append({"t": body, "sz": sz, "color": INK})
    text(slide, l + 0.26, t - 0.03, w - 0.26, 0.6, [para], line_spacing=1.05)


def stat(slide, l, t, w, number, lab, nsz=26, ncolor=GREEN, align=PP_ALIGN.LEFT):
    text(slide, l, t, w, 0.55, [{"t": number, "sz": nsz, "bold": True, "color": ncolor}], align=align)
    text(slide, l, t + nsz / 56.0 + 0.06, w, 0.32,
         [{"t": lab.upper(), "sz": 9.5, "bold": True, "color": GREY}], align=align)


def obox(slide, l, t, w, h, txt, border=HAIR, tcolor=INK, sz=10.5, bold=False, fill=WHITE):
    sp = frect(slide, l, t, w, h, fill, line=border, lw=1.0, shp=MSO_SHAPE.RECTANGLE)
    tf = sp.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.06); tf.margin_top = tf.margin_bottom = Inches(0.02)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = txt; r.font.size = Pt(sz); r.font.bold = bold
    r.font.color.rgb = tcolor; r.font.name = "Arial"
    return sp


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
s = slides[1]; style_title(s)
text(s, 0.36, 1.66, 9.3, 0.8,
     [[{"t": "A channel-aware loan-origination & partner-relationship copilot, ", "sz": 16, "color": INK},
       {"t": "on top of IDBI's existing LOS / BRE / LMS.", "sz": 16, "bold": True, "color": GREEN}]],
     line_spacing=1.1)
text(s, 0.36, 2.48, 9.3, 0.3,
     [{"t": "Retail lending is sourced through DSAs & dealers and runs on TAT + trust — so it works all four sides at once.", "sz": 11, "color": GREY}])
quad = [("Customer", "Only suitable, clearly-explained, instant offers — no spam, no black box."),
        ("RM / Bank", "A queue ranked by risk-adjusted profit, with a reason for every score."),
        ("Channel partner (DSA)", "Instant decisions, transparent auto-payouts, tiering — the loyalty moat."),
        ("Risk / Regulator", "Explainable, fair, adverse-selection-aware lending with an audit trail.")]
cw, ch = 4.56, 1.24
for i, (lab, body) in enumerate(quad):
    x = 0.36 + (i % 2) * 4.74; y = 2.9 + (i // 2) * 1.36
    panel(s, x, y, cw, ch, lab)
    text(s, x + 0.28, y + 0.56, cw - 0.55, 0.6, [{"t": body, "sz": 11.5, "color": INK}], line_spacing=1.08)

# ================================================================ Slide 3 — Opportunities
s = slides[2]; single = style_title(s)
ty = 1.7 if single else 2.06
panel(s, 0.36, ty, 4.56, 5.3 - ty, "How it's different")
for i, (lead, body) in enumerate([
        ("Channel-first.", "Models the DSA relationship — adverse-selection, TAT, tiering, churn."),
        ("Bank-grade economics.", "Ranks by P(convert) × (net interest income − expected credit loss)."),
        ("Explainable.", "Per-decision reason codes + Reg-B / RBI adverse-action codes."),
        ("Integrates, not replaces.", "An intelligence layer on top of LOS / BRE / LMS.")]):
    bullet(s, 0.64, ty + 0.66 + i * 0.72, 4.05, body, lead=lead, sz=11)
panel(s, 5.08, ty, 4.56, 5.3 - ty, "How it solves the problem")
for i, (lead, body) in enumerate([
        ("Speed + fit.", "Right lead → right product → right price, instantly, with a pro offer."),
        ("Lower NPAs.", "Flags risky sourcing before disbursal, not after."),
        ("Partner loyalty.", "Transparent, fast, tiered payouts → more & better volume."),
        ("The flywheel.", "Win the partner → volume → data → sharper models.")]):
    bullet(s, 5.36, ty + 0.66 + i * 0.72, 4.05, body, lead=lead, sz=11)

# ================================================================ Slide 4 — Features
s = slides[3]; style_title(s)
def feat(l, header, items):
    panel(s, l, 1.66, 4.56, 3.66, header)
    for i, t in enumerate(items):
        bullet(s, l + 0.28, 2.28 + i * 0.42, 4.05, t, sz=10.8)
feat(0.36, "Customer & RM", [
    "ML conversion-propensity queue (risk-adjusted)",
    "Explainable financial-health score (0–100)",
    "Deterministic eligibility, rate & EMI engine",
    "Suitability-first next-best-product advisory",
    "Editable offer + risk-based pricing in-band",
    "Premium branded PDF + WhatsApp / Gmail send",
    "Per-decision reason codes on every score"])
feat(5.08, "Channel & Partner", [
    "Partner / lead default-risk (adverse-selection)",
    "Channel-mix ROI + book concentration (HHI)",
    "Commission + clawback payout engine",
    "Duplicate / fraud lead detection",
    "Instant decision (<50 ms) + SLA / TAT clock",
    "Partner tiering + churn early-warning",
    "Agentic AI assistant (natural language)"])

# ================================================================ Slide 5 — Process flow
s = slides[4]; style_title(s)
panel(s, 0.36, 1.66, 9.28, 1.66)
stages = ["Lead\nsubmitted", "Instant\ndecision", "Ranked\nqueue", "Offer +\nprice", "PDF +\nsend", "Outcome\nlogged"]
iw, aw, x0, y = 1.28, 0.2, 0.55, 2.0
for i, txt in enumerate(stages):
    x = x0 + i * (iw + aw)
    text(s, x, y, iw, 0.5, [{"t": f"0{i+1}", "sz": 23, "bold": True, "color": GREEN}], align=PP_ALIGN.CENTER)
    text(s, x, y + 0.56, iw, 0.5, [{"t": txt, "sz": 11, "color": INK}], align=PP_ALIGN.CENTER, line_spacing=1.0)
    if i < len(stages) - 1:
        text(s, x + iw, y + 0.06, aw, 0.4, [{"t": "→", "sz": 16, "bold": True, "color": GREEN}], align=PP_ALIGN.CENTER)
panel(s, 0.36, 3.5, 9.28, 1.82)
text(s, 0.64, 3.72, 9.0, 0.3,
     [[{"t": "↻  Closed loop.  ", "sz": 12, "bold": True, "color": DEEP},
       {"t": "Outcomes (won / lost / default) retrain the ML models — the compounding data moat.", "sz": 12, "color": INK}]])
text(s, 0.64, 4.3, 9.0, 0.85,
     [[{"t": "Numbers boundary.  ", "sz": 12, "bold": True, "color": DEEP},
       {"t": "The deterministic engine owns every rupee (eligibility, rate, EMI, ECL); the ML owns "
             "probabilities; the LLM only phrases. The RM stays in control — every edit re-validates "
             "through the engine, so no invalid or non-compliant offer can ever leave.", "sz": 11.5, "color": INK}]],
     line_spacing=1.15)

# ================================================================ Slide 6 — Mockups
s = slides[5]; style_title(s)
panel(s, 0.36, 1.66, 4.56, 3.66)
text(s, 0.6, 1.82, 4.2, 0.3, [{"t": "RM DASHBOARD — RISK-ADJUSTED QUEUE", "sz": 9.5, "bold": True, "color": GREEN}])
picture(s, SHOTS / "dashboard.png", 0.56, 2.24, 4.16, 2.9)
panel(s, 5.08, 1.66, 4.56, 3.66)
text(s, 5.32, 1.82, 4.2, 0.3, [{"t": "PROSPECT PROFILE — REASON CODES", "sz": 9.5, "bold": True, "color": GREEN}])
picture(s, SHOTS / "prospect.png", 5.28, 2.24, 4.16, 2.9)

# ================================================================ Slide 7 — Architecture
s = slides[6]; style_title(s)
obox(s, 1.5, 1.7, 7.0, 0.44, "Presentation — FastAPI + Jinja2 + Tailwind  (RM dashboard · Partner portal · AI assistant)", border=GREEN, tcolor=DEEP, sz=10.5)
obox(s, 0.9, 2.42, 3.95, 0.44, "Layer 1 — Directives (SOPs in Markdown)", border=GREEN, tcolor=DEEP, sz=10.5)
obox(s, 5.15, 2.42, 3.95, 0.44, "Layer 2 — AI Orchestration (NVIDIA NIM LLM, de-identified)", border=GREEN, tcolor=DEEP, sz=10)
obox(s, 0.9, 3.14, 8.2, 0.46, "Layer 3 — Deterministic Engine + ML   ·   owns every number", border=GREEN, tcolor=WHITE, sz=11.5, fill=GREEN)
subs = ["Eligibility · Rate · EMI", "Economics (ECL / RAROC) + pricing", "ML: Propensity + Default-risk",
        "Explainability (reason codes)", "Commission + Clawback", "PDF (WeasyPrint)"]
for i, t in enumerate(subs):
    obox(s, 0.9 + (i % 3) * 2.79, 3.72 + (i // 3) * 0.46, 2.63, 0.4, t, border=HAIR, tcolor=INK, sz=9.5)
obox(s, 0.9, 4.68, 8.2, 0.4, "Data — products · partners · prospects · history · trained model artifacts (.pkl)", border=HAIR, tcolor=GREY, sz=9.5)
text(s, 0.9, 5.14, 8.2, 0.3, [{"t": "Integration (PoC): CIBIL bureau · KYC / e-consent (DPDP) · LOS / BRE / LMS · NVIDIA AI Enterprise", "sz": 9.5, "color": GREY}])

# ================================================================ Slide 8 — Technologies
s = slides[7]; style_title(s)
groups = [("Backend & Web", "Python 3.14 · FastAPI · Uvicorn · Jinja2 · Tailwind CSS · vanilla JS"),
          ("Machine learning & AI", "scikit-learn · NumPy / SciPy · joblib · occlusion XAI · NVIDIA NIM LLM"),
          ("Documents & PDF", "WeasyPrint · pango / cairo"),
          ("Quality & Deployment", "pytest (44 tests) · Playwright · Docker · Render / Railway / Cloud Run")]
y = 1.7
for name, items in groups:
    panel(s, 0.36, y, 9.28, 0.78)
    text(s, 0.64, y + 0.13, 9.0, 0.28, [{"t": name.upper(), "sz": 10.5, "bold": True, "color": GREEN}])
    text(s, 0.64, y + 0.44, 9.0, 0.3, [{"t": items, "sz": 12.5, "color": INK}])
    y += 0.9

# ================================================================ Slide 9 — Cost
s = slides[8]; style_title(s)
panel(s, 0.36, 1.66, 4.56, 2.92, "Prototype — today")
text(s, 0.56, 2.25, 4.2, 0.9, [{"t": "≈ ₹0", "sz": 44, "bold": True, "color": GREEN}])
text(s, 0.64, 3.3, 4.2, 1.0, [
    {"t": "Open-source stack", "sz": 11, "color": INK},
    {"t": "NVIDIA NIM free tier", "sz": 11, "color": INK},
    {"t": "Free-tier hosting · no licence cost", "sz": 11, "color": INK}], line_spacing=1.3)
panel(s, 5.08, 1.66, 4.56, 2.92, "Production PoC — indicative (annual)")
for i, t in enumerate(["LLM / GPU inference — usage-based",
                       "Cloud hosting + DB + storage — modest",
                       "Integration — LOS / BRE / KYC / CIBIL (one-time)",
                       "Model-ops — monitoring, retraining, governance"]):
    bullet(s, 5.36, 2.3 + i * 0.5, 4.05, t, sz=11)
panel(s, 0.36, 4.72, 9.28, 0.6)
text(s, 0.36, 4.86, 9.28, 0.32,
     [[{"t": "ROI  ", "sz": 12, "bold": True, "color": GREEN},
       {"t": "— cost saved (NPA reduction + payout-leakage → 0 + RM selling hours)  ≫  cost to run.", "sz": 12, "color": INK}]],
     align=PP_ALIGN.CENTER)

# ================================================================ Slide 10 — Snapshots
s = slides[9]; style_title(s)
grid = [("offer.png", "Editable offer — live EMI & risk-based pricing"),
        ("channel.png", "Channel intelligence — adverse selection, ROI, HHI"),
        ("submit.png", "Instant decision + adverse-action reason codes"),
        ("deck.png", "Built-in pitch deck (live numbers)")]
for i, (img, cap) in enumerate(grid):
    x = 0.36 + (i % 2) * 4.74; y = 1.72 + (i // 2) * 1.82
    panel(s, x, y, 4.56, 1.72)
    text(s, x + 0.22, y + 0.1, 4.2, 0.28, [{"t": cap.upper(), "sz": 8.5, "bold": True, "color": GREEN}])
    picture(s, SHOTS / img, x + 0.2, y + 0.44, 4.16, 1.16)

# ================================================================ Slide 11 — Performance
s = slides[10]; style_title(s)
panel(s, 0.36, 1.66, 9.28, 1.1, "Model performance — hold-out, synthetic (indicative)")
rule(s, 5.0, 2.02, 0.012, 0.62, HAIR)
stat(s, 0.64, 2.02, 4.2, "0.69 / 39", "Conversion propensity — AUC / Gini", nsz=25)
stat(s, 5.28, 2.02, 4.2, "0.81 / 62", "Partner default-risk — AUC / Gini", nsz=25)
panel(s, 0.36, 2.9, 9.28, 1.05, "Speed & integrity")
stat(s, 0.64, 3.24, 2.8, "< 50 ms", "Instant decision latency", nsz=20, ncolor=INK)
stat(s, 3.7, 3.24, 2.7, "~1–2 s", "LLM reply · 9 s timeout", nsz=20, ncolor=INK)
stat(s, 6.7, 3.24, 2.7, "0.22", "Feature share — no leakage", nsz=20, ncolor=INK)
panel(s, 0.36, 4.09, 9.28, 1.15, "Business impact — synthetic book")
stat(s, 0.64, 4.46, 2.8, "₹16.4 Cr", "pipeline value", nsz=21)
stat(s, 3.7, 4.46, 2.7, "₹0.68 Cr", "risk-adjusted value", nsz=21)
stat(s, 6.7, 4.46, 2.7, "44 / 44", "automated tests passing", nsz=21)

# ================================================================ Slide 12 — Future
s = slides[11]; style_title(s)
phases = [("Integrate", ["IDBI sandbox APIs", "CIBIL bureau + KYC", "e-consent (DPDP Act)", "LOS / BRE / LMS hooks"]),
          ("Harden", ["Retrain on real conv / NPA / TAT", "SHAP + PSI drift monitoring", "Auth / RBAC + audit trail", "Data residency"]),
          ("Scale", ["Partner mobile portal + WhatsApp", "OTP-gated secure delivery", "Collections & Early-Warning", "NVIDIA AI Enterprise / on-prem"])]
cw = 3.0
for i, (name, items) in enumerate(phases):
    l = 0.36 + i * (cw + 0.14)
    panel(s, l, 1.66, cw, 3.66)
    text(s, l + 0.24, 1.84, cw, 0.6, [{"t": f"0{i+1}", "sz": 24, "bold": True, "color": GREEN}])
    text(s, l + 0.9, 1.96, cw, 0.4, [{"t": name, "sz": 14, "bold": True, "color": DEEP}])
    rule(s, l + 0.24, 2.5, cw - 0.48, 0.014, HAIR)
    for j, t in enumerate(items):
        bullet(s, l + 0.24, 2.68 + j * 0.6, cw - 0.4, t, sz=10.5)

# ================================================================ Slide 13 — Links
s = slides[12]; single = style_title(s)
ty = 1.7 if single else 2.1
rows = [("GitHub Public Repository", "https://github.com/Shubham-33/Hack2Skill-IDBI-Hackathone"),
        ("Final Product Link (live prototype)", "https://prospect-assist-ai-2guf.onrender.com"),
        ("Demo Video Link (3 minutes)", "[ paste your unlisted YouTube / Drive link ]")]
h = 0.92
for i, (lab, url) in enumerate(rows):
    y = ty + i * (h + 0.14)
    panel(s, 0.36, y, 9.28, h)
    rule(s, 0.36, y + 0.16, 0.07, h - 0.32, GREEN)
    text(s, 0.64, y + 0.16, 9.0, 0.3, [{"t": lab.upper(), "sz": 11, "bold": True, "color": GREEN}])
    text(s, 0.64, y + 0.48, 9.0, 0.32, [{"t": url, "sz": 13, "color": INK}])

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
