#!/usr/bin/env python3
"""Fact-grounded promotional presentation of 286 historic department activities.

Runs on the built static site, not on source posts. Source media, URLs, event dates
and credited people remain unchanged. Editorial revisions are explicitly curated;
short archival articles are never padded with unverified claims.
"""
from __future__ import annotations
import html
import json
import re
from pathlib import Path
from functools import lru_cache

ROOT = Path(__file__).resolve().parents[1]
URL = "https://ai.k-bigdata.kr"
CARD = re.compile(r'<article class="activity-card">.*?</article>', re.S)
ACTIVITY = re.compile(r'activities/([^/]+)/index\.html$')
CURATED = {
    "sesac-hackathon-grand-prize-2025": (
        "서울시 새싹 해커톤 대상 수상, AI 서비스 개발 역량 입증",
        "2025 새싹(SeSAC) 해커톤에서 학과 학생 팀이 서울시 대상을 수상했습니다. AI 아이디어를 서비스로 구현하는 프로젝트 도전과 수상 성과를 소개합니다."),
    "alumni-ha-jae-hyeong-lecture-2026": (
        "부산대 대학원에 진학한 졸업생, 후배들에게 전한 진로 설계 경험",
        "7기 졸업생 하재형 선배가 재학 당시의 학업과 활동, 부산대학교 대학원 소프트웨어공학 전공 진학 과정, 현재의 대학원 생활을 공유했습니다."),
    "teacher-generative-ai-r-training-2026": (
        "고교 교사 대상 생성형 AI·R 실습 연수, 데이터 분석 교육 역량 강화",
        "2026년 7월 21~23일 고교 교사를 대상으로 15시간 동안 생성형 AI 도구와 R 기반 데이터 분석 실습 연수를 운영했습니다."),
    "kopo-773576": (
        "엔씨IDS 재직 졸업생이 전하는 IT 취업 준비와 개발자 성장 경험",
        "엔씨소프트 계열 엔씨IDS에 재직 중인 졸업생 이재훈 선배가 전공 학습, 프로젝트, 개발 직무와 취업 준비 경험을 후배들에게 공유했습니다."),
    "kopo-770067": (
        "LangChain·LangGraph로 배우는 AI 에이전트 구현, 졸업생 실무 특강",
        "9기 졸업생 김태승 강사가 LangChain·LangGraph·LangSmith를 활용한 AI 에이전트 설계와 실무 워크플로를 소개했습니다."),
    "department-funding-2025": (
        "AI·클라우드 실습환경 고도화, 학과 개편 사업 약 10억 원 확보",
        "2025년 학과 개편 사업 선정으로 약 10억 원의 교육환경 개선 예산을 확보하고 GPU 서버, 워크스테이션, 실습 공간 개선을 추진합니다."),
}
FEATURED = [
    "sesac-hackathon-grand-prize-2025",
    "gangseo-job-fair-2026",
    "kopo-699006",
]
CATEGORIES = (
    "수상·성과", "취업·진로", "전문가 특강", "멘토링·진로",
    "진로체험", "학생 프로젝트", "교원 연수", "산학협력",
    "연구·학술", "학과 행사", "지역사회 교육",
    "사회공헌·봉사", "학과 소식", "과거 기록", "기술·참고자료",
)
def esc(value: str) -> str:
    return html.escape(value, quote=True)

def strip_markup(value: str) -> str:
    return html.unescape(re.sub(r'<[^>]+>', ' ', value)).strip()

@lru_cache(maxsize=1)
def articles() -> dict[str, dict[str, str]]:
    result = {}
    text = (ROOT / "activities/index.html").read_text(encoding="utf-8")
    for card in CARD.findall(text):
        slug = re.search(r'<h3><a href="/activities/([^/]+)/"', card)
        title = re.search(r'<h3><a href="[^"]+">(.*?)</a></h3>', card, re.S)
        summary = re.search(r'</h3><p>(.*?)</p>', card, re.S)
        category = re.search(r'<div class="activity-card-meta"><span>(.*?)</span>', card)
        date = re.search(r'<time datetime="([^"]+)"', card)
        if not all((slug, title, summary, category, date)):
            raise ValueError("Malformed activity card in source archive")
        key = slug.group(1)
        label = html.unescape(title.group(1))
        lead = strip_markup(summary.group(1))
        if key in CURATED:
            label, lead = CURATED[key]
        result[key] = {
            "title": label, "lead": lead,
            "category": strip_markup(category.group(1)),
            "date": date.group(1),
        }
    if len(result) != 286:
        raise ValueError(f"Expected 286 article cards, got {len(result)}")
    return result

def replace_text_tag(source: str, tag: str, value: str) -> str:
    pattern = re.compile(r'(<'+tag+r'[^>]*>).*?(</'+tag+r'>)', re.S)
    return pattern.sub(lambda m: m.group(1)+esc(value)+m.group(2), source, count=1)

def meta(source: str, attribute: str, key: str, value: str) -> str:
    pattern = re.compile(r'(<meta\b(?=[^>]*\b'+attribute+r'="'+re.escape(key)+r'")[^>]*\bcontent=")([^"]*)(")', re.S)
    return pattern.sub(lambda m:m.group(1)+esc(value)+m.group(3),source,count=1)

def apply_cards(source: str) -> str:
    records = articles()
    def change(match):
        item = match.group(0)
        slug = re.search(r'<h3><a href="/activities/([^/]+)/"', item).group(1)
        if slug not in CURATED:
            return item
        record = records[slug]
        item = re.sub(r'(<h3><a href="[^"]+">).*?(</a></h3>)',
                      lambda m:m.group(1)+esc(record["title"])+m.group(2),item,count=1,flags=re.S)
        item = re.sub(r'(</h3><p>).*?(</p>)',
                      lambda m:m.group(1)+esc(record["lead"])+m.group(2),item,count=1,flags=re.S)
        item = re.sub(r'(\baria-label=")[^"]*(")',
                      lambda m:m.group(1)+esc(record["title"]+" 자세히 보기")+m.group(2),item,count=1)
        return item
    return CARD.sub(change, source)

def featured_section(archive: str) -> str:
    cards = {re.search(r'<h3><a href="/activities/([^/]+)/"', c).group(1):c
             for c in CARD.findall(archive)}
    out = []
    for slug in FEATURED:
        if slug not in cards:
            raise ValueError("Missing highlighted article: "+slug)
        c = cards[slug]
        item = articles()[slug]
        photo = re.search(r'<img\s+src="([^"]+)"', c)
        media = ('<img src="'+esc(photo.group(1))+'" alt="'+esc(item["title"]+' 관련 활동 사진')+
                 '" loading="lazy" decoding="async">') if photo else '<span class="activity-feature-placeholder">학과 활동</span>'
        out.append('<a class="activity-feature-card" href="/activities/'+esc(slug)+'/">'+
                   '<span class="activity-feature-media">'+media+'</span>'+
                   '<span class="activity-feature-body"><span class="activity-feature-category">'+
                   esc(item["category"])+'</span><strong>'+esc(item["title"])+
                   '</strong><span>'+esc(item["lead"])+'</span></span></a>')
    return ('<section class="activity-featured" aria-label="주요 학과 활동 성과">'
            '<div class="container"><div class="activity-featured-heading">'
            '<div><p class="activity-kicker">FEATURED STORIES</p>'
            '<h2>성과로 만나는 학과 이야기</h2></div>'
            '<p>수상, 현장 경험, 프로젝트로 이어지는 실무 교육</p></div>'
            '<div class="activity-featured-grid">'+''.join(out)+'</div></div></section>')

def archive_page(source: str) -> str:
    source = apply_cards(source)
    source = source.replace('교실 밖에서도<br>이어지는 배움',
                            '현장에서 배우고,<br>성과로 증명하다',1)
    source = source.replace('진로체험, 행사와 현장 활동을 통해 데이터와 AI가 실제 세상과 만나는 순간을 전합니다.',
                            '수상·프로젝트·현직자 특강·취업 준비까지, 학생들의 실제 활동과 성장 이야기를 소개합니다.',1)
    source = source.replace('<h2>학과 활동 소식</h2>', '<h2>전체 학과 활동</h2>',1)
    source = source.replace('<section class="activity-list">',
                            featured_section(source)+'\n<section class="activity-list">',1)
    def change_schema(match):
        data = json.loads(match.group(1))
        if data.get("@type") != "CollectionPage":
            return match.group(0)
        for entry in data.get("mainEntity",{}).get("itemListElement",[]):
            slug = entry.get("url","").rstrip("/").rsplit("/",1)[-1]
            if slug in CURATED:
                entry["name"] = articles()[slug]["title"]
        return '<script type="application/ld+json">'+json.dumps(data,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c")+'</script>'
    source = re.sub(r'<script type="application/ld\+json">(.*?)</script>',change_schema,source,count=1,flags=re.S)
    return source

def related(slug: str, category: str, current_date: str) -> str:
    pool = [(key,a) for key,a in articles().items() if key!=slug and a["category"]==category]
    if not pool:
        return ""
    # Prefer articles near the original event date; older archival stories are not
    # automatically associated with unrelated newer achievements.
    pool.sort(key=lambda x:(abs(int(x[1]["date"][:4])-int(current_date[:4])),x[1]["date"]), reverse=False)
    rows = []
    for key,entry in pool[:3]:
        rows.append('<a href="/activities/'+esc(key)+'/"><time datetime="'+esc(entry["date"])+
                    '">'+esc(entry["date"][:4])+'</time><span>'+esc(entry["title"])+'</span></a>')
    return '<nav class="activity-related" aria-label="관련 학과 활동"><h2>함께 보면 좋은 학과 활동</h2><div>'+''.join(rows)+'</div></nav>'

def detail_page(source: str, slug: str) -> str:
    rec = articles().get(slug)
    if rec is None:
        raise ValueError("Unexpected detail slug "+slug)
    original_images = re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', source)
    original_urls = re.findall(r'\bhref="([^"]+)"', source)
    if slug in CURATED:
        source = replace_text_tag(source,"h1",rec["title"])
        source = replace_text_tag(source,"title",rec["title"]+" | 빅데이터소프트웨어공학과")
        source = re.sub(r'(<p class="activity-lead">).*?(</p>)',
                        lambda m:m.group(1)+esc(rec["lead"])+m.group(2),source,count=1,flags=re.S)
        for attribute,key,value in (("name","description",rec["lead"]),
                                    ("property","og:title",rec["title"]+" | 빅데이터소프트웨어공학과"),
                                    ("property","og:description",rec["lead"]),
                                    ("name","twitter:title",rec["title"]+" | 빅데이터소프트웨어공학과"),
                                    ("name","twitter:description",rec["lead"])):
            source = meta(source,attribute,key,value)
        def change_schema(match):
            data = json.loads(match.group(1))
            if data.get("@type") in ("Article","NewsArticle","BlogPosting"):
                data["headline"] = rec["title"]
                data["description"] = rec["lead"]
            return '<script type="application/ld+json">'+json.dumps(data,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c")+'</script>'
        source = re.sub(r'<script type="application/ld\+json">(.*?)</script>',change_schema,source,count=1,flags=re.S)
    # Contextual rather than repeated generic image alternatives.
    source = re.sub(r'(\balt=")학과 활동 현장 사진(")',
                    lambda m:m.group(1)+esc(rec["title"]+" 관련 현장 사진")+m.group(2),source)
    # Eliminate a small set of low-information editorial phrases without
    # altering attributed statements, project results, or historical facts.
    replacements = {
        "이번 활동은 학교에서 학습한 기술과 실제 현장의 경험을 연결하는 학과 프로그램으로 운영되었습니다.":"",
        "앞으로도 많은 관심과 응원 부탁드립니다!":"",
        "많은 관심과 응원 부탁드립니다!":"",
        "이번 특강은 성공적으로 진행되었습니다.":"이번 특강을 진행했습니다.",
    }
    for old,new in replacements.items():
        source = source.replace(old,new)
    if rec["category"] in ("과거 기록","기술·참고자료") and int(rec["date"][:4]) <= 2022:
        notice = ('<aside class="activity-archive-note">이 글은 '+esc(rec["date"][:4])+
                  '년 당시의 활동·참고자료를 보존한 기록입니다. 현재 일정이나 모집 안내와는 다를 수 있습니다.</aside>')
        source = source.replace('<div class="activity-content">','<div class="activity-content">'+notice,1)
    related_markup = related(slug,rec["category"],rec["date"])
    if related_markup:
        source = source.replace('<div class="activity-cta">',related_markup+'<div class="activity-cta">',1)
    if original_images != re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', source):
        raise ValueError("Image source changed for "+slug)
    current_urls = re.findall(r'\bhref="([^"]+)"', source)
    if not set(original_urls).issubset(set(current_urls)):
        raise ValueError("Original link removed for "+slug)
    return source

def enhance_activity_page(source: str, relative: str) -> str:
    if relative == "activities/index.html":
        return archive_page(source)
    m = ACTIVITY.fullmatch(relative)
    if m:
        return detail_page(source,m.group(1))
    return source
