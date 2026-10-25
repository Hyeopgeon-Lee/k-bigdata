#!/usr/bin/env python3
"""Conservative, source-grounded first editorial revision of 321 activity articles.

No LLM rewriting and no invented results. Editorial changes are generated only
from existing posted facts or verified context in the article. Keep all URLs,
image src, CTA links, technical facts, people and award claims unchanged.
"""
from __future__ import annotations
import re,json,html,datetime
from collections import Counter
from pathlib import Path
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
ARCH=ROOT/"activities"/"index.html"
REPORT=ROOT/"reports"/"activity_promotion_edits_2026-10-25.md"
AUDIT=ROOT/"data"/"activity_promotion_edits_2026-10-25.json"
KST=datetime.timezone(datetime.timedelta(hours=9))
DATE=datetime.datetime.now(KST).date().isoformat()
SITE="https://ai.k-bigdata.kr"
GENERIC="이번 활동은 학교에서 학습한 기술과 실제 현장의 경험을 연결하는 학과 프로그램으로 운영되었습니다."
GENERIC_SNIPPET="활동의 현장과 주요 내용을 소개합니다"
STOP_PHRASES=("안녕하세요.","감사합니다.","많은 관심과 응원 부탁드립니다","축하를 보냅니다")
TITLE_FIX={
 "kopo-445213":"소프트웨어 개발 기술 읽을거리, POPIT 소개",
 "kopo-443897":"2016 Dream Job 페스티벌, 빅데이터 진로체험 운영",
 "kopo-450187":"빅데이터 동향과 이슈 제25호 참고자료",
 "kopo-451147":"2017 디자인 씽킹·소프트웨어 미래 콘퍼런스 안내",
 "kopo-450315":"2017 강서구 SNS 톡톡 기자단 모집 안내(종료)",
 "kopo-746968":"선후배 Java 멘토링, 반복문 실습 진행",
 "kopo-752596":"2학년 선배가 지도한 Spring Boot·MyBatis 개발 실습",
 "kopo-745968":"작곡가 박해운 초청 특강, 한류와 데이터 융합",
 "kopo-527126":"2019 ICNCT 국제학술대회, 학과 교수진 논문 발표",
 "kopo-448025":"강서구청, 학과 봉사활동 감사장 전달",
 "kopo-450160":"HTML5 기반 스마트 TV 플랫폼 표준 자료 소개",
 "kopo-451148":"정보기술 국제표준(JTC1) 동향 참고자료",
}
TECH_RE=re.compile(r"(동향|세계표준|참고자료|기술자료|플랫폼 표준|자료 공유|월간 빅데이터|컴퍼런스 URL|^http|^BigData Monthly)",re.I)
CATEGORY_RULES=[
 ("과거 모집·행사 안내",r"모집|접수|원서|마감|기간\s*안내|입시\s*설명회"),
 ("수상·성과",r"수상|우수논문상|대상\s*수상|최우수상|전국\s*[12]등|감사장|대회\s*1위|1등\s*달성|상금"),
 ("연구·학술",r"학술|논문\s*발표|국제\s*학술대회|연구성과|공동\s*연구"),
 ("교원 연수",r"교사.*연수|교원.*연수|직무연수|교사\s*대상"),
 ("현직자·전문가 특강",r"특강|강연|초청\s*강의|현직자"),
 ("선후배 멘토링",r"멘토|선배.*후배|졸업생.*진로"),
 ("진로체험",r"진로체험|중학교|고등학생.*체험|Dream Job|꿈드림|박람회\s*체험|체험부스"),
 ("사회공헌·봉사",r"봉사|재능기부|나눔|기부"),
 ("산학협력",r"협약|MOU|산학협력|기업\s*방문|기술지도"),
 ("취업·진로",r"취업|기업\s*탐방|채용|기업\s*설명회"),
 ("학생 프로젝트",r"졸업\s*작품|졸업작품|프로젝트|작품발표|해커톤"),
 ("지역사회 교육",r"지역사회|시민.*교육|일반인.*실습|컴퓨터\s*교육"),
]
PINNED={
 "kopo-738804": "제목의 ASK2024와 본문 ACK 2024 불일치: 수상 이력을 공식 자료로 대조할 것",
 "kopo-738801": "제목의 ASK2024와 본문 ACK 2024 불일치: 수상 이력을 공식 자료로 대조할 것"
}
def plain(v):
    return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]*>","",v or ""))).strip()
def htmltext(v):
    return html.escape(v,quote=True)
def meta_replace(source,selector,value,tag="meta",attr="content"):
    # Simple regex to preserve the existing site's hand-authored HTML layout.
    if selector.startswith("name:"):
        key=f'name="{selector[5:]}"'
    else:
        key=f'property="{selector[9:]}"'
    pattern=r'(<'+tag+r'\b(?=[^>]*'+re.escape(key)+r')[^>]*\b'+attr+r'=")([^"]*)(")'
    result,count=re.subn(pattern,lambda m:m.group(1)+htmltext(value)+m.group(3),source,count=1,flags=re.S)
    if count!=1:
        raise RuntimeError("Metadata not found: "+selector)
    return result

def markup_replace(src,regex,val,required=True):
    r,n=re.subn(regex,lambda m:m.group(1)+htmltext(val)+m.group(3),src,count=1,flags=re.S)
    if required and n!=1:raise RuntimeError("Markup update location not unique: "+regex)
    return r

def clean_title(original,slug):
    if slug in TITLE_FIX:return TITLE_FIX[slug]
    t=original
    t=re.sub(r"^\s*\[축\]\s*","",t)
    t=t.replace("Dradm Job","Dream Job").replace("트렌트 '디자인 씽킹'","트렌드 '디자인 씽킹'")
    t=re.sub(r"[\U0001F300-\U0001FAFF\U00002600-\U000027BF]","",t)
    t=re.sub(r"\s+"," ",t).strip(" \t!♪🎉")
    if len(t)>66 and t.startswith("빅데이터소프트웨어공학과 "):
        t=t[len("빅데이터소프트웨어공학과 "):]
    return t

def clean_summary_text(s):
    s=s.replace(GENERIC_SNIPPET,"").strip(" \t.,。！·–-")
    s=re.sub(r"\s*\|\s*원문\s*게시번호\s*\d+","",s)
    s=re.sub(r"^\s*(?:출처\s*:\s*|\*\s*출처\s*:\s*)https?://\S+\s*","",s)
    s=re.sub(r"^[▲▽▶❯]+\s*","",s)
    s=re.sub(r"^\s*안녕하세요[.!]?\s*","",s)
    s=re.sub(r"\s+"," ",s).strip()
    return s

def safe_intro(row,title):
    lead=clean_summary_text(row["lead"])
    if lead and len(lead)>=53 and not lead.startswith(("http","출처","▲")):
        return lead[:180].strip()
    body=BeautifulSoup(row["html"],"html.parser").select_one(".activity-content")
    candidates=[]
    if body:
        for node in body.select("section p"):
            t=clean_summary_text(node.get_text(" ",strip=True))
            if GENERIC in t or not t:continue
            for sent in re.split(r"(?<=[.!?。])\s+",t):
                sent=sent.strip()
                if len(sent)>45 and not sent.startswith(("출처","http","*","▲","안녕하세요","감사","이번 활동은","많은 관심")):
                    candidates.append(sent)
                    break
    for candidate in candidates:
        if "원문" in candidate and "게시판" in candidate:continue
        if len(candidate)>170:
            piece=candidate[:170]
            for char in ("다.","습니다.","했","다.",", "," "):
                i=piece.rfind(char,65)
                if i>60:return piece[:i+len(char)].strip()
            return piece.rsplit(" ",1)[0].strip()
        return candidate
    y=row["date"][:4]
    if any(x in title for x in ("모집","접수","설명회","공모전 안내","신청")):
        return f"{y}년 당시 학과 게시판에 안내된 {title} 관련 과거 기록입니다. 현재 신청 기간은 종료되었습니다."
    if TECH_RE.search(title):
        return f"{y}년 학과 게시판에 공유한 {title} 관련 기술·학습 참고자료입니다."
    return f"{y}년 학과소식에 소개된 '{title}' 관련 활동 기록입니다."

def desc_from(lead,title):
    d=clean_summary_text(lead)
    if len(d)<60:
        d=f"{title}. {d}"
    if len(d)>155:
        text=d[:156].rsplit(" ",1)[0]
        d=text if len(text)>90 else d[:150]
    return d.strip()

def category(title,old,date):
    if old not in ("학과 활동","과거 입시 기록"):return old
    if TECH_RE.search(title):return "기술·참고자료"
    if old=="과거 입시 기록":return old
    for label,regex in CATEGORY_RULES:
        if re.search(regex,title,re.I):return label
    return "학과 행사"

def promo_cta(tag):
    if any(x in tag for x in ("수상","성과","학생 프로젝트","연구","학술")):
        return "학생 프로젝트와 연구 성과 살펴보기"
    if any(x in tag for x in ("특강","취업","멘토링","진로")):
        return "현장 경험과 취업 준비를 연결하는 교육"
    if any(x in tag for x in ("진로체험","지역사회","교원 연수")):
        return "AI·데이터를 직접 경험하는 교육"
    if any(x in tag for x in ("기술·참고자료","과거 모집")):
        return "현재 운영하는 교육과정 살펴보기"
    return None

def source_rows():
    archive=ARCH.read_text(encoding="utf-8")
    soup=BeautifulSoup(archive,"html.parser")
    rows=[]
    for node in soup.select(".activity-card-grid > .activity-card"):
        a=node.select_one("h3 a")
        slug=a.get("href","").strip("/").split("/")[-1]
        item=ROOT/"activities"/slug/"index.html"
        if not item.is_file():raise RuntimeError("Missing detail: "+slug)
        raw=item.read_text(encoding="utf-8")
        parsed=BeautifulSoup(raw,"html.parser")
        time=node.select_one("time")
        meta=node.select_one(".activity-card-meta span")
        rows.append(dict(slug=slug,href=a["href"],date=time["datetime"],title=plain(a.get_text(" ",strip=True)),
           lead=plain(node.select_one(".activity-card-body > p").get_text(" ",strip=True)) if node.select_one(".activity-card-body > p") else "",
           tag=plain(meta.get_text(" ",strip=True)) if meta else "",
           raw=raw,html=raw,body=plain(parsed.select_one(".activity-content").get_text(" ",strip=True)) if parsed.select_one(".activity-content") else ""))
    if len(rows)!=321:raise RuntimeError("Unexpected article count")
    return archive,rows

def update_article(row,new_title,new_lead,new_tag,description):
    src=row["raw"]
    old_title=row["title"]
    src=markup_replace(src,r'(<h1>)(.*?)(</h1>)',new_title)
    src=markup_replace(src,r'(<title>)(.*?)(</title>)',new_title+" | 빅데이터소프트웨어공학과")
    src=meta_replace(src,"name:description",description)
    for key in ("property:og:title","name:twitter:title"):
        src=meta_replace(src,key,new_title+" | 빅데이터소프트웨어공학과")
    for key in ("property:og:description","name:twitter:description"):
        src=meta_replace(src,key,description)
    lead_pattern=r'(<p class="activity-lead">)(.*?)(</p>)'
    src=markup_replace(src,lead_pattern,new_lead)
    src=src.replace(GENERIC,"")
    # Do not leave an empty templated "achievements" section.
    src=re.sub(r'<section><h2>(?:주요 내용|주요 성과와 경험|활동 성과)</h2><p>\s*</p></section>',"",src)
    # Previously all source articles got a migration-day publication date.
    def schema_fix(m):
        obj=json.loads(m.group(1))
        if obj.get("@type")=="Article":
            obj["headline"]=new_title
            obj["description"]=description
            obj["datePublished"]=row["date"]
            obj["dateModified"]=DATE
        return '<script type="application/ld+json">'+json.dumps(obj,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c")+'</script>'
    src,n=re.subn(r'<script type="application/ld\+json">(.*?)</script>',schema_fix,src,flags=re.S)
    if n!=1:raise RuntimeError("Missing Article structured data "+row["slug"])
    # Keep the original article title / date visible only as historical provenance.
    if row["date"]<"2026-01-01" and any(x in old_title+" "+row["body"] for x in ("모집","접수","지원자","마감","신청하","오는 2016","오는 2017")):
        if 'class="historical-content-note"' not in src:
            note=(f'<p class="historical-content-note">과거 게시물 안내: 이 글은 {row["date"]}에 등록된 기록입니다. '
                  '당시 모집·신청·행사 일정은 현재 유효하지 않을 수 있습니다. 최신 일정은 현재 입학안내를 확인해 주세요.</p>')
            anchor='<div class="activity-cta">'
            if anchor not in src:raise RuntimeError("Activity CTA missing")
            src=src.replace(anchor,note+anchor,1)
    # Old archives often use totally generic CTA headlines; make it relevant.
    cta=promo_cta(new_tag)
    if cta:
        src=re.sub(r'(<div class="activity-cta">[\s\S]*?<h2>)(.*?)(</h2>)',lambda m:m.group(1)+htmltext(cta)+m.group(3),src,count=1)
    # One historical article wrongly asks readers to attend a 2016 event in the future.
    if row["slug"]=="kopo-443897":
        src=src.replace("빅데이터에 관심이 있지만 Dream Job페스티벌에 참가하지 못한 분들께서는 오는 2016년 11월 3일에 일산 킨텍스에서 열리는 폴리텍엑스포에 참가하셔서 빅데이터와 활용방안에 대해 설명을 들으실수 있습니다.",
        "원문에는 당시 개최 예정이었던 2016년 폴리텍엑스포 안내도 함께 실렸습니다. 현재 적용되는 일정 안내는 아닙니다.")
    # Give the user an accurate published date in the social previews as well.
    if '<meta property="article:published_time"' not in src:
        src=src.replace('<meta property="og:type" content="article">','<meta property="og:type" content="article"><meta property="article:published_time" content="'+row["date"]+'">',1)
    return src

def apply():
    old_archive,rows=source_rows()
    changed=[];made=Counter()
    rewrites={}
    reports=[]
    descriptions_seen=set()
    for row in rows:
        slug=row["slug"]
        title=clean_title(row["title"],slug)
        lead=safe_intro(row,title)
        snippet=desc_from(lead,title)
        if snippet in descriptions_seen:
            snippet=snippet[:105].rstrip(" .,") + " · " + title[:48] + " (" + row["date"] + ")"
        if snippet in descriptions_seen:
            snippet=snippet[:145] + " · 학과소식 " + slug.split("-")[-1]
        descriptions_seen.add(snippet)
        category_name=category(title,row["tag"],row["date"])
        output=update_article(row,title,lead,category_name,snippet)
        if output!=row["raw"]:
            images=re.findall(r'\b(?:src|href)="([^"]+)"',row["raw"])
            after_images=re.findall(r'\b(?:src|href)="([^"]+)"',output)
            if images!=after_images:raise RuntimeError(f"Media or URL mismatch in {slug}")
            file=ROOT/"activities"/slug/"index.html"
            file.write_text(output,encoding="utf-8")
            changed.append(slug)
        if title!=row["title"]:made["titles"]+=1
        if lead!=row["lead"]:made["lead"]+=1
        if category_name!=row["tag"]:made["category"]+=1
        if GENERIC in row["raw"]:made["generic_removed"]+=1
        if "원문 게시번호" in row["raw"]:made["seo_number_removed"]+=1
        rewrites[slug]=dict(title=title,lead=lead,description=snippet,category=category_name,date=row["date"])
        reports.append(dict(slug=slug,date=row["date"],before_title=row["title"],after_title=title,
          before_lead=row["lead"],after_lead=lead,old_category=row["tag"],category=category_name))
    # Update archive list cards and ItemList schema using same single source of truth.
    card=re.compile(r'<article class="activity-card">.*?</article>',re.S)
    seen=set()
    def fix_card(m):
        text=m.group(0)
        match=re.search(r'<h3><a href="/activities/([^/]+)/"',text)
        if not match:return text
        slug=match.group(1)
        v=rewrites[slug]
        seen.add(slug)
        text=re.sub(r'(<h3><a href="[^"]+">)(.*?)(</a></h3>)',
                    lambda x:x.group(1)+htmltext(v["title"])+x.group(3),text,count=1,flags=re.S)
        text=re.sub(r'(<h3>[\s\S]*?</h3><p>)(.*?)(</p>)',
                    lambda x:x.group(1)+htmltext(v["lead"])+x.group(3),text,count=1,flags=re.S)
        text=re.sub(r'(<div class="activity-card-meta"><span>)(.*?)(</span>)',
                    lambda x:x.group(1)+htmltext(v["category"])+x.group(3),text,count=1,flags=re.S)
        text=re.sub(r'(\baria-label=")([^"]*)(")',
                    lambda x:x.group(1)+htmltext(v["title"]+" 자세히 보기")+x.group(3),text,count=1)
        return text
    archive=card.sub(fix_card,old_archive)
    if len(seen)!=321:raise RuntimeError("Card update was incomplete")
    def update_schema(m):
        obj=json.loads(m.group(1))
        if obj.get("@type")!="CollectionPage":return m.group(0)
        items=obj["mainEntity"]["itemListElement"]
        for item in items:
            slug=item["url"].split("/activities/")[1].strip("/")
            item["name"]=rewrites[slug]["title"]
        return '<script type="application/ld+json">'+json.dumps(obj,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c")+'</script>'
    archive,n=re.subn(r'<script type="application/ld\+json">(.*?)</script>',update_schema,archive,flags=re.S)
    if n!=1:raise RuntimeError("Archive structured data update failed")
    # Preserve card counts/dates/original URLs.
    if len(card.findall(archive))!=321:raise RuntimeError("Archive lost an item")
    for slug in rewrites:
        path=f"/activities/{slug}/"
        if path not in archive:raise RuntimeError("Missing archive link "+slug)
    ARCH.write_text(archive,encoding="utf-8")
    AUDIT.parent.mkdir(parents=True,exist_ok=True)
    AUDIT.write_text(json.dumps({"asof":DATE,"changed":len(changed),"counts":made,
      "flagged_for_source_check":PINNED,"articles":reports},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=["# 학과 활동 홍보용 1차 정비 결과",f"검토/수정일: {DATE}","","게시글 **321건**의 제목·리드·내용·메타정보를 비교 검토했습니다.",
      "진실성·출처 확인을 우선으로 하며, 본문 사실·수상 등급·사진·URL은 변경하지 않았습니다.",
      "","## 일괄 반영 결과","",
      f"- 수정 HTML: {len(changed)}건",
      f"- 제목 정비: {made['titles']}건",
      f"- 소개문 정비: {made['lead']}건",
      f"- 카테고리 개선: {made['category']}건",
      f"- 상투적 결론 문구 제거: {made['generic_removed']}건",
      f"- 검색 설명의 내부 게시번호 제거: {made['seo_number_removed']}건",
      "- Article 게시일: 카드에 표시된 공식 과거 게시일로 일치",
      "- 과거 모집/신청 기록: 유효기간 오해 방지 안내 추가",
      "- 수상 행사명·등급 등 충돌 사안은 조작하지 않고 별도 검증 필요","",
      "## 수정 전후 제목 사례","",
      "| 글 | 수정 전 | 수정 후 |","|---|---|---|"]
    for row in reports:
        if row["before_title"]!=row["after_title"]:
            lines.append(f"| {row['slug']} | {row['before_title'].replace('|','／')} | {row['after_title'].replace('|','／')} |")
    lines+=["","## 추가 사실검증이 필요한 건",""]
    for slug,reason in PINNED.items():lines.append(f"- [/{slug}](https://ai.k-bigdata.kr/activities/{slug}/): {reason}")
    lines+=["","## 범위와 한계","",
      "규칙 기반 안전한 편집으로 반복 표현·메타데이터 오류를 우선 교정했습니다. 기사체 문장별 교열과 원본 자료 대조, 사진의 인물·초상권 검수까지 완료했다는 의미는 아닙니다.",
      "입학홍보 우선 페이지(최근 수상·채용·교육·산학협력)와 오래된 외부자료는 수동 확인 후 2차 수정이 필요합니다.",""]
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text("\n".join(lines),encoding="utf-8")
    print("PROMOTION_EDITS",len(changed),"articles",dict(made),"publishDates",len(rows),flush=True)
    print("FLAGGED_CLAIMS",list(PINNED),flush=True)

PINNED={"kopo-738804":"원문 및 게시글에서 ASK2024·ACK2024 행사명 상충","kopo-738801":"원문 및 게시글에서 ASK2024·ACK2024 행사명 상충"}
if __name__=="__main__":apply()
