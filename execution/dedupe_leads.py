"""Duplicate / multi-sourcing lead detection.

Same customer submitted through two channels → payout disputes + double effort.
A lightweight deterministic matcher on stable identity signals (name + income +
product + city), flagging near-duplicates across different partners.
"""
from __future__ import annotations

from collections import defaultdict

from config import load_json


def _key(p):
    # identity signal that survives across channels (in production: PAN/phone hash)
    return (p["name"].strip().lower(), round(p["monthly_income"], -3), p["requested_product"])


def find_duplicates(prospects: list[dict] | None = None) -> list[dict]:
    prospects = prospects or load_json("prospects.json")
    buckets = defaultdict(list)
    for p in prospects:
        buckets[_key(p)].append(p)
    dupes = []
    for key, group in buckets.items():
        if len(group) < 2:
            continue
        partners = {p["partner_id"] for p in group}
        dupes.append({
            "name": group[0]["name"],
            "product": group[0]["requested_product"],
            "count": len(group),
            "lead_ids": [p["id"] for p in group],
            "partners": sorted(partners),
            "cross_channel": len(partners) > 1,
            "note": ("Same customer sourced via multiple partners — attribution/payout conflict"
                     if len(partners) > 1 else "Duplicate submission from same partner"),
        })
    return dupes


if __name__ == "__main__":
    d = find_duplicates()
    print(f"Duplicate clusters found: {len(d)}")
    for x in d:
        print(f"  {x['name']:20} {x['product']:14} leads={x['lead_ids']} "
              f"partners={x['partners']} {'⚠ cross-channel' if x['cross_channel'] else ''}")
