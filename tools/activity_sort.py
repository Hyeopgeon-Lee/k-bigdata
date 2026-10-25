"""Stable newest-first ordering for the static department activity archive.

The activity archive is assembled by multiple historical importers in batches.
Sort at build time so new entries automatically appear in the correct position
regardless of their source chunk or repository insertion order.
"""
from __future__ import annotations

import json
import re
from datetime import date

SITE_URL = "https://ai.k-bigdata.kr"
GRID = re.compile(
    r'(?P<head><div class="activity-card-grid">\s*)'
    r'(?P<content>.*?)'
    r'(?P<tail>\s*</div></div></section>)',
    re.DOTALL,
)
CARD = re.compile(r'<article class="activity-card">.*?</article>', re.DOTALL)
TIME = re.compile(r'<time\s+datetime="(\d{4}-\d{2}-\d{2})"')
HREF = re.compile(r'<h3><a\s+href="(/activities/[^"]+/)"')
COMMENT = re.compile(r'<!--\s*(?:OFFICIAL_FIRST_PAGE|KOPO_PAGES_\d+_\d+)_(?:START|END)\s*-->')
SCHEMA = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.DOTALL)


def sort_activity_archive(html: str) -> str:
    """Reorder every card and the matching CollectionPage ItemList by shown date."""
    match = GRID.search(html)
    if match is None:
        raise ValueError("Activity card grid is missing; refusing silent unsorted deployment")

    body = match.group("content")
    cards = CARD.findall(body)
    if not cards:
        raise ValueError("Activity grid has no cards")

    residue = COMMENT.sub("", CARD.sub("", body))
    if residue.strip():
        raise ValueError("Unknown content within activity grid; sorting may discard markup")

    keyed: list[tuple[str, str, str]] = []
    for card in cards:
        dt = TIME.search(card)
        href = HREF.search(card)
        if not dt or not href:
            raise ValueError("Activity card requires an unambiguous date and detail URL")
        date.fromisoformat(dt.group(1))  # reject malformed or impossible dates
        keyed.append((dt.group(1), href.group(1), card))

    hrefs = [item[1] for item in keyed]
    if len(set(hrefs)) != len(hrefs):
        raise ValueError("Duplicate activity cards detected")

    # Python's stable sort retains the original relative order for same-day entries.
    keyed.sort(key=lambda item: item[0], reverse=True)
    ordered = "\n".join(item[2] for item in keyed)
    html = html[:match.start()] + match.group("head") + ordered + match.group("tail") + html[match.end():]

    schema_found = False
    def reorder_schema(m: re.Match[str]) -> str:
        nonlocal schema_found
        obj = json.loads(m.group(1))
        if obj.get("@type") != "CollectionPage":
            return m.group(0)
        schema_found = True
        itemlist = obj.get("mainEntity", {}).get("itemListElement", [])
        lookup = {item.get("url"): item for item in itemlist}
        full_urls = [SITE_URL + item[1] for item in keyed]
        if len(itemlist) != len(keyed) or set(lookup) != set(full_urls):
            raise ValueError("CollectionPage schema does not match activity cards")
        obj["mainEntity"]["itemListElement"] = [
            {**lookup[url], "position": i + 1}
            for i, url in enumerate(full_urls)
        ]
        return '<script type="application/ld+json">' + json.dumps(
            obj, ensure_ascii=False, separators=(",", ":")
        ).replace("<", "\\u003c") + "</script>"

    html = SCHEMA.sub(reorder_schema, html)
    if not schema_found:
        raise ValueError("CollectionPage structured data is absent")

    # Include all historical records, not just the latest two academic years.
    html = html.replace("<span>2025–2026</span>", "<span>2016–2026</span>", 1)
    return html
