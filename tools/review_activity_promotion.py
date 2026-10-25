#!/usr/bin/env python3
"""Six independent editorial lenses over every public activity article.

The six reviewers run in parallel; these are transparent deterministic audits,
not claims of six human or generative-AI experts. Each reads all actual title,
body, excerpt, SEO metadata and visual evidence references.
"""
from __future__ import annotations
import json,re,html,datetime
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
ARCH=ROOT/"activities"/"index.html"
OUT=ROOT/"reports"/"activity_promotion_review_2026-10-25.md"
JSON=ROOT/"data"/"activity_promotion_audit_2026-10-25.json"
ASOF=datetime.date(2026,10,25)
GENERICS=("활동의 현장과 주요 내용을 소개합니다","이번 활동은 학교에서 학습한 기술과 실제 현장의 경험을 연결하는 학과 프로그램으로 운영되었습니다","이번 활동은 학교에서 학습한 기술")
PROMO=("자랑스러운","당당히","뜻깊은","큰 박수","많은 응원","성공적으로","보람찬","많은 관심")
LEGACY=("빅데이터소프트웨어과","빅데이터과","데이터분석과")
UNVERIFIED=(r"\b100%\b",r"전원\s*취업",r"무조건\s*취업",r"취업\s*보장")
LEADS=("모집","접수","신청","지원자","마감","채용","원서","설명회","컨퍼런스")
SOURCE_ID=re.compile(r"^kopo-(\d+)$")
def clean(t): return re.sub(r"\s+"," ",html.unescape(str(t or ""))).strip()
def issue(slug,expert,code,severity,detail,action): return dict(slug=slug,expert=expert,code=code,severity=severity,detail=detail,action=action)
def records():
    soup=BeautifulSoup(ARCH.read_text(encoding="utf-8"),"html.parser")
    nodes=soup.select(".activity-card-grid > .activity-card")
    items=[]
    for n,node in enumerate(nodes,1):
        href=node.select_one("h3 a")
        if href is None:raise RuntimeError("Missing card link")
        uri=href.get("href","")
        slug=uri.strip("/").split("/")[-1]
        path=ROOT/"activities"/slug/"index.html"
        if not path.exists():raise RuntimeError(f"Missing linked detail page: {uri}")
        source=path.read_text(encoding="utf-8")
        detail=BeautifulSoup(source,"html.parser")
        published=node.select_one("time")
        if not published:raise RuntimeError(f"Date missing: {slug}")
        sections=detail.select(".activity-content > section")
        raw_sections=[{"heading":clean(e.select_one("h2").get_text(" ",strip=True) if e.select_one("h2") else ""),
                       "text":clean(e.get_text(" ",strip=True))} for e in sections]
        body=clean(" ".join(s["text"] for s in raw_sections))
        raw_article=detail.select_one(".activity-article")
        ld=detail.select_one('script[type="application/ld+json"]')
        schema=json.loads(ld.string) if ld and ld.string else {}
        def prop(select,attr="content"):
            e=detail.select_one(select)
            return clean(e.get(attr,"")) if e else ""
        d={"slug":slug,"url":uri,"date":published.get("datetime"),"year":int(published.get("datetime")[:4]),
           "tag":clean(node.select_one(".activity-card-meta span").get_text(" ",strip=True)) if node.select_one(".activity-card-meta span") else "",
           "card_title":clean(href.get_text(" ",strip=True)),
           "card_summary":clean(node.select_one(".activity-card-body > p").get_text(" ",strip=True)) if node.select_one(".activity-card-body > p") else "",
           "title":clean(detail.select_one("h1").get_text(" ",strip=True)) if detail.select_one("h1") else "",
           "lead":clean(detail.select_one(".activity-lead").get_text(" ",strip=True)) if detail.select_one(".activity-lead") else "",
           "body":body,"sections":raw_sections,"paragraphs":len(detail.select(".activity-content p")),
           "meta_description":prop('meta[name="description"]'),
           "og_title":prop('meta[property="og:title"]'),
           "schema_title":clean(schema.get("headline","")),
           "schema_date":clean(schema.get("datePublished","")),
           "og_image":prop('meta[property="og:image"]'),
           "canonical":prop('link[rel="canonical"]',"href"),
           "image_count":len(raw_article.select("figure img")) if raw_article else 0,
           "images":[dict(src=im.get("src"),alt=clean(im.get("alt",""))) for im in (raw_article.select("figure img") if raw_article else [])],
           "headings":[s["heading"] for s in raw_sections]}
        items.append(d)
    if len(items)!=321 or len({x["url"] for x in items})!=321:
        raise RuntimeError("Expected 321 distinct activity articles")
    return items

def reviewer_admissions(rows):
    out=[]
    for r in rows:
        sl=r["slug"];text=r["title"]+" "+r["lead"]+" "+r["body"]
        if r["year"]<2024 and any(k in text for k in LEADS) and not ("과거" in text or "당시" in text or "종료" in text):
            out.append(issue(sl,"입학홍보","obsolete_call", "high","과거 모집·참가 문구가 현재 안내처럼 보일 수 있음","원문 게시연도와 과거 기록 표시, 현행 입학안내 링크 분리"))
        if r["year"]<2026 and any(k in r["title"] for k in ("입시","수시","정시","원서")) and "과거" not in r["lead"]:
            out.append(issue(sl,"입학홍보","old_admission","high","이전 학년도 모집 게시물 안내 미흡","현재 입시 정보와 명확히 구분"))
        if not any(k in text for k in ("학생","실습","학습","진로","개발","교육","취업","프로젝트","연구","수상")) and len(r["body"])<130:
            out.append(issue(sl,"입학홍보","weak_value","medium","독자가 체감할 활동/교육 맥락 부족","확인된 사실이 없으면 자료실 성격으로 분류"))
    return out

def reviewer_career(rows):
    out=[]
    for r in rows:
        sl=r["slug"];topic=r["title"]+" "+r["body"]
        if any(k in r["title"] for k in ("취업","채용","현직자","기업","진로","멘토링")) and len(r["body"])<100:
            out.append(issue(sl,"취업·산학","thin_career","high","직무·멘토링 내용이 너무 짧음","원본에 기재된 기업·직무·실습 키워드로 보강"))
        if ("수상" in r["title"] or "대상" in r["title"]) and not any(k in topic for k in ("상","수상","대상","장려","금상","동상","최우수")):
            out.append(issue(sl,"취업·산학","award_claim","high","제목의 수상 주장과 본문 근거 불일치","상 이름·주최·수상자를 공식 글에서 재검증"))
        if "K-PaaS" in topic and "쿠버네티스" not in topic and "클라우드" not in topic:
            out.append(issue(sl,"취업·산학","thin_tech_context","low","독자에게 전문용어 맥락 부족","공식 근거로 용어 1문장 설명 추가 검토"))
    return out

def reviewer_writing(rows):
    out=[]
    for r in rows:
        sl=r["slug"];t=r["title"];body=r["body"];lead=r["lead"];summary=r["card_summary"]
        if any(p in body for p in GENERICS) or any(p in lead+" "+summary for p in GENERICS):
            out.append(issue(sl,"콘텐츠 편집","generic_copy","high","AI식 상투적·사실 불명확한 마무리/소개문","활동의 확인된 장소·참여 대상·기술·성과로 교체"))
        if len(t)>53:
            out.append(issue(sl,"콘텐츠 편집","title_long","medium",f"모바일에서 긴 제목 {len(t)}자","핵심 주체·행동·성과 중심 35~50자 권장"))
        if re.search(r"(?:\bhttps?://|^\[축\]|ㅎㅎ|ㅋㅋ|‼️|🇺🇸️|[🥇🎉✨])",t):
            out.append(issue(sl,"콘텐츠 편집","title_noise","medium","원시 URL·축하 표기·이모지가 제목에 혼입","중립적이고 검색 가능한 명사형 제목"))
        if len(lead)<50 or re.search(r"^(?:출처\s*:|\*?컨퍼런스 URL|▲|http)",lead):
            out.append(issue(sl,"콘텐츠 편집","weak_intro","high","첫 문단이 너무 짧거나 출처·이미지 설명으로 시작","원문 사실을 이용한 핵심정보 1~2문장 요약"))
        if len(body)<110:
            out.append(issue(sl,"콘텐츠 편집","thin_body","medium",f"본문 {len(body)}자","원문에 사실 없으면 억지로 늘리지 말고 기록형 콘텐츠로 처리"))
        if "교수님" in body or "선배님" in body or "저희" in body or "우리 학과" in body:
            out.append(issue(sl,"콘텐츠 편집","casual_style","low","기사체와 구어체·1인칭 혼용","존칭·감탄 최소화, 기관 홍보 기사체 정리"))
        if len(r["sections"])<2:
            out.append(issue(sl,"콘텐츠 편집","few_sections","low","독립 소제목 부족","확인된 사실에 따라 배경·활동·성과 구조"))
    return out

def reviewer_seo(rows):
    out=[]
    counts=Counter(x["title"] for x in rows)
    for r in rows:
        sl=r["slug"];d=r["date"];head=r["schema_date"]
        if head[:10]!=d:
            out.append(issue(sl,"SEO","incorrect_publish_date","high",f"원문 {d}, 구조화 데이터 발행일 {head[:10]}","게시일을 원문 기준으로 고정하고 수정일은 별도 유지"))
        if not r["meta_description"] or len(r["meta_description"])<40 or len(r["meta_description"])>190:
            out.append(issue(sl,"SEO","poor_snippet","medium","메타 설명이 너무 짧거나 너무 김","원문 사실 기반 70~155자 스니펫"))
        if counts[r["title"]]>1:
            out.append(issue(sl,"SEO","duplicate_title","medium","서로 다른 게시물의 제목 중복","게시연도·기관·성과로 구분"))
        if r["title"]!=r["card_title"]:
            out.append(issue(sl,"SEO","mismatch_title","medium","목록·본문 제목 불일치","H1·카드·구조화 데이터 제목 일관성"))
        if any(a in r["meta_description"] for a in ("활동의 현장과 주요 내용을 소개합니다","원문 게시번호")):
            out.append(issue(sl,"SEO","unnatural_description","medium","검색 결과에 내부 메타/상투어 노출","사실 중심 요약으로 변경"))
        if r["image_count"] and all(x["alt"] in ("학과 활동 현장 사진","학과 활동 사진") for x in r["images"]):
            out.append(issue(sl,"SEO","generic_alt","low","이미지 대체텍스트에 활동맥락 부족","주제·연도·사진 번호로 구체화"))
        if not r["canonical"].endswith(r["url"]):
            out.append(issue(sl,"SEO","broken_canonical","high","canonical이 개별 게시물 주소와 다름","정확한 URL로 수리"))
    return out

def reviewer_trust(rows):
    out=[]
    for r in rows:
        sl=r["slug"];t=r["title"];body=r["body"];headline=t+" "+body
        if "ASK2024" in t and "ACK 2024" in body:
            out.append(issue(sl,"사실검증","conflicting_event_name","critical","제목 ASK2024 / 본문 ACK 2024 불일치","공식 학술대회 자료 대조 전 임의 수정 금지"))
        for k in UNVERIFIED:
            if re.search(k,headline,re.I):
                out.append(issue(sl,"사실검증","unverified_absolute","critical","절대적 수치 또는 취업 보장 주장 확인 필요","원천 자료와 통계 범위 제시 또는 표현 유보"))
                break
        if r["year"]<=2020 and any(k in body for k in ("앞으로도 매주","다음 주","오는 2016년","오는 2017년","현재 모집")):
            out.append(issue(sl,"사실검증","expired_promise","high","오래된 행사 예고가 현재 진행처럼 표현","과거형으로 정리하고 당시 일정임을 표기"))
        if r["image_count"] and any("모자이크" in x["alt"] for x in r["images"]):
            out.append(issue(sl,"사실검증","outdated_image_note","low","이미지 설명이 실제 복원 상태와 다를 수 있음","사용 중인 파일 확인 후 설명 갱신"))
        if any(x in r["body"] for x in LEGACY):
            out.append(issue(sl,"사실검증","historical_name_left","low","띄어 쓴 과거 학과명이 본문에 남음","공식 현재 명칭 정책에 맞춰 띄어쓰기 변형도 검토"))
    return out

def reviewer_ux(rows):
    out=[]
    for r in rows:
        if r["tag"]=="학과 활동":
            out.append(issue(r["slug"],"UX·정보구조","generic_category","low","단일 포괄 카테고리로 탐색성 낮음","특강·대회·교육·연구·참고자료 여부로 세분화"))
        if re.search(r"^(?:https?://|[a-z0-9.-]+\.kr$)",r["title"],re.I):
            out.append(issue(r["slug"],"UX·정보구조","link_title","medium","외부 사이트 URL 자체가 제목","기술 참고자료로 이동 또는 설명형 제목"))
        if r["year"]<=2018 and ("자료" in r["title"] or "동향" in r["title"] or "표준" in r["title"]):
            out.append(issue(r["slug"],"UX·정보구조","legacy_reference","medium","오래된 기사·자료가 학과 현장활동과 혼재","기술자료 아카이브로 분류하되 URL은 보존"))
    return out

REVIEWERS={
 "입학홍보":reviewer_admissions,
 "취업·산학":reviewer_career,
 "콘텐츠 편집":reviewer_writing,
 "SEO":reviewer_seo,
 "사실검증":reviewer_trust,
 "UX·정보구조":reviewer_ux
}
def main():
    rows=records()
    with ThreadPoolExecutor(max_workers=6,thread_name_prefix="editorial") as pool:
        fut={role:pool.submit(func,rows) for role,func in REVIEWERS.items()}
        issues=[z for name in REVIEWERS for z in fut[name].result()]
    per_role=Counter(i["expert"] for i in issues)
    by_kind=Counter(i["code"] for i in issues)
    by_severity=Counter(i["severity"] for i in issues)
    per_slug=defaultdict(list)
    for i in issues:per_slug[i["slug"]].append(i)
    unique=sorted(per_slug,key=lambda sl:(-max({"critical":4,"high":3,"medium":2,"low":1}[v["severity"]] for v in per_slug[sl]),-len(per_slug[sl]),sl))
    summary={"asof":ASOF.isoformat(),"articles":len(rows),"reviewers":list(REVIEWERS),
     "findings":len(issues),"affected_articles":len(per_slug),"per_role":dict(per_role),
     "per_severity":dict(by_severity),"by_code":dict(by_kind),"issues":issues,
     "articles":[{k:v for k,v in row.items() if k!="body" and k!="sections" and k!="images"} for row in rows]}
    JSON.parent.mkdir(parents=True,exist_ok=True)
    JSON.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=["# 학과 활동 321건 홍보·콘텐츠 전수 점검","",
        "검토일: 2026-10-25 · 검토대상: ai.k-bigdata.kr/activities/ 전체 321건","",
        "**검토 범위:** 개별 글 제목, 두 개의 본문 단락, 목록 소개문, 검색 메타데이터, 구조화 데이터, 게시일, 이미지 설명과 본문 링크. 사진 얼굴의 인물 신원은 판단하지 않음.","",
        "**방법:** 6개 독립 전문가 관점의 규칙 기반 검사 함수를 병렬로 실행. 실제 홍보 전문가 6명 또는 별도 LLM 에이전트의 대면 심사 결과로 표현하지 않음.","",
        "## 전체 결과","",
        f"- 분석 게시글: **{len(rows)}건**",
        f"- 개선 사항 탐지: **{len(issues)}건**, 관련 게시글 **{len(per_slug)}건** (항목 중복 집계)",
        f"- 심각도: critical {by_severity['critical']}, high {by_severity['high']}, medium {by_severity['medium']}, low {by_severity['low']}","",
        "## 6개 검토 관점","",
        "| 관점 | 지적사항 수 | 우선 조치 |","|---|---:|---|"]
    phrases={"입학홍보":"과거 모집정보 구분과 교육효과 사실화","취업·산학":"기업·직무·프로젝트 성과의 구체성",
             "콘텐츠 편집":"과장·감탄·중복 소개문 정리","SEO":"발행일·검색 스니펫·제목 정합성",
             "사실검증":"성과·학술대회 명칭 검증","UX·정보구조":"카테고리 및 과거 참고자료 분리"}
    for name in REVIEWERS:lines.append(f"| {name} | {per_role[name]} | {phrases[name]} |")
    lines+=["","## 반복 문제 (자동 탐지)","","| 항목 | 건수 |","|---|---:|"]
    for kind,n in by_kind.most_common():lines.append(f"| {kind} | {n} |")
    lines+=["","## 우선 정비할 글 (상위 50건)","","| 순위 | 원문 게시일 | 제목 | 중요 이슈 |","|---:|---|---|---|"]
    lookup={x["slug"]:x for x in rows}
    for i,sl in enumerate(unique[:50],1):
        x=lookup[sl];found=per_slug[sl]
        codes=", ".join(dict.fromkeys(z["code"] for z in found))
        title=x["title"].replace("|","／").replace("\n"," ")
        lines.append(f"| {i} | {x['date']} | [{title}](https://ai.k-bigdata.kr{x['url']}) | {codes} |")
    lines+=["","## 편집·검증 원칙","",
        "1. 본문은 사실이 확인된 활동·참여 대상·기술·결과를 중심으로 재작성하고 출처에 없는 성과나 취업률을 만들지 않는다.",
        "2. 행사 개최일과 게시일, 공개 웹페이지 작성일을 혼동하지 않는다. 과거 모집글은 종료된 기록으로 명시한다.",
        "3. 학술대회·수상 내역 충돌은 관련 공식자료 대조 전 확정 문구를 임의 수정하지 않는다.",
        "4. 홍보를 위한 클릭 유도는 졸업작품·교육과정·현행 입학안내에 연결하며 과도한 반복 링크를 피한다.",
        "5. 기존 게시글 경로·사진·공유 URL은 유지하고, 검색 메타데이터를 본문과 동기화한다.",
        "6. 외부 기사를 수집한 과거 게시물은 학과의 직접 성과로 해석하지 않고 참고자료로 표시한다.",
        "",
        "## 후속 검증 필요","",
        "고위험 건은 원본 학교 게시판, 당시 공모전·기관 보도자료의 실제 서술과 대조 후 편집한다. 모든 고전 자료를 현재 교육실적처럼 홍보하지 않는다.",""]
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text("\n".join(lines),encoding="utf-8")
    print("REVIEW_COMPLETE",len(rows),"articles",len(issues),"issues",len(per_slug),"affected",flush=True)
    print("REVIEW_ROLES",json.dumps(dict(per_role),ensure_ascii=False),flush=True)
    print("TOP_ISSUES",json.dumps(by_kind.most_common(12),ensure_ascii=False),flush=True)
    print("IMPORTANT_EXAMPLES",json.dumps([{"slug":sl,"title":lookup[sl]["title"],"findings":[z["code"] for z in per_slug[sl]]} for sl in unique[:12]],ensure_ascii=False),flush=True)

if __name__=="__main__":main()
