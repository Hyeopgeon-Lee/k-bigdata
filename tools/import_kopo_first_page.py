#!/usr/bin/env python3
"""One-time import. The official KOPO detail URL requires POST, not GET."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
from html import escape
from urllib.parse import urljoin
import io, json, re
import requests
from bs4 import BeautifulSoup
import cv2
import numpy as np
from PIL import Image, ImageOps

ROOT=Path(__file__).resolve().parents[1]
BOARD="https://www.kopo.ac.kr/kangseo/board.do?menu=1550"
BASE="https://www.kopo.ac.kr"
SITE="https://ai.k-bigdata.kr"
POSTS=json.loads(r'''[{"id":"766164","slug":"sesac-hackathon-grand-prize-2025","title":"2025 새싹 해커톤, 서울시 대상 수상","tag":"공모전·수상","date":"2025-12-17","lead":"2025 새싹(SeSAC) 해커톤에서 학과 학생 팀이 서울시 대상을 수상했습니다.","sections":[["AI 아이디어를 실용적인 서비스로","AI를 활용해 새로운 변화를 만드는 주제로 열린 2025 새싹 해커톤에는 예선에 921명이 참가했습니다. 본선에서는 무박 2일간 기획, AI 모델 적용, 앱·웹 서비스 구현을 수행했습니다."],["학생 프로젝트 교육의 성과","학과 학생 팀은 AI 기반 서비스의 실용성과 구현 완성도를 인정받아 최종 대상을 수상했습니다. 이번 성과는 빅데이터와 인공지능, 클라우드 기술을 연결하는 프로젝트 중심 교육의 결과를 보여줍니다."]]},{"id":"762842","slug":"department-funding-2025","title":"학과 개편 사업 선정, 10억 원 예산 확보","tag":"학과 소식","date":"2025-11-08","lead":"학과 개편 사업 최종 선정으로 약 10억 원 규모의 교육환경 개선 예산을 확보했습니다.","sections":[["GPU 인프라와 교육공간 개선","학과는 개편 사업으로 확보한 예산을 바탕으로 GPU 워크스테이션과 GPU 서버, 실습 공간 리모델링 등을 추진한다고 발표했습니다."],["AI·빅데이터·클라우드 융합 교육","프로젝트 실습에 필요한 컴퓨팅 인프라를 확충하고 AI, 데이터 분석, 클라우드 기술을 접목하는 실무 교육과정을 강화하는 것이 핵심 방향입니다."]]},{"id":"749947","slug":"department-reorganization-2025","title":"빅데이터과, AI·소프트웨어 융합 교육 중심으로 개편","tag":"학과 안내","date":"2025-05-27","lead":"기존 빅데이터 분석 교육에 소프트웨어 개발과 AI·클라우드 실무를 더하는 학과 개편을 안내했습니다.","sections":[["2026학년도부터 교육 범위 확대","2025년 발표에서는 2026학년도 신입생부터 빅데이터과를 빅데이터소프트웨어과로 개편한다고 설명했습니다. 현재 학과 공식 명칭은 빅데이터소프트웨어공학과입니다."],["클라우드와 DevOps·프로젝트 실습 강화","개편 방향에는 K-PaaS, 웹 프로그래밍, DevOps, AI 기반 분석 등 현장형 기술 교육과 프로젝트 수행 역량의 강화가 포함됐습니다."]]},{"id":"786372","slug":"gangseo-job-fair-2026","existing":true,"title":"2026 강서구 취업박람회, 2학년 학생 참여","date":"2026-10-02"},{"id":"781895","slug":"alumni-ha-jae-hyeong-lecture-2026","title":"부산대학교 대학원 진학 졸업생 초청 진로 특강","tag":"졸업생·진로","date":"2026-08-11","lead":"부산대학교 대학원에서 소프트웨어공학을 전공하는 7기 졸업생이 후배들에게 진로 경험을 전했습니다.","sections":[["선배가 들려준 대학원 진학 과정","7기 졸업생 하재형 선배가 재학 중 학업과 활동, 부산대학교 대학원 컴퓨터공학과 소프트웨어공학 전공 진학 과정, 현재의 대학원 생활을 소개했습니다."],["다양한 진로 선택을 위한 조언","전공 역량을 키우는 학습 방법과 진로 계획 수립에 관한 실질적인 조언을 전하며 후배들과 경험을 나눴습니다."]]},{"id":"781894","slug":"teacher-generative-ai-r-training-2026","title":"고등학교 교사 대상 생성형 AI·R 데이터 분석 연수","tag":"교원 연수","date":"2026-08-11","lead":"2026년 7월 21일부터 23일까지 15시간 동안 생성형 AI와 R을 활용하는 교원 실습 연수를 운영했습니다.","sections":[["생성형 AI로 교육·연구 업무 탐색","Gemini와 NotebookLM 등 AI 도구를 활용한 자료 검색, 요약, 이미지 생성·분석, 교육자료 활용 방안을 직접 실습했습니다."],["R과 RStudio 기반 데이터 분석","R 개발환경을 구성해 관광객·상권·인구 통계와 공공·소셜데이터를 분석했습니다. 지도 시각화, 워드클라우드, 뉴스 키워드 분석 등으로 데이터 결과를 표현했습니다."]]},{"id":"781893","slug":"teacher-ai-llm-workshop-2026","title":"고등학교 교사 대상 인공지능·LLM 실습 연수","tag":"교원 연수","date":"2026-08-11","lead":"3일간 15시간의 실습으로 인공지능의 기초부터 LLM과 컴퓨터비전·업무자동화까지 다뤘습니다.","sections":[["Python·머신러닝 모델 실습","Python 개발환경을 만들고 성적 데이터 분석, 머신러닝, CNN을 이용한 꽃 이미지 분류 모델 등을 구현했습니다."],["컴퓨터비전과 업무 자동화","ONNX 얼굴 인식·나이 예측, 영상 변환과 얼굴 모자이크를 실습했습니다. Google Apps Script를 활용해 교육 관련 결과를 이메일로 알리는 자동화 프로그램도 만들었습니다."]]},{"id":"781892","slug":"public-vibe-coding-class-2026","title":"일반인 대상 생성형 AI 바이브코딩 실습 교육","tag":"지역사회 교육","date":"2026-08-11","lead":"2026년 7월 24일 일반인을 대상으로 생성형 AI를 활용한 Python 프로그래밍 교육을 진행했습니다.","sections":[["AI와 함께 만드는 프로그램","참가자들은 AI에 아이디어를 설명하고 생성된 코드를 수정하며 간단한 Python 게임을 제작했습니다. 복잡한 문법 지식이 없어도 결과물을 구현하는 방식을 경험했습니다."],["데이터 분석으로 확장하는 AI 활용","기초 게임 제작 외에도 데이터를 살펴보는 실습을 진행해 생성형 AI를 창작과 분석 도구로 활용하는 방법을 소개했습니다."]]},{"id":"780387","slug":"dongmyeong-school-vibe-coding-2026","title":"동명중학교 학생 대상 AI 바이브코딩 체험","tag":"청소년 진로체험","date":"2026-07-16","lead":"동명중학교 학생들이 생성형 AI와 함께 게임을 설계하고 수정하는 실습을 진행했습니다.","sections":[["자연어로 아이디어를 코드로 구현","학생들은 자연어로 프로그램을 설명하는 바이브코딩 방식으로 테트리스, 스네이크 게임, 숫자 야구 게임 등 자신만의 프로젝트를 만들었습니다."],["오류 수정과 문제해결 경험","프로그램 실행 과정에서 발생한 문제를 찾고 AI와 대화하며 개선하는 활동을 통해 인공지능을 소프트웨어 개발의 협업 도구로 활용하는 경험을 쌓았습니다."]]},{"id":"777791","slug":"kt-researcher-career-lecture-2026","title":"KT 현직자 초청 빅데이터·SW 취업 특강","tag":"취업·진로","date":"2026-06-10","lead":"KT 미래네트워크연구소 김은도 책임연구원이 소프트웨어·데이터 분야 취업 전략을 소개했습니다.","sections":[["현직자가 설명하는 개발 직무","2026년 6월 10일 개최된 재학생 특강에서는 기업의 빅데이터·소프트웨어 관련 직무와 실무 역량 요구사항을 현직자의 관점에서 설명했습니다."],["입사지원 준비의 구체적인 방향","포트폴리오 구성, 입사지원 방법, 면접 준비 등 학생들이 취업을 준비하며 점검할 항목을 다뤘습니다."]]}]''')
PUBLISHED=datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")
def h(x):return escape(str(x),quote=True)

def mosaic(img):
    arr=cv2.cvtColor(np.asarray(img),cv2.COLOR_RGB2BGR)
    gray=cv2.cvtColor(arr,cv2.COLOR_BGR2GRAY)
    faces=[]
    for name in ("haarcascade_frontalface_default.xml","haarcascade_profileface.xml"):
        detector=cv2.CascadeClassifier(cv2.data.haarcascades+name)
        faces.extend(list(detector.detectMultiScale(gray,scaleFactor=1.08,minNeighbors=3,minSize=(24,24))))
    mirror=cv2.flip(gray,1)
    side=cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_profileface.xml")
    faces.extend([(gray.shape[1]-x-w,y,w,ht) for x,y,w,ht in side.detectMultiScale(mirror,scaleFactor=1.08,minNeighbors=3,minSize=(24,24))])
    for x,y,w,ht in faces:
        m=max(w,ht)//5;x0=max(0,x-m);y0=max(0,y-m);x1=min(arr.shape[1],x+w+m);y1=min(arr.shape[0],y+ht+m)
        region=arr[y0:y1,x0:x1]
        if region.size:
            tiles=cv2.resize(region,(max(1,(x1-x0)//26),max(1,(y1-y0)//26)),interpolation=cv2.INTER_AREA)
            arr[y0:y1,x0:x1]=cv2.resize(tiles,(x1-x0,y1-y0),interpolation=cv2.INTER_NEAREST)
    return Image.fromarray(cv2.cvtColor(arr,cv2.COLOR_BGR2RGB)),len(faces)

def post_html(p,imgs):
    title=h(p["title"]); lead=h(p["lead"]); slug=h(p["slug"]); date=h(p["date"])
    url=f"{SITE}/activities/{slug}/"; image=SITE+imgs[0] if imgs else SITE+"/assets/promo/og-department.png"
    schema={"@context":"https://schema.org","@type":"Article","headline":p["title"],"description":p["lead"],
      "image":image,"datePublished":PUBLISHED,"dateModified":PUBLISHED,"inLanguage":"ko-KR",
      "mainEntityOfPage":{"@type":"WebPage","@id":url},
      "author":{"@type":"Organization","name":"한국폴리텍대학 서울강서캠퍼스 빅데이터소프트웨어공학과"},
      "publisher":{"@type":"Organization","name":"한국폴리텍대학 서울강서캠퍼스 빅데이터소프트웨어공학과","url":SITE}}
    figures=''.join(f'<figure class="activity-feature-image official-figure"><img src="{h(src)}" alt="{title} 활동 사진 {i+1}" loading="lazy"><figcaption>학과 활동 기록 사진 {i+1} · 얼굴 감지 부분 모자이크 처리</figcaption></figure>' for i,src in enumerate(imgs))
    if figures:figures='<div class="official-post-gallery">'+figures+'</div>'
    paragraphs=''.join(f'<section><h2>{h(s[0])}</h2><p>{h(s[1])}</p></section>' for s in p["sections"])
    return f'''<!doctype html><html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="index, follow, max-image-preview:large"><meta name="description" content="{lead}">
<link rel="canonical" href="{url}"><meta property="og:type" content="article"><meta property="og:locale" content="ko_KR">
<meta property="og:site_name" content="빅데이터소프트웨어공학과"><meta property="og:title" content="{title} | 빅데이터소프트웨어공학과">
<meta property="og:description" content="{lead}"><meta property="og:url" content="{url}"><meta property="og:image" content="{h(image)}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{title} | 빅데이터소프트웨어공학과">
<meta name="twitter:description" content="{lead}"><meta name="twitter:image" content="{h(image)}">
<title>{title} | 빅데이터소프트웨어공학과</title><link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/activities.css"><script defer src="/script.js"></script>
<script type="application/ld+json">{json.dumps(schema,ensure_ascii=False)}</script></head>
<body class="activity-page"><a class="skip-link" href="#main">본문으로 바로가기</a>
<header class="site-header scrolled" id="top"><div class="container header-inner"><a class="brand" href="/"><span class="brand-mark" aria-hidden="true">AI</span><span><strong>빅데이터소프트웨어공학과</strong><small>한국폴리텍대학 서울강서캠퍼스</small></span></a>
<button class="menu-toggle" type="button" aria-label="메뉴 열기" aria-expanded="false"><span></span><span></span><span></span></button>
<nav class="main-nav" aria-label="주요 메뉴"><a href="/#major">학과소개</a><a href="/projects/">학생작품</a><a href="/activities/">학과활동</a><a href="/employment/">취업·성과</a><a href="/admission/2027/">입학안내</a><a class="nav-cta" href="https://open.kakao.com/o/gEd0JIad" target="_blank" rel="noopener noreferrer">입학상담 ↗</a></nav>
</div></header><main id="main"><section class="activity-hero activity-post-hero"><div class="container">
<p class="activity-breadcrumb"><a href="/">학과 홈</a> › <a href="/activities/">학과 활동</a> › {h(p["tag"])}</p>
<p class="activity-kicker">DEPARTMENT ACTIVITIES · {h(p["tag"])}</p><h1>{title}</h1><p class="activity-lead">{lead}</p>
<div class="activity-post-meta"><span>빅데이터소프트웨어공학과</span><span>공식 학과소식 원문 작성일 {date}</span></div></div></section>
<article class="container activity-article">{figures}<div class="activity-content">{paragraphs}
<div class="activity-cta"><div><small>AI · DATA · SOFTWARE</small><h2>현장의 경험이 프로젝트 실력으로</h2><p>학과 교육과 학생들의 작품을 살펴보세요.</p></div>
<div class="activity-cta-links"><a href="/projects/">학생 프로젝트 →</a><a href="/admission/2027/">2027 입학안내 →</a></div></div>
<nav class="activity-post-nav" aria-label="학과 활동 글 이동"><a href="/activities/">← 학과 활동 전체보기</a></nav></div></article></main>
<footer class="article-footer activity-footer"><div class="container"><strong>빅데이터소프트웨어공학과</strong><span>한국폴리텍대학 서울강서캠퍼스</span><a href="/privacy.html">개인정보·분석 안내</a></div></footer></body></html>'''

def card(p,imgs):
    title=h(p["title"]);slug=h(p["slug"]);date=h(p["date"])
    if imgs: visual=f'<img src="{h(imgs[0])}" alt="{title} 활동 사진(자동 얼굴 모자이크 적용)" loading="lazy">'
    else:visual=f'<span class="official-post-poster" aria-hidden="true"><span>POLYTECH · {h(p["tag"])}</span><strong>{title}</strong></span>'
    return f'<article class="activity-card"><a class="activity-image-link" href="/activities/{slug}/" aria-label="{title} 자세히 보기">{visual}</a><div class="activity-card-body"><div class="activity-card-meta"><span>{h(p["tag"])}</span><time datetime="{date}">{date.replace("-",".")} 원문</time></div><h3><a href="/activities/{slug}/">{title}</a></h3><p>{h(p["lead"])}</p><a class="activity-read-more" href="/activities/{slug}/">활동 자세히 보기 →</a></div></article>'

session=requests.Session()
session.headers.update({"User-Agent":"Mozilla/5.0","Referer":BOARD})
records=[]
for p in POSTS:
    seq=p["id"]
    response=session.post(f"{BOARD}&mode=view&post={seq}",data={"pageIndex":"1"},timeout=45)
    response.raise_for_status()
    soup=BeautifulSoup(response.text,"html.parser")
    detail=soup.select_one("table.tbl_view")
    if not detail or not detail.select_one("td.txt_area"):raise RuntimeError(f"Detail missing for {seq}")
    text=detail.select_one("td.txt_area").get_text(" ",strip=True)
    if len(text)<55:raise RuntimeError(f"Article too short: {seq}")
    images=[]
    if not p.get("existing"):
        links=list(dict.fromkeys(urljoin(BASE,t["src"]) for t in detail.select('img[src*="kopoImg.do"]')))
        for i,src in enumerate(links):
            rsp=session.get(src,timeout=90);rsp.raise_for_status()
            original=Image.open(io.BytesIO(rsp.content))
            original=ImageOps.exif_transpose(original).convert("RGB")
            original.thumbnail((1440,1440),Image.Resampling.LANCZOS)
            edited,number=mosaic(original)
            path=f"assets/activities/official-board/{seq}-{i+1}.jpg"
            target=ROOT/path;target.parent.mkdir(parents=True,exist_ok=True)
            edited.save(target,"JPEG",quality=85,progressive=True,optimize=True)
            images.append("/"+path)
            print("PHOTO",seq,i+1,len(links),"face_rectangles",number,flush=True)
        path=ROOT/"activities"/p["slug"]/"index.html"
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(post_html(p,images),encoding="utf-8")
    records.append((p,images))
    print("SOURCE VERIFIED",seq,len(text),"characters",len(images),"photos",flush=True)

archive=ROOT/"activities"/"index.html"
content=archive.read_text(encoding="utf-8")
start="<!-- OFFICIAL_FIRST_PAGE_START -->";end="<!-- OFFICIAL_FIRST_PAGE_END -->"
block=start+"\n"+"\n".join(card(p,imgs) for p,imgs in records if not p.get("existing"))+"\n"+end
if start in content:
    content=re.sub(re.escape(start)+r".*?"+re.escape(end),lambda _:block,content,flags=re.S)
else:
    marker='<div class="activity-card-grid">'
    if content.count(marker)!=1:raise RuntimeError("Archive layout changed")
    content=content.replace(marker,marker+"\n"+block,1)
def schema_update(m):
    raw=json.loads(m.group(1))
    if raw.get("@type")!="CollectionPage":return m.group(0)
    seq=[p for p,_ in records]+[{"title":"소셜데이터로 읽는 미래직업, 진로체험 부스 운영","slug":"social-data-career-trends"}]
    raw["mainEntity"]={"@type":"ItemList","itemListElement":[{"@type":"ListItem","position":n+1,"name":p["title"],"url":SITE+"/activities/"+p["slug"]+"/"} for n,p in enumerate(seq)]}
    return '<script type="application/ld+json">'+json.dumps(raw,ensure_ascii=False,separators=(",",":"))+'</script>'
content=re.sub(r'<script type="application/ld\+json">(.*?)</script>',schema_update,content,flags=re.S)
content=content.replace('학과 활동 소식</h2></div><span>2026</span>','학과 활동 소식</h2></div><span>2025–2026</span>')
archive.write_text(content,encoding="utf-8")
csspath=ROOT/"activities.css";css=csspath.read_text(encoding="utf-8")
if "/* official-board styles */" not in css:
    css+='\n/* official-board styles */\n.official-post-poster{box-sizing:border-box;display:flex;flex-direction:column;justify-content:space-between;height:100%;padding:2rem;background:linear-gradient(125deg,#071a33,#27639a);color:white}.official-post-poster span{font-size:.72rem;letter-spacing:.13em;color:#d7f9b7;font-weight:800}.official-post-poster strong{font-size:clamp(1.35rem,2.8vw,2rem);line-height:1.48;word-break:keep-all}.official-post-gallery{display:grid;gap:1.2rem}.official-post-gallery .official-figure{margin:0}.official-post-gallery .official-figure:first-child{margin-top:-1.5rem}.official-post-gallery img{max-height:750px;object-fit:contain;background:#e8edf3}\n'
    csspath.write_text(css,encoding="utf-8")
build=ROOT/"tools"/"build_site.py";txt=build.read_text(encoding="utf-8")
anchor='    ("activities/social-data-career-trends/", "activities/social-data-career-trends/index.html"),'
if anchor not in txt:raise RuntimeError("Build anchor not found")
extra=''.join(f'    ("activities/{p["slug"]}/", "activities/{p["slug"]}/index.html"),\n' for p,_ in records if not p.get("existing") and f'("activities/{p["slug"]}/"' not in txt)
build.write_text(txt.replace(anchor,extra+anchor,1),encoding="utf-8")
print("COMPLETED",len(records),"official posts including existing duplicate; images",sum(len(z) for _,z in records))
