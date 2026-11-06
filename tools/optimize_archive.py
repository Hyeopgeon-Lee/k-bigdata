"""Post-validation static archive pagination and image-size enrichment.

Runs AFTER the legacy full-archive editorial regression suite. Source archive and
all permanent article URLs remain untouched; only the published _site is split.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import struct
from datetime import date
from html import unescape
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_site"
PAGE_SIZE = 12
BASE = "https://ai.k-bigdata.kr"

CARD = re.compile(r'<article class="activity-card">.*?</article>', re.S)
GRID = re.compile(r'(<div class="activity-card-grid">)(.*?)(</div></div></section>)', re.S)
SCHEMA = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
IMG = re.compile(r'<img\b[^>]*>', re.I)


def attr(tag: str, name: str) -> str:
    match = re.search(r'\b' + re.escape(name) + r'="([^"]*)"', tag)
    return unescape(match.group(1)) if match else ""


def label(markup: str) -> str:
    return unescape(re.sub(r'<[^>]+>', '', markup)).strip()


def card_data(card: str) -> dict:
    link = re.search(r'<h3><a\b[^>]*>(.*?)</a>', card, re.S)
    heading = link.group(1) if link else ""
    time = re.search(r'<time\b[^>]*>', card)
    image = IMG.search(card)
    category = re.search(r'<div class="activity-card-meta"><span>(.*?)</span>', card, re.S)
    summary = re.search(r'</h3><p>(.*?)</p>', card, re.S)
    return {
        "url": attr(link.group(0), 'href') if link else "",
        "title": label(heading), "category": label(category.group(1)) if category else "기타",
        "date": attr(time.group(0), 'datetime') if time else "",
        "summary": label(summary.group(1)) if summary else "",
        "image": attr(image.group(0), 'src') if image else "",
        "alt": attr(image.group(0), 'alt') if image else "",
        "width": int(attr(image.group(0), 'width') or 600) if image else 600,
        "height": int(attr(image.group(0), 'height') or 450) if image else 450,
    }


def page_url(number: int) -> str:
    return "/activities/" if number == 1 else f"/activities/page/{number}/"


def pagination(number: int, count: int) -> str:
    pieces = ['<nav class="archive-static-pagination" aria-label="학과 활동 목록 페이지 이동">',
              f'<p>전체 학과 활동 · {number} / {count} 페이지</p><div class="archive-page-links">']
    if number > 1:
        pieces.append(f'<a rel="prev" href="{page_url(number-1)}">← 이전</a>')
    for pos in sorted(set([1, max(1, number - 1), number, min(count, number + 1), count])):
        current = ' aria-current="page"' if pos == number else ''
        pieces.append(f'<a href="{page_url(pos)}"{current}>{pos}</a>')
    if number < count:
        pieces.append(f'<a rel="next" href="{page_url(number+1)}">다음 →</a>')
    pieces.append('</div></nav>')
    return ''.join(pieces)


def narrow_schema(markup: str, selected: list[dict]) -> str:
    urls = {BASE + entry['url'] for entry in selected}
    def replace(match: re.Match) -> str:
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            return match.group(0)
        if data.get('@type') != 'CollectionPage':
            return match.group(0)
        rows = data.get('mainEntity', {}).get('itemListElement', [])
        selected_rows = [dict(row, position=i+1) for i, row in enumerate(
            row for row in rows if row.get('url') in urls)]
        data['mainEntity']['itemListElement'] = selected_rows
        return '<script type="application/ld+json">' + json.dumps(
            data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c') + '</script>'
    return SCHEMA.sub(replace, markup)


def image_size(path: Path) -> tuple[int, int] | None:
    try:
        with path.open('rb') as f:
            header = f.read(30)
            if header.startswith(b'\x89PNG\r\n\x1a\n'):
                return struct.unpack('>II', header[16:24])
            if header[:2] == b'\xff\xd8':
                f.seek(2)
                while True:
                    if f.read(1) != b'\xff':
                        return None
                    code = f.read(1)
                    while code == b'\xff':
                        code = f.read(1)
                    if not code or code in (b'\xd9', b'\xda'):
                        return None
                    length_bytes = f.read(2)
                    if len(length_bytes) < 2:
                        return None
                    length = struct.unpack('>H', length_bytes)[0]
                    if code[0] in (0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb):
                        data = f.read(5)
                        return struct.unpack('>HH', data[1:5])[::-1]
                    f.seek(length - 2, 1)
            if header[:4] == b'RIFF' and header[8:12] == b'WEBP':
                if header[12:16] == b'VP8X':
                    return (1 + int.from_bytes(header[24:27], 'little'),
                            1 + int.from_bytes(header[27:30], 'little'))
        return None
    except (OSError, ValueError, struct.error):
        return None


def enrich_images() -> int:
    count = 0
    dimensions: dict[str, tuple[int, int] | None] = {}
    for page in (OUT / 'activities').rglob('index.html'):
        if '/page/' in page.as_posix():
            continue
        original = page.read_text(encoding='utf-8')
        def fix(match: re.Match) -> str:
            nonlocal count
            tag = match.group(0)
            if 'width=' in tag and 'height=' in tag:
                return tag
            src = attr(tag, 'src')
            if not src.startswith('/assets/'):
                return tag
            if src not in dimensions:
                dimensions[src] = image_size(OUT / src.lstrip('/'))
            dims = dimensions[src]
            if not dims:
                return tag
            width, height = dims
            if not width or not height or width > 20000 or height > 20000:
                return tag
            extra = ''
            if not re.search(r'\bwidth=', tag):
                extra += f' width="{width}"'
            if not re.search(r'\bheight=', tag):
                extra += f' height="{height}"'
            if extra:
                count += 1
            return tag[:-1] + extra + '>'
        updated = IMG.sub(fix, original)
        if updated != original:
            page.write_text(updated, encoding='utf-8')
    return count


def paginate() -> tuple[int, int]:
    source = OUT / "activities" / "index.html"
    original = source.read_text(encoding='utf-8')
    m = GRID.search(original)
    if not m:
        raise ValueError("Activity archive grid missing in generated output")
    cards = CARD.findall(m.group(2))
    if len(cards) < 280:
        raise ValueError("Archive unexpectedly shrank; pagination aborted")
    items = [card_data(card) for card in cards]
    if len({a['url'] for a in items}) != len(items):
        raise ValueError("Archive has duplicate activity URLs")
    total = math.ceil(len(cards)/PAGE_SIZE)
    destination = OUT / "assets" / "data"
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "activity-index.json").write_text(
        json.dumps(items, ensure_ascii=False, separators=(',', ':')), encoding="utf-8")
    for page_no in range(1,total+1):
        begin=(page_no-1)*PAGE_SIZE
        chosen=cards[begin:begin+PAGE_SIZE]
        view=items[begin:begin+PAGE_SIZE]
        content=original[:m.start(2)] + '\n'.join(chosen) + \
            m.group(3).replace('</div></section>',pagination(page_no,total)+'</div></section>',1) + \
            original[m.end():]
        content=narrow_schema(content,view)
        if page_no > 1:
            url=BASE+page_url(page_no)
            content=re.sub(r'(<link rel="canonical" href=")[^"]+', lambda mt:mt.group(1)+url, content, count=1)
            content=re.sub(r'(<meta property="og:url" content=")[^"]+', lambda mt:mt.group(1)+url, content, count=1)
            content=re.sub(r'<title>(.*?)</title>',lambda mt:'<title>'+f'학과 활동 · {page_no}페이지 | 빅데이터소프트웨어공학과'+'</title>',content,count=1)
            content=re.sub(r'<section class="activity-featured"[^>]*>.*?</section>','',content,flags=re.S)
        page=OUT/page_url(page_no).lstrip('/')/'index.html'
        page.parent.mkdir(parents=True,exist_ok=True)
        page.write_text(content,encoding='utf-8')
    return len(items),total


def add_sitemap(total: int) -> None:
    sitemap = OUT / 'sitemap.xml'
    tree=ET.parse(sitemap)
    ns='http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('',ns)
    for page in range(2,total+1):
        entry=ET.SubElement(tree.getroot(),f'{{{ns}}}url')
        ET.SubElement(entry,f'{{{ns}}}loc').text=BASE+page_url(page)
        ET.SubElement(entry,f'{{{ns}}}lastmod').text=date.today().isoformat()
    tree.write(sitemap,encoding='utf-8',xml_declaration=True)
    manifest=OUT/'content-manifest.json'
    if manifest.exists():
        m=json.loads(manifest.read_text(encoding='utf-8'))
        for page in range(1,total+1):
            href=BASE+page_url(page)
            f=OUT/page_url(page).lstrip('/')/'index.html'
            m[href]={"hash":hashlib.sha256(f.read_bytes()).hexdigest(),"lastmod":date.today().isoformat()}
        manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')


def main() -> None:
    repaired=enrich_images()
    cards,pages=paginate()
    add_sitemap(pages)
    print(f"Optimized archive: {cards} cards across {pages} static pages, {repaired} image dimensions restored")


if __name__ == '__main__':
    main()
