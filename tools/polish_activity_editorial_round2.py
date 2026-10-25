#!/usr/bin/env python3
"""Second editorial QA pass on all CURRENT 286 department news articles.

Curated headlines and leads are grounded in the corresponding historical
article contents; do not modify original photo assets, links or evidence.
"""
from __future__ import annotations
import html,json,re
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/"activities"/"index.html"
REPORT=ROOT/"reports"/"activity_editorial_full_review_2026-10-25.md"
CARD=re.compile(r'<article class="activity-card">.*?</article>',re.S)
JSONLD=re.compile(r'<script type="application/ld\+json">(.*?)</script>',re.S)
SITE="https://ai.k-bigdata.kr"
POLISHED={
 "kopo-752594":("AI 전문가·인사담당자 초청, 2학년 취업 실무교육","2025년 6월 25~26일 학과 2학년 학생을 대상으로 현직 개발자·AI 전문가·인사담당자·진로 컨설턴트를 초청해 자기소개서와 면접·포트폴리오 준비를 다뤘습니다.","취업·진로"),
 "kopo-762210":("2025 프로젝트경진대회, 우수상·장려상 수상","2025년 프로젝트경진대회에서 학과 학생들이 AI·클라우드 기반 모의투자 프로그램으로 우수상, 소비 데이터 시각화 기능을 구현한 스마트 가계부로 장려상을 수상했습니다.","수상·성과"),
 "kopo-699006":("K-PaaS 서비스 공모전 전국 1위, 과기정통부 장관상","학과 학생들이 K-PaaS 기반 여행지 추천 플랫폼을 개발해 개방형 클라우드 플랫폼 서비스 개발 공모전에서 전국 1위로 과학기술정보통신부 장관상을 수상했습니다.","수상·성과"),
 "kopo-773180":("SQL 퀴즈 특강, 질의 작성·문제 해결 실습","SQL 퀴즈 풀이 특강에서 학생들이 주요 SQL 문법과 문제 유형을 직접 풀고, 질의 작성 과정과 자주 발생하는 오류를 함께 점검했습니다.","전문가 특강"),
 "kopo-750361":("방과후 컴퓨터·코딩지도사 수료식, 여성 재취업 교육","학과가 운영한 12주간의 방과후 컴퓨터·코딩지도사 과정 수료식이 열렸습니다. 교육생들은 ITQ 사무자동화와 스크래치·엔트리 코딩 지도법을 실습했습니다.","지역사회 교육"),
 "kopo-734728":("코웨이 황윤영 졸업생, SW 개발 직무 특강","코웨이에서 소프트웨어 개발자로 재직 중인 황윤영 졸업생이 후배들에게 개발 업무와 프로젝트 경험, 협업 역량, 대학원 진학 과정을 공유했습니다.","멘토링·진로"),
 "kopo-734727":("로지스올시스템즈 박수진 졸업생 초청 취업 특강","로지스올시스템즈에서 소프트웨어 개발자로 근무하는 박수진 졸업생이 후배들에게 취업 준비 과정과 개발 직무, 포트폴리오·면접 경험을 소개했습니다.","멘토링·진로"),
 "kopo-727468":("방과후 컴퓨터·코딩지도사 교육과정 수료식","6월 21일 진행된 방과후 컴퓨터·코딩지도사 과정 수료식에서 교육생들이 스크래치·엔트리, 언플러그드 코딩, 아두이노 등 실습 기반 교육을 마무리했습니다.","지역사회 교육"),
 "kopo-612409":("1기 졸업생 문주현·박수용, 숭실대 대학원 석사 취득","학과 1기 졸업생 문주현·박수용이 숭실대학교 일반대학원 컴퓨터학과 석사과정을 마치고 학위를 취득했습니다. 졸업 후 진학 성과를 소개합니다.","멘토링·진로"),
 "kopo-485394":("2017 SW동아리 재능기부 챌린지 전국 3위 수상","2017년 SW동아리 재능기부 챌린지에서 학과 학생들이 전국 3위를 수상했습니다. 전년도 전국 2위에 이어 2년 연속 수상한 활동입니다.","수상·성과"),
 "kopo-483717":("2017 농협 핀테크 아이디어톤, 학과 학생 전국 3위","2017년 농협이 주최한 핀테크 아이디어톤 공모전에서 학과 학생팀이 본선에 진출해 3위를 수상했습니다.","수상·성과"),
 "kopo-453392":("2017 ICNCT 국제학술대회, 교수진 최우수논문상","김영운·이협건 교수가 2017 ICNCT 국제학술대회에서 사물인터넷 환경의 Apache Spark 기반 실시간 빅데이터 분석 연구로 최우수논문상을 받았습니다.","연구·학술"),
 "kopo-446171":("2016 폴리텍 엑스포, 학과 빅데이터 교육 소개","2016년 11월 2~3일 일산 킨텍스에서 열린 폴리텍 엑스포에 학과가 참가해 빅데이터 분석 교육을 관람객에게 소개했습니다.","학과 행사"),
 "kopo-591399":("학과 빅데이터 분석 교육 소개 카드뉴스","2020년 학과 게시판에 공개된 카드뉴스로, 당시 빅데이터 분석 교육과 학과의 특징을 소개했습니다.","학과 소식"),
 "kopo-746516":("2학년 선배 주도 Java 멘토링, if 조건문 실습","2학년 선배들이 1학년 신입생을 대상으로 Java 프로그래밍 야간 멘토링을 진행했습니다. if 조건문을 직접 작성하며 동작 원리를 함께 학습했습니다.","멘토링·진로"),
 "kopo-747615":("선후배 Java 멘토링, 객체지향·캡슐화 실습","2025년 4월 15일 진행된 선후배 Java 멘토링에서 1학년 학생들이 클래스와 객체, 생성자, 캡슐화 등 객체지향 프로그래밍의 핵심 개념을 예제로 학습했습니다.","멘토링·진로"),
 "kopo-727467":("카카오엔터테인먼트 손성용 개발자 초청 Spring 특강","카카오엔터테인먼트 손성용 시니어 개발자가 학생들에게 Spring Framework의 DI·IoC·AOP, Spring Boot 활용과 서비스 아키텍처 설계 사례를 소개했습니다.","전문가 특강"),
 "kopo-734721":("고교 교원 대상 생성형 AI 실습 연수, Llama 3.1 활용","2024년 9월 2~6일 고교 교원 대상 AI 연수에서 TensorFlow 모델 학습, OpenCV·Tesseract 이미지 인식, Llama 3.1 기반 생성형 AI 서비스 개발을 실습했습니다.","교원 연수"),
 "kopo-727478":("Spring Boot 실무 특강, MariaDB 연동·웹 개발 실습","8월 1~2일 열린 Spring Boot 특강에서 학생들이 MariaDB를 설치하고 공지사항 웹 페이지를 구성하며 백엔드 웹 개발의 기초 구조를 실습했습니다.","전문가 특강"),
 "kopo-727469":("2024 KB굿잡 취업박람회, 학과 홍보부스 운영","2024년 5월 27일 코엑스에서 열린 KB굿잡 취업박람회에서 학과가 AI·클라우드·빅데이터 교육과 진로 방향을 소개하는 홍보부스를 운영했습니다.","취업·진로"),
 "kopo-707046":("AI 진로체험 1기, Python·OpenCV 이미지 처리 실습","2023년 10월 21일과 28일 열린 AI 진로체험 수업에서 참가 학생들이 Python·OpenCV 이미지 처리와 워드클라우드 제작 실습에 참여했습니다.","진로체험"),
 "kopo-707045":("빅데이터 진로체험 1기, R 분석·시각화 실습","2023년 10월 21일과 28일 진행된 빅데이터 진로체험에서 참가 학생들이 R 프로그래밍과 데이터 분석·시각화 실습을 통해 전공 분야를 탐색했습니다.","진로체험"),
 "kopo-759557":("시스원 손병홍 이사 특강, AX 시대 IT 직무·기술 변화","시스원 손병홍 이사가 학생들에게 AI 전환(AX), 클라우드·보안·데이터 기술의 변화와 기업 현장에서 요구하는 직무역량을 소개했습니다.","전문가 특강"),
 "kopo-750981":("선후배 멘토링, Spring Boot·MariaDB 연동 실습","2학년 선배들이 1학년 학생을 대상으로 Spring Boot·MariaDB 연동 실습을 지도했습니다. MyBatis 기반 DB 연결, Controller·View 구조와 코드 오류 해결을 다뤘습니다.","멘토링·진로"),
}
def esc(t):return html.escape(t,quote=True)
def rxtext(text,pattern,updated):
    newer,n=re.subn(pattern,lambda m:m.group(1)+esc(updated)+m.group(3),text,count=1,flags=re.S)
    if n!=1:raise RuntimeError("Missing markup field "+pattern)
    return newer
def rewrite_meta(text,key,value,kind):
    attr="property" if kind=="property" else "name"
    rex=r'(<meta\b(?=[^>]*'+re.escape(attr+'="'+key+'"')+r')[^>]*\bcontent=")(.*?)(")'
    return rxtext(text,rex,value)
def update_page(raw,title,lead,category):
    links=re.findall(r'(?:src|href)="([^"]+)"',raw)
    src=rxtext(raw,r'(<h1>)(.*?)(</h1>)',title)
    src=rxtext(src,r'(<title>)(.*?)(</title>)',title+" | 빅데이터소프트웨어공학과")
    src=rxtext(src,r'(<p class="activity-lead">)(.*?)(</p>)',lead)
    for key,val,kind in (
        ("description",lead,"name"),("og:title",title+" | 빅데이터소프트웨어공학과","property"),
        ("og:description",lead,"property"),("twitter:title",title+" | 빅데이터소프트웨어공학과","name"),
        ("twitter:description",lead,"name")):
        src=rewrite_meta(src,key,val,kind)
    src=re.sub(r'(<p class="activity-kicker">DEPARTMENT ACTIVITIES · )(.*?)(</p>)',
               lambda m:m.group(1)+esc(category)+m.group(3),src,count=1)
    def ld(m):
        obj=json.loads(m.group(1))
        if obj.get("@type")=="Article":
            obj["headline"]=title;obj["description"]=lead
        return '<script type="application/ld+json">'+json.dumps(obj,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c")+"</script>"
    src=JSONLD.sub(ld,src,count=1)
    if links!=re.findall(r'(?:src|href)="([^"]+)"',src):
        raise RuntimeError("Photo / href changed")
    return src
def main():
    source=INDEX.read_text(encoding="utf-8")
    edits={}
    rows=CARD.findall(source)
    if len(rows)!=286:raise RuntimeError("Expected 286 posts")
    for card in rows:
        title=re.search(r'<h3><a href="(/activities/([^/]+)/)">([^<]*)</a></h3>',card)
        if not title:raise RuntimeError("List card invalid")
        slug=title.group(2)
        if slug in POLISHED:
            new_title,new_lead,new_cat=POLISHED[slug]
        else:
            old=html.unescape(title.group(3))
            new_title=re.sub(r'(?<=[가-힣])\.\s+(?=[가-힣A-Z])'," — ",old)
            new_title=new_title.replace("코딩지도사 교육과정 수료식 진행","코딩지도사 교육과정 수료식 진행")
            if new_title==old:continue
            page=BeautifulSoup((ROOT/"activities"/slug/"index.html").read_text(encoding="utf-8"),"html.parser")
            new_lead=page.select_one('.activity-lead').get_text(" ",strip=True)
            new_cat=page.select_one('.activity-kicker').get_text(" ",strip=True).split("·",1)[-1].strip()
        file=ROOT/"activities"/slug/"index.html"
        original=file.read_text(encoding="utf-8")
        result=update_page(original,new_title,new_lead,new_cat)
        if result!=original:
            file.write_text(result,encoding="utf-8")
            edits[slug]=(new_title,new_lead,new_cat)
    def change_card(m):
        c=m.group(0)
        slug=re.search(r'<h3><a href="/activities/([^/]+)/"',c).group(1)
        if slug not in edits:return c
        title,lead,cat=edits[slug]
        c=rxtext(c,r'(<h3><a href="[^"]+">)(.*?)(</a></h3>)',title)
        c=rxtext(c,r'(</h3><p>)(.*?)(</p>)',lead)
        c=rxtext(c,r'(<div class="activity-card-meta"><span>)(.*?)(</span>)',cat)
        c=re.sub(r'(\baria-label=")[^"]*(")',lambda q:q.group(1)+esc(title+" 자세히 보기")+q.group(2),c,count=1)
        return c
    output=CARD.sub(change_card,source)
    def set_archive_schema(m):
        obj=json.loads(m.group(1))
        if obj.get("@type")=="CollectionPage":
            for item in obj["mainEntity"]["itemListElement"]:
                slug=item["url"].split("/activities/")[-1].strip("/")
                if slug in edits:item["name"]=edits[slug][0]
        return '<script type="application/ld+json">'+json.dumps(obj,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c")+"</script>"
    output=JSONLD.sub(set_archive_schema,output)
    assert len(CARD.findall(output))==286
    assert "kopo-738806/" not in output and "kopo-707036/" not in output
    INDEX.write_text(output,encoding="utf-8")
    with REPORT.open("a",encoding="utf-8") as f:
        f.write("\n## 추가 교열: 수상·취업·교육 핵심 게시글 및 제목 문장부호\n\n")
        f.write(f"원문을 다시 읽고 핵심 24건의 설명문과 제목을 수정했습니다. 최종 추가 교열 파일 {len(edits)}건입니다.\n\n")
        for slug,(title,_,_) in edits.items():
            f.write(f"- [{title}]({SITE}/activities/{slug}/)\n")
    print("CURATED_EDITORIAL_POLISH",len(edits),"posts","fact_specific",len(POLISHED),flush=True)
if __name__=="__main__":
    main()
