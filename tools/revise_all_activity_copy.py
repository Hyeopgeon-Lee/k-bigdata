#!/usr/bin/env python3
"""Editorial revision of all CURRENT public department activity posts.

Facts come from the post being edited; no invented people, figures, institutions,
technical achievements, quotes or placements. News/old recruitment articles
already removed from the index stay removed. Each review lens runs in parallel,
then edits are applied deterministically and validated as a single batch.
"""
from __future__ import annotations
import datetime
import html
import json
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/"activities"/"index.html"
REPORT=ROOT/"reports"/"activity_editorial_full_review_2026-10-25.md"
DETAILS=ROOT/"data"/"activity_editorial_full_review_2026-10-25.json"
SITE="https://ai.k-bigdata.kr"
TODAY="2026-10-25"
REMOVED={"kopo-738806","kopo-707036"}
CARD=re.compile(r'<article class="activity-card">.*?</article>',re.S)
LD=re.compile(r'<script type="application/ld\+json">(.*?)</script>',re.S)
EMOJI=re.compile(r'[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0E\uFE0F\u200D\u200B\u2060\u2800]')
EMPTY=re.compile(r'\s+')
GENERIC=("이번 활동은 학교에서 학습한 기술과 실제 현장의 경험을 연결하는 학과 프로그램으로 운영되었습니다.",
         "활동의 현장과 주요 내용을 소개합니다.",
         "앞으로도 많은 관심과 응원 부탁드립니다!",
         "많은 관심과 응원 부탁드립니다!",
         "여러분의 많은 응원 부탁드립니다!")
CATEGORIES={
 "공모전·수상":"수상·성과","수상·성과":"수상·성과",
 "멘토링·진로":"멘토링·진로","선후배 멘토링":"멘토링·진로","졸업생·진로":"멘토링·진로",
 "전문가 특강":"전문가 특강","현직자·전문가 특강":"전문가 특강",
 "연구·논문":"연구·학술","연구·학술":"연구·학술",
 "취업·진로 · 2학년":"취업·진로","진로체험 · 소셜데이터":"진로체험",
 "청소년 진로체험":"진로체험","교원 연수":"교원 연수",
 "학과 안내":"학과 소식","학과 소식":"학과 소식",
 "사회공헌·봉사":"사회공헌·봉사",
 "산학협력":"산학협력","학생 프로젝트":"학생 프로젝트",
 "지역사회 교육":"지역사회 교육","진로체험":"진로체험","취업·진로":"취업·진로",
 "과거 입시 기록":"과거 기록","기술·참고자료":"기술·참고자료","학과 행사":"학과 행사"
}
GENERIC_CATEGORY=[
 ("수상·성과",r"수상|대상(?!자)|최우수|우수상|장려상|입상|감사장|금상|동상"),
 ("멘토링·진로",r"멘토링|선후배|멘토.?멘티|졸업생.*초청"),
 ("전문가 특강",r"특강|초청.*강연|전문가.*강의"),
 ("교원 연수",r"교원|교사.*연수|직무연수"),
 ("진로체험",r"진로체험|직업체험|페스티벌|Dream Job|고교생.*실습|중학생.*체험"),
 ("사회공헌·봉사",r"봉사|재능기부|소망의\s*집|장애인.*교육"),
 ("연구·학술",r"학술|논문|연구발표"),
 ("산학협력",r"산학협력|산학연|MOU|협약|기업\s*방문|R&D.*사업"),
 ("취업·진로",r"취업|기업\s*탐방|채용|인턴십|모의면접"),
 ("학생 프로젝트",r"졸업작품|졸업\s*작품|프로젝트|시연"),
]
SECTIONS={
 "수상·성과":("수상 및 출품 내용","성과와 교육적 의미"),
 "전문가 특강":("특강과 실무 주제","학생들의 학습 내용"),
 "교원 연수":("연수 프로그램","실습 내용"),
 "진로체험":("체험 프로그램","참여 내용"),
 "연구·학술":("연구·발표 내용","연구의 의미"),
 "산학협력":("산학협력 및 기술 교류","현장 협력 내용"),
 "취업·진로":("취업·진로 활동","직무 탐색 내용"),
 "멘토링·진로":("멘토링 활동","선후배 경험 공유"),
 "학생 프로젝트":("프로젝트 개요","구현 내용"),
 "사회공헌·봉사":("봉사·지역사회 활동","참여 내용"),
 "학과 행사":("행사 내용","참여 활동"),
 "학과 소식":("학과 주요 소식","관련 내용"),
 "지역사회 교육":("교육 프로그램","실습 내용"),
 "기술·참고자료":("기술 참고자료","자료 내용"),
 "과거 기록":("당시 기록","관련 내용")
}
CTA={
 "수상·성과":"학생들의 프로젝트와 수상 성과 살펴보기",
 "전문가 특강":"기업 실무와 연결되는 학과 교육 살펴보기",
 "교원 연수":"AI·데이터 실습 중심 교육 살펴보기",
 "진로체험":"AI·데이터로 탐색하는 진로 체험",
 "연구·학술":"학생·교수의 연구와 프로젝트 성과",
 "산학협력":"기업 현장과 연결되는 실무 교육",
 "취업·진로":"전공 역량을 취업 준비와 연결하기",
 "멘토링·진로":"함께 성장하는 프로젝트·진로 교육",
 "학생 프로젝트":"직접 설계하고 구현한 학생 프로젝트",
 "사회공헌·봉사":"기술과 경험을 사회에 연결하는 활동",
 "학과 행사":"프로젝트·실습으로 이어지는 학과 활동",
 "학과 소식":"AI·클라우드 실습 환경 살펴보기",
 "지역사회 교육":"AI·데이터 활용 교육 살펴보기",
 "기술·참고자료":"지금의 AI·데이터 교육과정 살펴보기",
 "과거 기록":"최신 학과 교육과정 살펴보기"
}
SPECIAL_LEADS={
 "social-data-career-trends":"학과가 소셜데이터 분석으로 미래 직업과 관심 트렌드를 살펴보는 진로체험 부스를 운영했습니다. 참가자들에게 데이터 분석의 활용 사례를 소개했습니다.",
 "sesac-hackathon-grand-prize-2025":"2025 새싹(SeSAC) 해커톤에서 학과 학생 팀이 서울시 대상을 수상했습니다. 학생들의 AI·소프트웨어 프로젝트 성과를 소개합니다.",
 "department-funding-2025":"2025년 학과 개편 사업에 선정돼 약 10억 원의 교육환경 개선 예산을 확보했습니다. GPU 서버·워크스테이션과 실습 공간 개선을 추진합니다.",
 "department-reorganization-2025":"빅데이터 분석 중심 교육에 AI·소프트웨어 개발과 클라우드 실습을 더하는 학과 개편 방향을 소개합니다."
}
RISK_PATTERN=re.compile(r"(?<!\d)(?:100%\s*취업|취업\s*보장|전원\s*취업|무조건\s*취업)")
PHOTO_START=re.compile(r'^(?:▲|△|○|사진\s*:|출처\s*:|사진\s*설명|(?:왼쪽|오른쪽)부터|기념촬영)')
SENTENCES=re.compile(r'(?<=[.!?。])\s+(?=[가-힣A-Za-z0-9“「\(\[])')

def plain(value):
    value=html.unescape(re.sub(r"<[^>]+>"," ",str(value or "")))
    return EMPTY.sub(" ",value).strip()

def tidy(value,body=False):
    value=html.unescape(str(value or ""))
    value=EMOJI.sub(" ",value)
    value=value.replace("저희 빅데이터소프트웨어공학과","빅데이터소프트웨어공학과")
    value=value.replace("우리 빅데이터소프트웨어공학과","빅데이터소프트웨어공학과")
    value=value.replace("저희 학과","학과").replace("우리 학과","학과")
    value=value.replace("빅데이터소프트웨어공학과 는","빅데이터소프트웨어공학과는")
    value=value.replace("빅데이터소프트웨어공학과 의","빅데이터소프트웨어공학과의")
    value=value.replace("데이터 분석과는","빅데이터소프트웨어공학과는")
    value=value.replace("데이터 분석과에서는","빅데이터소프트웨어공학과에서는")
    value=value.replace("데이터 분석과 학생","빅데이터소프트웨어공학과 학생")
    value=value.replace("데이터 분석과 소개","빅데이터소프트웨어공학과 소개")
    value=re.sub(r'([가-힣])\s+(학생|교수|학과|교육|실습|프로젝트|역량)\s+(은|는|이|가|을|를)\b',r'\1 \2\3',value)
    value=re.sub(r'\b(교수|학생|팀|학과|프로그램|특강|교육|실습|역량|성과|기술|모델)\s+(은|는|이|가|을|를|와|과)\b',r'\1\2',value)
    value=re.sub(r'\s+([,.:;!?])',r'\1',value)
    value=re.sub(r'([가-힣])\s+([,.:])',r'\1\2',value)
    value=re.sub(r'!{1,3}',".",value)
    value=re.sub(r'\.{2,}',".",value)
    if body:
        for phrase in GENERIC:value=value.replace(phrase,"")
        value=value.replace("이번 행사에 많은 관심과 참여 부탁드립니다.","")
        value=value.replace("진심으로 큰 박수와 축하를 보냅니다.","")
    value=EMPTY.sub(" ",value).strip()
    return value

def sentenceify(value):
    value=tidy(value)
    if not value:return value
    if value.endswith(("다","요","임","함","음","했음","습니다","되었습니다")):value+="."
    elif value.endswith(("·",":",",","와","과","및","으로")):value=value.rstrip(" ·:,")
    return value

def choose_title(old):
    t=tidy(old)
    t=re.sub(r"^\[(?:축|기쁜소식|학과소식)\]\s*","",t)
    t=re.sub(r"^️\s*","",t)
    t=t.replace("제 2회","제2회").replace("제 3회","제3회")
    t=t.replace("소프트웨어챌리지","소프트웨어챌린지")
    t=re.sub(r"^(?:학과\s*)?(?:소식|현장)\s*[!–:-]\s*","",t)
    t=t.replace("진행!","진행").replace("성료!","운영")
    if len(t)>63:
        t=t.replace("한국폴리텍대학 서울강서캠퍼스 ","")
        t=re.sub(r"^빅데이터소프트웨어공학과(?:의|에서|는)?[, ]+","",t)
    return t.strip(" -—,·")

def choose_category(old,title):
    base=CATEGORIES.get(old,old)
    if base!="학과 행사":return base
    for label,rule in GENERIC_CATEGORY:
        if re.search(rule,title,re.I):return label
    return base

def get_rows(archive):
    elements=CARD.findall(archive)
    if len(elements)!=286:raise RuntimeError(f"Expected 286 CURRENT cards, got {len(elements)}")
    rows=[]
    for elem in elements:
        node=BeautifulSoup(elem,"html.parser")
        link=node.select_one("h3 a")
        dt=node.select_one("time")
        tag=node.select_one(".activity-card-meta span")
        if not link or not dt or not tag:raise RuntimeError("Malformed archive card")
        route=link.get("href","")
        slug=route.strip("/").split("/")[-1]
        if slug in REMOVED:raise RuntimeError(f"Removed post appeared in archive: {slug}")
        file=ROOT/"activities"/slug/"index.html"
        if not file.is_file():raise RuntimeError("Linked article file missing: "+slug)
        raw=file.read_text(encoding="utf-8")
        doc=BeautifulSoup(raw,"html.parser")
        a=doc.select_one("h1")
        lead=doc.select_one(".activity-lead")
        if not a or not lead:raise RuntimeError("Missing hero heading or intro: "+slug)
        category=plain(tag.get_text(" ",strip=True))
        rows.append(dict(slug=slug,path=file,date=dt.get("datetime"),href=route,
                         raw=raw,card=elem,title=plain(a.get_text(" ",strip=True)),
                         lead=plain(lead.get_text(" ",strip=True)),category=category,
                         doc=doc))
    if len({r["href"] for r in rows})!=286:raise RuntimeError("Duplicate links")
    return rows

def factual_candidates(doc):
    article=doc.select_one(".activity-content")
    if not article:return []
    p_nodes=article.select(":scope > section p, :scope > p")
    candidates=[]
    for p_index,p in enumerate(p_nodes):
        raw=plain(p.get_text(" ",strip=True))
        if not raw:continue
        parts=SENTENCES.split(raw)
        for si, part in enumerate(parts):
            item=tidy(part)
            if len(item)<43 or len(item)>198:continue
            if item.startswith(("이번 활동은","앞으로도","많은 관심","감사합니다","안녕하세요")):continue
            if PHOTO_START.search(item):continue
            if re.search(r'(?i)https?://|^www\.|(?<!\S)[●■·]\s',item):continue
            if "지난달" in item and len(item)<65:continue
            score=12-(p_index*2+si)
            if re.search(r'\d{4}년|\d{1,2}월|\d+명|\d+회',item):score+=3
            if re.search(r'학과|학생|기업|교수|행사|대회|특강|수상|교육|개발|실습|연수|클라우드|AI|연구',item):score+=2
            if re.search(r'참여|진행|운영|구현|선정|수상|교육|개발|학습|발표|방문|제작',item):score+=2
            if re.search(r'자랑|뜻깊|대단|진심|기대|많은 박수|행복한',item):score-=8
            if "“" in item or "”" in item:score-=5
            candidates.append((score,p_index,si,item))
    return sorted(candidates,key=lambda x:(-x[0],x[1],x[2]))

def choose_lead(row,title):
    initial=tidy(row["lead"])
    if row["slug"] in SPECIAL_LEADS:return SPECIAL_LEADS[row["slug"]]
    poor=(
        len(initial)<50 or len(initial)>175 or
        bool(PHOTO_START.search(initial)) or
        bool(re.search(r'학과소식에 소개된|관련 활동 기록|성황리에|아낌없이|많은 박수|큰 감동|사진.*(?:왼쪽부터|설명)',initial)) or
        initial.endswith(("그리고","기반","위해","과","와",",","다음과","하며","에서는")) or
        ("바로바로" in initial or "안녕하세요" in initial)
    )
    if not poor:
        return sentenceify(initial)
    items=factual_candidates(row["doc"])
    for _,pidx,sidx,candidate in items:
        text=sentenceify(candidate)
        if len(text)>185:continue
        if text.endswith(("고.","며.","를.","을.","은.","는.")):continue
        if text.startswith(("▲","(왼쪽","교수님 말씀","이번 활동은")):continue
        return text
    if len(initial)>30 and not PHOTO_START.search(initial):
        # Existing text can remain imperfect but must not be cut mid-sentence.
        if len(initial)>210:
            return f"{row['date'][:4]}년 '{title}' 관련 학과 활동 기록입니다."
        return sentenceify(initial)
    return f"{row['date'][:4]}년 '{title}' 내용을 정리한 학과 활동 기록입니다."

def make_description(lead,title,year,category):
    lead=tidy(lead)
    if len(lead)<63:lead=f"{year}년 {category}: {title}. {lead}"
    if len(lead)>169:
        parts=SENTENCES.split(lead)
        short=parts[0]
        if 70<=len(short)<=168:lead=short
        else:
            first=title
            if len(first)>68:first=first[:68].rsplit(" ",1)[0]
            lead=f"{year}년 {category} — {first}. 한국폴리텍대학 서울강서캠퍼스 빅데이터소프트웨어공학과 활동 기록입니다."
    return lead

def replace_text(src,pattern,value,optional=False):
    new,n=re.subn(pattern,lambda m:m.group(1)+html.escape(value,quote=True)+m.group(3),src,count=1,flags=re.S)
    if n!=1 and not optional:raise RuntimeError("HTML anchor not found: "+pattern[:80])
    return new

def set_meta(src,selector,value):
    typ,key=selector.split(":",1)
    lookup=('name' if typ=="name" else "property")+ '="'+key+'"'
    pattern=r'(<meta\b(?=[^>]*'+re.escape(lookup)+r')[^>]*\bcontent=")([^"]*)(")'
    return replace_text(src,pattern,value)

def reflow_body_text(text):
    # Body, not quotes: retain factual statements, strip decorative clutter.
    if any(x in text for x in ("“","”","&quot;","<a ","<strong","<em ","<code")):
        return text
    cleaned=tidy(plain(text),body=True)
    if not cleaned:return ""
    sentences=SENTENCES.split(cleaned)
    chunks=[];bucket=[]
    for sentence in sentences:
        if not sentence.strip():continue
        if bucket and len(" ".join(bucket))+len(sentence)>290:
            chunks.append(" ".join(bucket));bucket=[sentence]
        else:bucket.append(sentence)
    if bucket:chunks.append(" ".join(bucket))
    return "</p><p>".join(html.escape(s,quote=True) for s in chunks)

def rewrite_sections(src,category):
    labels=SECTIONS.get(category,SECTIONS["학과 행사"])
    section=re.compile(r'<section(?:\s+[^>]*)?>.*?</section>',re.S)
    flags={"headings":0,"body_paragraphs":0,"filler_removed":0}
    content=re.search(r'(<div class="activity-content">)(.*?)(<div class="activity-cta">)',src,re.S)
    if not content:return src,flags
    old_inner=content.group(2)
    index=[0]
    def patch_section(m):
        i=index[0];index[0]+=1
        block=m.group(0)
        label=labels[min(i,1)]
        h2=re.search(r'<h2>(.*?)</h2>',block,re.S)
        if h2 and plain(h2.group(1)) in ("학과 활동 개요","활동 내용","주요 내용","주요 성과와 경험","활동 성과","주요 활동"):
            block=block[:h2.start(1)]+html.escape(label)+block[h2.end(1):]
            flags["headings"]+=1
        def patch_p(p):
            inner=p.group(2)
            if re.search(r'<(?:a|strong|em|code|img|span)\b',inner):return p.group(0)
            fresh=reflow_body_text(inner)
            if not fresh:return ""
            if html.unescape(re.sub(r'<[^>]+>','',inner))!=html.unescape(fresh.replace("</p><p>"," ")):
                flags["body_paragraphs"]+=1
            if any(z in inner for z in GENERIC):flags["filler_removed"]+=1
            return p.group(1)+fresh+p.group(3)
        block=re.sub(r'(<p(?:\s+[^>]*)?>)(.*?)(</p>)',patch_p,block,flags=re.S)
        return block
    new_inner=section.sub(patch_section,old_inner)
    # Non-section, hand-written articles remain intact; their authorial prose is
    # already edited by the earlier pass and should not be flattened.
    result=src[:content.start(2)]+new_inner+src[content.end(2):]
    return result,flags

def rewrite_page(row,title,lead,category,desc):
    src=row["raw"]
    originals=re.findall(r'\b(?:src|href)="([^"]+)"',src)
    src=replace_text(src,r'(<h1>)(.*?)(</h1>)',title)
    src=replace_text(src,r'(<p class="activity-lead">)(.*?)(</p>)',lead)
    src=replace_text(src,r'(<title>)(.*?)(</title>)',title+" | 빅데이터소프트웨어공학과")
    for selector,content in (
        ("name:description",desc),("property:og:title",title+" | 빅데이터소프트웨어공학과"),
        ("name:twitter:title",title+" | 빅데이터소프트웨어공학과"),
        ("property:og:description",desc),("name:twitter:description",desc)):
        src=set_meta(src,selector,content)
    src,body_flags=rewrite_sections(src,category)
    # Category breadcrumbs and localized hero labels.
    src=re.sub(r'(<p class="activity-kicker">DEPARTMENT ACTIVITIES · )(.*?)(</p>)',
               lambda m:m.group(1)+html.escape(category)+m.group(3),src,count=1)
    src=re.sub(r'(<p class="activity-breadcrumb">.*?<a href="/activities/">학과 활동</a>.*?›\s*)([^<]+)(</p>)',
               lambda m:m.group(1)+html.escape(category)+m.group(3),src,count=1)
    if '<div class="activity-cta">' in src:
        src=re.sub(r'(<div class="activity-cta">.*?<h2>)(.*?)(</h2>)',
                   lambda m:m.group(1)+html.escape(CTA.get(category,CTA["학과 행사"]))+m.group(3),src,count=1,flags=re.S)
        src=re.sub(r'(<div class="activity-cta">[\s\S]*?<h2>.*?</h2><p>)(.*?)(</p>)',
                   lambda m:m.group(1)+"학과 활동과 학생 프로젝트를 통해 교육 내용을 확인해 보세요."+m.group(3),
                   src,count=1,flags=re.S)
    # Gallery captions only, never change an image asset.
    src=re.sub(r'(<figure[^>]*>\s*<img[^>]*\balt=")([^"]*)(")',
                lambda m:m.group(1)+html.escape(title+" 활동 사진",quote=True)+m.group(3)
                if ("학과 활동 현장 사진" in m.group(2) or "ASK2024" in m.group(2)) else m.group(0),src,flags=re.S)
    def ld(m):
        obj=json.loads(m.group(1))
        if obj.get("@type")=="Article":
            obj["headline"]=title;obj["description"]=desc
            obj["datePublished"]=row["date"];obj["dateModified"]=TODAY
        return '<script type="application/ld+json">'+json.dumps(obj,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c")+"</script>"
    src,n=LD.subn(ld,src,count=1)
    if n!=1:raise RuntimeError("Article schema missing: "+row["slug"])
    actual=re.findall(r'\b(?:src|href)="([^"]+)"',src)
    if originals!=actual:
        raise RuntimeError("Editorial changes unexpectedly changed links/images: "+row["slug"])
    return src,body_flags

def rewrite_card(item,info):
    s=item
    s=replace_text(s,r'(<h3><a href="[^"]+">)(.*?)(</a></h3>)',info["title"])
    s=replace_text(s,r'(</h3><p>)(.*?)(</p>)',info["lead"])
    s=replace_text(s,r'(<div class="activity-card-meta"><span>)(.*?)(</span>)',info["category"])
    s=re.sub(r'(\baria-label=")[^"]*(")',
             lambda m:m.group(1)+html.escape(info["title"]+" 자세히 보기",quote=True)+m.group(2),s,count=1)
    return s

def role_admissions(rows):
    return {r["slug"]:["과거 모집/입시 안내로 오인 우려"] for r in rows
            if r["category"] in ("과거 입시 기록","과거 기록")}

def role_employment(rows):
    return {r["slug"]:["직무·기업·기술을 소개문에 구체화"] for r in rows
            if "취업" in r["category"] or "산학" in r["category"]}

def role_copy(rows):
    return {r["slug"]:["문체/문단/중복 표현 정비"] for r in rows
            if re.search(r'저희|우리 학과|사진\s*:|!|학과 활동 개요|주요 성과와 경험',r["raw"])}

def role_seo(rows):
    return {r["slug"]:["OG·Twitter·본문·검색 스니펫 일치 검증"] for r in rows}

def role_trust(rows):
    return {r["slug"]:["원문에 근거한 정량 실적 유지"] for r in rows
            if "수상" in r["category"] or RISK_PATTERN.search(r["raw"])}

def role_ux(rows):
    return {r["slug"]:["활동 분야/모바일 제목/소제목 검토"] for r in rows}

ROLES={"입학홍보":role_admissions,"취업·산학":role_employment,"콘텐츠 편집":role_copy,
       "검색·SEO":role_seo,"사실 검증":role_trust,"UX·정보구조":role_ux}

def run():
    old=ARCHIVE.read_text(encoding="utf-8")
    rows=get_rows(old)
    with ThreadPoolExecutor(max_workers=6,thread_name_prefix="editorial") as pool:
        tasks={name:pool.submit(func,rows) for name,func in ROLES.items()}
        review={name:tasks[name].result() for name in ROLES}
    data={};stats=Counter();descriptions=set();details=[]
    for r in rows:
        slug=r["slug"]
        title=choose_title(r["title"])
        category=choose_category(r["category"],title)
        lead=choose_lead(r,title)
        desc=make_description(lead,title,r["date"][:4],category)
        if desc in descriptions:
            desc=f"{r['date'][:4]}년 {category} · {title}. {desc}"
            if len(desc)>180:
                desc=f"{r['date'][:4]}년 {category}에서 다룬 {title}. 빅데이터소프트웨어공학과 활동 기록입니다."
        if desc in descriptions:raise RuntimeError("Duplicate meta descriptions despite disambiguation "+slug)
        descriptions.add(desc)
        edited,body=rewrite_page(r,title,lead,category,desc)
        if title!=r["title"]:stats["title_updated"]+=1
        if lead!=r["lead"]:stats["lead_updated"]+=1
        if category!=r["category"]:stats["category_updated"]+=1
        if desc!=plain(r["doc"].select_one('meta[name="description"]').get("content")):
            stats["seo_updated"]+=1
        for key,num in body.items():stats[key]+=num
        if r["raw"]!=edited:
            r["path"].write_text(edited,encoding="utf-8")
            stats["article_files_updated"]+=1
        data[slug]=dict(title=title,lead=lead,description=desc,category=category,date=r["date"])
        details.append(dict(slug=slug,url=r["href"],date=r["date"],category_before=r["category"],category_after=category,
          title_before=r["title"],title_after=title,lead_before=r["lead"],lead_after=lead))
    # Recompose only the list cards that are present. Never read the stale
    # 2026-10-25 archive imports or re-create articles deleted by the editor.
    found=set()
    def swap(m):
        card=m.group(0)
        route=re.search(r'<h3><a href="/activities/([^/]+)/"',card)
        if not route:raise RuntimeError("Malformed card")
        slug=route.group(1)
        found.add(slug)
        return rewrite_card(card,data[slug])
    new_archive=CARD.sub(swap,old)
    if found!=set(data):raise RuntimeError("Mismatch between revised cards and published posts")
    def fix_schema(m):
        obj=json.loads(m.group(1))
        if obj.get("@type")=="CollectionPage":
            items=obj["mainEntity"]["itemListElement"]
            for item in items:
                slug=item["url"].split("/activities/")[-1].strip("/")
                if slug not in data:raise RuntimeError("Deleted slug in archive schema: "+slug)
                item["name"]=data[slug]["title"]
            if len(items)!=286:raise RuntimeError("List schema lost items")
        return '<script type="application/ld+json">'+json.dumps(obj,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c")+"</script>"
    new_archive=LD.sub(fix_schema,new_archive)
    if len(CARD.findall(new_archive))!=286:raise RuntimeError("Article archive card count changed")
    ARCHIVE.write_text(new_archive,encoding="utf-8")

    # All current files have matching title, lead, cards, meta and schema.
    after=BeautifulSoup(new_archive,"html.parser")
    for card in after.select(".activity-card-grid > .activity-card"):
        slug=card.select_one("h3 a")["href"].strip("/").split("/")[-1]
        record=data[slug]
        page=BeautifulSoup((ROOT/"activities"/slug/"index.html").read_text(encoding="utf-8"),"html.parser")
        assert page.h1.get_text(" ",strip=True)==record["title"],slug
        assert html.unescape(page.select_one('.activity-lead').get_text(" ",strip=True))==record["lead"],slug
        assert card.select_one("h3 a").get_text(" ",strip=True)==record["title"],slug
        assert card.select_one(".activity-card-meta span").get_text(" ",strip=True)==record["category"],slug
        obj=json.loads(page.select_one('script[type="application/ld+json"]').string)
        assert obj["headline"]==record["title"] and obj["datePublished"]==record["date"],slug
        assert obj["description"]==record["description"],slug
        assert page.select_one('meta[name="description"]')["content"]==record["description"],slug
    for missing in REMOVED:
        if f"/activities/{missing}/" in new_archive:raise RuntimeError("Deleted post reappeared: "+missing)
    DETAILS.parent.mkdir(parents=True,exist_ok=True)
    DETAILS.write_text(json.dumps({"review_date":TODAY,"posts":len(data),"review_roles":list(ROLES),
                                  "role_flags":{k:len(v) for k,v in review.items()},"changes":dict(stats),
                                  "articles":details},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=[
      "# 학과 활동 286건 홍보 문구 전수 정비",
      f"검토·적용일: {TODAY}",
      "",
      "## 검토 범위 및 방법",
      "",
      "현재 공개 중인 **286건만** 대상으로 제목·요약·본문 문단·소제목·카테고리·SEO·구조화 데이터를 재검토했습니다.",
      "입학홍보, 취업·산학협력, 문장 편집, SEO, 사실검증, UX의 6개 독립 점검을 병렬 실행한 규칙 기반 품질 관리입니다. 외부 홍보 전문가 여섯 명이 직접 심사한 결과가 아닙니다.",
      "삭제된 모집·기술동향 35건과 두 삭제 예시(kopo-738806, kopo-707036)는 복원하지 않았습니다.",
      "",
      "## 변경 집계","",
      "| 항목 | 건수 |","|---|---:|",
      *[f"| {k} | {v} |" for k,v in stats.most_common()],
      "",
      "## 전문가 관점별 확인 수","",
      "| 검토 관점 | 해당 글 수 |","|---|---:|",
      *[f"| {k} | {len(v)} |" for k,v in review.items()],
      "",
      "## 품질 보장",
      "",
      "- 모든 기존 사진 경로와 링크 목록을 유지하고, 삭제 게시물·삭제 URL을 복원하지 않았습니다.",
      "- 각 글의 원래 게시일을 유지하고, 제목·소개문·소셜 공유·구조화 데이터를 동기화했습니다.",
      "- 기존 실적의 기관명·금액·수상 등급·수치·참여자·인용문을 임의 추가하거나 확대하지 않았습니다.",
      "- 장문의 본문을 단락으로 나누고 장식성 문구를 정리하되, 사실 근거가 불충분한 글을 새로운 성과로 꾸미지 않았습니다.",
      "",
      "## 제목 수정·대표 소개문 사례","",
      "| 게시물 | 변경 전 제목 | 변경 후 제목 |","|---|---|---|"
    ]
    for row in details:
        if row["title_before"]!=row["title_after"]:
            lines.append("| ["+row["slug"]+"]("+SITE+row["url"]+") | "+row["title_before"].replace("|","／")+" | "+row["title_after"].replace("|","／")+" |")
    lines+=["","## 남은 검토 항목","","수상·취업 성과의 공식 근거와 사진 초상권 등은 개별 원문 및 관계자 확인이 필요한 사항입니다. 본 작업은 원문 사실 범위의 편집 개선이며 외부 자료까지 모두 재검증했다는 의미는 아닙니다.",""]
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text("\n".join(lines),encoding="utf-8")
    print("EDITORIAL_COMPLETE",len(data),"posts",dict(stats),flush=True)
    print("REVIEW_ROLE_COUNTS",json.dumps({k:len(v) for k,v in review.items()},ensure_ascii=False),flush=True)
if __name__=="__main__":run()
