"""Deployment gate for generated HTML, metadata, links, RSS and public data."""
import json
import re
import unittest
import xml.etree.ElementTree as ET
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
from admission_build import load_admissions, state_at, enhance_page, round_cards
from employment_build import sanitize, FIELDS
from notify_indexnow import urls_from_sitemap
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'_site';HOST='https://ai.k-bigdata.kr'
class Page(HTMLParser):
    def __init__(self,text):
        super().__init__();self.tags=[];self.feed(text)
    def handle_starttag(self,tag,attrs):self.tags.append((tag,dict(attrs)))
    def find(self,tag,attr,value):return [a for t,a in self.tags if t==tag and a.get(attr)==value]
class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.map=ET.parse(OUT/'sitemap.xml');cls.urls=urls_from_sitemap((OUT/'sitemap.xml').read_bytes())
        cls.pages=[]
        for url in cls.urls:
            path=url.removeprefix(HOST+'/');file=OUT/(path+'index.html' if not Path(path).suffix else path)
            text=file.read_text(encoding='utf-8');cls.pages.append((url,file,text,Page(text)))
    def test_admissions_and_date_generated_seo(self):
        data=load_admissions()
        cases=[('2026-10-02T00:00:00+09:00','수시2차','upcoming'),('2026-11-11T00:00:00+09:00','수시2차','open'),('2026-11-28T00:00:00+09:00','정시모집','upcoming'),('2027-01-04T00:00:00+09:00','정시모집','open'),('2027-01-23T00:00:00+09:00','정규모집 종료','closed')]
        source=(ROOT/'index.html').read_text(encoding='utf-8')
        for instant,name,phase in cases:
            state=state_at(instant);self.assertEqual(state['phase'],phase)
            page=enhance_page(source,'index.html',state,data)
            self.assertIn(name,Page(page).find('meta','name','description')[0]['content'])
            self.assertIn(name,re.search(r'<title>(.*?)</title>',page)[1])
            self.assertNotIn('og-share-2027-susi1.png',page)
            self.assertIn(state['announcement'],page)
        self.assertEqual(len(data['rounds']),3)
    def test_all_required_urls_and_no_duplicates(self):
        for path in ('','admission/2027/','projects/','employment/','ai-software/','data-analysis/','backend-software/','seoul-it-college/','career-portfolio/','insights/','activities/','activities/social-data-career-trends/','activities/gangseo-job-fair-2026/'):
            self.assertIn(HOST+'/'+path,self.urls)
        self.assertEqual(len(self.urls),len(set(self.urls)))
        for entry in self.map.getroot():self.assertRegex(entry.find('{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod').text,r'^\d{4}-\d{2}-\d{2}$')
    def test_metadata_and_schema(self):
        titles=[];descriptions=[]
        for url,file,text,page in self.pages:
            with self.subTest(url=url):
                title=re.search(r'<title>(.*?)</title>',text,re.S);self.assertIsNotNone(title);self.assertTrue(title[1].strip());titles.append(title[1])
                descriptions.append(page.find('meta','name','description')[0]['content'])
                self.assertEqual(page.find('link','rel','canonical')[0]['href'],url)
                self.assertNotIn('noindex',page.find('meta','name','robots')[0]['content'])
                self.assertEqual(len([t for t,a in page.tags if t=='h1']),1)
                for prop in ('og:image','og:title','og:description'):
                    self.assertTrue(page.find('meta','property',prop)[0]['content'])
                for prop in ('twitter:title','twitter:description','twitter:image'):self.assertTrue(page.find('meta','name',prop)[0]['content'])
                image=page.find('meta','property','og:image')[0]['content'];self.assertTrue((OUT/image.removeprefix(HOST+'/')).is_file())
                self.assertNotIn('og-share-2027-susi1.png',text)
                for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>',text,re.S):
                    value=json.loads(raw);self.assertTrue(value)
                    for schema in (value if isinstance(value,list) else [value]):
                        self.assertTrue(schema.get('@type'));self.assertEqual(schema['@context'],'https://schema.org')
                        if schema['@type']=='FAQPage':
                            self.assertEqual(len(schema['mainEntity']),len([t for t,a in page.tags if t=='details']))
                            for item in schema['mainEntity']:
                                self.assertTrue(item['name']);self.assertTrue(item['acceptedAnswer']['text'])
        self.assertEqual(len(titles),len(set(titles)));self.assertEqual(len(descriptions),len(set(descriptions)))
    def test_internal_links_assets_and_anchors(self):
        for url,file,text,page in self.pages:
            for tag,attrs in page.tags:
                value=attrs.get('href') if tag in ('a','link') else attrs.get('src') if tag in ('img','script') else None
                if not value:continue
                parsed=urlparse(unescape(value))
                if parsed.scheme in ('tel','mailto'):continue
                if parsed.netloc and parsed.netloc!='ai.k-bigdata.kr':
                    self.assertEqual(parsed.scheme,'https');continue
                path=unquote(parsed.path)
                target=OUT/path.lstrip('/') if path.startswith('/') or parsed.netloc else file.parent/path
                if not path:target=file
                if target.is_dir():target=target/'index.html'
                with self.subTest(url=url,link=value):
                    self.assertTrue(target.is_file(),str(target))
                    if parsed.fragment and target.suffix=='.html':self.assertIn(f'id="{parsed.fragment}"',target.read_text(encoding='utf-8'))
    def test_feed_xml_and_body(self):
        rss=ET.parse(OUT/'feed.xml');items=rss.findall('./channel/item');self.assertTrue(items)
        for item in items:
            for key in ('title','link','guid','pubDate','description','source'):self.assertTrue(item.find(key).text)
            self.assertIn('<p>',item.find('description').text);self.assertGreater(len(item.find('description').text),500)
            self.assertEqual(item.find('guid').get('isPermaLink'),'true')
            self.assertTrue(item.find('source').get('url').startswith('https://'))
    def test_employment_allowlist_and_fallback(self):
        raw={'graduation_year':'2025','company':'회사','job':'개발','email':'private@example.com','PIN':'1234','alumni_id':'secret','masked_name':'김○○'}
        cleaned=sanitize([raw]);self.assertEqual(set(cleaned[0]),FIELDS)
        self.assertNotIn('private',json.dumps(cleaned));self.assertEqual(sanitize([dict(raw,job='010-1234-5678')]),[])
        page=(OUT/'employment/index.html').read_text(encoding='utf-8')
        records=json.loads(re.search(r'<script id="employment-fallback" type="application/json">(.*?)</script>',page,re.S)[1])
        self.assertTrue(records);self.assertTrue(all(set(row)==FIELDS for row in records))
        self.assertIn('employment-card',page);self.assertNotIn('취업현황을 불러오는 중입니다.',page)
        self.assertIn('employment-mini-card',(OUT/'index.html').read_text(encoding='utf-8'))
    def test_verification_and_robots(self):
        self.assertEqual((OUT/'robots.txt').read_text(encoding='utf-8'),(ROOT/'robots.txt').read_text(encoding='utf-8'))
        for file in [*ROOT.glob('google*.html'),*ROOT.glob('naver*.html')]:self.assertEqual(file.read_bytes(),(OUT/file.name).read_bytes())
    def test_images_1200_630(self):
        import struct
        for name in ('og-department.png','og-admission-2027-susi2.png','og-admission-2027-regular.png','og-insights.png','og-projects.png','og-employment.png'):
            self.assertEqual(struct.unpack('>II',(OUT/'assets/promo'/name).read_bytes()[16:24]),(1200,630))
    def test_activity_department_name_consistency(self):
        """All published activity articles use the current official department name."""
        legacy=('빅데이터소프트웨어과', '빅데이터과', '데이터분석과')
        count=0
        for url,file,html,_page in self.pages:
            if '/activities/' not in url:
                continue
            count+=1
            for old in legacy:
                with self.subTest(page=url,old_name=old):
                    self.assertNotIn(old,html)
        self.assertGreaterEqual(count,287)

    def test_activity_cards_newest_first_and_schema_consistent(self):
        """All 321+ activity cards are sorted across the entire pagination range."""
        source=(OUT/'activities/index.html').read_text(encoding='utf-8')
        cards=re.findall(r'<article class="activity-card">.*?</article>',source,re.S)
        self.assertEqual(len(cards),286)
        dates=[re.search(r'<time datetime="(\d{4}-\d{2}-\d{2})"',c)[1] for c in cards]
        self.assertEqual(dates,sorted(dates,reverse=True))
        urls=[re.search(r'<h3><a href="(/activities/[^"]+/)"',c)[1] for c in cards]
        self.assertEqual(len(urls),len(set(urls)))
        self.assertEqual(dates[0],'2026-10-25')
        self.assertEqual(dates[-1],'2016-10-31')
        script=re.search(r'<script type="application/ld\+json">(.*?)</script>',source,re.S)
        self.assertIsNotNone(script)
        schema=json.loads(script[1])
        items=schema['mainEntity']['itemListElement']
        self.assertEqual([x['position'] for x in items],list(range(1,len(cards)+1)))
        self.assertEqual([x['url'] for x in items],[HOST+x for x in urls])
        self.assertIn('2016–2026',source)

    def test_indexnow_empty_and_invalid(self):
        for xml in (b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"/>',b'not XML'):
            with self.assertRaises((ValueError,ET.ParseError)):urls_from_sitemap(xml)

class ActivityPromotionTests(unittest.TestCase):
    """Editorial, preservation, semantic markup and archive regression gate."""

    @classmethod
    def setUpClass(cls):
        cls.index = (OUT/'activities/index.html').read_text(encoding='utf-8')
        cls.cards = re.findall(r'<article class="activity-card">.*?</article>',cls.index,re.S)
        cls.source_index = (ROOT/'activities/index.html').read_text(encoding='utf-8')
        cls.source_cards = re.findall(r'<article class="activity-card">.*?</article>',cls.source_index,re.S)

    def test_all_286_urls_dates_media_preserved(self):
        self.assertEqual(len(self.cards),286)
        self.assertEqual(len(self.source_cards),286)
        def indexed(cards):
            return {re.search(r'<h3><a href="/activities/([^/]+)/"',c).group(1):c for c in cards}
        before,after = indexed(self.source_cards),indexed(self.cards)
        self.assertEqual(set(before),set(after))
        self.assertNotIn('kopo-738806/',self.index)
        self.assertNotIn('kopo-707036/',self.index)
        for slug in before:
            with self.subTest(slug=slug):
                src = before[slug]
                dst = after[slug]
                self.assertEqual(re.search(r'<time datetime="([^"]+)"',src).group(1),
                                 re.search(r'<time datetime="([^"]+)"',dst).group(1))
                self.assertEqual(re.findall(r'<img\b[^>]*\bsrc="([^"]+)"',src),
                                 re.findall(r'<img\b[^>]*\bsrc="([^"]+)"',dst))
                self.assertTrue((OUT/'activities'/slug/'index.html').is_file())

    def test_main_promotional_gallery_and_source_titles(self):
        self.assertIn('class="activity-featured"',self.index)
        self.assertEqual(self.index.count('class="activity-feature-card"'),3)
        self.assertIn('현장에서 배우고,',self.index)
        self.assertIn('전체 학과 활동',self.index)
        self.assertEqual(len(re.findall(r'alt="학과 활동 현장 사진"',self.index)),0)
        recent = sum(re.search(r'<time datetime="(\d{4})-',c).group(1) in ('2025','2026') for c in self.cards)
        self.assertEqual(recent,61)
        for title in ('새싹 해커톤 대상','엔씨IDS 재직 졸업생','AI·클라우드 실습환경'):
            self.assertIn(title,self.index)

    def test_details_have_contextual_navigation_and_consistent_claims(self):
        related = 0
        facts = 0
        for card in self.cards:
            slug = re.search(r'<h3><a href="/activities/([^/]+)/"',card).group(1)
            built = (OUT/'activities'/slug/'index.html').read_text(encoding='utf-8')
            raw = (ROOT/'activities'/slug/'index.html').read_text(encoding='utf-8')
            with self.subTest(slug=slug):
                self.assertEqual(
                    re.findall(r'<img\b[^>]*\bsrc="([^"]+)"',raw),
                    re.findall(r'<img\b[^>]*\bsrc="([^"]+)"',built),
                    'original gallery and photo src must not change')
                self.assertNotIn('alt="학과 활동 현장 사진"',built)
                self.assertIn('href="https://ai.k-bigdata.kr/activities/'+slug+'/"',built)
                self.assertTrue(re.search(r'<h1>.+?</h1>',built,re.S))
                if 'class="activity-related"' in built:
                    related += 1
                if 'class="activity-story-facts"' in built:
                    facts += 1
        self.assertGreaterEqual(related,270)
        self.assertEqual(facts,61)

    def test_filters_are_keyboard_accessible_and_have_real_content(self):
        script = (OUT/'activity-pagination.js').read_text(encoding='utf-8')
        stylesheet = (OUT/'activities.css').read_text(encoding='utf-8')
        for token in ("type = 'search'","addSelect('연도'","addSelect('활동 분야'",
                      "setAttribute('aria-pressed'","addEventListener('popstate'",
                      "PAGE_SIZE = 12"):
            self.assertIn(token,script)
        for rule in ('.activity-toolbar','.activity-featured-grid',
                     '.activity-related','.activity-featured[hidden]'):
            self.assertIn(rule,stylesheet)

if __name__=='__main__':unittest.main()
