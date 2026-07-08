# Generate Offer (Editable PDF)

## Goal
Turn a recommendation into an RM-editable, professional, compliant PDF offer for the customer.

## Inputs
- Prospect + chosen product/amount/rate/tenure (RM may edit).

## Tools / Scripts
- `execution/eligibility.py` — `validate_offer_edit()` re-validates edits (clamp rate to band, recompute EMI, cap amount).
- `execution/generate_offer_pdf.py` — renders `web/templates/offer.html` via WeasyPrint.
- `execution/generate_pitch.py` — WhatsApp/email copy (compliance-checked).

## Steps
1. RM edits fields in `/offer/{id}`; each edit POSTs to `/offer/{id}/recompute` → EMI/eligibility re-validated live.
2. `/offer/{id}/pdf` renders the branded PDF from the validated fields.
3. `/send/{id}` returns WhatsApp/Gmail URL-spec links (no OAuth) with compliant copy.

## Outputs
- A premium IDBI-branded PDF + outreach copy.

## Edge cases & learnings
- WeasyPrint needs native pango/cairo → run with `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib` (see `run.sh`).
- Banned phrases (guaranteed returns etc.) are stripped by `generate_pitch.compliance_check`.
- PII over WhatsApp/Gmail is a demo-only shortcut; production uses an OTP-gated secure link.
