"""Personalized outreach copy (email + WhatsApp) for an offer.

LLM writes the WORDING only; all numbers come from the deterministic offer. A
compliance guard strips banned/guaranteed-return phrasing. Degrades to a clean
template when the LLM is unavailable.
"""
from __future__ import annotations

import re

import nvidia_llm

BANNED = [
    r"guarantee\w*", r"assured returns?", r"risk[- ]free", r"100%\s*approv\w*",
    r"no\s*questions?\s*asked", r"instant\s*cash",
]


def compliance_check(text: str) -> tuple[str, list[str]]:
    flags = []
    clean = text
    for pat in BANNED:
        if re.search(pat, clean, re.IGNORECASE):
            flags.append(pat)
            clean = re.sub(pat, "[removed]", clean, flags=re.IGNORECASE)
    return clean, flags


def generate_pitch(prospect: dict, offer: dict, use_llm: bool = True,
                   language: str = "English") -> dict:
    name = prospect["name"].split()[0]
    product = offer["product_name"]
    amt, rate, emi_v, ten = (offer["offered_amount"], offer["rate"],
                             offer["emi"], offer["tenure_months"])

    pitch = None
    if use_llm and nvidia_llm.available():
        safe = nvidia_llm.deidentify(prospect)
        lang_note = ("" if language.lower() == "english"
                     else f" Write ALL fields in {language} "
                          f"({'Roman script' if 'hinglish' in language.lower() else 'native script'}), "
                          f"but keep product names, ₹ figures and % as-is.")
        out = nvidia_llm.complete_json(
            "You write compliant, warm, concise loan outreach for an IDBI Bank RM. "
            "Use ONLY the numbers provided. No guarantees or assured-return language." + lang_note,
            f"Customer first name: {name}. De-identified profile: {safe}. Offer: {offer}.\n"
            'Return {"email_subject","email_body","whatsapp_text"} '
            "(email_body <=90 words, whatsapp_text <=45 words).",
        )
        if out and all(k in out for k in ("email_subject", "email_body", "whatsapp_text")):
            pitch = out

    if pitch is None:  # deterministic fallback
        pitch = {
            "email_subject": f"{name}, your pre-approved {product} from IDBI Bank",
            "email_body": (
                f"Dear {name},\n\nBased on your profile, you are eligible for an IDBI "
                f"{product} of up to ₹{amt:,} at {rate}% p.a. for {ten} months "
                f"(indicative EMI ₹{emi_v:,.0f}/month). The attached offer has the full "
                f"details and terms. I'd be glad to help you take this forward.\n\n"
                f"Warm regards,\nIDBI Bank Relationship Team"),
            "whatsapp_text": (
                f"Hi {name}, IDBI has a pre-approved {product} up to ₹{amt:,} at {rate}% "
                f"(EMI ₹{emi_v:,.0f}/mo). Details in the attached offer — shall I proceed?"),
        }

    flags_all = []
    for k in ("email_subject", "email_body", "whatsapp_text"):
        pitch[k], flags = compliance_check(pitch[k])
        flags_all += flags
    pitch["compliance_flags"] = flags_all
    return pitch


if __name__ == "__main__":
    from config import load_json
    from eligibility import check_eligibility
    p = load_json("prospects.json")[0]
    offer = check_eligibility(p, p["requested_product"])
    pitch = generate_pitch(p, offer, use_llm=False)
    print("SUBJECT:", pitch["email_subject"])
    print("WHATSAPP:", pitch["whatsapp_text"])
    print("flags:", pitch["compliance_flags"])
