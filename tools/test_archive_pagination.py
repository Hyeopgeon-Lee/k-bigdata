"""Post-optimization deployment checks. Run after tools/optimize_archive.py."""
from __future__ import annotations

import json
import math
import re
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'_site'
PER_PAGE=12
CARD=re.compile(r'<article class="activity-card">.*?</article>',re.S)

class OptimizedArchiveTests(unittest.TestCase):
    def test_archive_paginated_without_data_loss(self):
        source=(ROOT/'activities/index.html').read_text(encoding='utf-8')
        original=CARD.findall(source)
        records=json.loads((OUT/'assets/data/activity-index.json').read_text(encoding='utf-8'))
        self.assertEqual(len(original),len(records))
        self.assertGreaterEqual(len(records),280)
        slugs=lambda cards:[re.search(r'<h3><a href="([^"]+)"',c).group(1) for c in cards]
        expected=set(slugs(original))
        self.assertEqual(expected,{r['url'] for r in records})
        self.assertEqual(len(expected),len(records))
        total=math.ceil(len(records)/PER_PAGE)
        received=[]
        for page in range(1,total+1):
            destination=OUT/'activities/index.html' if page==1 else OUT/f'activities/page/{page}/index.html'
            self.assertTrue(destination.is_file(),str(destination))
            content=destination.read_text(encoding='utf-8')
            cards=CARD.findall(content)
            self.assertEqual(len(cards),min(PER_PAGE,len(records)-(page-1)*PER_PAGE))
            received.extend(slugs(cards))
            self.assertIn('archive-static-pagination',content)
            self.assertIn('site-refresh.css',content)
            self.assertIn('activity-pagination.js',content)
            if page>1:
                self.assertIn(f'<link rel="canonical" href="https://ai.k-bigdata.kr/activities/page/{page}/"',content)
                self.assertIn(f'학과 활동 · {page}페이지',content)
        # The build deliberately publishes newest-first, which can differ from
        # the hand-maintained source archive. Preserve every URL and the
        # generated search-index order rather than asserting source order.
        self.assertEqual(received,[entry['url'] for entry in records])
        self.assertEqual(set(received),expected)
        self.assertLess((OUT/'activities/index.html').stat().st_size,130_000)

    def test_visitor_journey_stable(self):
        homepage=(OUT/'index.html').read_text(encoding='utf-8')
        order=['id="major"','id="campus-film"','id="roadmap"',
               'id="projects"','id="outcomes"','id="activities"','id="admission"']
        positions=[homepage.index(x) for x in order]
        self.assertEqual(positions,sorted(positions))
        self.assertIn('site-refresh.css',homepage)
        self.assertIn('nav-cta',homepage)
        self.assertIn('id="guides"',homepage)
        self.assertIn('id="stories"',homepage)
        self.assertIn('id="faq-title"',homepage)
        self.assertNotIn('STUDENT PROJECT SHOWCASE',homepage)
        self.assertIn('DEPARTMENT INTRODUCTION',homepage)
        self.assertNotIn('campus-film-title" hidden',homepage)

    def test_no_internal_edits_published(self):
        for path in ('data','reports','tools','.github'):
            self.assertFalse((OUT/path).exists(),path)
        self.assertTrue((OUT/'assets/data/activity-index.json').is_file())

    def test_sitemap_pagination(self):
        tree=ET.parse(OUT/'sitemap.xml')
        ns={'n':'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls={p.text for p in tree.findall('n:url/n:loc',ns)}
        for number in range(2,math.ceil(len(json.loads((OUT/'assets/data/activity-index.json').read_text(encoding='utf-8')))/PER_PAGE)+1):
            self.assertIn(f'https://ai.k-bigdata.kr/activities/page/{number}/',urls)

if __name__=='__main__':
    unittest.main()
