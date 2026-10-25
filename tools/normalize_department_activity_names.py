"""Normalize historic department names across public activity articles.

The official department name is 빅데이터소프트웨어공학과. The migration updates
only publication HTML, keeping URLs, image assets and original-source files intact.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVITIES = ROOT / "activities"
CURRENT = "빅데이터소프트웨어공학과"
LEGACY = ("빅데이터소프트웨어과", "빅데이터과", "데이터분석과")
ARTICLE = re.compile(r'<article class="activity-card">.*?</article>', re.S)
HREF = re.compile(r'\b(?:href|src)="([^"]*)"')


def normalize_text(html: str) -> str:
    """Normalize visible article text, titles, alt, SEO and JSON-LD consistently."""
    for old in LEGACY:
        html = html.replace(old, CURRENT)
    return html


def all_activity_pages(root: Path = ACTIVITIES) -> list[Path]:
    return sorted(root.rglob("index.html"))


def migrate() -> tuple[int, int, dict[str, int]]:
    paths = all_activity_pages()
    if len(paths) < 322:
        raise RuntimeError(f"Expected archive and 321+ activity posts, found {len(paths)} files")

    changes = dict.fromkeys(LEGACY, 0)
    written = 0
    for path in paths:
        original = path.read_text(encoding="utf-8")
        for term in LEGACY:
            changes[term] += original.count(term)
        normalized = normalize_text(original)

        # No new or removed links, image paths, or gallery markup.
        if HREF.findall(original) != HREF.findall(normalized):
            raise RuntimeError(f"URL or asset changed in {path}")
        if original.count('<article class="activity-card">') != normalized.count('<article class="activity-card">'):
            raise RuntimeError(f"Activity cards changed in {path}")

        if original != normalized:
            path.write_text(normalized, encoding="utf-8")
            written += 1

    for path in paths:
        content = path.read_text(encoding="utf-8")
        if any(term in content for term in LEGACY):
            raise RuntimeError(f"Legacy name remains in {path}")

    archive = (ACTIVITIES / "index.html").read_text(encoding="utf-8")
    if len(ARTICLE.findall(archive)) != 321:
        raise RuntimeError("Expected 321 archive cards after migration")
    print("DEPARTMENT_NAME_MIGRATION", f"updated_files={written}",
          f"pages_checked={len(paths)}",
          "replacements=" + ",".join(f"{key}:{count}" for key, count in changes.items()))
    return written, len(paths), changes


if __name__ == "__main__":
    migrate()
