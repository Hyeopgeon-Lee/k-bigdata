"""Admission SEO and visible HTML generation using the SAME Node state engine as the browser."""
import json
import os
import re
import subprocess
from datetime import datetime, timedelta, timezone
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://ai.k-bigdata.kr'
KST = timezone(timedelta(hours=9))

def load_admissions():
    data = json.loads((ROOT / 'data/admissions.json').read_text(encoding='utf-8'))
    assert data['timezone'] == 'Asia/Seoul'
    assert data['year'] == 2027 and len(data['rounds']) == 3
    for r in data['rounds']:
        for k in ('start','end','interview','result'):
            datetime.strptime(r[k], '%Y-%m-%d')
        assert r['start'] <= r['end'] < r['interview'] <= r['result']
        assert r['seats'] > 0 and re.fullmatch(r'\d{2}:\d{2}', r['deadlineTime'])
    return data

def state_at(now=None):
    instant = now or os.environ.get('BUILD_TIME') or datetime.now(KST).isoformat()
    code = "const a=require('./admission.js');console.log(JSON.stringify(a.getState(new Date(process.argv[1]))));"
    result = subprocess.run(['node', '-e', code, instant], cwd=ROOT, check=True, capture_output=True, encoding='utf-8')
    return json.loads(result.stdout)

def json_script(value):
    return json.dumps(value, ensure_ascii=False, separators=(',',':')).replace('<', '\\u003c')

def meta(page, key, value, property=False):
    attr = 'property' if property else 'name'
    tag = f'<meta {attr}="{key}" content="{escape(value, quote=True)}" />'
    pattern = r'<meta\s+[^>]*' + attr + r'="' + re.escape(key) + r'"[^>]*>'
    return re.sub(pattern, lambda _: tag, page) if re.search(pattern,page) else page.replace('</head>', tag+'\n</head>')

def bind_state(page, state, data):
    page = re.sub(r'(<([\w-]+)\b[^>]*\bdata-admission="(\w+)"[^>]*>)(.*?)</\2>',
                  lambda m: m[1]+escape(str(state.get(m[3],'')))+f'</{m[2]}>', page, flags=re.S)
    def link(m):
        attrs = re.sub(r'\s+(?:href|target|rel|aria-label|data-admission-phase)="[^"]*"', '', m[1])
        attrs += f' href="{escape(state["href"],quote=True)}" data-admission-phase="{state["phase"]}"'
        if not state['href'].startswith('/'):
            attrs += ' target="_blank" rel="noopener noreferrer"'
        return '<a'+attrs+'>'+escape(state['button'])+' →</a>'
    page = re.sub(r'<a([^>]*\bdata-admission-link\b[^>]*)>.*?</a>', link, page, flags=re.S)
    page = re.sub(r'<p([^>]*data-admission-pending[^>]*)>.*?</p>',
        lambda m: '<p'+re.sub(r'\s+hidden','',m[1])+(' hidden' if not state['pending'] else '')+'>'+escape(state['pending'])+'</p>',page,flags=re.S)
    if '/admission.js' in page:
        payload = f'<script>window.ADMISSIONS_DATA={json_script(data)};</script>\n'
        page = re.sub(r'(<script\s+defer\s+src="/admission.js">)',lambda m:payload+m[1],page)
    return page

def nav():
    return ('<nav class="main-nav" id="main-navigation" aria-label="주요 메뉴">'
        '<a href="/#major">학과소개</a><a href="/#roadmap">교육과정</a>'
        '<a href="/projects/">학생작품</a><a href="/employment/">취업·성과</a>'
        '<a href="/admission/2027/">입학안내</a>'
        '<a class="nav-cta" href="https://open.kakao.com/o/gEd0JIad" target="_blank" rel="noopener noreferrer">입학상담 ↗</a></nav>')

def conversion_links():
    return '<section class="journey-links" aria-label="지원 전 확인할 정보"><div class="container"><h2>학생의 결과를 확인하고, 입학을 준비하세요.</h2><p><a href="/projects/">학생 프로젝트</a> → <a href="/employment/">졸업생 취업현황</a> → <a href="/admission/2027/">2027 입학안내</a></p></div></section>'

class FAQReader(HTMLParser):
    def __init__(self):
        super().__init__(); self.items=[]; self.current=None; self.part=None
    def handle_starttag(self, tag, attrs):
        if tag=='details': self.current={'q':'','a':''}
        if self.current is not None and tag in ('summary','p'): self.part='q' if tag=='summary' else 'a'
    def handle_data(self,text):
        if self.current is not None and self.part: self.current[self.part]+=text
    def handle_endtag(self,tag):
        if tag in ('summary','p'): self.part=None
        if tag=='details' and self.current:
            self.items.append(self.current); self.current=None

def enhance_page(page, relative, state, data):
    page = re.sub(r'<nav class="main-nav"[^>]*>.*?</nav>', lambda _:nav(),page,flags=re.S)
    image_name = ('og-insights.png' if relative.startswith('insights/') or relative=='post.html' else
                  'og-projects.png' if relative.startswith('projects/') else
                  'og-employment.png' if relative.startswith('employment/') else 'og-department.png')
    if relative in ('index.html','admission/2027/index.html'):
        image_name=state['socialImage']
        title=state['seoTitle'] if relative=='index.html' else f'2027 입학안내 · {state["name"]} | 한국폴리텍대학 서울강서캠퍼스'
        page=re.sub(r'<title>.*?</title>',lambda _:f'<title>{escape(title)}</title>',page,flags=re.S)
        description=state['seoDescription'] if relative=='index.html' else f'{state["title"]} 접수기간·모집인원·면접·합격발표와 지원 전 FAQ. 학생 프로젝트·취업현황을 확인하고 공식 모집요강·카카오 상담·원서접수로 연결하세요.'
        for key in ('description','twitter:description'): page=meta(page,key,description)
        page=meta(page,'og:description',state['ogDescription'],True)
        page=meta(page,'og:title',title,True); page=meta(page,'twitter:title',title)
    image=SITE+'/assets/promo/'+image_name
    for key in ('og:image','og:image:secure_url'): page=meta(page,key,image,True)
    for key,value in (('og:image:width','1200'),('og:image:height','630'),('og:image:type','image/png')): page=meta(page,key,value,True)
    page=meta(page,'twitter:image',image)
    canonical=re.search(r'<link rel="canonical" href="([^"]+)"',page)
    if canonical:page=meta(page,'og:url',unescape(canonical[1]),True)
    page=meta(page,'og:image:alt','한국폴리텍대학 서울강서캠퍼스 빅데이터소프트웨어공학과',True)
    title=re.search(r'<title>(.*?)</title>',page,re.S)
    description=re.search(r'<meta name="description" content="([^"]+)"',page)
    if title and not re.search(r'property="og:title"',page):page=meta(page,'og:title',unescape(title[1]),True)
    if description and not re.search(r'property="og:description"',page):page=meta(page,'og:description',unescape(description[1]),True)
    if title: page=meta(page,'twitter:title',unescape(title[1]))
    if description: page=meta(page,'twitter:description',unescape(description[1]))
    if canonical and relative.startswith('insights/') and relative!='insights/index.html':
        breadcrumb={'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'학과 홈','item':SITE+'/'},{'@type':'ListItem','position':2,'name':'AI·IT 인사이트','item':SITE+'/insights/'},{'@type':'ListItem','position':3,'name':unescape(title[1]).split(' | ')[0],'item':unescape(canonical[1])}]}
        page=page.replace('</head>',f'<script type="application/ld+json">{json_script(breadcrumb)}</script>\n</head>')
    page=bind_state(page,state,data)
    if relative=='admission/2027/index.html' and state['phase']=='upcoming':
        page=page.replace('href="/admission/2027/" data-admission-phase=', 'href="#schedule" data-admission-phase=')
    if relative=='index.html':
        webpage={'@context':'https://schema.org','@type':'WebPage','name':state['seoTitle'],'description':state['seoDescription'],'url':SITE+'/','about':{'@type':'EducationalOrganization','name':'한국폴리텍대학 서울강서캠퍼스 빅데이터소프트웨어공학과','url':SITE+'/'}}
        page=page.replace('</head>',f'<script type="application/ld+json">{json_script(webpage)}</script>\n</head>')
    if relative not in ('index.html','privacy.html','404.html','post.html') and not relative.startswith('insights/'):
        page=page.replace('</main>',conversion_links()+'</main>')
    if '<footer' in page:
        extra='<p class="seo-footer-links"><a href="/ai-software/">AI 전공 가이드</a> · <a href="/data-analysis/">데이터 교육</a> · <a href="/backend-software/">백엔드 교육</a> · <a href="/seoul-it-college/">서울 IT학과 선택</a> · <a href="/career-portfolio/">취업 포트폴리오</a> · <a href="/insights/">AI·IT 인사이트</a> · <a href="/admission/2027/">2027 입학안내</a></p>'
        page=page.replace('</footer>',extra+'</footer>')
    # Derive FAQ schema only from questions and answers actually rendered on this page.
    faq=FAQReader(); faq.feed(page)
    if faq.items:
        schema={'@context':'https://schema.org','@type':'FAQPage','mainEntity':[
            {'@type':'Question','name':x['q'].strip().rstrip('+').strip(),'acceptedAnswer':{'@type':'Answer','text':x['a'].strip()}} for x in faq.items]}
        page=page.replace('</head>',f'<script type="application/ld+json">{json_script(schema)}</script>\n</head>')
    return page

def round_cards(data, state):
    cards=[]
    for r in data['rounds']:
        status='접수중' if r['id']==state['roundId'] and state['status']=='OPEN' else '예정' if r['start']>datetime.fromisoformat(os.environ.get('BUILD_TIME') or datetime.now(KST).isoformat()).astimezone(KST).date().isoformat() else '접수 종료'
        cards.append(f'<article class="round-card" id="{r["id"]}"><span class="round-status" data-round-status="{r["id"]}" data-status="{ "open" if status=="접수중" else "upcoming" if status=="예정" else "closed" }">{status}</span><h3>{r["name"]}</h3><dl><div><dt>원서접수</dt><dd>{r["start"].replace("-",".")} ~<br>{r["end"].replace("-",".")} {r["deadlineTime"]}</dd></div><div><dt>모집인원</dt><dd>{r["seats"]}명</dd></div><div><dt>면접</dt><dd>{r["interview"].replace("-",".")}</dd></div><div><dt>최초 발표</dt><dd>{r["result"].replace("-",".")}</dd></div></dl><a href="{escape(data["guideUrl"],quote=True)}" target="_blank" rel="noopener noreferrer">공식 모집요강 확인 ↗</a></article>')
    return ''.join(cards)

def reorder_home(page):
    # Capture top-level main sections via balanced HTML tags rather than nested regex.
    main=re.search(r'(<main id="main">)(.*?)(</main>)',page,re.S)
    content=main[2]; sections=[]; depth=0; start=0
    for m in re.finditer(r'</?section\b[^>]*>',content):
        if m[0].startswith('</'):
            depth-=1
            if depth==0: sections.append(content[start:m.end()])
        else:
            if depth==0:start=m.start()
            depth+=1
    def rank(s):
        if 'class="hero"' in s:return 0
        if 'id="projects"' in s:return 1
        if 'employment-preview"' in s:return 2
        if 'achievements-section' in s:return 3
        if 'id="major"' in s:return 4
        if 'id="roadmap"' in s:return 5
        if 'id="guides"' in s:return 6
        if 'id="admission"' in s:return 7
        if 'faq-section' in s:return 8
        return 9
    return page[:main.start(2)]+'\n'.join(sorted(sections,key=rank))+page[main.end(2):]
