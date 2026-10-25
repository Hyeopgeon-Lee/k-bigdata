#!/usr/bin/env python3
"""Manual source-grounded polish for high-risk and high-value promotional stories.

Evidence: the existing historical article body. For the two KIPS 2024 posts,
the ACK 2024 award listing in the Korean Information Processing Society program.
No change to photos, date, original claim category or source URL.
"""
import json,re,html
from pathlib import Path
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
ARCH=ROOT/"activities"/"index.html"
DOMAIN="https://ai.k-bigdata.kr"
PUBLISHED="2026-10-25"
OFFICIAL="https://kips.or.kr/bbs/3879/11133"
# Original article texts were individually reviewed for the facts in these summaries.
UPDATES={
"kopo-738804":(
 "ACK 2024 논문경진대회 동상, 맵리듀스 데이터 압축 연구 성과",
 "김원집·김하윤 학생과 이협건·김영운 교수가 공동 연구한 데이터 압축 방식별 맵리듀스 성능 비교 논문이 ACK 2024 논문경진대회에서 동상을 수상했습니다.",
 "수상·성과"),
"kopo-738801":(
 "한국정보처리학회 ACK 2024 동상, 학생·교수 공동연구",
 "2024년 11월 1일 열린 한국정보처리학회 ACK 2024 논문경진대회에서 김원집·김하윤 학생과 이협건·김영운 교수의 공동 논문이 동상을 수상했습니다.",
 "수상·성과"),
"kopo-746968":(
 "선후배 Java 멘토링, 반복문 실습 진행",
 "2025년 4월 8일, 2학년 선배들이 1학년 학생들을 위해 Java의 for·while·do-while 반복문을 예제로 설명하고 함께 실습했습니다.",
 "선후배 멘토링"),
"kopo-746591":(
 "2025 ICT 한이음 드림업 공모전, 학과 프로젝트 2팀 선정",
 "2025 ICT 한이음 드림업 공모전에서 학과 1·2학년 학생이 참여한 ‘곁봄’과 ‘메르핸드’ 프로젝트가 함께 선정됐습니다. AI·OCR·수어 학습 기술을 활용한 아이디어입니다.",
 "수상·성과"),
"kopo-707043":(
 "2023 프로젝트 경진대회, 7기 허지혜 학생 최우수상",
 "2023학년도 프로젝트 경진대회에서 7기 허지혜 학생이 최우수상을 받았습니다. LF융합실습지원센터 졸업작품 발표회에서 프로젝트 성과를 공유했습니다.",
 "수상·성과"),
"kopo-450315":(
 "2017 강서구 SNS 톡톡 기자단 모집 안내(종료)",
 "강서구 SNS 톡톡 기자단의 2017년 모집 안내를 보존한 게시물입니다. 접수 마감일은 2017년 1월 13일이며 현재 신청 가능한 공고가 아닙니다.",
 "과거 모집·행사 안내"),
"kopo-451148":(
 "정보기술 국제표준(JTC1) 동향 참고자료",
 "정보기술 국제표준화 협력과 상호운용성, JTC1의 활동 동향을 다룬 2017년 기술 참고자료입니다.",
 "기술·참고자료"),
"kopo-450160":(
 "HTML5 기반 스마트 TV 플랫폼 표준 자료 소개",
 "2016년 6월 24일 제·개정된 HTML5 기반 스마트 TV 플랫폼 표준(TTAK.KO-07.0111/R2)의 적용 범위와 인터페이스 요구사항을 소개합니다.",
 "기술·참고자료"),
"kopo-445213":(
 "소프트웨어 개발 기술 읽을거리, POPIT 소개",
 "2016년 학과 게시판에서 소프트웨어 개발자의 기술 글과 경험을 살펴볼 수 있는 POPIT 사이트를 참고자료로 안내했습니다.",
 "기술·참고자료"),
"kopo-527126":(
 "2019 ICNCT 국제학술대회, 학과 교수진 논문 발표",
 "김영운·이협건 교수가 2019년 1월 일본 류큐대학에서 개최된 ICNCT 국제학술대회에 참석해 연구 논문을 발표했습니다.",
 "연구·논문"),
"kopo-443897":(
 "2016 Dream Job 페스티벌, 빅데이터 진로체험 운영",
 "2016년 9월 7일 방화근린공원에서 열린 제3회 Dream Job 페스티벌에서 학과가 빅데이터 활용 사례를 소개하고 학생·시민 대상 진로 상담을 진행했습니다.",
 "진로체험"),
"kopo-462836":(
 "제6회 학과 봉사활동, 교남소망의집 방문",
 "2017년 학과 학생들이 교남소망의집을 방문해 환경 정리와 산책 활동을 도우며 지역사회 봉사활동을 진행했습니다.",
 "사회공헌·봉사"),
"kopo-511067":(
 "고용노동부 중소기업 탐방, 이력서·모의면접 실습",
 "2018년 9월 17~19일 학과 학생들이 중소기업 탐방 프로그램에 참여해 한글과컴퓨터 기업 탐방, 미래 이력서 작성, 모의면접 실습을 진행했습니다.",
 "취업·진로"),
"kopo-495740":(
 "2018 미래직업 전망 자료, 빅데이터 전문가 주목",
 "2018년 한국고용정보원의 ‘4차 산업혁명 미래 일자리 전망’ 보고서를 소개한 참고자료입니다. 당시 빅데이터·인공지능 등 기술직군의 변화를 살펴봤습니다.",
 "기술·참고자료"),
"kopo-448020":(
 "2016 SW동아리 재능기부 사업 전국 2위, 슈퍼개발자팀 수상",
 "2016년 학과 SW동아리 슈퍼개발자팀이 소상공인용 푸드트럭 앱을 개발해 ‘SW동아리 재능기부 챌린지’에서 전국 2위를 차지하고 정보통신기술진흥센터장상을 받았습니다.",
 "수상·성과"),
"kopo-633739":(
 "PaaS-TA 오픈랩 확산 워크숍, 클라우드 교육 협력",
 "2021년 한국폴리텍대학 서울강서캠퍼스와 숭실대·건국대·한국산업기술대 등이 오픈랩 워크숍에 참여해 PaaS-TA 기반 클라우드 교육 협력 방안을 논의했습니다.",
 "산학협력"),
"kopo-463357":(
 "2017 SW동아리 재능기부 사업 2년 연속 선정",
 "2017년 학과 슈퍼개발자 동아리팀이 SW동아리 재능기부 챌린지 지원 사업에 2년 연속 선정돼 소상공인용 소프트웨어 개발비 1,100만 원을 지원받았습니다.",
 "수상·성과"),
"kopo-509708":(
 "2018 문화데이터 경진대회, 이지흠 학생 최우수상",
 "2018년 제6회 문화데이터 활용 경진대회에서 1학년 이지흠 학생이 공공 문화데이터 활용 아이디어로 최우수상과 상금 200만 원을 받았습니다.",
 "수상·성과"),
"kopo-504250":(
 "ICT 학점연계 인턴십 사업, 2017·2018년 연속 선정",
 "학과가 과학기술정보통신부 ICT 학점연계 프로젝트 인턴십 참여학과로 2017·2018년 연속 선정돼 학생들이 기업 R&D 프로젝트에 참여할 기회를 얻었습니다.",
 "취업·진로"),
"kopo-707039":(
 "LG CNS 변재영 책임 초청, 클라우드 네이티브·MSA 특강",
 "LG CNS 변재영 책임이 학생들에게 클라우드 네이티브 개발, 마이크로서비스 아키텍처(MSA)와 기업의 디지털 전환 사례를 소개했습니다.",
 "현직자·전문가 특강"),
"kopo-727480":(
 "2024 고교 교원 AI 연수, Llama 3·컴퓨터비전 실습",
 "2024년 강서양천교육지원청과 연계한 교원 직무연수에서 Llama 3 기반 생성형 AI, 얼굴 인식, 이미지 변환 등을 활용한 인공지능 실습을 진행했습니다.",
 "교원 연수"),
"kopo-501832":(
 "2018 산학연 R&D 과제 선정, 자동차 정비 데이터 분석",
 "2018년 학과 교수진이 이아이티서비스와 함께 자동차 정비 견적 데이터의 수집·분석 및 추천 알고리즘을 연구하는 산학연협력 기술개발 과제에 선정됐습니다.",
 "산학협력"),
"kopo-460887":(
 "2017 창업아이템 경진대회 참가 모집 안내(종료)",
 "2017년 제1회 4차산업혁명 대비 창업아이템 경진대회의 참가 자격과 일정을 안내한 과거 자료입니다. 당시 접수는 2017년 5월 26일에 마감됐습니다.",
 "과거 모집·행사 안내"),
"kopo-699007":(
 "K-PaaS 서비스 공모전 수상, AI 활용 재활용 추천 서비스",
 "학과 학생들이 일회용품 인식과 맞춤형 재활용 추천 기능을 구현한 K-PaaS 기반 서비스로 개방형 클라우드 플랫폼 공모전에서 한국지능정보사회진흥원장상을 받았습니다.",
 "수상·성과"),
"kopo-471648":(
 "ICT 학점연계 인턴십, 학과 학생 6명 선정",
 "2017년 학과 학생 6명이 ICT 학점연계 프로젝트 인턴십에 선정돼 KCC정보통신·나스텍·메빅슨·무하유·엔블리스컴즈 등 기업에서 직무 실습 기회를 얻었습니다.",
 "취업·진로"),
"kopo-711758":(
 "K-PaaS 공모전 2년 연속 대상, AI 실종자 찾기 서비스",
 "학생들이 AI로 과거 사진의 현재 얼굴을 예측하는 실종자·해외 입양자 찾기 서비스를 개발해 K-PaaS 공모전에서 2년 연속 대상(과기정통부 장관상)을 수상했습니다.",
 "수상·성과"),
"kopo-727476":(
 "서울 강서양천 고교생, R·소셜데이터 분석 진로체험",
 "2024년 한서고·세현고·공항고·명덕여고 학생들이 학과 진로체험에 참여해 R 기반 공공데이터 분석과 소셜미디어 트렌드 분석을 실습했습니다.",
 "진로체험"),
"kopo-445198":(
 "2016 김영운 교수 기고, R을 활용한 빅데이터 분석",
 "2016년 학과 게시판에서 김영운 교수의 빅데이터 분석 관련 외부 기고문을 소개했습니다. 데이터 수집과 분석의 활용 범위를 다룬 당시의 참고자료입니다.",
 "기술·참고자료"),
}
def patch_meta(s,key,value):
    path='name="'+key[5:]+'"' if key.startswith("name:") else 'property="'+key[9:]+'"'
    pattern=r'(<meta\b(?=[^>]*'+re.escape(path)+r')[^>]*\bcontent=")[^"]*(")'
    out,n=re.subn(pattern,lambda m:m.group(1)+html.escape(value,quote=True)+m.group(2),s,count=1,flags=re.S)
    if n!=1:raise RuntimeError("Meta key absent "+key)
    return out
def body_replace(s,tit,lead):
    x=re.sub(r'(<h1>).*?(</h1>)',lambda m:m.group(1)+html.escape(tit,quote=True)+m.group(2),s,count=1,flags=re.S)
    x=re.sub(r'(<title>).*?(</title>)',lambda m:m.group(1)+html.escape(tit+" | 빅데이터소프트웨어공학과",quote=True)+m.group(2),x,count=1,flags=re.S)
    x=re.sub(r'(<p class="activity-lead">).*?(</p>)',lambda m:m.group(1)+html.escape(lead,quote=True)+m.group(2),x,count=1,flags=re.S)
    for name,val in [("name:description",lead),("property:og:title",tit+" | 빅데이터소프트웨어공학과"),
                     ("name:twitter:title",tit+" | 빅데이터소프트웨어공학과"),
                     ("property:og:description",lead),("name:twitter:description",lead)]:
        x=patch_meta(x,name,val)
    def ld(m):
        val=json.loads(m.group(1))
        if val.get("@type")=="Article":
            val["headline"]=tit
            val["description"]=lead
        return '<script type="application/ld+json">'+json.dumps(val,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c")+'</script>'
    x,n=re.subn(r'<script type="application/ld\+json">(.*?)</script>',ld,x,flags=re.S)
    if n!=1:raise RuntimeError("JSON-LD missing")
    return x
def run():
    original_archive=(ROOT/"activities"/"index.html").read_text(encoding="utf-8")
    changed=[]
    for slug,(title,lead,tag) in UPDATES.items():
        path=ROOT/"activities"/slug/"index.html"
        old=path.read_text(encoding="utf-8")
        fresh=body_replace(old,title,lead)
        if slug in ("kopo-738804","kopo-738801"):
            # Two 2024 posts refer to the same prize-winning KIPS paper.
            # The society's official ACK 2024 award schedule records bronze.
            official=('<p class="activity-official-evidence">공식 수상 근거: '
               '<a href="'+OFFICIAL+'" target="_blank" rel="noopener noreferrer">'
               '한국정보처리학회 ACK 2024 논문경진대회 수상 결과</a></p>')
            if "class=\"activity-official-evidence\"" not in fresh:
                fresh=fresh.replace('<div class="activity-cta">',official+'<div class="activity-cta">',1)
        if re.findall(r'(?:src|href)="([^"]+)"',old)!=re.findall(r'(?:src|href)="([^"]+)"',fresh):
            # The two KIPS pages deliberately gain one cited official source link.
            if slug not in ("kopo-738804","kopo-738801"):raise RuntimeError("Unexpected link/image change "+slug)
        path.write_text(fresh,encoding="utf-8")
        changed.append(slug)
    def fix_card(m):
        card=m.group(0)
        match=re.search(r'<h3><a href="/activities/([^/]+)/"',card)
        if not match or match.group(1) not in UPDATES:return card
        title,lead,tag=UPDATES[match.group(1)]
        card=re.sub(r'(<h3><a href="[^"]+">).*?(</a></h3>)',lambda n:n.group(1)+html.escape(title,quote=True)+n.group(2),card,count=1,flags=re.S)
        card=re.sub(r'(</h3><p>).*?(</p>)',lambda n:n.group(1)+html.escape(lead,quote=True)+n.group(2),card,count=1,flags=re.S)
        card=re.sub(r'(<div class="activity-card-meta"><span>).*?(</span>)',lambda n:n.group(1)+html.escape(tag,quote=True)+n.group(2),card,count=1,flags=re.S)
        card=re.sub(r'(\baria-label=")[^"]*(")',lambda n:n.group(1)+html.escape(title+" 자세히 보기",quote=True)+n.group(2),card,count=1)
        return card
    archive=re.sub(r'<article class="activity-card">.*?</article>',fix_card,original_archive,flags=re.S)
    def fix_list(m):
        data=json.loads(m.group(1))
        if data.get("@type")!="CollectionPage":return m.group(0)
        for item in data.get("mainEntity",{}).get("itemListElement",[]):
            slug=item["url"].split("/activities/")[-1].strip("/")
            if slug in UPDATES:item["name"]=UPDATES[slug][0]
        return '<script type="application/ld+json">'+json.dumps(data,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c")+'</script>'
    archive=re.sub(r'<script type="application/ld\+json">(.*?)</script>',fix_list,archive,flags=re.S)
    if archive.count('class="activity-card"')!=321:raise RuntimeError("Cards changed")
    (ROOT/"activities"/"index.html").write_text(archive,encoding="utf-8")
    report=ROOT/"reports"/"activity_promotion_edits_2026-10-25.md"
    with report.open("a",encoding="utf-8") as f:
        f.write("\n## 2차 기사별 사실 기반 교열 (추가 28건)\n\n")
        f.write("기존 본문에서 확인된 기업·일시·교육 내용·수상 사실을 이용해 제목/요약을 문장 단위로 보강했습니다.\n")
        f.write("한국정보처리학회 공식 프로그램에서 ACK 2024 동상임을 확인해 ASK 표기 충돌 2건을 정정했습니다.\n\n")
        for slug,(title,_,_) in UPDATES.items():f.write(f"- [{title}](https://ai.k-bigdata.kr/activities/{slug}/)\n")
    print("HIGH_PRIORITY_POLISH",len(changed),"posts, source-verified ACK claims 2",flush=True)
if __name__=="__main__":run()
