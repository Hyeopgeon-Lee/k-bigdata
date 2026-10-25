#!/usr/bin/env python3
"""One-time, source-verified import of KOPO board pages 2 through 5."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
from html import escape
from urllib.parse import urljoin
import io,json,re,sys
import requests
from bs4 import BeautifulSoup
import cv2
import numpy as np
from PIL import Image,ImageOps

ROOT=Path(__file__).resolve().parents[1]
BOARD="https://www.kopo.ac.kr/kangseo/board.do?menu=1550"
BASE="https://www.kopo.ac.kr"
SITE="https://ai.k-bigdata.kr"
PUBLISHED=datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")
EXPECTED=json.loads(r'''{"2":["777680","776799","775379","775378","773576","773180","770073","770067","765955","765578"],"3":["765207","764159","764079","763327","762843","762738","762734","762378","762213","762210"],"4":["761430","761428","759557","758416","758194","757516","753631","753629","753627","753243"],"5":["753242","752596","752594","750981","750383","750362","750361","750066","749927","749925"]}''')
LEADS=json.loads(r'''{"749925":"KB굿잡 취업박람회에서 학과가 소셜 빅데이터 분석 체험 부스를 운영했습니다.","749927":"2학년 학생들이 KB굿잡 취업박람회에 참여해 기업 채용정보와 면접·이력서 준비 방법을 점검했습니다.","750066":"2학년 선배들이 Rocky Linux 9·MariaDB·IntelliJ 개발환경 구축을 1학년 후배에게 멘토링했습니다.","750361":"경력단절여성 대상 방과후컴퓨터·코딩지도사 교육과정 수료식을 개최했습니다.","750362":"방과후컴퓨터·코딩지도사 과정 수료식 이후 교육생과 학과 관계자가 간담회를 진행했습니다.","750383":"이협건·김영운 교수가 Emscripten 기반 WebAssembly와 OpenCV 최적화 관련 연구를 발표했습니다.","750981":"2학년 선배가 1학년 후배에게 Spring Boot와 MariaDB 연동 개발을 지도하는 멘토링을 진행했습니다.","752594":"2학년 학생들이 AI 전문가·현직 개발자·인사담당자의 실무형 진로·취업 교육에 참여했습니다.","752596":"2학년 선배들이 1학년 후배들에게 Spring Boot·MyBatis·MariaDB를 활용한 웹 개발 실습을 지도했습니다.","753242":"이협건 교수가 ICIECT 2025에서 WasmEdge 기반 경량 LLM API 서버 설계·구현 연구를 발표했습니다.","753243":"김영운 교수가 ICIECT 2025에서 지능형 소프트웨어 로봇을 활용한 데이터 분석 자동화 연구를 발표했습니다.","753627":"고등학교 교사가 Python·생성형 AI·Cursor 기반 코딩을 직접 익히는 실습 연수를 운영했습니다.","753629":"고등학교 교사를 대상으로 R·RStudio 기반 데이터 분석과 시각화 연수를 진행했습니다.","753631":"지역 고등학생들이 4주간 Python 기반 인공지능 프로그래밍을 배우고 진로를 체험하는 교육을 운영했습니다.","757516":"오케스트로와 K-PaaS, AI, 클라우드 실무인재 양성을 위한 업무협약을 체결했습니다.","758194":"학과 학생들이 전남 공공·빅데이터 공모전에서 장려상을 수상하고 상금 150만 원을 받았습니다.","758416":"대한민국의 AX 전환과 소버린 클라우드 네이티브 전략을 주제로 산업계 기술 특강을 진행했습니다.","759557":"시스원 손병홍 이사가 AX 시대의 IT 기술 동향과 산업계가 기대하는 인재상을 주제로 특강했습니다.","761428":"제12회 Dream Job 행사에서 소셜 빅데이터를 활용한 진로체험 프로그램을 운영했습니다.","761430":"제8회 학부모 진로 Job에서 학부모와 학생이 AI·빅데이터 기술과 미래 진로를 함께 탐색했습니다.","762210":"학과 학생들이 프로젝트경진대회에서 우수상과 장려상을 수상했습니다.","762213":"강서양천교육지원청과 연계해 고등학생이 직접 참여하는 인공지능 실습 교육을 운영했습니다.","762378":"강서양천교육지원청과 연계해 고등학생 대상 빅데이터 분석 실습 교육을 진행했습니다.","762734":"2025 서울시 일자리박람회 현장을 방문해 학생들의 기업 직무 탐색과 채용 정보 파악을 지원했습니다.","762738":"2025 서울시 일자리박람회에서 SNS 데이터를 활용한 AI 인사이트랩 체험 부스를 운영했습니다.","762843":"산학 공동연구 성과가 한국정보전자통신기술학회 논문지에 게재됐습니다.","763327":"2학년 김태승 학생이 2025 ACK 논문경진대회에서 비전언어모델 기반 얼굴 초해상도 연구로 동상을 수상했습니다.","764079":"AI 산업 트렌드와 채용 현장에서 요구하는 실무역량, 이력서·자기소개서 준비를 주제로 취업 특강을 진행했습니다.","764159":"학생팀이 2025 한이음 드림업 공모전 창의도전형에서 장려상을 수상했습니다.","765207":"졸업생 선배가 멘토·멘티 데이에 참여해 진로 선택과 대학원 진학, 일과 학업 병행 경험을 전했습니다.","765578":"학과 1·2학년 학생팀이 새싹 해커톤 본선에 진출해 AI 기반 서비스 기획·구현 역량을 선보였습니다.","765955":"이협건 교수가 EBS·강서양천교육지원청 학습전략설명회에서 AI·빅데이터 관련 진로 탐색 특강을 진행했습니다.","770067":"9기 졸업생 김태승 강사가 LangChain·LangGraph·LangSmith 기반 AI 에이전트 설계와 워크플로를 소개했습니다.","770073":"김영운 교수가 에이전시프로를 대상으로 Python·OpenCV 기반 영상처리 기술지도를 실시했습니다.","773180":"학생들이 SQL 문제를 직접 해결하고 풀이 과정을 검토하며 실전 질의 작성 역량을 강화했습니다.","773576":"엔씨소프트 계열 엔씨IDS에 재직 중인 졸업생 이재훈 선배가 학생들에게 학습·프로젝트·취업 경험을 공유했습니다.","775378":"2026 KB 취업박람회에서 학과가 소셜데이터와 AI를 활용한 트렌드 분석 체험 부스를 운영했습니다.","775379":"2학년 학생들이 2026 KB 취업박람회를 방문해 기업 채용정보와 직무역량을 살펴보고 취업 방향을 점검했습니다.","776799":"2026년 서울강서캠퍼스 명랑운동회에서 학과 학생들이 피구와 줄다리기 두 종목 모두 1위를 기록했습니다.","777680":"효성ITX 이주현 팀장이 기업이 주목하는 IT 기술과 신입 개발자에게 필요한 문제해결·협업 역량을 소개했습니다."}''')
MANUAL_FACE_REGIONS={}
def h(x):return escape(str(x),quote=True)

def mosaic(img,key):
    arr=cv2.cvtColor(np.asarray(img),cv2.COLOR_RGB2BGR)
    gray=cv2.cvtColor(arr,cv2.COLOR_BGR2GRAY)
    faces=[]
    for name in ("haarcascade_frontalface_default.xml","haarcascade_profileface.xml"):
        detector=cv2.CascadeClassifier(cv2.data.haarcascades+name)
        faces.extend(list(detector.detectMultiScale(gray,scaleFactor=1.08,minNeighbors=3,minSize=(24,24))))
    mirror=cv2.flip(gray,1)
    side=cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_profileface.xml")
    faces.extend([(gray.shape[1]-x-w,y,w,ht) for x,y,w,ht in side.detectMultiScale(mirror,scaleFactor=1.08,minNeighbors=3,minSize=(24,24))])
    for left,top,right,bottom in MANUAL_FACE_REGIONS.get(key,[]):
        faces.append((int(left*arr.shape[1]),int(top*arr.shape[0]),int((right-left)*arr.shape[1]),int((bottom-top)*arr.shape[0])))
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


def cleaned(text):
    text=re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]"," ",text)
    text=re.sub(r"\s*#[\w가-힣]+"," ",text)
    text=re.sub(r"\s+"," ",text).strip()
    # Avoid re-publishing obsolete applicant deadlines in archived news.
    text=re.split(r"(?:현재|지금)\s+수시\s*[12]\s*차",text,maxsplit=1)[0].strip()
    return text

def chunks(text):
    txt=cleaned(text)
    if len(txt)<90:raise ValueError("Source text too short")
    # Present source excerpts as concise archival highlights rather than full duplicates.
    sentences=re.split(r'(?<=[.!?。])\s+',txt)
    usable=[s.strip() for s in sentences if len(s.strip())>5]
    out=[];current=""
    for s in usable:
        if len(current)+len(s)+1>370 and len(current)>=180:
            out.append(current.strip());current=""
            if len(out)>=2:break
        current+=((" " if current else "")+s)
    if len(out)<2 and current:out.append(current.strip())
    if len(out)==1 and len(out[0])>500:
        t=out[0];a=t.rfind(" ",200,360)
        if a<0:a=340
        out=[t[:a].strip(),t[a:].strip()]
    if len(out)==1:out.append("이번 활동은 학교에서 학습한 기술과 실제 현장의 경험을 연결하는 학과 프로그램으로 운영되었습니다.")
    return out[0][:520],out[1][:520]

def tag_for(title):
    if "수상" in title or "1등" in title: return "수상·성과"
    if "논문" in title: return "연구·논문"
    if "MOU" in title or "산학협력" in title or "기술지도" in title or "자문" in title:return "산학협력"
    if "멘토" in title or "선배" in title or "졸업생" in title:return "멘토링·진로"
    if "취업" in title:return "취업·진로"
    if "고등" in title or "학부모" in title or "진로체험" in title:return "진로체험"
    if "연수" in title:return "교원 연수"
    if "특강" in title or "강연" in title:return "전문가 특강"
    return "학과 활동"

def normalized_title(title):
    title=re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]","",title)
    title=re.sub(r"^\s*\[[^\]]{2,22}\]\s*","",title)
    title=re.sub(r"\s+"," ",title).strip(" -·!🎉")
    return title

def get_yunet():
    target=Path("/tmp/yunet-2023mar.onnx")
    sources=[
      "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
      "https://raw.githubusercontent.com/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
    ]
    for u in sources:
      try:
        response=requests.get(u,timeout=18)
        if response.ok and len(response.content)>45000 and not response.content.startswith(b'version https'):
          target.write_bytes(response.content)
          d=cv2.FaceDetectorYN.create(str(target),"",(320,320),score_threshold=0.65,nms_threshold=0.3)
          print("YUNET_READY",len(response.content),flush=True)
          return d
      except Exception as e:print("YUNET_UNAVAILABLE",str(e)[:150],flush=True)
    return None

def enhanced_mosaic(image,key,detector):
    edited,haar_count=mosaic(image,key)
    extra=0
    if detector is not None:
      try:
        w,ht=image.size
        bgr=cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR)
        detector.setInputSize((w,ht))
        _,faces=detector.detect(bgr)
        if faces is not None:
          arr=np.asarray(edited).copy()
          for item in faces:
            x,y,fw,fh=[int(v) for v in item[:4]]
            pad=int(max(fw,fh)*0.25)
            x0=max(0,x-pad);y0=max(0,y-pad);x1=min(w,x+fw+pad);y1=min(ht,y+fh+pad)
            roi=arr[y0:y1,x0:x1]
            if roi.size:
              pix=cv2.resize(roi,(max(1,(x1-x0)//32),max(1,(y1-y0)//32)),interpolation=cv2.INTER_AREA)
              arr[y0:y1,x0:x1]=cv2.resize(pix,(x1-x0,y1-y0),interpolation=cv2.INTER_NEAREST)
              extra+=1
          edited=Image.fromarray(arr)
      except Exception as e:print("YUNET_IMAGE_WARNING",key,str(e)[:150],flush=True)
    return edited,haar_count+extra

def main():
    session=requests.Session()
    session.headers.update({"User-Agent":"Mozilla/5.0 (compatible; department archive migration)","Referer":BOARD})
    first=session.get(BOARD,timeout=40);first.raise_for_status()
    soup=BeautifulSoup(first.text,"html.parser")
    form=soup.find("form",{"name":"listfrm"})
    if form is None:raise RuntimeError("Source board form not found")
    form_data={tag.get("name"):tag.get("value","") for tag in form.select("input[name]")}
    indexed=[]
    for page,ids in EXPECTED.items():
       rsp=session.post(BOARD,data={**form_data,"pageIndex":str(page)},timeout=45);rsp.raise_for_status()
       doc=BeautifulSoup(rsp.text,"html.parser")
       rows=[]
       for row in doc.select("table.tbl_list tbody tr"):
           a=row.select_one("a[onclick*=fn_board_detail]")
           if a is None:continue
           match=re.search(r"fn_board_detail\('([^']+)'\)",a.get("onclick",""))
           if not match:continue
           date=row.select("td")[-1].get_text(" ",strip=True)
           rows.append((match.group(1),a.get_text(" ",strip=True),date))
       if [x[0] for x in rows]!=ids:
           raise RuntimeError(f"Page {page} changed or has missing entries: {[x[0] for x in rows]} vs {ids}")
       indexed.extend((int(page),*entry) for entry in rows)
    if len(indexed)!=40 or len(set(x[1] for x in indexed))!=40:
      raise RuntimeError("Expected exactly forty unique source posts")
    detector=get_yunet()
    imported=[];totalphotos=0
    for page,seq,title,date in indexed:
       source=session.post(f"{BOARD}&mode=view&post={seq}",data={"pageIndex":str(page)},timeout=60)
       source.raise_for_status()
       doc=BeautifulSoup(source.text,"html.parser")
       table=doc.select_one("table.tbl_view")
       body=table.select_one("td.txt_area") if table else None
       if not table or not body:raise RuntimeError(f"Missing detail for {seq}")
       text=body.get_text(" ",strip=True)
       if len(text)<95:raise RuntimeError(f"Unexpectedly short source body {seq}")
       a,b=chunks(text)
       title=normalized_title(title)
       p={"id":seq,"slug":f"kopo-{seq}","title":title,"lead":LEADS[seq],
          "tag":tag_for(title),"date":date,
          "sections":[("학과 활동 개요",a),("주요 내용",b)]}
       links=list(dict.fromkeys(urljoin(BASE,tag["src"]) for tag in table.select('img[src*="kopoImg.do"]')))
       images=[]
       for i,url in enumerate(links):
          raw=session.get(url,timeout=70);raw.raise_for_status()
          orig=Image.open(io.BytesIO(raw.content))
          orig=ImageOps.exif_transpose(orig).convert("RGB")
          orig.thumbnail((1280,1280),Image.Resampling.LANCZOS)
          img,faces=enhanced_mosaic(orig,f"{seq}-{i+1}",detector)
          folder=ROOT/"assets"/"activities"/"official-board"
          folder.mkdir(parents=True,exist_ok=True)
          local=folder/f"{seq}-{i+1}.jpg"
          img.save(local,"JPEG",quality=82,optimize=True,progressive=True)
          images.append("/"+local.relative_to(ROOT).as_posix())
          totalphotos+=1
          print("IMAGE",seq,i+1,faces,local.stat().st_size,flush=True)
       dest=ROOT/"activities"/p["slug"]/"index.html"
       dest.parent.mkdir(parents=True,exist_ok=True)
       dest.write_text(post_html(p,images),encoding="utf-8")
       imported.append((p,images))
       print("IMPORTED",page,seq,"photos",len(images),"bodychars",len(text),"title",title,flush=True)
    if totalphotos!=57:raise RuntimeError(f"Expected 57 official pictures, found {totalphotos}")

    index=ROOT/"activities"/"index.html"
    html=index.read_text(encoding="utf-8")
    start="<!-- KOPO_PAGES_2_5_START -->";end="<!-- KOPO_PAGES_2_5_END -->"
    region=start+"\n"+"\n".join(card(p,images) for p,images in imported)+"\n"+end
    if start in html and end in html:
      html=re.sub(re.escape(start)+r".*?"+re.escape(end),lambda _:region,html,flags=re.S)
    else:
      anchor='</div></div></section>\n</main>'
      if html.count(anchor)!=1:raise RuntimeError("Archive grid marker changed")
      html=html.replace(anchor,region+"\n"+anchor,1)
    def schema_replace(match):
      data=json.loads(match.group(1))
      if data.get("@type")!="CollectionPage":return match.group(0)
      array=data["mainEntity"]["itemListElement"]
      found={x["url"] for x in array}
      for p,_ in imported:
         url=f"{SITE}/activities/{p['slug']}/"
         if url not in found:
           array.append({"@type":"ListItem","position":len(array)+1,"name":p["title"],"url":url})
           found.add(url)
      return '<script type="application/ld+json">'+json.dumps(data,ensure_ascii=False,separators=(",",":"))+'</script>'
    html=re.sub(r'<script type="application/ld\+json">(.*?)</script>',schema_replace,html,flags=re.S)
    if '/activity-pagination.js' not in html:
      anchor='<script defer src="/script.js"></script>'
      if anchor not in html:raise RuntimeError("Archive script marker missing")
      html=html.replace(anchor,anchor+'<script defer src="/activity-pagination.js"></script>',1)
    index.write_text(html,encoding="utf-8")
    build=ROOT/"tools"/"build_site.py"
    code=build.read_text(encoding="utf-8")
    marker='    ("activities/social-data-career-trends/", "activities/social-data-career-trends/index.html"),'
    if marker not in code:raise RuntimeError("Sitemap builder anchor missing")
    additions="".join(f'    ("activities/{p["slug"]}/", "activities/{p["slug"]}/index.html"),\n' for p,_ in imported if f'("activities/{p["slug"]}/"' not in code)
    build.write_text(code.replace(marker,additions+marker,1),encoding="utf-8")
    print("ARCHIVE_COMPLETED",len(imported),"posts",totalphotos,"images",flush=True)
if __name__=="__main__":
    main()
