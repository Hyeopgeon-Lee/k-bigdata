import copy
import json
import unittest
from pathlib import Path
from generate_post import validate, publish
from build_site import render_body

class InsightTests(unittest.TestCase):
    def setUp(self):
        self.post=json.loads((Path(__file__).resolve().parents[1]/'data/posts.json').read_text(encoding='utf-8'))[0]
    def test_researched_article_passes(self):validate(self.post)
    def test_short_keyword_article_rejected(self):
        p=copy.deepcopy(self.post);p['sections']=p['sections'][:1]
        with self.assertRaises(ValueError):validate(p)
    def test_banned_boilerplate_rejected(self):
        p=copy.deepcopy(self.post);p['sections'][0]['paragraphs'].append('학과 홍보용')
        with self.assertRaises(ValueError):validate(p)
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):publish(self.post,[self.post],today=self.post['date'])
    def test_future_dated_post_rejected(self):
        with self.assertRaises(ValueError):publish(self.post,[],today='2026-09-15')
    def test_html_is_escaped_and_table_renders(self):
        p=copy.deepcopy(self.post);p['sections'][0]['paragraphs']=['<script>alert(1)</script>']
        body=render_body(p)
        self.assertNotIn('<script>',body);self.assertIn('&lt;script&gt;',body)
        self.assertIn('<table>',body);self.assertIn('id="section-10"',body)
if __name__=='__main__':unittest.main()
